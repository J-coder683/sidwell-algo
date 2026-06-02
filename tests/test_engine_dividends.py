"""
test_engine_dividends.py — Part B: dividend payout modelling in StatementsEngine.

Covers:
 - map_historical exposes dividend_payout_pct
 - AJP dividend_payout_ratio overrides the historical average
 - Projected equity grows by NI × (1 − payout) per year (not full NI)
 - Projected cash is lower by the dividend each year vs payout=0
 - Balance check ≈ 0 every year when dividends are active
 - proj["dividends"] is populated
 - Intrinsic value per share is UNCHANGED by payout (UFCF pre-dividend)
"""

import pytest
from sidwell.ajp.schema import AJP, AJPMeta, AJPAssumption
from sidwell.engine.statements import StatementsEngine
from valuation.dcf import run_dcf_valuation


# ── shared fixtures ────────────────────────────────────────────────────────────

def _make_meta():
    return AJPMeta(
        ticker="PAYTST", as_of="2025-03-31", currency="INR_MM",
        sources_ingested=[], fiscal_year_end_month=3,
        last_actual_fy="FY2025", is_holdco=False, scenario_active="BASE",
    )


def _blank_ajp():
    return AJP(meta=_make_meta(), assumptions=[])


def _ajp_with_payout(payout: float):
    return AJP(
        meta=_make_meta(),
        assumptions=[
            AJPAssumption(
                driver_id="dividend_payout_ratio",
                value=payout,
                unit="ratio",
                source_type="ANALYST_ESTIMATE",
                rationale="Test fixture",
                confidence="MEDIUM",
            )
        ],
    )


def _base_hist(payout_pcts=None):
    """Minimal realistic historical data. payout_pcts in % (e.g. [60.0, 62.0])."""
    pl = {
        "sales":             [1000.0, 1100.0, 1210.0],
        "cogs":              [500.0, 550.0, 605.0],
        "operating profit":  [150.0, 165.0, 181.5],
        "depreciation":      [50.0, 55.0, 60.5],
        "interest":          [10.0, 10.0, 10.0],
        "profit before tax": [140.0, 155.0, 171.0],
        "tax":               [35.0, 38.75, 42.75],
        "tax %":             [25.0, 25.0, 25.0],
        "net profit":        [105.0, 116.25, 128.25],
    }
    if payout_pcts:
        pl["dividend payout %"] = payout_pcts
    return {
        "years_annual": ["Mar 2023", "Mar 2024", "Mar 2025"],
        "annual": {
            "profit_loss": pl,
            "balance_sheet": {
                "equity capital":    [500.0, 500.0, 500.0],
                "reserves":          [200.0, 250.0, 310.0],
                "borrowings":        [100.0, 100.0, 100.0],
                "fixed assets":      [400.0, 440.0, 484.0],
                "trade payables":    [80.0, 88.0, 96.8],
                "inventories":       [100.0, 110.0, 121.0],
                "trade receivables": [120.0, 132.0, 145.2],
                "cash equivalents":  [50.0, 55.0, 60.5],
            },
            "cash_flow": {
                "fixed assets purchased": [45.0, 49.5, 54.45],
                "cash from operating activity": [130.0, 143.0, 157.3],
            },
        },
        "ratios": {
            "debtor days":    [43.8, 43.8, 43.8],
            "inventory days": [73.0, 73.0, 73.0],
            "days payable":   [58.4, 58.4, 58.4],
        },
    }


# ── Part B tests ───────────────────────────────────────────────────────────────

def test_map_historical_exposes_dividend_payout_pct():
    """map_historical must surface 'dividend payout %' from screener as dividend_payout_pct."""
    stmts = _base_hist(payout_pcts=[40.0, 50.0, 60.0])
    hist = StatementsEngine.map_historical(stmts)
    dp = hist["is"].get("dividend_payout_pct", [])
    assert dp, "dividend_payout_pct missing from mapped_is"
    # map_historical uses convert_ratio_row (no ×10 multiplier)
    assert dp[0] == pytest.approx(40.0), f"Expected 40.0, got {dp[0]}"
    assert dp[2] == pytest.approx(60.0), f"Expected 60.0, got {dp[2]}"


