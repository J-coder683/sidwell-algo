# Antigravity Implementation Prompt — Sidwell DCF Engine v0.7 (banker-grade rebuild)

> **Coding agent:** Gemini 3.1 Pro in Antigravity.
> **Repo:** `J-coder683/sidwell-algo` (Python 3.12, venv at `.venv/`).
> **Source of truth:** `Sidwell_DCF_Rebuild_Plan.md` and `Reference Models/reference_models.md` in the repo root. Read both fully before writing code. This prompt is the build order; those two files are the spec detail.

---

## 0. THE ONE NON-NEGOTIABLE RULE (read first)

**No LLM / inference call may ever appear inside the deterministic engine.**

- Gemini runs **upstream only**: it reads filings + earnings calls and writes a single structured file — the **Assumption Justification Pack (AJP)**, `<TICKER>_AJP.json`.
- The **engine** is pure, deterministic Python: it reads the AJP + the quantitative data already scraped, then computes and renders. It never calls Gemini/OpenAI/Anthropic.
- **Enforce with CI:** add a test that greps the engine package (`sidwell/engine/`) for `import` of `google.generativeai`, `google.genai`, `anthropic`, `openai`, `boto3`, or `requests` and **fails the build** if any appear. This test is part of the definition of done.

Everything else in this prompt serves that wall.

---

## 1. WHAT EXISTS TODAY — AND WHAT YOU MUST NOT BREAK

Current flat repo (confirm before refactoring): `value.py` (CLI), `app.py` (Streamlit), `data/` (scrapers: `screener.py` for India, `stockanalysis.py` for US; `public.py` Damodaran/FRED; `documents.py`), `analysis/` (`qualitative.py` Gemini Flash extraction + `prompts/`), `valuation/dcf.py`, `lenses/{buffett,marks,kkr,blackstone,apollo}.py`, `reports/render.py` (markdown), `exports/{excel.py,pdf.py}`, `frameworks/*.md`, `tests/`.

**Hard regression constraints — the build is NOT done if any of these break:**

