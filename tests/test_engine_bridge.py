"""
test_engine_bridge.py — TDD tests for sidwell.engine.bridge.BridgeEngine

Bridge formula (non-holdco):
  equity_core = EV + cash - debt - NCI - preferred + investments - pension + NOLs

Holdco SOTP path:
  equity = sum(seg.value_mm * seg.stake_pct) * (1 - holdco_discount)

All expected values are independently hand-derived.
"""

import pytest
from sidwell.ajp.schema import AJP, AJPMeta, AJPAssumption, AJPSegment
from sidwell.engine.bridge import BridgeEngine


def _make_meta(is_holdco: bool = False) -> AJPMeta:
    return AJPMeta(
        ticker="TEST", as_of="2025-03-31", currency="INR",
        sources_ingested=[], fiscal_year_end_month=3,
        last_actual_fy="FY2025", is_holdco=is_holdco, scenario_active="BASE",
    )


def _make_assumption(driver_id: str, value, **kwargs) -> AJPAssumption:
    return AJPAssumption(
        driver_id=driver_id, value=value, unit="mm",
        source_type="TEST", confidence="HIGH",
        rationale="test", interrogation_refs=[],
        **kwargs,
    )


def _make_ajp(assumptions: list, is_holdco: bool = False) -> AJP:
    return AJP(meta=_make_meta(is_holdco=is_holdco), assumptions=assumptions)


def _make_bs(
    cash: float = 0.0,
    borrowings: float = 0.0,
    leases: float = 0.0,
    nci: float = 0.0,
    investments: float = 0.0,
) -> dict:
    return {
        "cash_equivalents": [cash],
        "borrowings": [borrowings],
        "lease_liabilities": [leases],
        "non_controlling_int": [nci],
        "investments": [investments],
    }


# ---------------------------------------------------------------------------
# Test 1: Base case — all items zero except EV and cash
#
# EV=1000, cash=200, debt=0, NCI=0, preferred=0, investments=0, pension=0, NOLs=0
# equity = 1000 + 200 - 0 - 0 - 0 + 0 - 0 + 0 = 1200
# ---------------------------------------------------------------------------
def test_base_case_cash_only():
    bs = _make_bs(cash=200.0)
    ajp = _make_ajp([])
    res = BridgeEngine.calculate(ev=1000.0, hist_bs=bs, ajp=ajp)
    assert abs(res["equity_value"] - 1200.0) < 1e-9
    assert abs(res["cash"] - 200.0) < 1e-9
    assert res["is_holdco"] is False


# ---------------------------------------------------------------------------
# Test 2: Debt (borrowings + leases) reduces equity
#
# EV=1000, cash=300, borrowings=400, leases=100
# total_debt = 500
# equity = 1000 + 300 - 500 = 800
# ---------------------------------------------------------------------------
def test_debt_and_leases_reduce_equity():
    bs = _make_bs(cash=300.0, borrowings=400.0, leases=100.0)
    ajp = _make_ajp([])
    res = BridgeEngine.calculate(ev=1000.0, hist_bs=bs, ajp=ajp)
    assert abs(res["debt"] - 500.0) < 1e-9
    assert abs(res["equity_value"] - 800.0) < 1e-9


# ---------------------------------------------------------------------------
# Test 3: NCI subtracted, investments added
#
# EV=1000, cash=0, NCI=50, investments=80
# equity = 1000 + 0 - 0 - 50 + 80 = 1030
# ---------------------------------------------------------------------------
def test_nci_and_investments():
    bs = _make_bs(nci=50.0, investments=80.0)
    ajp = _make_ajp([])
    res = BridgeEngine.calculate(ev=1000.0, hist_bs=bs, ajp=ajp)
    assert abs(res["nci"] - 50.0) < 1e-9
    assert abs(res["investments"] - 80.0) < 1e-9
    assert abs(res["equity_value"] - 1030.0) < 1e-9


# ---------------------------------------------------------------------------
# Test 4: Preferred stock subtracted
#
# EV=2000, cash=100, preferred=200
# equity = 2000 + 100 - 200 = 1900
# ---------------------------------------------------------------------------
def test_preferred_stock_reduces_equity():
    bs = _make_bs(cash=100.0)
    ajp = _make_ajp([_make_assumption("preferred_stock", 200.0)])
    res = BridgeEngine.calculate(ev=2000.0, hist_bs=bs, ajp=ajp)
    assert abs(res["preferred"] - 200.0) < 1e-9
    assert abs(res["equity_value"] - 1900.0) < 1e-9


