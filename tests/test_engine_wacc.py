"""
test_engine_wacc.py — TDD tests for sidwell.engine.wacc.WACCEngine

All expected values are independently hand-derived, NOT captured from the engine.
See calculation walkthrough in tests/expected_calculations.md.

Hamada formula reminder:
  βU = βL / (1 + (1 - t) * D/E)
  βL = βU * (1 + (1 - t) * D/E)
  Ke = Rf + βL * ERP
  WACC_current = We*Ke_current + Wd*Kd_after_tax
  WACC_target  = (1-d_cap)*Ke_target  + d_cap*Kd_after_tax
  avg_WACC = (WACC_current + WACC_target) / 2
"""

import math
import pytest
from sidwell.ajp.schema import AJP, AJPMeta, AJPAssumption
from sidwell.engine.wacc import WACCEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ajp(assumptions: list[dict]) -> AJP:
    """Minimal AJP fixture."""
    meta = AJPMeta(
        ticker="TEST",
        as_of="2025-03-31",
        currency="INR",
        sources_ingested=[],
        fiscal_year_end_month=3,
        last_actual_fy="FY2025",
        is_holdco=False,
        scenario_active="BASE",
    )
    parsed = []
    for a in assumptions:
        parsed.append(AJPAssumption(
            driver_id=a["driver_id"],
            value=a["value"],
            unit=a.get("unit", "pct"),
            source_type="TEST",
            confidence="HIGH",
            rationale=a.get("rationale", "test"),
            interrogation_refs=[],
        ))
    return AJP(meta=meta, assumptions=parsed)


def _minimal_fin(debt: float = 0.0, market_cap: float = 100.0) -> dict:
    return {"ticker": "TEST", "current_price": 10.0, "market_cap": market_cap, "debt": debt}


# ---------------------------------------------------------------------------
# Test 1: Pure equity company (D/E = 0) — Hamada reduces to identity
#
# Given: asset_beta = 0.8 (peer median), Rf = 5%, ERP = 6%, t = 25%
#        market_cap = 100, debt = 0
#        target_debt_to_cap = 0 → target D/E = 0
#        pretax_kd = 8% (not used if D=0)
#
# Current: D/E = 0/100 = 0
#   βL_current = 0.8 * (1 + 0.75*0) = 0.8
#   Ke_current = 0.05 + 0.8*0.06 = 0.098
#   WACC_current = 1.0*0.098 + 0.0*... = 0.098
#
# Target: target_d_cap = 0 → target D/E = 0
#   βL_target = 0.8, Ke_target = 0.098
#   WACC_target = 1.0*0.098 = 0.098
#
# avg_WACC = 0.098
# ---------------------------------------------------------------------------
def test_pure_equity_no_debt():
    peer_betas = [{"beta": 0.8, "debt": 0.0, "equity": 100.0}]
    ajp = _make_ajp([
        {"driver_id": "risk_free_rate", "value": 0.05},
        {"driver_id": "equity_risk_premium", "value": 0.06},
        {"driver_id": "country_risk_premium", "value": 0.00},
        {"driver_id": "tax_rate", "value": 0.25},
        {"driver_id": "peer_betas", "value": peer_betas},
        {"driver_id": "pretax_cost_of_debt_override", "value": 0.08},
        {"driver_id": "target_debt_to_cap", "value": 0.0},
    ])
    fin = _minimal_fin(debt=0.0, market_cap=100.0)
    res = WACCEngine.calculate(fin, ajp)

    # asset_beta = 0.8 / (1 + 0.75*0) = 0.8
    assert abs(res["median_asset_beta"] - 0.8) < 1e-9
    # βL = 0.8
    assert abs(res["current_levered_beta"] - 0.8) < 1e-9
    # Ke = 0.05 + 0.8*0.06 = 0.098
    assert abs(res["current_ke"] - 0.098) < 1e-9
    # WACC = 0.098
    assert abs(res["current_wacc"] - 0.098) < 1e-9
    assert abs(res["avg_wacc"] - 0.098) < 1e-9


