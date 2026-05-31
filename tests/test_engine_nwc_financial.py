"""
test_engine_nwc_financial.py — regression for the financial-company NWC phantom.

Bug (GROWW.NS, FY27): the operating working-capital framework (AR/Inv/AP from
DSO/DIO/DPO × revenue) is inapplicable to a brokerage. Its "trade payables" are
client-settlement / float balances (~₹80,570mm) — not operating payables — and
it carries zero inventory, so DIO/DPO silently fall back to 30/45 days. The
projection rebuilds NWC on a days × revenue basis that bears no relation to the
historical balance, and Year-1 absorbs the entire reconciliation gap as a single
phantom: ΔNWC_FY27 ≈ +₹73,646mm (larger than total revenue), dragging UFCF deeply
negative. FY28+ are tiny — confirming a one-time Year-1 anchor discontinuity.

Fix: financial-sector companies (is_financial, set in the data layer like is_bank)
freeze operating working capital flat at its historical anchor, so ΔNWC = 0 across
the projection. FCF for a capital-light broker ≈ NOPAT + D&A − CapEx.
"""

import pytest
from sidwell.ajp.schema import AJP, AJPMeta
from sidwell.engine.statements import StatementsEngine


def _make_meta() -> AJPMeta:
    return AJPMeta(
        ticker="GROWWLIKE", as_of="2026-03-31", currency="INR_MM",
        sources_ingested=[], fiscal_year_end_month=3,
        last_actual_fy="FY2026", is_holdco=False, scenario_active="BASE",
    )


def _broker_statements() -> dict:
    """Raw GROWW-like brokerage statements (crore inputs → mm after map ×10).

    Hallmarks of a financial: zero inventory, trade 'payables' dominated by
    client/settlement float that dwarfs fee revenue, and screener supplying only
    debtor-days (inventory/payable days absent → engine fallbacks of 30/45)."""
    return {
        "years_annual": ["Mar 2022", "Mar 2023", "Mar 2024", "Mar 2025", "Mar 2026"],
        "annual": {
            "profit_loss": {
                "sales":             [427.0, 1142.0, 2794.0, 4061.0, 4645.0],
                "operating profit":  [-233.0, 399.0, 743.0, 2530.0, 2744.0],
                "depreciation":      [20.0, 25.0, 30.0, 35.0, 40.0],
                "interest":          [0.0, 0.0, 0.0, 0.0, 0.0],
                "profit before tax": [-253.0, 374.0, 713.0, 2495.0, 2704.0],
                "tax":               [0.0, 94.0, 179.0, 624.0, 676.0],
                "net profit":        [-253.0, 280.0, 534.0, 1871.0, 2028.0],
            },
            "balance_sheet": {
                "equity capital":   [60.0, 60.0, 61.0, 61.0, 62.0],
                "reserves":         [500.0, 800.0, 1400.0, 3300.0, 5400.0],
                "borrowings":       [0.0, 0.0, 0.0, 0.0, 360.0],
                "fixed assets":     [286.0, 321.0, 396.0, 402.0, 253.0],
                "inventories":      [0.0, 0.0, 0.0, 0.0, 0.0],
                "trade receivables":[14.0, 36.0, 69.0, 97.0, 277.0],
                "trade payables":   [1245.0, 1373.0, 3916.0, 4595.0, 8057.0],  # float
                "cash equivalents": [565.0, 1661.0, 3682.0, 4256.0, 8339.0],
            },
            "cash_flow": {
                "fixed assets purchased": [-30.0, -35.0, -40.0, -45.0, -50.0],
            },
        },
        # Only debtor days available; inventory/payable days absent (broker).
        "ratios": {
            "debtor days":  [12.0, 11.0, 9.0, 8.0, 12.8],
            "inventory days": [],
            "days payable": [],
        },
    }


def _broker_hist() -> dict:
    """Mapped historicals (the shape run_projections consumes)."""
    return StatementsEngine.map_historical(_broker_statements())


def test_unfrozen_projection_exhibits_year1_phantom():
    """Documents the bug: without the financial freeze, Year-1 ΔNWC is a phantom
    larger than revenue, concentrated entirely in the first projected year."""
    hist = _broker_hist()
    proj = StatementsEngine.run_projections(hist, _make_ajp_blank())

    fy1_rev = proj["revenue"][0]
    fy1_dnwc = proj["nwc_change"][0]
    # Phantom: Year-1 ΔNWC exceeds total Year-1 revenue (the pathology).
    assert fy1_dnwc > fy1_rev, (
        f"expected the documented phantom (ΔNWC>{fy1_rev:.0f}); got {fy1_dnwc:.0f}"
    )
    # And it is a one-time Year-1 jump: later years are orders of magnitude smaller.
    assert abs(proj["nwc_change"][1]) < 0.01 * fy1_dnwc