# ---------------------------------------------------------------------------
# Test 5: Unfunded pension reduces equity
#
# EV=1500, cash=0, pension=300
# equity = 1500 - 300 = 1200
# ---------------------------------------------------------------------------
def test_pension_reduces_equity():
    bs = _make_bs()
    ajp = _make_ajp([_make_assumption("unfunded_pension", 300.0)])
    res = BridgeEngine.calculate(ev=1500.0, hist_bs=bs, ajp=ajp)
    assert abs(res["pension"] - 300.0) < 1e-9
    assert abs(res["equity_value"] - 1200.0) < 1e-9


# ---------------------------------------------------------------------------
# Test 6: NOL tax shield adds to equity
#
# EV=1000, NOLs=150
# equity = 1000 + 150 = 1150
# ---------------------------------------------------------------------------
def test_nols_add_to_equity():
    bs = _make_bs()
    ajp = _make_ajp([_make_assumption("nols", 150.0)])
    res = BridgeEngine.calculate(ev=1000.0, hist_bs=bs, ajp=ajp)
    assert abs(res["nols"] - 150.0) < 1e-9
    assert abs(res["equity_value"] - 1150.0) < 1e-9


# ---------------------------------------------------------------------------
# Test 7: Full non-holdco bridge with all items
#
# EV=5000, cash=300, borrowings=800, leases=200, NCI=100, investments=250,
# preferred=150, pension=50, NOLs=200
# total_debt = 800 + 200 = 1000
# equity = 5000 + 300 - 1000 - 100 - 150 + 250 - 50 + 200 = 4450
# ---------------------------------------------------------------------------
def test_full_bridge_all_items():
    bs = _make_bs(cash=300.0, borrowings=800.0, leases=200.0, nci=100.0, investments=250.0)
    ajp = _make_ajp([
        _make_assumption("preferred_stock", 150.0),
        _make_assumption("unfunded_pension", 50.0),
        _make_assumption("nols", 200.0),
    ])
    res = BridgeEngine.calculate(ev=5000.0, hist_bs=bs, ajp=ajp)
    expected = 5000 + 300 - 1000 - 100 - 150 + 250 - 50 + 200
    assert abs(res["equity_value"] - expected) < 1e-9
    assert abs(res["equity_value_core"] - expected) < 1e-9


# ---------------------------------------------------------------------------
# Test 8: Holdco SOTP path — equity comes from segment sum * stakes
#
# Segments:
#   SegA: value_mm=10000, stake=0.51   → contribution = 5100
#   SegB: value_mm=4000,  stake=1.00   → contribution = 4000
# holdco_discount = 0.20
# SOTP = 5100 + 4000 = 9100
# equity_holdco = 9100 * (1-0.20) = 7280
# ---------------------------------------------------------------------------
def test_holdco_sotp_path():
    from sidwell.ajp.schema import AJPAssumption, AJPSegment

    seg_a = AJPSegment(name="SubsidiaryA", valuation_method="DCF", stake_pct=0.51, value_mm=10000.0)
    seg_b = AJPSegment(name="SubsidiaryB", valuation_method="market", stake_pct=1.00, value_mm=4000.0)

    segments_assumption = AJPAssumption(
        driver_id="segments",
        value=[],
        unit="mm",
        source_type="TEST",
        confidence="HIGH",
        rationale="test",
        interrogation_refs=[],
        segments=[seg_a, seg_b],
    )
    discount_assumption = _make_assumption("holdco_discount", 0.20)
    ajp = _make_ajp([segments_assumption, discount_assumption], is_holdco=True)

    bs = _make_bs(cash=500.0, borrowings=200.0)  # irrelevant in holdco path
    res = BridgeEngine.calculate(ev=10000.0, hist_bs=bs, ajp=ajp)

    expected_sotp = 10000.0 * 0.51 + 4000.0 * 1.0
    expected_equity = expected_sotp * (1 - 0.20)

    assert res["is_holdco"] is True
    assert abs(res["sotp_value"] - expected_sotp) < 1e-6
    assert abs(res["equity_value"] - expected_equity) < 1e-6
    # Core EV bridge should be ignored when is_holdco=True
    assert res["equity_value"] != res["equity_value_core"]


