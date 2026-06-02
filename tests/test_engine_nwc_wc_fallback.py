"""
test_engine_nwc_wc_fallback.py — Tests for the NWC fallback hierarchy (Part D):
  P1: AJP working_capital_days
  P2: screener WC-days average (tested in test_engine_nwc_working_capital_days.py)
  P3: NWC/Revenue ratio from comprehensive BS
  P4: trade-only AR+Inv-AP

Plus per-leg balance fallback (derive DSO/DIO/DPO from actual balance when blank).
Also tests Fix-2: no Year-1 phantom on the NWC-ratio path.

All tests are offline — no network, no LLM, no screener calls.
"""
import pytest
from sidwell.ajp.schema import AJP, AJPAssumption, AJPMeta
from sidwell.engine.statements import StatementsEngine


def _meta() -> AJPMeta:
    return AJPMeta(
        ticker="TEST", as_of="2026-03-31", currency="INR_MM",
        sources_ingested=[], fiscal_year_end_month=3,
        last_actual_fy="FY2026", is_holdco=False, scenario_active="BASE",
    )


def _blank_ajp() -> AJP:
    return AJP(meta=_meta(), assumptions=[])


def _neg_nwc_statements() -> dict:
    """Fixture: no WC-days in screener; comprehensive NWC clearly NEGATIVE
    (large 'other liability items' → OCL > AR+Inv − AP).
    Trade-only NWC = AR+Inv−AP is POSITIVE so we can verify Priority-3 fires
    (not the positive trade-only result).

    Values in crore; map_historical multiplies by 10 → mm.
    """
    return {
        "years_annual": ["Mar 2024", "Mar 2025"],
        "annual": {
            "profit_loss": {
                "sales":            [900.0, 1000.0],
                "operating profit": [135.0, 150.0],
                "depreciation":     [45.0,  50.0],
                "interest":         [0.0,   0.0],
                "profit before tax":[90.0,  100.0],
                "tax":              [22.5,  25.0],
                "net profit":       [67.5,  75.0],
                "cogs":             [630.0, 700.0],
            },
            "balance_sheet": {
                "equity capital":        [200.0, 200.0],
                "reserves":              [300.0, 350.0],
                "borrowings":            [100.0, 100.0],
                "fixed assets":          [500.0, 520.0],
                "trade receivables":     [45.0,  50.0],   # AR ~50 days of revenue
                "inventories":           [27.0,  30.0],   # Inv
                "trade payables":        [54.0,  60.0],   # AP
                "cash equivalents":      [50.0,  55.0],
                # Large other liabilities → net WC comprehensively negative
                "other liability items": [90.0,  100.0],
            },
            "cash_flow": {
                "fixed assets purchased": [-50.0, -52.0],
            },
        },
        "ratios": {
            # All screener WC-day ratios absent
            "debtor days":          [None, None],
            "inventory days":       [None, None],
            "days payable":         [None, None],
            "working capital days": [],  # no WC-days at all → Priority 3 fires
        },
    }


def _inventory_only_statements() -> dict:
    """Fixture for per-leg balance fallback tests.
    - Inventory > 0, COGS > 0, but inventory_days all blank
    - DSO and DPO also blank, but we add AR and AP too
    """
    return {
        "years_annual": ["Mar 2025"],
        "annual": {
            "profit_loss": {
                "sales":            [1000.0],
                "operating profit": [150.0],
                "depreciation":     [40.0],
                "interest":         [0.0],
                "profit before tax":[110.0],
                "tax":              [27.5],
                "net profit":       [82.5],
                "cogs":             [700.0],   # needed for DIO/DPO derivation
            },
            "balance_sheet": {
                "equity capital":   [500.0],
                "reserves":         [200.0],
                "borrowings":       [0.0],
                "fixed assets":     [400.0],
                "trade receivables":[0.0],     # AR = 0, DSO fallback won't fire
                "inventories":      [50.0],    # Inv > 0, DIO should be derived
                "trade payables":   [0.0],     # AP = 0
                "cash equivalents": [50.0],
            },
            "cash_flow": {
                "fixed assets purchased": [-40.0],
            },
        },
        "ratios": {
            "debtor days":          [None],
            "inventory days":       [None],   # blank → per-leg fallback should fire
            "days payable":         [None],
            "working capital days": [],
        },
    }


def _no_inventory_statements() -> dict:
    """Fixture: Inventory = 0, inventory_days blank — fallback must NOT fabricate."""
    stmts = _inventory_only_statements()
    stmts["annual"]["balance_sheet"]["inventories"] = [0.0]
    return stmts


# ─── Helper to extract the hist dict ─────────────────────────────────────────

def _hist(stmts):
    return StatementsEngine.map_historical(stmts)


