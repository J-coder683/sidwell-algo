"""
test_engine_terminal.py — TDD tests for sidwell.engine.terminal.TerminalEngine

All expected values are independently hand-derived.

Gordon Growth:  TV_gordon = FCF_n * (1+g) / (WACC - g)
Exit Multiple:  TV_exit   = EBITDA_n * EV/EBITDA_mult
Average:        avg_TV    = (TV_gordon + TV_exit) / 2
"""

import pytest
from sidwell.ajp.schema import AJP, AJPMeta, AJPAssumption
from sidwell.engine.terminal import TerminalEngine


def _make_ajp(assumptions: list[dict]) -> AJP:
    meta = AJPMeta(
        ticker="TEST", as_of="2025-03-31", currency="INR",
        sources_ingested=[], fiscal_year_end_month=3,
        last_actual_fy="FY2025", is_holdco=False, scenario_active="BASE",
    )
    parsed = [
        AJPAssumption(
            driver_id=a["driver_id"], value=a["value"], unit="pct",
            source_type="TEST", confidence="HIGH",
            rationale="test", interrogation_refs=[],
        )
        for a in assumptions
    ]
    return AJP(meta=meta, assumptions=parsed)


def _make_proj(ufcf_last: float, ebit_last: float, da_last: float) -> dict:
    """Minimal proj dict — engine only reads the last element of each list."""
    return {
        "ufcf": [ufcf_last],
        "ebit": [ebit_last],
        "da": [da_last],
    }


# ---------------------------------------------------------------------------
# Test 1: Gordon growth TV — baseline
#
# FCF_n = 1000, g = 3%, WACC = 10%
# TV_gordon = 1000 * 1.03 / (0.10 - 0.03) = 1030 / 0.07 = 14,714.285...
# ---------------------------------------------------------------------------
def test_gordon_growth_baseline():
    proj = _make_proj(ufcf_last=1000.0, ebit_last=500.0, da_last=100.0)
    ajp = _make_ajp([
        {"driver_id": "terminal_growth", "value": 0.03},
        {"driver_id": "exit_ev_ebitda_multiple", "value": 10.0},
    ])
    res = TerminalEngine.calculate(proj, wacc=0.10, ajp=ajp)

    expected_gordon = 1000.0 * 1.03 / (0.10 - 0.03)
    assert abs(res["gordon_tv"] - expected_gordon) < 1e-3


# ---------------------------------------------------------------------------
# Test 2: Exit-multiple TV
#
# EBITDA_n = EBIT + DA = 500 + 100 = 600
# multiple = 10x
# TV_exit = 600 * 10 = 6000
# ---------------------------------------------------------------------------
def test_exit_multiple():
    proj = _make_proj(ufcf_last=1000.0, ebit_last=500.0, da_last=100.0)
    ajp = _make_ajp([
        {"driver_id": "terminal_growth", "value": 0.03},
        {"driver_id": "exit_ev_ebitda_multiple", "value": 10.0},
    ])
    res = TerminalEngine.calculate(proj, wacc=0.10, ajp=ajp)

    expected_ebitda = 500.0 + 100.0   # 600
    expected_exit = expected_ebitda * 10.0  # 6000
    assert abs(res["multiple_tv"] - expected_exit) < 1e-9


# ---------------------------------------------------------------------------
# Test 3: Averaging — avg_TV is the arithmetic mean
# ---------------------------------------------------------------------------
def test_averaging_is_arithmetic_mean():
    proj = _make_proj(ufcf_last=1000.0, ebit_last=500.0, da_last=100.0)
    ajp = _make_ajp([
        {"driver_id": "terminal_growth", "value": 0.03},
        {"driver_id": "exit_ev_ebitda_multiple", "value": 10.0},
    ])
    res = TerminalEngine.calculate(proj, wacc=0.10, ajp=ajp)

    expected_avg = (res["gordon_tv"] + res["multiple_tv"]) / 2.0
    assert abs(res["avg_tv"] - expected_avg) < 1e-9


# ---------------------------------------------------------------------------
# Test 4: WACC == g boundary → Gordon TV should be 0 (engine guard)
# ---------------------------------------------------------------------------
def test_wacc_equals_g_returns_zero_gordon():
    proj = _make_proj(ufcf_last=1000.0, ebit_last=500.0, da_last=100.0)
    ajp = _make_ajp([
        {"driver_id": "terminal_growth", "value": 0.10},   # same as WACC
        {"driver_id": "exit_ev_ebitda_multiple", "value": 8.0},
    ])
    res = TerminalEngine.calculate(proj, wacc=0.10, ajp=ajp)

    # Division by zero guard: gordon_tv must be 0, not inf or NaN
    assert res["gordon_tv"] == 0.0


# ---------------------------------------------------------------------------
# Test 5: Higher multiple raises TV_exit proportionally
#
# EBITDA = 600.  TV_exit(mult=12) = 7200, TV_exit(mult=6) = 3600
# ratio = 7200/3600 = 2.0 (proportional to multiple ratio 12/6)
# ---------------------------------------------------------------------------
def test_exit_multiple_proportional():
    proj = _make_proj(ufcf_last=1000.0, ebit_last=500.0, da_last=100.0)
    ajp_12x = _make_ajp([
        {"driver_id": "terminal_growth", "value": 0.03},
        {"driver_id": "exit_ev_ebitda_multiple", "value": 12.0},
    ])
    ajp_6x = _make_ajp([
        {"driver_id": "terminal_growth", "value": 0.03},
        {"driver_id": "exit_ev_ebitda_multiple", "value": 6.0},
    ])
    res_12 = TerminalEngine.calculate(proj, wacc=0.10, ajp=ajp_12x)
    res_6 = TerminalEngine.calculate(proj, wacc=0.10, ajp=ajp_6x)

    ratio = res_12["multiple_tv"] / res_6["multiple_tv"]
    assert abs(ratio - 2.0) < 1e-9


# ---------------------------------------------------------------------------
# Test 6: Terminal reinvestment row — Gordon TV decreases as g decreases
#
# FCF_n = 1000, WACC = 10%
# g=4%: TV = 1000*1.04/0.06 = 17333.3
# g=2%: TV = 1000*1.02/0.08 = 12750.0
# Monotonically decreasing as g falls from 4 → 2
# ---------------------------------------------------------------------------
def test_gordon_monotone_decreasing_as_g_falls():
    proj = _make_proj(ufcf_last=1000.0, ebit_last=200.0, da_last=50.0)
    results = []
    for g in [0.04, 0.03, 0.02]:
        ajp = _make_ajp([
            {"driver_id": "terminal_growth", "value": g},
            {"driver_id": "exit_ev_ebitda_multiple", "value": 10.0},
        ])
        res = TerminalEngine.calculate(proj, wacc=0.10, ajp=ajp)
        results.append(res["gordon_tv"])

    # g=4% > g=3% > g=2% → TV should strictly decrease
    assert results[0] > results[1] > results[2]

    # Spot check: g=4%
    expected_g4 = 1000.0 * 1.04 / (0.10 - 0.04)
    assert abs(results[0] - expected_g4) < 1e-3

    # Spot check: g=2%
    expected_g2 = 1000.0 * 1.02 / (0.10 - 0.02)
    assert abs(results[2] - expected_g2) < 1e-3