def test_frozen_financial_has_no_nwc_phantom():
    """The fix: freezing working capital for a financial zeroes ΔNWC every year."""
    hist = _broker_hist()
    proj = StatementsEngine.run_projections(
        hist, _make_ajp_blank(), freeze_working_capital=True
    )

    for i, d in enumerate(proj["nwc_change"]):
        assert abs(d) < 1.0, f"frozen ΔNWC must be ~0 in year {i}, got {d:.2f}mm"

    # UFCF must reduce to NOPAT + D&A − CapEx (no working-capital term).
    for i in range(len(proj["ufcf"])):
        expected = proj["nopat"][i] + proj["da"][i] - proj["capex"][i]
        assert abs(proj["ufcf"][i] - expected) < 1.0


def test_frozen_financial_balance_sheet_still_ties():
    """Freezing WC must not break the integrated balance sheet."""
    hist = _broker_hist()
    proj = StatementsEngine.run_projections(
        hist, _make_ajp_blank(), freeze_working_capital=True
    )
    for i, bc in enumerate(proj["balance_check"]):
        assert abs(bc) < 1.0, f"balance check failed in year {i}: {bc:.4f}mm"


def _make_ajp_blank() -> AJP:
    """Empty-assumption AJP → engine uses its historical-default drivers."""
    return AJP(meta=_make_meta(), assumptions=[])


# ---------------------------------------------------------------------------
# End-to-end: adapter → engine → workbook, with is_financial set by the caller
# (the data layer sets this in production; here we set it on the payload).
# ---------------------------------------------------------------------------
def _broker_fin(is_financial: bool) -> dict:
    return {
        "ticker": "GROWWLIKE", "current_price": 200.0, "market_cap": 1_200_000.0,
        "shares_outstanding": 6000.0, "is_bank": False, "is_financial": is_financial,
        "fcf": [1000.0, 1500.0, 1800.0, 2000.0],  # all positive → not cyclical
        "statements": _broker_statements(),
    }


def test_adapter_financial_kills_nwc_phantom_end_to_end():
    from valuation.dcf import run_dcf_valuation
    res = run_dcf_valuation(_broker_fin(is_financial=True), {}, 0.07, None)
    rev1 = res["projections"][0]["revenue"]
    for p in res["projections"]:
        assert abs(p["working_capital_change"]) < 0.01 * rev1, (
            f"financial projection must have ~0 ΔNWC, got {p['working_capital_change']:.0f}"
        )


def _first_projection_col(ws) -> int:
    """Column index of the first projection year (header label ends with 'E')."""
    for c in range(3, ws.max_column + 1):
        v = ws.cell(row=2, column=c).value
        if isinstance(v, str) and v.rstrip().endswith("E"):
            return c
    raise AssertionError("no projection column found")


def test_workbook_financial_bs_holds_wc_flat():
    """The rendered workbook must mirror the freeze: FCF-sheet ΔNWC ~0 and the BS
    AR projection cells are static constants (not days-driven formulas). The
    non-financial render of the same company keeps the days formulas — the
    behavior is gated solely by is_financial."""
    from valuation.dcf import run_dcf_valuation
    from sidwell.render.workbook import WorkbookRenderer

    def render(is_financial):
        res = run_dcf_valuation(_broker_fin(is_financial=is_financial), {}, 0.07, None)
        return WorkbookRenderer(res["engine_results"], res["ajp"]).render()

    wb_fin = render(True)
    # FCF sheet: Year-1 "Change in NWC" (row 4, first projection col) ~ 0.
    fcf = wb_fin["8_FCF_DCF"]
    fy1_dnwc = fcf.cell(row=4, column=_first_projection_col(fcf)).value
    assert abs(fy1_dnwc) < 1.0, f"workbook FY1 ΔNWC must be ~0, got {fy1_dnwc}"

    # BS sheet: financial → AR is a static constant; non-financial → days formula.
    bs_fin = wb_fin["5_Balance_Sheet"]
    ar_fin = bs_fin.cell(row=7, column=_first_projection_col(bs_fin))
    assert ar_fin.data_type != "f", "frozen AR must be a constant, not a days formula"

    bs_op = render(False)["5_Balance_Sheet"]
    ar_op = bs_op.cell(row=7, column=_first_projection_col(bs_op))
    assert ar_op.data_type == "f", "non-financial AR must remain a days-driven formula"