# ---------------------------------------------------------------------------
# Test 1: inventory derived from balance when DIO blank
# ---------------------------------------------------------------------------
def test_inventory_derived_from_balance_when_dio_blank():
    """When inventory_days is blank but Inventory > 0 and COGS > 0,
    the per-leg balance fallback derives DIO and produces non-zero projected inv."""
    hist = _hist(_inventory_only_statements())
    proj = StatementsEngine.run_projections(hist, _blank_ajp())

    # The balance fallback should have set a non-zero DIO
    au = proj["assumptions_used"]
    assert au["dio_days"] > 0.0, (
        f"DIO should be derived from Inv/COGS balance, got {au['dio_days']}"
    )

    # All projected inventories must be > 0 (proportional to COGS)
    for i, inv in enumerate(proj["inv"]):
        assert inv > 0, f"year {i}: projected inv should be > 0, got {inv}"


# ---------------------------------------------------------------------------
# Test 2: when inventory = 0, DIO stays 0 (no fabrication)
# ---------------------------------------------------------------------------
def test_no_inventory_no_fabrication():
    """When Inventory = 0 (last actual), the per-leg balance fallback must NOT
    derive a non-zero DIO — stays 0.0 (no fabrication)."""
    hist = _hist(_no_inventory_statements())
    proj = StatementsEngine.run_projections(hist, _blank_ajp())

    au = proj["assumptions_used"]
    assert au["dio_days"] == 0.0, (
        f"DIO should stay 0 when Inventory = 0, got {au['dio_days']}"
    )

    # All projected inventories must be zero
    for i, inv in enumerate(proj["inv"]):
        assert inv == 0.0, f"year {i}: projected inv should be 0, got {inv}"


# ---------------------------------------------------------------------------
# Test 3: Priority-3 (NWC/Revenue ratio) gives NEGATIVE NWC, not trade-only
# ---------------------------------------------------------------------------
def test_nwc_ratio_path_negative():
    """When no WC-days exists and OCL > AR+Inv, comprehensive NWC is negative.
    Priority-3 must project negative NWC rather than the positive trade-only."""
    hist = _hist(_neg_nwc_statements())
    proj = StatementsEngine.run_projections(hist, _blank_ajp())

    au = proj["assumptions_used"]
    # Priority 3 must have fired
    assert au["nwc_ratio_target"] is not None, "Priority-3 must have set nwc_ratio_target"
    assert au["nwc_ratio_target"] < 0, (
        f"nwc_ratio_target should be negative, got {au['nwc_ratio_target']:.4f}"
    )
    # Caveat must be set
    assert au["nwc_caveat"] is not None, "nwc_caveat should be set for Priority-3 path"

    # All projected NWC must be negative (trade-only would have been positive)
    for i, nwc in enumerate(proj["nwc"]):
        assert nwc < 0, (
            f"year {i}: NWC should be negative on Priority-3 path, got {nwc:.1f}"
        )


# ---------------------------------------------------------------------------
# Test 4 (Fix-2): No Year-1 phantom ΔNWC on the NWC-ratio path
# ---------------------------------------------------------------------------
def test_nwc_ratio_path_no_year1_phantom():
    """Fix-2: verify there is no large ΔNWC spike in Year 1 on the P3 path.

    Year-0 anchor (nwc_net_0) uses nwc_ratio_target × last_sales, and the
    projection uses nwc_ratio_target × sales, so ΔNWC[0] is small (proportional
    to revenue growth) and the same sign as ΔNWC[1].
    """
    hist = _hist(_neg_nwc_statements())
    proj = StatementsEngine.run_projections(hist, _blank_ajp())

    nwc_change = proj["nwc_change"]
    revenue    = proj["revenue"]

    # |ΔNWC[0]| < 10% of revenue[0]  (not a large phantom)
    assert abs(nwc_change[0]) < 0.10 * revenue[0], (
        f"Year-1 ΔNWC ({nwc_change[0]:.1f}) too large vs revenue ({revenue[0]:.1f}) "
        f"— possible Year-1 phantom"
    )

    # ΔNWC[0] and ΔNWC[1] should have the same sign (no reversal)
    if len(nwc_change) > 1 and nwc_change[1] != 0:
        assert nwc_change[0] * nwc_change[1] >= 0, (
            f"ΔNWC sign flip between year 0 ({nwc_change[0]:.2f}) "
            f"and year 1 ({nwc_change[1]:.2f}) — phantom jump"
        )


# ---------------------------------------------------------------------------
# Test 5: Balance check still ties on the NWC-ratio path
# ---------------------------------------------------------------------------
def test_balance_still_ties_on_nwc_ratio_path():
    """The balance check must be zero (within 1 mm) for every projection year
    on the Priority-3 NWC/Revenue ratio path."""
    hist = _hist(_neg_nwc_statements())
    proj = StatementsEngine.run_projections(hist, _blank_ajp())

    balance_checks = proj.get("balance_check", [])
    assert balance_checks, "balance_check array must be present in projection output"
    for i, bc in enumerate(balance_checks):
        assert abs(bc) < 1.0, (
            f"year {i}: balance_check {bc:.4f} ≥ 1.0 mm — balance sheet doesn't tie"
        )