1. **The 222 existing tests must stay green** (`tests/` — run `.venv/Scripts/python.exe -m pytest tests/ -q`). Plus the new tests you write.
2. **The lens contract is sacred.** The 5 lenses read from `dcf_results`: `current_price`, `intrinsic_value_per_share`, `assumptions["tax_rate"]`, `assumptions["revenue_growth"]`, `assumptions["target_industry"]`. The new engine **replaces** `run_dcf_valuation` but its return value MUST remain a superset of today's `dcf_results` dict so the lenses, `reports/render.py`, `value.py`, and `app.py` keep working.
3. **Bank handling (v0.7.7) must be preserved exactly.** When `financials["is_bank"]` is true, the engine returns `not_applicable=True`, `intrinsic_value_per_share=None`, `wacc=None`, `projections=[]`, plus `not_applicable_reason`. The lenses already mark margin-of-safety checks `applicable=False` for banks (Buffett /13, Marks /12) and the report shows a "DDM coming soon" note. Do not regress this.
4. **Cyclical + structurally-cash-burning `ValueError` branches** in the current DCF (for non-bank tickers with non-positive intrinsic) must remain for the non-bank path.
5. **No PDFs/Excel written to disk by the extraction pipeline** — qualitative + AJP extraction stay in-memory (URL → BytesIO → pdfplumber → text → Gemini → JSON cache). The workbook is returned/saved only by the explicit export path.
6. **Cost rule:** all Gemini calls stay on **Gemini Flash** (the user's GCP budget is ~₹500/month; current spend ~₹15–20/month). The AJP must not double the bill — see §4.

### 1.1 NEW: rich historical data is already scraped — consume it, do NOT re-scrape

`data/scrapers/screener.py` (v0.8) now returns, in addition to the legacy 4-year keys, a `fin["statements"]` block with **up to 10 fiscal years** of fully itemized statements. **Use this as the historical foundation for the 3-statement model and the bridge.** Do not add new scraping for line items it already provides. Structure:

```python
fin["statements"] = {
  "years_annual": ["Mar 2017", ..., "Mar 2026"],   # oldest→newest, up to 10, TTM excluded
  "quarters":     [...],                            # up to 10 recent quarter labels
  "annual": {
    "profit_loss":   { "<label>": [values aligned to years_annual], ... },
    "balance_sheet": { ... },
    "cash_flow":     { ... },
  },
  "quarterly": { "profit_loss": { ... } },
  "ratios":      { "debtor days": [...], "inventory days": [...], "days payable": [...],
                   "cash conversion cycle": [...], "working capital days": [...], "roce %": [...] },
  "top_ratios":  { ... }, "peers": [ ... ],
}
```

**UNITS — important:** every numeric value in `fin["statements"]` is in **₹ crore** (as displayed on screener.in), NOT rupees. The workbook renders **₹ millions**, so **convert ₹ crore → ₹ mm by × 10** (1 crore = 10 million). The legacy top-level keys (`fin["revenue"]` etc.) remain in absolute rupees — don't mix the two; build the model off `statements`.

**Actual line-item keys available (normalized, lower-case)** — map the model to these names:
- **profit_loss:** `sales`, `sales growth %`, `expenses`, `material cost %`, `manufacturing cost %`, `employee cost %`, `other cost %`, `operating profit`, `opm %`, `other income`, `interest`, `depreciation`, `profit before tax`, `tax %`, `net profit`, `profit from associates`, `minority share`, `eps in rs`, `dividend payout %`. (Banks: `revenue` / `financing profit` instead of `sales` / `operating profit`.)
- **balance_sheet:** `equity capital`, `reserves`, `borrowings`, `long term borrowings`, `short term borrowings`, `lease liabilities`, **`non controlling int`**, `trade payables`, `other liability items`, `total liabilities`, `fixed assets`, `gross block`, `accumulated depreciation`, `cwip`, `investments`, `inventories`, `trade receivables`, `cash equivalents`, `loans n advances`, `other asset items`, `total assets`.
- **cash_flow:** `cash from operating activity`, `receivables`, `inventory`, `payables`, `working capital changes`, `direct taxes`, `cash from investing activity`, `fixed assets purchased`, `fixed assets sold`, `investments purchased`, `investments sold`, `cash from financing activity`, `proceeds from borrowings`, `repayment of borrowings`, `dividends paid`, `net cash flow`, `free cash flow`.

**This means the bridge fix (§6.9) and the 3-statement (§6.1) are now mostly DATA-DRIVEN for Indian tickers**: `non controlling int`, `lease liabilities`, `investments` (associates proxy) come straight from `statements.balance_sheet`; itemized WC from `cash_flow` + the `ratios` days. The AJP (§4) now supplies only forward-looking judgment + the line items screener does NOT have (preferred stock, pension, NOLs, option/RSU tranches) and US tickers where `statements` is absent. Where neither source has a value, flag `[ENGINE-EST]` per §4.3 — never omit.

---

## 2. SCOPE OF THIS PR

Deliver an institutional, self-justifying, **3-statement-backed** DCF that looks and behaves like the reference models (EasyJet, STLD, Alphabet, Ascend). Concretely, this PR includes **both**:

- **The deterministic engine + banker-grade workbook** (the plan's Phase 1 + the 3-statement and historical-reconciliation items the user is pulling forward from Phase 2).
- **The Gemini AJP producer** so the model runs end-to-end on a live ticker (not just fixtures).

**Explicitly OUT of scope (defer, but design the AJP schema to already carry their fields):** public + M&A comps / football-field; news + sell-side-ER ingestion into the AJP. Mark these clearly as Phase 2.

Because this is large, **before coding, confirm the repo layout (§5) and propose a stacked-commit sequence** (suggested: (1) AJP schema+loader+fixture+CI wall; (2) engine math + 3-statement; (3) workbook render + formatting; (4) AJP producer; (5) integration + consumer rewire). Land as stacked commits on one branch.

---

## 3. THE AI ↔ ENGINE WALL (architecture)

```
 GEMINI (upstream, AI-side)              AJP (JSON)            ENGINE (deterministic)
 analysis/ajp_builder.py        ──────────────────────▶   sidwell/engine/* + sidwell/render/*
 • reads ARs + 3 concalls (reuse the                       • reads AJP + scraped quant data
   in-memory pipeline already in                           • projects, builds 3 statements,
   analysis/qualitative.py)                                  discounts, bridges, renders xlsx
 • emits per-driver values + scenarios                     • ZERO inference calls (CI-enforced)
   + source tag + confidence + rationale
```

The engine owns ALL arithmetic. Gemini supplies only forward-looking judgment + the rationale/source/confidence annotation for every input (including engine-computed ones, which Gemini annotates but does not invent — see plan §5.3).

---

## 4. THE AJP — CONTRACT + PRODUCER + ENGINE BEHAVIOUR

### 4.1 Schema (`sidwell/ajp/ajp.schema.json` + dataclasses in `sidwell/ajp/schema.py`)

One entry per model input. Base each entry on the plan §4 schema:

```jsonc
{
  "meta": {
    "ticker": "BBTC.NS", "as_of": "2026-05-29", "gemini_run_id": "...",
    "currency": "INR_MM",                      // engine renders in ₹ millions
    "sources_ingested": ["AR_FY25","Q1FY26_call","Q2FY26_call","Q3FY26_call"],
    "fiscal_year_end_month": 3,                // drives FY labelling
    "last_actual_fy": "FY2025",                // most recent reported FY
    "is_holdco": true,                         // → SOTP/NAV path + NCI handling
    "scenario_active": "BASE"
  },
  "assumptions": [
    {
      "driver_id": "stage1_revenue_growth",    // stable key the engine maps to a cell
      "value": 0.085, "unit": "ratio",
      "scenario": { "BEAR": 0.05, "BASE": 0.085, "BULL": 0.11 },
      "split": { "volume": 0.06, "price": 0.025 },   // optional
      "source_type": "MGMT_GUIDANCE",          // enum, §4.4
      "confidence": "HIGH",                     // HIGH|MEDIUM|LOW|UNVERIFIED
      "verify_flag": null,                      // null|"ER"|"NEWS"|"EST"
      "rationale": "Mgmt guided 8–9% on Q3FY26 call (~12:04): ~6% volume, ~2.5% price ...",
      "interrogation_refs": ["1.1","1.2","1.4"]
    }
  ]
}
```

**Extend the schema** beyond the plan §4 so it carries everything the 3-statement + full bridge need (these are the `driver_id`s the engine expects — emit one entry each, or fall back per §4.3):

- **Revenue/margins:** `stage1_revenue_growth`, `stage2_terminal_convergence_growth`, `ebit_margin_target`, `ebit_margin_path` (or start+target), `tax_rate` (annotation of engine value), `sbc_pct_revenue`.
- **Convergence targets:** `capex_pct_sales_target`, `da_pct_sales_target`, `da_capex_converge_year`.
- **Working capital:** `dso_days`, `dio_days`, `dpo_days` — **prefer the scraped `statements.ratios` (`debtor days` / `inventory days` / `days payable`) and `statements.cash_flow` (`receivables`/`inventory`/`payables`) as the historical base; the AJP supplies only the forward path / overrides.** Fall back to `nwc_pct_sales` if absent. Plus `terminal_nwc_treatment`.
- **WACC:** `peer_betas` (list for Hamada), `target_debt_to_cap`, `equity_risk_premium`/`country_risk_premium`/`risk_free_rate` (annotations of engine values), `pretax_cost_of_debt_override`.
- **Terminal:** `terminal_growth`, `exit_ev_ebitda_multiple`, `reinvestment_ronic`.
- **Bridge:** `minority_interest`, `preferred_stock`, `associates_investments`, `unfunded_pension`, `capital_leases`, `nols`, `other_noncore_assets`. **Prefer the scraped `statements.balance_sheet` where present** — `non controlling int` → minority_interest, `lease liabilities` → capital_leases, `investments` → associates_investments. The AJP supplies the rest (preferred, pension, NOLs) and overrides; US tickers (no `statements`) rely entirely on the AJP.
- **Dilution:** `options_outstanding` (tranches: count + strike), `rsus_psus_outstanding`.
- **Holdco SOTP (when `is_holdco`):** `segments` (name, valuation method, stake %, value or driver), `holdco_discount`, `holdco_net_debt`.

### 4.2 Producer (`analysis/ajp_builder.py` — AI-side, NOT under `sidwell/engine/`)

- Reuse the **existing in-memory document pipeline** (`data/documents.py` discovery + `analysis/qualitative.py` PDF→text) — do not re-implement scraping or write PDFs to disk.
- **Cost-optimal design (required):** read each ticker's documents **once**. Prefer emitting the AJP from the **same Gemini call** that already produces the qualitative signals (one request returns `{qualitative: {...}, ajp: {...}}`), so you pay input tokens once. If a separate call is cleaner, **cache** it (Gemini context caching) and version the cache key.
- New prompt file `analysis/prompts/ajp_extraction.md` (or extend `qualitative_extraction.md`) instructing Gemini to output AJP-conformant JSON: every entry needs a non-empty `rationale`, an `interrogation_refs` tag, a `source_type`, and a `confidence`. Bump a `AJP_PROMPT_VERSION` constant to version the cache.
- **Validate** the produced AJP against `ajp.schema.json`. On invalid output: one repair retry, then fail with a clear error. Cache the validated AJP as `<TICKER>_AJP_<AJP_PROMPT_VERSION>.json` in the existing cache dir.
- Model = **Gemini Flash** (cost rule). Graceful-degrade: if Gemini/keys unavailable, the producer returns no AJP and the engine runs entirely on `[ENGINE-EST]` fallbacks (§4.3) — it never crashes.

### 4.3 Engine ingest / fallback / flagging (deterministic)

`sidwell/ajp/loader.py` loads + validates the AJP. Per assumption, the engine:
- Writes `value` to the input cell (blue font, §7).
- Writes `"[<SOURCE_TAG>] <rationale>"` to the Notes/Justification column.
- If `confidence < HIGH` **or** `verify_flag` set **or** `confidence == UNVERIFIED`: append the bracket flag (e.g. ` [VERIFY: ER]`) and **fill the cell yellow**.
- If `scenario` present: wire BEAR/BASE/BULL into the scenario block so the §7 switch toggles them.
- If a required `driver_id` is **missing**: engine falls back to its own computed/historical value, tags it `[ENGINE-EST]`, confidence `LOW`, flag `[VERIFY]`. **Never error; never insert an unflagged number.**
- Write an AJP `validation_report` + a **coverage score** (count HIGH/MED/LOW/flagged) to the Sources sheet and Cover.

### 4.4 Source taxonomy
`source_type` enum → `[TAG]` prefix: `FILING · EARNINGS_CALL · MGMT_GUIDANCE · SELL_SIDE_ER · NEWS · MACRO_FRED · DAMODARAN · PEER_COMPS · MARKET_CONVENTION · ENGINE_COMPUTED · ASSUMED`. Bracket flags: `[VERIFY: ER]`, `[VERIFY: NEWS]`, `[EST]`, `[ENGINE-EST]`. Anything below HIGH confidence gets a flag (plan §5.2).

**Ship a fixture `tests/fixtures/BBTC.NS_AJP.json`** that is schema-valid, `is_holdco=true`, with segment splits + NCI, so the SOTP/NCI path and flag logic are unit-testable without a live Gemini call.

---

## 5. MODULE / PACKAGE LAYOUT

Adopt the plan §7 package (confirm against the actual repo first; if conflicts, surface to the user before refactoring):

```
sidwell/
  ajp/      schema.py · loader.py · ajp.schema.json
  engine/   projections.py · statements.py · wacc.py · terminal.py · bridge.py · shares.py · fcf.py
            #  ↑ DETERMINISTIC ONLY — CI forbids inference/network imports here
  render/   workbook.py · formats.py
  cli.py    run(ticker, ajp_path|auto) -> xlsx
analysis/   ajp_builder.py   # AI-side producer (NOT under sidwell/engine/)
```

`valuation/dcf.py`'s `run_dcf_valuation` becomes a thin adapter that calls the new engine and returns the backward-compatible `dcf_results` superset (§1.2). `exports/excel.py` is **replaced** by `sidwell/render/workbook.py`; keep `reports/render.py` (markdown) working, updated minimally to read the new output.

---

## 6. ENGINE MECHANICS (all from `Sidwell_DCF_Rebuild_Plan.md` §6.3 + `reference_models.md` §2.2)

1. **3-statement core (new, user-requested):** build **Income Statement, Balance Sheet, Cash Flow** with **historical actuals + projections**, and a **`Balance Check` row that must equal zero** (EasyJet/Ascend pattern). **The historical line items are ALREADY scraped — read them from `fin["statements"]` (§1.1), up to 10 years, ₹ crore (×10 → ₹ mm).** Do not re-scrape. Map: IS from `statements.annual.profit_loss`, BS from `balance_sheet` (incl. `trade receivables`, `inventories`, `trade payables`, `gross block`, `accumulated depreciation`, `non controlling int`, `lease liabilities`), CF from `cash_flow` (incl. itemized `receivables`/`inventory`/`payables`). Where a specific line is genuinely absent for a ticker, flag `[ENGINE-EST]`. Include a **debt & equity schedule** with interest on **beginning** balances (handles circularity) and a revolver/cash-sweep where data allows.
2. **Driver-based revenue** (units × price where the AJP `split` is present), not a single CAGR.
3. **Growth fade / convergence:** Stage 1 explicit → Stage 2 **linearly decays** to terminal g (assert monotonic step-down in tests). EBIT margin, CapEx/Sales, NWC/Sales each **glide to their AJP target** by the final explicit year (Alphabet target-year style).
4. **CapEx ↔ D&A reconciliation:** D&A converges toward CapEx in steady state; stop pasting D&A as independent values.
5. **Itemized working capital** via DSO/DIO/DPO — seed from the scraped `statements.ratios` (`debtor days`/`inventory days`/`days payable`) and `statements.balance_sheet` (`trade receivables`/`inventories`/`trade payables`); project forward off the AJP path; fall back to NWC/Sales only if data missing (flagged).
6. **UFCF + mid-year discounting:** discount periods 0.5, 1.5, … (toggleable); explicit `Discount Period` row.
7. **WACC:** unlever peer betas → median asset beta → relever (Hamada) at **current AND target** capital structure; **synthetic-rating cost of debt** (interest-coverage → spread → Kd, Damodaran table) replacing naive interest/debt; average methods.
8. **Dual terminal value:** Gordon **and** exit EV/EBITDA; show both, average, flag divergence > a threshold. **Terminal reinvestment:** `ΔNWC_terminal = TerminalRevenue × g × (NWC/Revenue)` so terminal FCF isn't inflated.
9. **Full EV→equity bridge:** EV → (+) cash → (−) debt → (−) **minority interest** → (−) preferred → (+) associates/investments → (−) pension → (−) capital leases → (±) NOLs → equity → ÷ **diluted** shares.
10. **Holdco → SOTP/NAV path** when `meta.is_holdco`: sum segment stake values + other segments − holdco net debt − holdco discount, instead of consolidated UFCF. (This is the BBTC ~4x mis-valuation fix — must be exercised by the BBTC fixture test.)
11. **Diluted shares** via **treasury-stock method** on options + RSUs/PSUs (Alphabet `Shares` sheet), deterministic, from AJP `options_outstanding`/`rsus_psus_outstanding`.

---

## 7. WORKBOOK STRUCTURE + FORMATTING (banker standard)

**Currency: ₹ millions throughout.** Every header states units, e.g. `Revenue (₹ mm)`. The `fin["statements"]` values are in **₹ crore → × 10 to get ₹ mm** (1 crore = 10 million). (The legacy `fin[...]` keys are in absolute rupees; do not mix bases — build off `statements`.)

**Year columns / labelling (user-requested, critical):** use real fiscal-year names, **not** "Year 1…10". Derive the FY label from `statements.years_annual` (e.g. `"Mar 2025"` → `FY2025`, since FY ends March for Indian tickers; use `meta.fiscal_year_end_month` for the general case). Append **`A`** for historical actuals and **`E`** for projected/estimated, e.g. given the 10 scraped actuals `FY2017A…FY2026A`, project the next 10 as `FY2027E … FY2036E`. Keep **all scraped historical actual years** (up to 10) to the left of the projections; project **10 explicit years** (5 Stage-1 + 5 Stage-2 fade). Most-recent actual FY = last entry of `statements.years_annual`.

**Sheets (confirm/adjust names with the user-visible plan §6.1; include the 3-statement set the user added):**
1. `1_Cover` — ticker, date, price, intrinsic, upside, WACC, g, **confidence summary** (HIGH/MED/LOW/flagged counts).
2. `2_Drivers_Scenarios` — BEAR/BASE/BULL switch → ACTIVE column.
3. `3_Assumptions_Justifications` — the heart: each input value (blue) + source tag + rationale + confidence + flag, grouped by the 5 interrogation pillars.
4. `4_Income_Statement` — historical (A) + projected (E), full build (revenue → EBIT → NOPAT/net income).
5. `5_Balance_Sheet` — A + E, with **`Balance Check` = 0** row.
6. `6_Cash_Flow` — A + E (CFO/CFI/CFF), ties to BS cash.
7. `7_Debt_Schedule` — interest on beginning balances; revolver/cash-sweep where data allows.
8. `8_FCF_DCF` — UFCF build, mid-year discounting, PV.
9. `9_WACC` — Hamada unlever/relever (current + target), synthetic-rating Kd, method average.
10. `10_Terminal` — Gordon + exit EV/EBITDA, cross-check/average, terminal reinvestment row.
11. `11_Valuation_Bridge` — full EV→equity incl. NCI/preferred/associates/pension/leases/NOLs; SOTP path for holdco; ÷ diluted shares.
12. `12_Sensitivity` — WACC × g **and** WACC × exit multiple.
13. `13_Sources` — source list + AJP validation report + coverage score.

**Formatting (reference_models.md §2.1):** blue = hardcoded inputs; black = formulas; green = cross-sheet links; **yellow fill = flagged/needs-check**. Years as text; `%` as `0.0%`; multiples `0.0x`; currency `#,##0`; negatives in parentheses `(123)`; zeros as `-`. One professional font (Calibri/Arial). **All assumptions are separate cells referenced by formula — no hardcodes inside formulas. Zero `#REF!/#DIV/0!/#VALUE!/#NAME?` on export — gate export on a recalc check.**

---

## 8. INTEGRATION (rewire consumers)

- `valuation/dcf.py::run_dcf_valuation` → thin adapter over `sidwell.engine` returning the backward-compatible `dcf_results` superset (preserve all keys in §1.2; add new rich keys for the workbook).
- **Preserve the bank short-circuit and cyclical/cash-burning branches** exactly (§1.3, §1.4).
- `value.py` (CLI) + `app.py` (Streamlit) + `reports/render.py` (markdown) + `exports/pdf.py`: update to consume the new output; the new `.xlsx` comes from `sidwell/render/workbook.py` (retire `exports/excel.py`). Keep the existing per-lens PDF + bank "N/A" rendering working.
- The lenses are unchanged except they now receive a more accurate `intrinsic_value_per_share`.

---

## 9. ACCEPTANCE CRITERIA = DEFINITION OF DONE (write tests FIRST, TDD)

1. **AI-wall test:** build fails if any inference/network import exists under `sidwell/engine/`.
2. **AJP validation:** malformed AJP → clear error; missing `driver_id` → engine falls back, flags `[ENGINE-EST]`, never crashes. Unit-tested on fixtures.
3. **Flag propagation:** an `UNVERIFIED`/`verify_flag` input → yellow cell + bracketed note. Tested on the fixture AJP.
4. **No unflagged hardcodes:** every input cell has a non-empty Notes entry with a source tag. Test scans the rendered workbook.
5. **Zero formula errors** on export (recalc gate).
6. **Balance check = 0** on the 3-statement for the fixture(s).
7. **Bridge correctness:** on the **BBTC holdco fixture**, NCI is deducted / SOTP path taken; intrinsic is sane vs spot (no ~4x artifact).
8. **Math reconciliation:** one ticker hand-checked end-to-end; PV, TV, EV, equity, per-share tie within rounding.
9. **Convergence:** Stage-2 growth strictly decays toward g (assert monotonic step-down); CapEx/D&A converge.
10. **Year labelling:** columns render as `FY####A`/`FY####E` in ₹ mm — asserted.
11. **No regressions:** the existing **222 tests pass**; bank tickers still return `not_applicable` and lenses score Buffett /13, Marks /12; cyclical/cash-burning tickers still raise their documented `ValueError`; the scraper's `fin["statements"]` and legacy 4-year keys are unchanged.
12. **No PDFs/Excel written by the extraction pipeline** (in-memory only).

---

## 10. PROCESS INSTRUCTIONS FOR ANTIGRAVITY

1. Read `Sidwell_DCF_Rebuild_Plan.md` + `Reference Models/reference_models.md` fully first.
2. **Confirm the actual repo layout** before any refactor; if the proposed `sidwell/` package conflicts with reality, **surface the §9 design decision and the conflict to the user** rather than guessing.
3. Propose the **stacked-commit sequence** (§2) and proceed commit-by-commit, TDD throughout (tests before implementation).
4. Keep the engine free of any LLM/network call. Keep all Gemini work in `analysis/ajp_builder.py` on **Gemini Flash**, reading documents once (cost rule).
5. Do not weaken or delete the v0.7.7 bank handling or the cyclical branches.
6. **Out of scope (defer to Phase 2, but keep AJP schema fields ready):** public + M&A comps / football-field; news + sell-side-ER ingestion.
7. On completion, run the full test suite and report: tests passed, coverage score on a sample ticker, and any inputs that fell back to `[ENGINE-EST]`.
