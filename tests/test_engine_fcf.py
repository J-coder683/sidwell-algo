"""
test_engine_fcf.py — TDD tests for sidwell.engine.fcf.FCFEngine

All expected values are independently hand-derived.

Mid-year discounting: discount period for year i (0-indexed) = i + 0.5
  PV_i = FCF_i / (1+WACC)^(i+0.5)

Terminal value discounting: end-of-year n
  PV_TV = TV / (1+WACC)^n
"""

import math
import pytest
from sidwell.engine.fcf import FCFEngine


def _make_terminal(avg_tv: float) -> dict:
    return {"avg_tv": avg_tv}


# ---------------------------------------------------------------------------
# Test 1: Single-year FCF — mid-year period = 0.5
#
# FCF = [1000], WACC = 10%, TV = 5000
# PV_FCF_0 = 1000 / 1.10^0.5 = 1000 / 1.04881 = 953.46...
# PV_TV     = 5000 / 1.10^1  = 5000 / 1.10     = 4545.45...
# EV        = 953.46 + 4545.45 = 5498.91...
# ---------------------------------------------------------------------------
def test_single_year_mid_year_discount():
    proj = {"ufcf": [1000.0]}
    terminal = _make_terminal(avg_tv=5000.0)
    res = FCFEngine.calculate(proj, wacc=0.10, terminal=terminal)

    expected_pv0 = 1000.0 / (1.10 ** 0.5)
    expected_pv_tv = 5000.0 / (1.10 ** 1)
    expected_ev = expected_pv0 + expected_pv_tv

    assert abs(res["pv_ufcf_list"][0] - expected_pv0) < 1e-4
    assert abs(res["pv_tv"] - expected_pv_tv) < 1e-4
    assert abs(res["enterprise_value"] - expected_ev) < 1e-4


# ---------------------------------------------------------------------------
# Test 2: Three-year FCFs — mid-year periods 0.5, 1.5, 2.5
#
# FCFs = [100, 110, 121], WACC = 8%, TV = 2000
# PV_0 = 100 / 1.08^0.5 = 100 / 1.03923 = 96.225
# PV_1 = 110 / 1.08^1.5 = 110 / 1.12437 = 97.832
# PV_2 = 121 / 1.08^2.5 = 121 / 1.21432 = 99.644
# cum_pv = 96.225 + 97.832 + 99.644 = 293.701
# PV_TV  = 2000 / 1.08^3  = 2000 / 1.25971 = 1587.66
# EV = 293.701 + 1587.66 = 1881.36
# ---------------------------------------------------------------------------
def test_three_year_mid_year_periods():
    proj = {"ufcf": [100.0, 110.0, 121.0]}
    terminal = _make_terminal(avg_tv=2000.0)
    res = FCFEngine.calculate(proj, wacc=0.08, terminal=terminal)

    fcfs = [100.0, 110.0, 121.0]
    wacc = 0.08
    expected_pvs = [fcfs[i] / (1.08 ** (i + 0.5)) for i in range(3)]
    expected_cum = sum(expected_pvs)
    expected_pv_tv = 2000.0 / (1.08 ** 3)
    expected_ev = expected_cum + expected_pv_tv

    for i in range(3):
        assert abs(res["pv_ufcf_list"][i] - expected_pvs[i]) < 1e-3, f"PV mismatch at year {i}"

    assert abs(res["cum_pv_ufcf"] - expected_cum) < 1e-3
    assert abs(res["pv_tv"] - expected_pv_tv) < 1e-3
    assert abs(res["enterprise_value"] - expected_ev) < 1e-3


# ---------------------------------------------------------------------------
# Test 3: Discount factors list (end-of-year) are increasing powers of (1/1+WACC)
#
# discount_factor_list[i] = 1 / (1+WACC)^(i+1)  [note: end-of-year, not mid-year]
# This is separate from the mid-year PV computation; it drives the report table
# ---------------------------------------------------------------------------
def test_discount_factor_list_end_of_year():
    proj = {"ufcf": [100.0, 200.0, 300.0]}
    terminal = _make_terminal(avg_tv=1000.0)
    res = FCFEngine.calculate(proj, wacc=0.10, terminal=terminal)

    for i in range(3):
        expected_df = 1.0 / (1.10 ** (i + 1))
        assert abs(res["discount_factor_list"][i] - expected_df) < 1e-9, \
            f"Discount factor mismatch at index {i}"


# ---------------------------------------------------------------------------
# Test 4: Negative FCFs are discounted correctly (no special handling assumed)
# ---------------------------------------------------------------------------
def test_negative_fcf_discounted():
    proj = {"ufcf": [-500.0]}
    terminal = _make_terminal(avg_tv=10000.0)
    res = FCFEngine.calculate(proj, wacc=0.10, terminal=terminal)

    expected_pv = -500.0 / (1.10 ** 0.5)
    assert abs(res["pv_ufcf_list"][0] - expected_pv) < 1e-4
    # Enterprise value should still be > 0 if TV dominates
    assert res["enterprise_value"] > 0


# ---------------------------------------------------------------------------
# Test 5: Zero UFCF throughout — EV equals PV of terminal only
# ---------------------------------------------------------------------------
def test_zero_fcf_ev_equals_pv_tv():
    proj = {"ufcf": [0.0, 0.0, 0.0, 0.0, 0.0]}
    terminal = _make_terminal(avg_tv=8000.0)
    res = FCFEngine.calculate(proj, wacc=0.10, terminal=terminal)

    expected_pv_tv = 8000.0 / (1.10 ** 5)
    assert abs(res["cum_pv_ufcf"]) < 1e-9
    assert abs(res["pv_tv"] - expected_pv_tv) < 1e-4
    assert abs(res["enterprise_value"] - expected_pv_tv) < 1e-4


# ---------------------------------------------------------------------------
# Test 6: Ten-year standard case — verify period 9 has discount period 9.5
#
# WACC = 12%, FCF_9 = 200
# PV_9 = 200 / 1.12^9.5
# ---------------------------------------------------------------------------
def test_ten_year_last_period_is_9_5():
    fcfs = [100.0 * (1.08 ** i) for i in range(10)]
    proj = {"ufcf": fcfs}
    terminal = _make_terminal(avg_tv=5000.0)
    res = FCFEngine.calculate(proj, wacc=0.12, terminal=terminal)

    expected_pv9 = fcfs[9] / (1.12 ** 9.5)
    assert abs(res["pv_ufcf_list"][9] - expected_pv9) < 1e-3

    # TV discounted at end of year 10 (period 10)
    expected_pv_tv = 5000.0 / (1.12 ** 10)
    assert abs(res["pv_tv"] - expected_pv_tv) < 1e-3