def test_dividend_payout_reduces_equity_not_ufcf():
    """With 60% payout, equity grows by 40% of NI per year (not 100%)."""
    hist = StatementsEngine.map_historical(_base_hist())
    ajp60 = _ajp_with_payout(0.60)
    ajp0  = _ajp_with_payout(0.0)
    proj60 = StatementsEngine.run_projections(hist, ajp60)
    proj0  = StatementsEngine.run_projections(hist, ajp0)

    ni0   = proj60["net_income"][0]
    eq0_60 = proj60["equity"][0]
    eq0_0  = proj0["equity"][0]

    # With 0% payout: eq[0] = hist_eq + NI[0] (adds full NI)
    # With 60% payout: eq[0] = hist_eq + NI[0]*0.4 (adds only retained)
    # So the difference should be NI[0]*0.6
    expected_diff = ni0 * 0.60
    actual_diff   = eq0_0 - eq0_60
    assert actual_diff == pytest.approx(expected_diff, rel=1e-6), (
        f"Equity diff (60% vs 0% payout) should be NI×60%={expected_diff:.2f}, "
        f"got {actual_diff:.2f} (eq0_60={eq0_60:.2f}, eq0_0={eq0_0:.2f})"
    )

    # Also verify equity[0] < equity[0] with zero payout
    assert eq0_0 > eq0_60, "Zero-payout equity should exceed 60%-payout equity"


def test_dividend_reduces_cash():
    """Projected cash must be lower with 60% payout than with 0% payout (ceteris paribus)."""
    hist = StatementsEngine.map_historical(_base_hist())
    proj60 = StatementsEngine.run_projections(hist, _ajp_with_payout(0.60))
    proj0  = StatementsEngine.run_projections(hist, _ajp_with_payout(0.0))
    # Cash should be lower every year when dividends are paid
    for i, (c60, c0) in enumerate(zip(proj60["cash"], proj0["cash"])):
        assert c60 <= c0 + 1.0, (
            f"Year {i+1}: cash with 60% payout ({c60:.0f}) should be ≤ zero-payout ({c0:.0f})"
        )


def test_dividends_stored_in_proj():
    """proj['dividends'] must be populated and equal NI × payout."""
    hist = StatementsEngine.map_historical(_base_hist())
    payout = 0.45
    proj = StatementsEngine.run_projections(hist, _ajp_with_payout(payout))
    assert "dividends" in proj, "proj['dividends'] not present"
    assert len(proj["dividends"]) == 10
    for i, (d, ni) in enumerate(zip(proj["dividends"], proj["net_income"])):
        assert d == pytest.approx(ni * payout, rel=1e-9), (
            f"Year {i+1}: dividends={d:.2f}, expected {ni*payout:.2f}"
        )


def test_balance_check_zero_with_dividends():
    """Balance check must be ≈0 every year when dividends are active."""
    hist = StatementsEngine.map_historical(_base_hist())
    proj = StatementsEngine.run_projections(hist, _ajp_with_payout(0.60))
    for i, bc in enumerate(proj["balance_check"]):
        assert abs(bc) < 1.0, (
            f"Balance check failed in year {i+1}: {bc:.4f}mm (payout=60%)"
        )


def test_ajp_dividend_overrides_historical_average():
    """AJP dividend_payout_ratio=0.80 must override the historical 40% average."""
    hist = StatementsEngine.map_historical(_base_hist(payout_pcts=[40.0, 40.0, 40.0]))
    ajp = _ajp_with_payout(0.80)
    proj = StatementsEngine.run_projections(hist, ajp)
    au = proj["assumptions_used"]
    assert au["dividend_payout_ratio"] == pytest.approx(0.80), (
        f"AJP payout should be 0.80, got {au['dividend_payout_ratio']}"
    )
    # Derive hist_eq from the 0%-payout baseline: eq[0]_0 = hist_eq + NI[0]
    proj0  = StatementsEngine.run_projections(hist, _ajp_with_payout(0.0))
    hist_eq = proj0["equity"][0] - proj0["net_income"][0]
    ni0 = proj["net_income"][0]
    # With 80% payout: eq[0] = hist_eq + NI[0]*(1-0.80)
    assert proj["equity"][0] == pytest.approx(hist_eq + ni0 * 0.20, rel=1e-6), (
        f"Equity[0]={proj['equity'][0]:.2f}, expected {hist_eq + ni0*0.20:.2f}"
    )


def test_historical_average_used_when_ajp_silent():
    """When AJP is silent, the historical recency-weighted average is used."""
    # Historical payout = 60% in all 3 years → weighted avg ≈ 60%
    hist = StatementsEngine.map_historical(_base_hist(payout_pcts=[60.0, 60.0, 60.0]))
    proj = StatementsEngine.run_projections(hist, _blank_ajp())
    au = proj["assumptions_used"]
    # recency-weighted avg of [0.60, 0.60, 0.60] = 0.60
    assert au["dividend_payout_ratio"] == pytest.approx(0.60, rel=1e-6), (
        f"Expected payout 0.60 from history, got {au['dividend_payout_ratio']}"
    )


