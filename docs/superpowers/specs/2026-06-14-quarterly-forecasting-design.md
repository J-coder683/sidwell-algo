# Quarterly Data for Forecasting — Design Spec

**Date:** 2026-06-14
**Status:** Approved, pending implementation
**Decision:** v1 = "surface + feed the AI" — quarterly informs the model's
forecast assumptions (which flow into the DCF via the AJP) but the deterministic
engine's annual base logic is NOT changed. Auto-adjusting the engine base is a
deferred v2.

## Problem

Sidwell forecasts off annual data only. The scrapers already *locate* quarterly
data (`screener.py` finds the `quarters` table; `edgar.py` has quarterly
structures) but only to strip the TTM column from annual tables — the quarterly
series is never surfaced. Recent quarters are the freshest forward signal
(momentum, seasonality, cycle inflection), and the Marks cycle read is currently
sourced only from concall prose, not hard quarterly numbers.

## Sources (verified, free)
- **US — stockanalysis** `/stocks/{t}/financials/?p=quarterly` (20 quarters of
  Revenue, Operating Income, Net Income, EPS; free). Likely has an
  `api.stockanalysis.com` JSON endpoint — prefer it if found.
- **India — screener** the `quarters` section table (Sales, Operating Profit,
  OPM %, Net Profit per quarter), already located in `screener.py`.
- EDGAR quarterly structures exist as a US fallback.

---

## Layer 1 — Surface a quarterly series (data layer)

Parse the last ~12 quarters and attach to the financials dict:
```python
financials["quarterly"] = {
    "periods": ["Q1 2024", ...],         # most-recent-last
    "revenue": [...],                     # absolute, same units as annual (INR rupees / USD)
    "operating_profit": [...],
    "net_income": [...],
    "opm": [...],                         # operating margin per quarter (ratio)
}
```
- India: parse the screener `quarters` table; apply the same crore→rupee scaling
  the annual path uses.
- US: scrape the stockanalysis quarterly income statement (same approach as the
  existing annual scraper, quarterly URL/param), or its API endpoint.
- **Graceful:** any failure leaves `financials["quarterly"]` absent. Must NOT
  break or alter existing annual parsing.

## Layer 2 — Derived deterministic signals (light pre-processing)

New helper (e.g. `analysis/quarterly.py`) computing from `financials["quarterly"]`:
- `ttm_revenue`, `ttm_operating_profit` (sum of last 4 quarters)
- `latest_q_yoy_growth` (latest quarter vs same quarter a year ago — seasonality-safe)
- `ttm_yoy_growth` (TTM vs prior TTM)
- `qoq_accel_sign` (is sequential growth accelerating or decelerating)
- `seasonality_flag` (bool: do quarter-of-year revenue shares vary materially)

These are surfaced as context/anchors; in v1 they do NOT override the engine base.

## Layer 3 — Feed the AI (the primary v1 payoff)

- Extend `analysis/historical_context.py::build_historical_context_md` to append a
  **Quarterly Trend** markdown table (last ~12 quarters: revenue, YoY %, OPM %)
  plus the Layer-2 derived signals — only when `financials["quarterly"]` exists.
- Add a prompt instruction in `analysis/prompts/qualitative_extraction.md`
  directing the model to use the quarterly trend for: `cycle_position`
  (momentum/inflection evidence), `forward_guidance` grounding, and flagging
  deceleration/seasonality. Keep it short (a few lines) to avoid prompt bloat.
- **Bump `PROMPT_VERSION`** in `analysis/qualitative.py` (cache-key invariant —
  required by any prompt change).

## Layer 4 — Display (app)

A quarterly revenue + OPM mini-trend (Altair) in the DCF tab (or near the
historical context). Reuse existing chart styling / CSS color vars.

## Tests
- Quarterly parsing for each source against saved fixture HTML (follow the
  existing scraper test pattern; no live network — offline, <15s).
- Layer-2 signals: TTM sum, seasonality-safe YoY, seasonality flag, graceful
  behavior on short/missing series.
- `build_historical_context_md` includes the quarterly block when present and
  omits it cleanly when absent (existing annual output unchanged otherwise).
- No change to existing annual parsing or DCF/lens outputs (regression).

## Non-goals (deferred)
- Auto-adjusting the engine's base revenue / growth deterministically (v2).
- Quarterly DCF projection (not planned — annual projection stays).
- Metric Lab quarterly tokens (possible later).

## Suggested phasing for implementation
- **Phase 1:** Layer 1 + Layer 2 + tests (data foundation, independently verifiable).
- **Phase 2:** Layer 3 (AI context + prompt + PROMPT_VERSION) + Layer 4 (display).
