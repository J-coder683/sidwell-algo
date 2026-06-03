"""
tests/test_comps.py — Offline tests for valuation.comps.run_comps_valuation.

fetch_fn is always mocked so no network calls happen.

Fixture design
--------------
A "clean" peer has:
  market_cap  = 2_000_000_000  rupees  (2e9 ÷ 1e7 = 200 crore market cap)
  borrowings  = 20 cr
  lease liab  = 0
  cash equiv  = 10 cr
  non ctrl    = 0
  investments = 0
  EV          = 200 + 20 - 10 = 210 cr
  op profit   = 30 cr
  depreciation= 10 cr  → EBITDA = 40 cr   → EV/EBITDA = 210/40 = 5.25
  sales       = 105 cr              → EV/Sales  = 210/105 = 2.0
  trailing_pe = 15.0
  net profit  = 18 cr
  shares_outstanding = 1e7  (10 million shares)

  current_price (implied) = market_cap / shares = 2e9 / 1e7 = 200 ₹

Scale anchor (Test 4)
---------------------
peer identical to target → EV/Sales =2.0 → implied EV_cr=2.0×105=210
  → equity_cr = 210+10-20 = 200 cr → per_share = 200×1e7/1e7 = 200 ₹  ✓
"""

import pytest
from valuation.comps import run_comps_valuation


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_peer_fin(
    market_cap_rupees: float = 2_000_000_000,  # 2e9 rupees = 200 crore
    borrowings: float = 20.0,
    lease_liabilities: float = 0.0,
    cash_equiv: float = 10.0,
    nci: float = 0.0,
    investments: float = 0.0,
    op_profit: float = 30.0,
    depreciation: float = 10.0,
    sales: float = 105.0,
    net_profit: float = 18.0,
    trailing_pe: float = 15.0,
    shares: float = 1e7,
) -> dict:
    return {
        "market_cap": market_cap_rupees,
        "trailing_pe": trailing_pe,
        "shares_outstanding": shares,
        "statements": {
            "annual": {
                "profit_loss": {
                    "operating profit": [op_profit],
                    "depreciation": [depreciation],
                    "sales": [sales],
                    "net profit": [net_profit],
                },
                "balance_sheet": {
                    "borrowings": [borrowings],
                    "lease liabilities": [lease_liabilities],
                    "cash equivalents": [cash_equiv],
                    "non controlling int": [nci],
                    "investments": [investments],
                },
            }
        },
    }


_TARGET_FIN = _make_peer_fin()   # default clean fixture; current_price = 200 ₹


# ---------------------------------------------------------------------------
# Derived expected values (hand-verified)
# ---------------------------------------------------------------------------
# peer_a (default): EV=210, EBITDA=40, sales=105 → EV/EBITDA=5.25, EV/Sales=2.0, P/E=15
# peer_b: mcap=300 cr (3e9 rupees), debt=30, cash=15 → EV=315
#         EBITDA=35+5=40 → EV/EBITDA=315/40=7.875
#         sales=126      → EV/Sales=315/126=2.5
#         P/E=18
# median EV/EBITDA = (5.25+7.875)/2 = 6.5625
# median EV/Sales  = (2.0+2.5)/2    = 2.25
# median P/E       = (15+18)/2      = 16.5

_PEER_B = _make_peer_fin(
    market_cap_rupees=3_000_000_000,  # 300 crore
    borrowings=30.0, cash_equiv=15.0,
    op_profit=35.0, depreciation=5.0,   # EBITDA=40
    sales=126.0,
    net_profit=22.0,
    trailing_pe=18.0,
)


# ---------------------------------------------------------------------------
# Test 1: Two clean peers — all three methods, range low < high
# ---------------------------------------------------------------------------

def test_two_clean_peers_full_result():
    """Two peers with all valid multiples → medians correct, all methods computed,
    comps_range.low < comps_range.high."""

    calls = {"PEER_A.NS": _make_peer_fin(), "PEER_B.NS": _PEER_B}
    result = run_comps_valuation(_TARGET_FIN, ["PEER_A.NS", "PEER_B.NS"],
                                 fetch_fn=calls.__getitem__)

    assert result["error"] is None
    assert result["n_peers"] == 2
    assert result["n_valid"] == 2

    m = result["medians"]

    # EV/EBITDA: (5.25 + 7.875) / 2 = 6.5625
    assert m["ev_ebitda"] is not None
    assert abs(m["ev_ebitda"]["med"] - 6.5625) < 1e-6
    assert m["ev_ebitda"]["min"] == pytest.approx(5.25,  rel=1e-5)
    assert m["ev_ebitda"]["max"] == pytest.approx(7.875, rel=1e-5)

    # EV/Sales: (2.0 + 2.5) / 2 = 2.25
    assert m["ev_sales"] is not None
    assert abs(m["ev_sales"]["med"] - 2.25) < 1e-6

    # P/E: (15 + 18) / 2 = 16.5
    assert m["pe"] is not None
    assert abs(m["pe"]["med"] - 16.5) < 1e-6

    # All three implied_per_share present and positive
    imp = result["implied_per_share"]
    assert imp["ev_ebitda"] is not None and imp["ev_ebitda"] > 0
    assert imp["ev_sales"]  is not None and imp["ev_sales"]  > 0
    assert imp["pe"]        is not None and imp["pe"]        > 0

    # comps_range has low < high (three distinct implied values)
    cr = result["comps_range"]
    assert cr is not None
    assert cr["low"] < cr["high"]


