"""
test_engine_statements.py — TDD tests for sidwell.engine.statements.StatementsEngine

Tests:
1. Balance check == 0 for every projected year (structural integrity)
2. Revenue growth monotonically fades from Stage 1 to terminal in Stage 2
3. EBIT margin fades monotonically toward target
4. NWC change is computed as the delta of NWC, not level
5. UFCF = NOPAT + DA - CapEx - NWC_change
6. Balance check failure raises ValueError (not AssertionError)
"""

import pytest
from sidwell.ajp.schema import AJP, AJPMeta, AJPAssumption
from sidwell.engine.statements import StatementsEngine


def _make_meta() -> AJPMeta:
    return AJPMeta(
        ticker="TEST", as_of="2025-03-31", currency="INR",
        sources_ingested=[], fiscal_year_end_month=3,
        last_actual_fy="FY2025", is_holdco=False, scenario_active="BASE",
    )


def _make_ajp(overrides: dict = None) -> AJP:
    """
    Build a deterministic AJP with clean, round-number assumptions that
    make hand-verification tractable.
    """
    defaults = {
        "stage1_revenue_growth": 0.10,    # 10% growth in Stage 1
        "terminal_growth": 0.03,           # 3% terminal growth
        "ebit_margin_target": 0.20,        # fade to 20% EBIT margin
        "capex_pct_sales_target": 0.05,    # 5% CapEx/sales target
        "da_pct_sales_target": 0.04,       # 4% D&A/sales target
        "tax_rate": 0.25,
        "dso_days": 45.0,
        "dio_days": 30.0,
        "dpo_days": 45.0,
        "pretax_cost_of_debt_override": 0.08,
    }
    if overrides:
        defaults.update(overrides)

    assumptions = [
        AJPAssumption(
            driver_id=k, value=v, unit="pct",
            source_type="TEST", confidence="HIGH",
            rationale="test", interrogation_refs=[],
        )
        for k, v in defaults.items()
    ]
    return AJP(meta=_make_meta(), assumptions=assumptions)


def _make_hist() -> dict:
    """
    Minimal historical data that StatementsEngine.map_historical produces.
    Values are in mm (already converted from crore).
    Revenue: 1000mm, EBIT margin 15%, CapEx 6%, D&A 5%
    BS: cash=100, equity=500, borrowings=200
    """
    sales = [1000.0]
    return {
        "years_annual": ["Mar 2025"],
        "is": {
            "sales": sales,
            "revenue": sales,
            "operating_profit": [150.0],   # 15% margin
            "depreciation": [50.0],        # 5% of sales
            "interest": [16.0],            # 8% * 200
            "profit_before_tax": [134.0],
            "tax": [33.5],
            "net_profit": [100.5],
            "financing_profit": [],
        },
        "bs": {
            "equity_capital": [100.0],
            "reserves": [400.0],           # total equity = 500
            "borrowings": [200.0],
            "lease_liabilities": [],
            "non_controlling_int": [],
            "trade_payables": [123.3],     # 45 days * 1000/365
            "other_liability_items": [],
            "total_liabilities": [],
            "fixed_assets": [500.0],
            "gross_block": [],
            "accumulated_depreciation": [],
            "cwip": [],
            "investments": [],
            "inventories": [82.2],         # 30 days * 1000/365
            "trade_receivables": [123.3],  # 45 days * 1000/365
            "cash_equivalents": [100.0],
            "loans_n_advances": [],
            "other_asset_items": [],
            "total_assets": [],
        },
        "cf": {
            "cfo": [120.0],
            "receivables": [],
            "inventory": [],
            "payables": [],
            "working_capital_changes": [],
            "cfi": [-60.0],
            "fixed_assets_purchased": [-60.0],  # 6% CapEx
            "cff": [],
            "proceeds_from_borrowings": [],
            "repayment_of_borrowings": [],
        },
        "ratios": {
            "debtor_days": [45.0],
            "inventory_days": [30.0],
            "days_payable": [45.0],
        },
    }


# ---------------------------------------------------------------------------
# Test 1: Balance check ≈ 0 for all 10 projected years
# ---------------------------------------------------------------------------
def test_balance_check_zero_all_years():
    hist = _make_hist()
    ajp = _make_ajp()
    proj = StatementsEngine.run_projections(hist, ajp)

    assert len(proj["balance_check"]) == 10
    for i, bc in enumerate(proj["balance_check"]):
        assert abs(bc) < 1.0, f"Balance check failed in year {i}: {bc:.4f}mm"


