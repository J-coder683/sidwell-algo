# Marks Why-Now Hybrid + Probabilistic MoS Overlay — Design Spec

**Date:** 2026-06-14
**Status:** Approved, pending implementation
**Two independent workstreams (implement and verify separately).**

---

## Workstream A — Marks check 14 (why-now) becomes hybrid

### Problem
Marks drops 5 of 14 checks when qualitative is unavailable (common on Cloud).
Of the five soft checks (5, 11, 12, 13, 14), only #14 (why-now / patient
opportunism) has a clean quantitative proxy: an observable price dislocation.
But `financials` carries no price history at lens-evaluation time. Check 5's
only in-lens proxy (margin-vs-peak) is misleading and is therefore deferred;
11/12/13 are irreducibly qualitative and stay soft.

### A1. Data plumbing (`value.py::analyze`)
After `financials = public.fetch_financials(ticker)`, best-effort fetch price
history and attach a derived scalar:

```python
try:
    from data.stooq import fetch_price_history
    _ph = fetch_price_history(ticker)            # DataFrame[Date, Close], empty on failure
    if _ph is not None and not _ph.empty:
        _closes = _ph["Close"].tail(252)         # ~1 trading year
        financials["price_high_1y"] = float(_closes.max())
except Exception as e:
    logger.warning(f"Price history unavailable for {ticker}: {e}")
```

Graceful: on any failure the key is simply absent. No new hard dependency in the
offline test path (lens tests pass fixtures directly; `value.analyze` is not run
offline).

### A2. Check 14 hybrid logic (`lenses/marks.py`)
Hard path (when `price_high_1y` present and `current_price > 0`):
```python
DISLOCATION_MIN = 0.20
drawdown = (price_high_1y - current_price) / price_high_1y   # fraction off the 1y high
hard_dislocation = drawdown >= DISLOCATION_MIN
```
Combined verdict:
- `passed` = `hard_dislocation` OR (LLM `why_now_signal.verdict == "dislocation_present"`)
- `applicable` = (hard path available) OR (qualitative available for this check)
- excluded (N/A) only when BOTH the hard path and qual are unavailable
- `proximity` = `proximity(drawdown, DISLOCATION_MIN, "above")` when the hard
  path is available; else None
- `detail` reports the drawdown and, when present, the LLM dislocation read.

This converts #14 from soft-only to hybrid: on Cloud with no qual but with price
history, #14 now scores instead of dropping.

### A3. Framework doc
Update `frameworks/marks.md` check 14 to document the hard path (price drawdown
>= 20% from 1y high) alongside the existing soft dislocation read. This is a
legitimate semantics change (the check is now hybrid), unlike pure-annotation work.

### A4. Tests
- New unit tests for #14: hard-only (qual absent, drawdown >= 20% -> pass &
  applicable), soft-only (no price high, LLM dislocation -> pass & applicable),
  both, and neither (-> N/A excluded).
- Marks verdicts shift for any fixture where #14 now applies. Snapshot
  (`tests/expected_report.md`) updates are EXPECTED but every changed line must
  be reviewed — only #14's line/score/verdict and dependent totals should move.
- Add `price_high_1y` to Marks fixtures where the hard path should be exercised.
- Offline suite stays green and < 15s.

### A5. Non-goals
- Check 5 stays soft (deferred — needs sector-cycle data not yet fetched).
- Checks 11/12/13 unchanged.

---

## Workstream B — Probabilistic margin-of-safety overlay (app-only)

### Problem
Every lens gates price on the single-point intrinsic value. The Monte Carlo band
(`valuation/monte_carlo.py`) already yields `prob_intrinsic_gt_price`, but it runs
lazily in the app and nothing surfaces it on the lens checks.

### B1. Behavior
Pure UI overlay in `app.py`. When Monte Carlo has been run for the current ticker
(results held in `st.session_state`), overlay a secondary badge
**"P(intrinsic > price) = X%"** on the margin-of-safety check rows in the lens
tabs:
- Buffett check key `12_margin_of_safety`
- Marks check key `1_deep_mos`

### B2. Constraints
- Zero change to lens logic, `passed`, `score`, `max_score`, `verdict`, or the
  markdown report. Annotation-only, app-only.
- When MC has not been run (no session results), render exactly as today.
- Reuse the existing `prob_intrinsic_gt_price` from the MC results dict; do not
  recompute.

### B3. Tests
App-layer overlay; no offline test change required beyond confirming the suite
stays green. (The MC engine itself is already covered by `tests/test_monte_carlo.py`.)
