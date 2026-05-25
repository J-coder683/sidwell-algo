# Antigravity prompt — paste this into a new Antigravity workspace

---

You are building **Sidwell**, a Python tool that values companies and applies investor frameworks (Buffett, Marks, KKR/Blackstone, distressed) to produce investment recommendations.

## Read these first (in this order)
1. `PROJECT.md` — vision, architecture, module sequence, constraints
2. `DATA_SOURCES.md` — required libraries, APIs, caching policy
3. `frameworks/buffett.md` — the lens you will implement this run
4. `frameworks/_future_lenses.md` — stubs to leave for future phases

## v0 deliverable (this run only)
Working end-to-end pipeline for ONE company through the Buffett lens.

```bash
python value.py ASIANPAINT.NS
```

Must produce a markdown report containing:
1. **Company snapshot** — price, market cap, last 5 years of revenue / gross margin / EBIT / FCF / debt / equity
2. **DCF valuation** — 5-year explicit forecast + Gordon-growth terminal, with every WACC component sourced (risk-free from FRED, ERP + beta from Damodaran data, debt cost from filings)
3. **Buffett lens** — all 8 checks per `frameworks/buffett.md`, each with ✅/❌ and the computed value next to the threshold
4. **Margin-of-safety check** — current price vs. DCF intrinsic value
5. **Verdict** — BUY / WAIT / WATCH / SKIP with one-paragraph reasoning per the rules in `frameworks/buffett.md`

## Hard constraints
- **Python 3.11+** only. No Jupyter. CLI script.
- **Free libraries only**: yfinance, nsepython, pandas, numpy, requests, pyyaml, fredapi, pytest. Nothing else.
- **No paid APIs.** FRED is free with free key — OK. Anything that charges, no.
- **No LLM calls anywhere in the pipeline.** The whole thing must be deterministic and runnable offline (with cache).
- **Every assumption traceable.** WACC inputs, projection drivers, comparable selection — all must appear in the report with a source.

## Mandatory project structure
```
sidwell/
├── value.py                  # CLI entry point — parses ticker, dispatches
├── data/
│   ├── __init__.py
│   ├── public.py             # yfinance + nsepython fetchers, with caching
│   ├── private.py            # YAML reader (stub for v0 — full impl in phase 5)
│   └── cache.py              # ~/.sidwell/cache/ TTL-based file cache
├── valuation/
│   ├── __init__.py
│   ├── dcf.py                # IMPLEMENT — full DCF
│   ├── comps.py              # stub — raise NotImplementedError
│   ├── precedent.py          # stub
│   └── lbo.py                # stub
├── lenses/
│   ├── __init__.py
│   ├── buffett.py            # IMPLEMENT — all 8 checks per spec
│   ├── marks.py              # stub
│   ├── kkr_blackstone.py     # stub
│   └── distressed.py         # stub
├── reports/
│   ├── __init__.py
│   └── render.py             # markdown report builder
├── frameworks/               # the .md spec files (read-only references — DO NOT EDIT)
├── tests/
│   ├── test_dcf.py           # at least 3 tests including a known-answer hand calc
│   ├── test_buffett.py       # at least 3 tests — known passes, known fails, edge case
│   └── test_data.py          # mock-based, no live API calls in tests
├── output/                   # generated reports land here
├── requirements.txt
├── README.md                 # how to install + run
└── .env.example              # FRED_API_KEY=, SEC_USER_AGENT=
```

## Verification (you are done when ALL of these pass)
1. `pip install -r requirements.txt` works on a clean venv
2. `pytest tests/` — all tests green
3. `python value.py ASIANPAINT.NS` — runs to completion, writes `output/asianpaints_report.md`
4. The report's Buffett score for Asian Paints is **6 or 7 out of 8** with margin-of-safety check **failing** (current price > 0.75 × DCF intrinsic). Verdict should be **WAIT**. If your output disagrees, debug rather than reshape the rules.
5. Re-running with no internet (after first run cached) still produces the report

## Leave as Artifacts
- The generated `output/asianpaints_report.md`
- The pytest output
- A 1-page `BUILD_NOTES.md` documenting any assumptions you made that aren't in the spec, plus any places you deviated and why

## What NOT to do
- Don't implement Marks, KKR/Blackstone, distressed lenses — stubs only
- Don't implement comps, precedent, LBO — stubs only
- Don't build a web UI
- Don't add any LLM call anywhere
- Don't paper over data-fetch failures with mock data in production code — fail loudly with a clear error
- Don't invent new Buffett checks; the 8 in the spec are exhaustive for v0

## After v0 ships
Stop and wait for instructions before building phase 2 (Marks lens). The architecture must be reviewed against a real first run before extending.

---