def test_zero_payout_when_no_history_and_no_ajp():
    """No historical payout + no AJP → payout defaults to 0.0 (no fabrication)."""
    hist = StatementsEngine.map_historical(_base_hist())  # no dividend_payout_pcts
    proj = StatementsEngine.run_projections(hist, _blank_ajp())
    au = proj["assumptions_used"]
    assert au["dividend_payout_ratio"] == pytest.approx(0.0), (
        f"Expected 0.0 payout with no data, got {au['dividend_payout_ratio']}"
    )
    # dividends should all be 0 (or near-zero)
    for d in proj["dividends"]:
        assert abs(d) < 0.01, f"Non-zero dividend with payout=0: {d}"


def test_intrinsic_value_unchanged_by_payout():
    """UFCF is pre-dividend → intrinsic_value_per_share must be the same at 0% and 60% payout.

    This confirms the UFCF DCF model is unaffected by dividends (the bridge uses
    current net cash, not projected cash).
    """
    fin = {
        "ticker": "TEST", "current_price": 100.0, "market_cap": 5000.0,
        "shares_outstanding": 50.0,
        "years": ["2023", "2024", "2025"],
        "revenue": [1000.0, 1100.0, 1210.0],
        "gross_profit": [400.0, 440.0, 484.0],
        "ebit": [150.0, 165.0, 181.5],
        "interest_expense": [0.0] * 3,
        "tax_provision": [37.5, 41.25, 45.375],
        "pretax_income": [150.0, 165.0, 181.5],
        "net_income": [112.5, 123.75, 136.125],
        "total_assets": [800.0] * 3,
        "total_equity": [600.0] * 3,
        "cash": [60.5, 66.55, 73.205],
        "debt": [50.0] * 3,
        "capex": [45.0, 49.5, 54.45],
        "depreciation": [20.0, 22.0, 24.2],
        "working_capital_change": [0.0] * 3,
        "fcf": [100.0] * 3,
        "statements": {
            "years_annual": ["Mar 2023", "Mar 2024", "Mar 2025"],
            "annual": {
                "profit_loss": {
                    "sales":             [100.0, 110.0, 121.0],
                    "cogs":              [50.0, 55.0, 60.5],
                    "operating profit":  [15.0, 16.5, 18.15],
                    "depreciation":      [2.0, 2.2, 2.42],
                    "interest":          [0.0, 0.0, 0.0],
                    "profit before tax": [15.0, 16.5, 18.15],
                    "tax":               [3.75, 4.125, 4.5375],
                    "tax %":             [25.0, 25.0, 25.0],
                    "net profit":        [11.25, 12.375, 13.6125],
                },
                "balance_sheet": {
                    "equity capital":    [50.0, 50.0, 50.0],
                    "reserves":          [20.0, 25.0, 31.0],
                    "borrowings":        [5.0, 5.0, 5.0],
                    "fixed assets":      [40.0, 44.0, 48.4],
                    "trade payables":    [8.0, 8.8, 9.68],
                    "inventories":       [10.0, 11.0, 12.1],
                    "trade receivables": [12.0, 13.2, 14.52],
                    "cash equivalents":  [6.05, 6.655, 7.3205],
                },
                "cash_flow": {
                    "fixed assets purchased": [4.5, 4.95, 5.445],
                    "cash from operating activity": [13.0, 14.3, 15.73],
                },
            },
            "ratios": {
                "debtor days":    [43.8, 43.8, 43.8],
                "inventory days": [73.0, 73.0, 73.0],
                "days payable":   [58.4, 58.4, 58.4],
            },
        },
    }
    # Run with payout=0 and payout=0.60; expect same intrinsic value
    fin0 = dict(fin)
    fin60 = dict(fin)
    fin60["statements"]["annual"]["profit_loss"]["dividend payout %"] = [0.60, 0.60, 0.60]

    res0  = run_dcf_valuation(fin0, {}, 0.04, None)
    res60 = run_dcf_valuation(fin60, {}, 0.04, None)

    iv0  = res0["intrinsic_value_per_share"]
    iv60 = res60["intrinsic_value_per_share"]

    assert iv0 == pytest.approx(iv60, rel=1e-4), (
        f"Intrinsic value changed with dividend payout: {iv0:.2f} vs {iv60:.2f}"
    )