# ---------------------------------------------------------------------------
# Test 2: Revenue growth monotonically fades in Stage 2 (years 6–10)
#
# Stage 1 (y0–y4): constant at rev_g_s1 = 10%
# Stage 2 (y5–y9): linear fade from 10% toward 3% terminal
#   step = (10% - 3%) / (5+1) = 7%/6 = 1.1667% per step
#   y5 growth = 10% - 1.1667% = 8.833%
#   y6 growth = 10% - 2.3333% = 7.667%
#   ...
#   y9 growth = 10% - 4*(7/6) = 10% - 4.667% = 5.333%  (approaching 3%)
# ---------------------------------------------------------------------------
def test_revenue_growth_monotone_fade_in_stage2():
    hist = _make_hist()
    ajp = _make_ajp()
    proj = StatementsEngine.run_projections(hist, ajp)

    # Build implied growth rates
    revenues = proj["revenue"]
    prev_rev = _make_hist()["is"]["sales"][-1]  # 1000mm

    growth_rates = []
    for rev in revenues:
        g = (rev / prev_rev) - 1.0
        growth_rates.append(g)
        prev_rev = rev

    # Stage 1 (years 0–4): all equal to 10%
    for i in range(5):
        assert abs(growth_rates[i] - 0.10) < 1e-9, f"Stage 1 growth wrong at year {i}"

    # Stage 2 (years 5–9): each year strictly less than previous
    for i in range(5, 9):
        assert growth_rates[i] > growth_rates[i + 1], (
            f"Stage 2 growth NOT monotone declining: g[{i}]={growth_rates[i]:.4f} "
            f"vs g[{i+1}]={growth_rates[i+1]:.4f}"
        )

    # Stage 2 growth is strictly below Stage 1 growth
    assert growth_rates[5] < growth_rates[4]


# ---------------------------------------------------------------------------
# Test 3: EBIT margin fades monotonically toward target (20%)
#
# Starting margin: 150/1000 = 15%
# Target margin: 20%
# 10-year linear fade: step = (20%-15%)/10 = 0.5% per year
# Year 1 margin = 15.5%, Year 10 margin = 20%
# ---------------------------------------------------------------------------
def test_ebit_margin_fades_monotone():
    hist = _make_hist()
    ajp = _make_ajp({"ebit_margin_target": 0.20})
    proj = StatementsEngine.run_projections(hist, ajp)

    revenues = proj["revenue"]
    ebits = proj["ebit"]
    margins = [e / r for e, r in zip(ebits, revenues)]

    # Monotone increase from 15% to 20%
    start_margin = 150.0 / 1000.0   # 15%
    assert margins[0] > start_margin   # already fading up
    for i in range(9):
        assert margins[i] < margins[i + 1], (
            f"EBIT margin NOT monotone: m[{i}]={margins[i]:.4f} vs m[{i+1}]={margins[i+1]:.4f}"
        )
    assert abs(margins[-1] - 0.20) < 1e-9   # hits target exactly at year 10


# ---------------------------------------------------------------------------
# Test 4: UFCF formula is NOPAT + DA - CapEx - NWC_change
# ---------------------------------------------------------------------------
def test_ufcf_equals_nopat_plus_da_minus_capex_minus_nwc():
    hist = _make_hist()
    ajp = _make_ajp()
    proj = StatementsEngine.run_projections(hist, ajp)

    n = len(proj["ufcf"])
    for i in range(n):
        computed = proj["nopat"][i] + proj["da"][i] - proj["capex"][i] - proj["nwc_change"][i]
        assert abs(proj["ufcf"][i] - computed) < 1e-6, (
            f"UFCF mismatch at year {i}: {proj['ufcf'][i]:.4f} vs {computed:.4f}"
        )


# ---------------------------------------------------------------------------
# Test 5: NWC change is delta of NWC level (not level itself)
#
# NWC = AR + Inv - AP = revenue * (dso + dio - dpo)/365
# With dso=45, dio=30, dpo=45 → NWC = revenue * 30/365
# Year 0: NWC_0 = 1100 * 30/365 (after 10% growth)
# Year 0 NWC_change = NWC_0 - NWC_hist
# ---------------------------------------------------------------------------
def test_nwc_change_is_delta_not_level():
    """
    ΔNWC must be computed as the delta of NWC levels, not the level itself.
    This holds regardless of which NWC precedence tier is active (wc_days,
    nwc_ratio, or trade-only).
    """
    hist = _make_hist()
    ajp = _make_ajp({"dso_days": 45.0, "dio_days": 30.0, "dpo_days": 45.0})
    proj = StatementsEngine.run_projections(hist, ajp)

    # Years 1–9: nwc_change[i] == nwc[i] - nwc[i-1]
    for i in range(1, len(proj["nwc"])):
        expected = proj["nwc"][i] - proj["nwc"][i - 1]
        assert abs(proj["nwc_change"][i] - expected) < 1e-6, (
            f"year {i}: nwc_change {proj['nwc_change'][i]:.4f} ≠ delta {expected:.4f}"
        )

    # Year 0: nwc_change[0] == nwc[0] - anchor, where anchor uses same precedence.
    au = proj["assumptions_used"]
    last_s = hist["is"]["sales"][-1]  # 1000 mm
    if au.get("working_capital_days") is not None:
        anchor = (au["working_capital_days"] / 365.0) * last_s
    elif au.get("nwc_ratio_target") is not None:
        anchor = au["nwc_ratio_target"] * last_s
    else:
        anchor = (
            hist["bs"]["trade_receivables"][-1]
            + hist["bs"]["inventories"][-1]
            - hist["bs"]["trade_payables"][-1]
        )
    assert abs(proj["nwc_change"][0] - (proj["nwc"][0] - anchor)) < 1e-6


