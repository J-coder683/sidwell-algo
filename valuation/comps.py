"""
valuation/comps.py — Simplified trailing trading comps.

Peers are caller-supplied. Multiples are computed from screener P&L/BS data
(not scraped from a screener multiple screen, which is unreliable / paywalled).

Scale convention
----------------
- All intermediate arithmetic is in CRORE (matches screener statements).
- market_cap from fin dict is in RUPEES → divide by 1e7 to get crore.
- Final per-share values are in RUPEES → multiply equity_cr × 1e7 / shares.

Bridge sign convention (mirrors sidwell/engine/bridge.py line 25)
------------------------------------------------------------------
  equity_value = ev + cash - debt - nci - preferred + investments - pension + nols

For comps (preferred/pension/nols are zero / not available from trailing data):
  equity_cr = ev_cr + cash - debt - nci + investments
"""

import logging
from statistics import median

from data.scrapers.screener import fetch_screener_financials

logger = logging.getLogger("sidwell.valuation.comps")

_MIN_PEERS = 2
_MAX_PEERS = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _last(arr):
    """Return last non-None element of arr, or None."""
    for x in reversed(arr or []):
        if x is not None:
            return x
    return None


def _metrics(fin: dict) -> dict:
    """Extract trailing valuation metrics from a screener financials dict.

    Everything that flows into multiples/bridge stays in CRORE.
    market_cap is in rupees → /1e7 for crore.
    """
    st = fin["statements"]["annual"]
    bs = st["balance_sheet"]
    pl = st["profit_loss"]

    mcap_cr = (fin.get("market_cap") or 0) / 1e7

    debt = ((_last(bs.get("borrowings")) or 0)
            + (_last(bs.get("lease liabilities")) or 0))
    cash = _last(bs.get("cash equivalents")) or 0
    nci  = _last(bs.get("non controlling int")) or 0
    inv  = _last(bs.get("investments")) or 0

    ev = mcap_cr + debt - cash

    ebitda = ((_last(pl.get("operating profit")) or 0)
              + (_last(pl.get("depreciation")) or 0))
    sales  = (_last(pl.get("sales")) or _last(pl.get("revenue")))
    np_    = _last(pl.get("net profit"))

    return {
        "ev":     ev,
        "ebitda": ebitda,
        "sales":  sales,
        "pe":     fin.get("trailing_pe"),
        "debt":   debt,
        "cash":   cash,
        "nci":    nci,
        "inv":    inv,
        "np":     np_,
        "shares": fin.get("shares_outstanding"),
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_comps_valuation(
    target_financials: dict,
    peer_tickers: list,
    fetch_fn=fetch_screener_financials,
) -> dict:
    """Run simplified trailing trading comps.

    Parameters
    ----------
    target_financials : dict
        Screener financials dict for the target company (already fetched).
    peer_tickers : list[str]
        2–5 peer tickers (e.g. ["INFY.NS", "WIPRO.NS"]).
    fetch_fn : callable
        Screener fetch function; swapped for a mock in tests.

    Returns
    -------
    dict with keys:
        peer_multiples   – per-peer raw multiples
        medians          – {ev_ebitda, ev_sales, pe} → {min, med, max}
        implied_per_share – {ev_ebitda, ev_sales, pe} in RUPEES
        comps_range      – {low, high} over valid methods
        excluded         – list of (ticker, reason) tuples
        n_peers          – raw count supplied
        n_valid          – peers for which ≥1 multiple was usable
        caveat           – non-empty when n_valid < 3
        error            – present (and non-None) when result is degenerate
    """
    n_peers = len(peer_tickers or [])

    # ── Peer count guard (return graceful error, no exception) ──────────────
    if n_peers < _MIN_PEERS:
        return _error_result(
            peer_tickers or [],
            f"Too few peers supplied ({n_peers}); minimum is {_MIN_PEERS}.",
        )

    # ── Collect raw peer multiples ──────────────────────────────────────────
    peer_multiples: list[dict] = []
    excluded: list[tuple[str, str]] = []

    ev_ebitda_vals: list[float] = []
    ev_sales_vals:  list[float] = []
    pe_vals:        list[float] = []

    peers_with_any_multiple: set[str] = set()

    for ticker in peer_tickers[:_MAX_PEERS]:
        try:
            pfin = fetch_fn(ticker)
            m = _metrics(pfin)
        except Exception as exc:
            excluded.append((ticker, f"fetch/parse error: {exc}"))
            continue

        row: dict = {"ticker": ticker}
        any_valid = False

        # EV/EBITDA
        if m["ebitda"] is not None and m["ebitda"] > 0 and m["ev"] is not None:
            ratio = m["ev"] / m["ebitda"]
            row["ev_ebitda"] = ratio
            ev_ebitda_vals.append(ratio)
            any_valid = True
        else:
            row["ev_ebitda"] = None
            excluded.append((ticker, "EV/EBITDA: non-positive or missing EBITDA"))

        # EV/Sales
        if m["sales"] is not None and m["sales"] > 0 and m["ev"] is not None:
            ratio = m["ev"] / m["sales"]
            row["ev_sales"] = ratio
            ev_sales_vals.append(ratio)
            any_valid = True
        else:
            row["ev_sales"] = None
            excluded.append((ticker, "EV/Sales: non-positive or missing sales"))

        # P/E
        pe = m["pe"]
        if pe is not None and pe > 0:
            row["pe"] = pe
            pe_vals.append(pe)
            any_valid = True
        else:
            row["pe"] = None
            excluded.append((ticker, "P/E: None or non-positive"))

        row["ev"]     = m["ev"]
        row["ebitda"] = m["ebitda"]
        row["sales"]  = m["sales"]
        peer_multiples.append(row)

        if any_valid:
            peers_with_any_multiple.add(ticker)

    n_valid = len(peers_with_any_multiple)

    # ── Minimum valid-peer guard ────────────────────────────────────────────
    if n_valid < _MIN_PEERS:
        return _error_result(
            peer_tickers,
            f"Fewer than {_MIN_PEERS} peers had any usable multiple "
            f"(n_valid={n_valid}). Check that peer tickers exist on screener.",
            peer_multiples=peer_multiples,
            excluded=excluded,
            n_peers=n_peers,
            n_valid=n_valid,
        )

    # ── Compute medians ─────────────────────────────────────────────────────
    def _stats(vals: list[float]) -> dict | None:
        if not vals:
            return None
        return {"min": min(vals), "med": median(vals), "max": max(vals)}

    medians = {
        "ev_ebitda": _stats(ev_ebitda_vals),
        "ev_sales":  _stats(ev_sales_vals),
        "pe":        _stats(pe_vals),
    }

    # ── Target metrics ──────────────────────────────────────────────────────
    t = _metrics(target_financials)

    # ── Implied per-share (RUPEES) ──────────────────────────────────────────
    implied: dict[str, float | None] = {
        "ev_ebitda": None,
        "ev_sales":  None,
        "pe":        None,
    }

    valid_implied: list[float] = []

    # Helper: bridge EV → equity → per-share (crore → rupees)
    def _ev_to_ps(ev_cr: float) -> float | None:
        shares = t.get("shares")
        if not shares or shares <= 0:
            return None
        eq_cr = ev_cr + t["cash"] - t["debt"] - t["nci"] + t["inv"]
        return (eq_cr * 1e7) / shares

    if medians["ev_ebitda"] and t["ebitda"] is not None and t["ebitda"] > 0:
        ev_cr = medians["ev_ebitda"]["med"] * t["ebitda"]
        ps = _ev_to_ps(ev_cr)
        if ps is not None:
            implied["ev_ebitda"] = ps
            valid_implied.append(ps)

    if medians["ev_sales"] and t["sales"] is not None and t["sales"] > 0:
        ev_cr = medians["ev_sales"]["med"] * t["sales"]
        ps = _ev_to_ps(ev_cr)
        if ps is not None:
            implied["ev_sales"] = ps
            valid_implied.append(ps)

    if medians["pe"] and t["np"] is not None and t["shares"] and t["shares"] > 0:
        target_eps = (t["np"] * 1e7) / t["shares"]   # rupees per share
        implied["pe"] = medians["pe"]["med"] * target_eps
        valid_implied.append(implied["pe"])

    comps_range = (
        {"low": min(valid_implied), "high": max(valid_implied)}
        if valid_implied else None
    )

    caveat = "n<3 is noisy" if n_valid < 3 else ""

    return {
        "peer_multiples":    peer_multiples,
        "medians":           medians,
        "implied_per_share": implied,
        "comps_range":       comps_range,
        "excluded":          excluded,
        "n_peers":           n_peers,
        "n_valid":           n_valid,
        "caveat":            caveat,
        "error":             None,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _error_result(
    peer_tickers,
    error_msg: str,
    peer_multiples=None,
    excluded=None,
    n_peers=None,
    n_valid=0,
) -> dict:
    logger.warning("run_comps_valuation: %s", error_msg)
    return {
        "peer_multiples":    peer_multiples or [],
        "medians":           {"ev_ebitda": None, "ev_sales": None, "pe": None},
        "implied_per_share": {"ev_ebitda": None, "ev_sales": None, "pe": None},
        "comps_range":       None,
        "excluded":          excluded or [],
        "n_peers":           n_peers if n_peers is not None else len(peer_tickers or []),
        "n_valid":           n_valid,
        "caveat":            "",
        "error":             error_msg,
    }