# ---------------------------------------------------------------------------
# Test 2: Hamada unlever from levered peer beta
#
# Peer: βL = 1.2, debt = 40, equity = 60, t = 30%
#   D/E = 40/60 = 0.6667
#   βU = 1.2 / (1 + 0.7 * 0.6667) = 1.2 / 1.4667 = 0.81818...
#
# Current company: market_cap = 80, debt = 20, t = 30%
#   D/E = 20/80 = 0.25
#   βL_current = 0.81818 * (1 + 0.7*0.25) = 0.81818 * 1.175 = 0.96136
#   Rf = 4%, ERP = 5%
#   Ke_current = 0.04 + 0.96136*0.05 = 0.04 + 0.04807 = 0.08807
#   Kd_after_tax = 0.07 * (1-0.30) = 0.049
#   We = 80/100 = 0.80, Wd = 20/100 = 0.20
#   WACC_current = 0.80*0.08807 + 0.20*0.049 = 0.07046 + 0.0098 = 0.08026
#
# Target: d_cap = 0.30 → D/E_target = 0.30/0.70 = 0.4286
#   βL_target = 0.81818 * (1 + 0.7*0.4286) = 0.81818 * 1.30 = 1.06364
#   Ke_target = 0.04 + 1.06364*0.05 = 0.04 + 0.05318 = 0.09318
#   WACC_target = 0.70*0.09318 + 0.30*0.049 = 0.06523 + 0.01470 = 0.07993
#
# avg_WACC = (0.08026 + 0.07993)/2 = 0.08009 (5dp)
# ---------------------------------------------------------------------------
def test_hamada_unlever_relever():
    # Peer betas (single peer)
    peer_betas = [{"beta": 1.2, "debt": 40.0, "equity": 60.0}]
    ajp = _make_ajp([
        {"driver_id": "risk_free_rate", "value": 0.04},
        {"driver_id": "equity_risk_premium", "value": 0.05},
        {"driver_id": "country_risk_premium", "value": 0.00},
        {"driver_id": "tax_rate", "value": 0.30},
        {"driver_id": "peer_betas", "value": peer_betas},
        {"driver_id": "pretax_cost_of_debt_override", "value": 0.07},
        {"driver_id": "target_debt_to_cap", "value": 0.30},
    ])
    fin = _minimal_fin(debt=20.0, market_cap=80.0)
    res = WACCEngine.calculate(fin, ajp)

    # Unlevered beta
    expected_bu = 1.2 / (1 + 0.70 * (40.0 / 60.0))
    assert abs(res["median_asset_beta"] - expected_bu) < 1e-6

    # Current levered beta
    current_de = 20.0 / 80.0
    expected_bl_curr = expected_bu * (1 + 0.70 * current_de)
    assert abs(res["current_levered_beta"] - expected_bl_curr) < 1e-6

    # Target levered beta
    target_de = 0.30 / 0.70
    expected_bl_tgt = expected_bu * (1 + 0.70 * target_de)
    assert abs(res["target_levered_beta"] - expected_bl_tgt) < 1e-6

    # Ke current
    expected_ke_curr = 0.04 + expected_bl_curr * 0.05
    assert abs(res["current_ke"] - expected_ke_curr) < 1e-6

    # WACC current
    after_tax_kd = 0.07 * 0.70
    we = 80.0 / 100.0
    wd = 20.0 / 100.0
    expected_wacc_curr = we * expected_ke_curr + wd * after_tax_kd
    assert abs(res["current_wacc"] - expected_wacc_curr) < 1e-6

    # WACC target
    expected_ke_tgt = 0.04 + expected_bl_tgt * 0.05
    expected_wacc_tgt = 0.70 * expected_ke_tgt + 0.30 * after_tax_kd
    assert abs(res["target_wacc"] - expected_wacc_tgt) < 1e-6

    # avg_WACC
    expected_avg = (expected_wacc_curr + expected_wacc_tgt) / 2.0
    assert abs(res["avg_wacc"] - expected_avg) < 1e-6