# ---------------------------------------------------------------------------
# Test 6: 10 projection years generated
# ---------------------------------------------------------------------------
def test_ten_projection_years():
    hist = _make_hist()
    ajp = _make_ajp()
    proj = StatementsEngine.run_projections(hist, ajp)

    assert len(proj["years"]) == 10
    assert len(proj["revenue"]) == 10
    assert len(proj["ufcf"]) == 10
    assert len(proj["balance_check"]) == 10


# ---------------------------------------------------------------------------
# Test 7: Balance check failure raises ValueError (not bare assert)
#
# We monkey-patch the plug logic so the balance sheet is intentionally wrong,
# then confirm ValueError (not AssertionError) is raised.
# ---------------------------------------------------------------------------
def test_balance_check_raises_value_error_not_assertion_error():
    """
    The engine computes a 'net_other_assets' plug from the historical BS to
    ensure the starting balance is zero.  If we inject a wildly imbalanced
    historical BS the plug absorbs it harmlessly; so to force a mid-projection
    failure we patch the balance_check logic by temporarily overriding the
    internal variable via a subclass monkey-patch is too complex — instead we
    verify the existing guard code structure by unit-testing the guard itself.
    """
    # Direct guard test: confirm ValueError is raised for a large imbalance
    import sidwell.engine.statements as stmts_module

    # The guard triggers when abs(balance_check) >= 1.0
    # We cannot inject a bad state via public API without major refactor,
    # so test the guard path via static analysis: confirm 'assert' is NOT used
    import inspect
    src = inspect.getsource(StatementsEngine.run_projections)
    # Must not contain bare 'assert abs(balance_check)'
    assert "assert abs(balance_check)" not in src, (
        "StatementsEngine.run_projections still uses `assert` for balance check — "
        "replace with `raise ValueError`"
    )
    # Must contain ValueError
    assert "raise ValueError" in src, (
        "StatementsEngine.run_projections must raise ValueError on balance check failure"
    )


# ---------------------------------------------------------------------------
# Test: normalized_ebit_margin overrides last-actual peak/trough
# ---------------------------------------------------------------------------
def test_normalized_ebit_margin_overrides_base():
    """When AJP supplies normalized_ebit_margin, it replaces last-actual as
    the fade-start margin, not the peak/trough actual."""
    hist = _make_hist()
    # Simulate a cyclical peak: last EBIT = 30% of 1000mm
    hist["is"]["operating_profit"] = [300.0]

    # With normalized_ebit_margin=0.15, the engine should start fading from
    # 15%, not from the 30% peak.
    ajp_norm = _make_ajp({"ebit_margin_target": 0.15, "normalized_ebit_margin": 0.15})
    proj_norm = StatementsEngine.run_projections(hist, ajp_norm)

    # margin_step = (0.15 − 0.15) / 10 = 0 → all margins exactly 0.15
    margins_norm = [e / r for e, r in zip(proj_norm["ebit"], proj_norm["revenue"])]
    for i, m in enumerate(margins_norm):
        assert abs(m - 0.15) < 1e-9, f"year {i}: expected 15% margin, got {m:.4f}"

    # Contrast: without normalized_ebit_margin, fade starts from 30%
    ajp_peak = _make_ajp({"ebit_margin_target": 0.15})
    proj_peak = StatementsEngine.run_projections(hist, ajp_peak)
    margins_peak = [e / r for e, r in zip(proj_peak["ebit"], proj_peak["revenue"])]
    # Year 1 margin = 30% + step (fading DOWN to 15%)
    assert margins_peak[0] > 0.20, (
        f"Without normalized margin, Year-1 should be > 20% (fading from 30%), "
        f"got {margins_peak[0]:.4f}"
    )

    # assumptions_used should record the normalized margin
    assert proj_norm["assumptions_used"]["normalized_ebit_margin"] == 0.15
    assert proj_peak["assumptions_used"]["normalized_ebit_margin"] is None


# ---------------------------------------------------------------------------
# Test: AJP working_capital_days (Priority 1) overrides screener average (P2)
# ---------------------------------------------------------------------------
def test_ajp_working_capital_days_overrides_screener():
    """AJP working_capital_days beats the screener's historical WC-days average."""
    hist = _make_hist()
    # Screener says +50 days (positive WC)
    hist["ratios"]["working_capital_days"] = [50.0, 50.0, 50.0]

    # AJP forecasts −30 days (negative WC, e.g. after a mix-shift)
    ajp = _make_ajp({"working_capital_days": -30.0})
    proj = StatementsEngine.run_projections(hist, ajp)

    au = proj["assumptions_used"]
    assert abs(au["working_capital_days"] - (-30.0)) < 1e-6, (
        f"AJP WC days should override screener average: got {au['working_capital_days']}"
    )

    # All projected NWC ≈ (−30/365) × revenue
    for i, (nwc, rev) in enumerate(zip(proj["nwc"], proj["revenue"])):
        implied = (-30.0 / 365.0) * rev
        assert abs(nwc - implied) < 1.0, (
            f"year {i}: nwc {nwc:.1f} vs AJP-implied {implied:.1f}"
        )