# ---------------------------------------------------------------------------
# Test 9: Holdco with zero discount
#
# discount=0 → equity = sotp_value
# ---------------------------------------------------------------------------
def test_holdco_zero_discount():
    from sidwell.ajp.schema import AJPAssumption, AJPSegment

    seg = AJPSegment(name="Sub", valuation_method="DCF", stake_pct=0.75, value_mm=8000.0)
    seg_assumption = AJPAssumption(
        driver_id="segments", value=[], unit="mm",
        source_type="TEST", confidence="HIGH", rationale="test",
        interrogation_refs=[], segments=[seg],
    )
    ajp = _make_ajp([seg_assumption, _make_assumption("holdco_discount", 0.0)], is_holdco=True)
    bs = _make_bs()
    res = BridgeEngine.calculate(ev=0.0, hist_bs=bs, ajp=ajp)

    expected_sotp = 8000.0 * 0.75
    assert abs(res["equity_value"] - expected_sotp) < 1e-6


# ---------------------------------------------------------------------------
# Test 10: L&T-like conglomerate with huge financial subsidiary debt
# 
# EV=5000, cash=500, borrowings=10000 (huge due to NBFC), leases=0
# Core EV bridge equity = 5000 + 500 - 10000 = -4500 (Crushed!)
# SOTP segments: Core (5000), NBFC sub (3000 * 1.0), IT sub (4000 * 0.7)
# Total SOTP = 5000 + 3000 + 2800 = 10800. Discount = 0.1
# Equity = 10800 * 0.9 = 9720
# ---------------------------------------------------------------------------
def test_lt_sotp_ignores_huge_debt():
    from sidwell.ajp.schema import AJPAssumption, AJPSegment
    
    seg_core = AJPSegment(name="Core", valuation_method="core", stake_pct=1.0, value_mm=5000.0)
    seg_nbfc = AJPSegment(name="NBFC", valuation_method="consol", stake_pct=1.0, value_mm=3000.0)
    seg_it = AJPSegment(name="IT_Sub", valuation_method="stake", stake_pct=0.7, value_mm=4000.0)
    
    seg_assump = AJPAssumption(
        driver_id="segments", value=[], unit="mm", source_type="TEST",
        confidence="HIGH", rationale="test", interrogation_refs=[],
        segments=[seg_core, seg_nbfc, seg_it]
    )
    ajp = _make_ajp([seg_assump, _make_assumption("holdco_discount", 0.1)], is_holdco=True)
    bs = _make_bs(cash=500.0, borrowings=10000.0)
    
    res = BridgeEngine.calculate(ev=5000.0, hist_bs=bs, ajp=ajp)
    
    assert res["sotp_used"] is True
    assert res["valuation_method"] == "SOTP"
    assert res["equity_value_core"] == -4500.0 # Proves standard bridge crushes it
    assert abs(res["sotp_value"] - 10800.0) < 1e-6
    assert abs(res["equity_value"] - 9720.0) < 1e-6
    assert res["valuation_caveat"] is None


# ---------------------------------------------------------------------------
# Test 11: Sanity fallback when SOTP total is implausibly low
# 
# EV=5000, core equity=5000. SOTP segments sum to 1000 (< 25% of 5000)
# Should fall back to EV bridge and flag caveat.
# ---------------------------------------------------------------------------
def test_sotp_sanity_fallback_implausible_value():
    from sidwell.ajp.schema import AJPAssumption, AJPSegment
    
    seg_partial = AJPSegment(name="Small_Sub", valuation_method="stake", stake_pct=0.5, value_mm=2000.0) # stake value 1000
    
    seg_assump = AJPAssumption(
        driver_id="segments", value=[], unit="mm", source_type="TEST",
        confidence="HIGH", rationale="test", interrogation_refs=[],
        segments=[seg_partial]
    )
    ajp = _make_ajp([seg_assump], is_holdco=True)
    bs = _make_bs()
    
    res = BridgeEngine.calculate(ev=5000.0, hist_bs=bs, ajp=ajp)
    
    assert res["sotp_used"] is False
    assert res["valuation_method"] == "EV_bridge"
    assert res["equity_value"] == res["equity_value_core"] # Fails back
    assert res["valuation_caveat"] is not None
    assert "implausibly low" in res["valuation_caveat"]


# ---------------------------------------------------------------------------
# Test 12: Heuristic flag for massive debt / financial sub
# ---------------------------------------------------------------------------
def test_heuristic_financial_sub_caveat():
    ajp = _make_ajp([], is_holdco=False)
    # EV=1000, debt=600 (>50% of EV), investments=150 (>10% of EV)
    bs = _make_bs(borrowings=600.0, investments=150.0)
    
    res = BridgeEngine.calculate(ev=1000.0, hist_bs=bs, ajp=ajp)
    
    assert res["sotp_used"] is False
    assert res["valuation_method"] == "EV_bridge"
    assert res["valuation_caveat"] is not None
    assert "Consolidated debt is very large" in res["valuation_caveat"]