# ---------------------------------------------------------------------------
# Test 3: Multiple peers — median unlever/relever
#
# Peers:
#   P1: βL=0.9, D=0, E=100  → βU = 0.9
#   P2: βL=1.5, D=50, E=50, t=25% → βU = 1.5/(1+0.75) = 1.5/1.75 = 0.857
#   P3: βL=1.2, D=30, E=70, t=25% → βU = 1.2/(1+0.75*30/70) = 1.2/1.3214 = 0.9079
#
# median([0.9, 0.857, 0.9079]) = 0.9 (middle value when sorted: 0.857, 0.9, 0.9079)
# ---------------------------------------------------------------------------
def test_multiple_peers_median_unlever():
    peer_betas = [
        {"beta": 0.9, "debt": 0.0, "equity": 100.0},
        {"beta": 1.5, "debt": 50.0, "equity": 50.0},
        {"beta": 1.2, "debt": 30.0, "equity": 70.0},
    ]
    ajp = _make_ajp([
        {"driver_id": "risk_free_rate", "value": 0.05},
        {"driver_id": "equity_risk_premium", "value": 0.05},
        {"driver_id": "country_risk_premium", "value": 0.00},
        {"driver_id": "tax_rate", "value": 0.25},
        {"driver_id": "peer_betas", "value": peer_betas},
        {"driver_id": "pretax_cost_of_debt_override", "value": 0.08},
        {"driver_id": "target_debt_to_cap", "value": 0.20},
    ])
    fin = _minimal_fin(debt=0.0, market_cap=100.0)
    res = WACCEngine.calculate(fin, ajp)

    bu_p1 = 0.9
    bu_p2 = 1.5 / (1 + 0.75 * (50.0 / 50.0))
    bu_p3 = 1.2 / (1 + 0.75 * (30.0 / 70.0))
    betas_sorted = sorted([bu_p1, bu_p2, bu_p3])
    median_bu = betas_sorted[1]  # three values: pick middle
    assert abs(res["median_asset_beta"] - median_bu) < 1e-6


# ---------------------------------------------------------------------------
# Test 4: Synthetic-rating Kd override is wired correctly
#
# If pretax_kd = 0.09 and t = 0.30 → after_tax_kd = 0.063
# ---------------------------------------------------------------------------
def test_synthetic_kd_after_tax():
    ajp = _make_ajp([
        {"driver_id": "risk_free_rate", "value": 0.05},
        {"driver_id": "equity_risk_premium", "value": 0.05},
        {"driver_id": "country_risk_premium", "value": 0.00},
        {"driver_id": "tax_rate", "value": 0.30},
        {"driver_id": "pretax_cost_of_debt_override", "value": 0.09},
        {"driver_id": "target_debt_to_cap", "value": 0.20},
    ])
    fin = _minimal_fin(debt=0.0, market_cap=100.0)
    res = WACCEngine.calculate(fin, ajp)

    assert abs(res["pretax_kd"] - 0.09) < 1e-9
    assert abs(res["after_tax_kd"] - 0.09 * 0.70) < 1e-9


# ---------------------------------------------------------------------------
# Test 5: No peers → fallback asset_beta = 1.0 (documented engine fallback)
# ---------------------------------------------------------------------------
def test_no_peers_fallback_asset_beta():
    ajp = _make_ajp([
        {"driver_id": "risk_free_rate", "value": 0.05},
        {"driver_id": "equity_risk_premium", "value": 0.05},
        {"driver_id": "country_risk_premium", "value": 0.00},
        {"driver_id": "tax_rate", "value": 0.25},
        {"driver_id": "pretax_cost_of_debt_override", "value": 0.08},
        {"driver_id": "target_debt_to_cap", "value": 0.20},
        # no peer_betas in AJP
    ])
    fin = _minimal_fin(debt=0.0, market_cap=100.0)
    res = WACCEngine.calculate(fin, ajp)
    # Documented fallback per engine code comment
    assert abs(res["median_asset_beta"] - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# Test 6: Country risk premium is additive to mature ERP
#
# Rf=5%, mature_ERP=5%, CRP=2% → total_erp=7%
# βL=1.0 → Ke = 5% + 1.0*7% = 12%
# ---------------------------------------------------------------------------
def test_country_risk_premium_adds_to_erp():
    ajp = _make_ajp([
        {"driver_id": "risk_free_rate", "value": 0.05},
        {"driver_id": "equity_risk_premium", "value": 0.05},
        {"driver_id": "country_risk_premium", "value": 0.02},
        {"driver_id": "tax_rate", "value": 0.25},
        {"driver_id": "peer_betas", "value": [{"beta": 1.0, "debt": 0.0, "equity": 100.0}]},
        {"driver_id": "pretax_cost_of_debt_override", "value": 0.08},
        {"driver_id": "target_debt_to_cap", "value": 0.0},
    ])
    fin = _minimal_fin(debt=0.0, market_cap=100.0)
    res = WACCEngine.calculate(fin, ajp)
    assert abs(res["total_erp"] - 0.07) < 1e-9
    assert abs(res["current_ke"] - 0.12) < 1e-9