# ---------------------------------------------------------------------------
# Test 2: Negative-EBITDA peer excluded from EV/EBITDA but used for P/E
# ---------------------------------------------------------------------------

def test_negative_ebitda_peer_excluded_from_ev_ebitda_kept_for_pe():
    """A peer with negative EBITDA must appear in excluded[] for EV/EBITDA
    but its positive P/E must still contribute to the P/E multiple pool."""

    peer_good = _make_peer_fin()   # EV/EBITDA=5.25, EV/Sales=2.0, P/E=15
    peer_bad_ebitda = _make_peer_fin(
        op_profit=-50.0,            # EBITDA = -50 + 5 = -45 → excluded from EV/EBITDA
        depreciation=5.0,
        sales=90.0,
        trailing_pe=12.0,           # valid P/E — must still contribute
        net_profit=10.0,
    )

    calls = {"GOOD.NS": peer_good, "BAD.NS": peer_bad_ebitda}
    result = run_comps_valuation(
        _TARGET_FIN, ["GOOD.NS", "BAD.NS"],
        fetch_fn=calls.__getitem__,
    )

    assert result["error"] is None

    m = result["medians"]

    # EV/EBITDA: only peer_good contributes → min=med=max=5.25
    assert m["ev_ebitda"] is not None
    assert m["ev_ebitda"]["min"] == pytest.approx(5.25, rel=1e-4)
    assert m["ev_ebitda"]["med"] == pytest.approx(5.25, rel=1e-4)

    # P/E: both peers → median of [15, 12] = 13.5
    assert m["pe"] is not None
    assert abs(m["pe"]["med"] - 13.5) < 1e-6

    # BAD.NS must be in excluded for the EV/EBITDA reason
    ebitda_excl = [t for t, r in result["excluded"]
                   if t == "BAD.NS" and "EV/EBITDA" in r]
    assert ebitda_excl, (
        f"BAD.NS should be excluded from EV/EBITDA; excluded={result['excluded']}"
    )


# ---------------------------------------------------------------------------
# Test 3: Fewer than 2 valid peers → graceful error, no exception
# ---------------------------------------------------------------------------

def test_fewer_than_two_valid_peers_returns_graceful_error():
    """If both peers have every multiple invalid, n_valid < 2 → error result,
    no ValueError/exception raised."""

    # Both peers: negative EBITDA/sales, no P/E → zero valid multiples
    bad_peer = _make_peer_fin(
        op_profit=-100.0, depreciation=0.0,   # EBITDA < 0
        sales=0.0,                             # sales zero → EV/Sales excluded
        trailing_pe=None,                      # no P/E
        net_profit=-5.0,
    )

    calls = {"BAD_A.NS": bad_peer, "BAD_B.NS": bad_peer}
    result = run_comps_valuation(
        _TARGET_FIN, ["BAD_A.NS", "BAD_B.NS"],
        fetch_fn=calls.__getitem__,
    )

    # Must NOT raise; must return a dict with a non-None error field
    assert isinstance(result, dict)
    assert result["error"] is not None
    assert result["comps_range"] is None
    assert result["implied_per_share"]["ev_ebitda"] is None
    assert result["implied_per_share"]["ev_sales"]  is None
    assert result["implied_per_share"]["pe"]        is None


# ---------------------------------------------------------------------------
# Test 4: Scale anchor — identical peer/target → implied ≈ current_price
# ---------------------------------------------------------------------------

def test_scale_anchor_identical_peer_implies_current_price():
    """When a peer's financials are identical to the target's, the EV/Sales and
    EV/EBITDA implied per-share values must equal the target's current price.

    Hand derivation
    ---------------
    target: mcap=2e9 rupees, shares=1e7 → current_price = 200 ₹
    peer EV = 200 + 20 - 10 = 210 cr  (in crore, same as target)
    EV/EBITDA = 210/40 = 5.25 → implied_EV_cr = 5.25×40 = 210
    bridge: equity_cr = 210 + 10 - 20 - 0 + 0 = 200 cr
    per_share = 200 × 1e7 / 1e7 = 200 ₹  ✓

    EV/Sales = 210/105 = 2.0 → implied_EV_cr = 2.0×105 = 210 → same bridge → 200 ₹ ✓
    """

    clone_peer = _make_peer_fin()   # identical to _TARGET_FIN
    calls = {"CLONE_A.NS": clone_peer, "CLONE_B.NS": clone_peer}

    result = run_comps_valuation(
        _TARGET_FIN, ["CLONE_A.NS", "CLONE_B.NS"],
        fetch_fn=calls.__getitem__,
    )

    assert result["error"] is None

    target_current_price = 200.0   # rupees = 2e9 / 1e7

    imp = result["implied_per_share"]

    assert imp["ev_ebitda"] is not None, "EV/EBITDA implied should be computed"
    assert abs(imp["ev_ebitda"] - target_current_price) < 0.01, (
        f"EV/EBITDA implied {imp['ev_ebitda']:.4f} ≠ target price {target_current_price}"
    )

    assert imp["ev_sales"] is not None, "EV/Sales implied should be computed"
    assert abs(imp["ev_sales"] - target_current_price) < 0.01, (
        f"EV/Sales implied {imp['ev_sales']:.4f} ≠ target price {target_current_price}"
    )
