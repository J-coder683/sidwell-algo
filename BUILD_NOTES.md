# BUILD NOTES — Sidwell v0.2

This document outlines key technical assumptions, calculation methods, architectural justifications, statistical conventions, model limitations, and migration notes for Sidwell v0.1 / v0.1.1 / v0.2.

## 1. Valuation Assumptions (DCF & WACC)

### Risk-Free Rate ($R_f$)
- **India**: Sourced from FRED series `INDIRLTLT01STM` (Interest Rates: Long-Term Government Bond Yields: 10-Year for India), yielding **7.12%** for our cached data.
- **US**: Sourced from FRED series `DGS10` (10-Year Treasury Constant Maturity Rate).

### Equity Risk Premium (ERP)
- Sourced from Aswath Damodaran's NYU Stern dataset (`ctryprem.xlsx`).
- For India, the default spread is added to the mature market ERP to yield a total ERP of **6.41%** (Mature ERP: 4.23%, Country Risk Premium: 2.18%).

### Beta ($\beta$)
- **Industry source**: We use Damodaran's industry **unlevered beta** for the ticker's mapped category (per `TICKER_INDUSTRY_MAP` in `data/public.py`). Tickers not in the map fall through to `DEFAULT_INDUSTRY` ("Chemical (Specialty)") with source tag `"default"`.
- **Re-levering**: The engine re-levers the unlevered beta using the target company's own capital structure:
  $$\beta_{levered} = \beta_{unlevered} \times \left(1 + (1 - t) \times \frac{\text{Debt}}{\text{Equity}}\right)$$
  For Asian Paints, due to its low leverage (D/E ratio $\approx 0.89\%$), the target levered beta is **0.96**.
- **Industry levered beta is fallback only**: If re-levering produces an invalid result (≤ 0 or > 3.0, indicating data issues), the engine falls back to Damodaran's industry-default levered beta. This is a guardrail, not the primary path.
- **Asian Paints v0.1.1 mapping**: `ASIANPAINT.NS` → `"Household Products"` (confirmed present in `'Industry Averages'` sheet by category-string audit — see Section 7).

### Cost of Debt ($K_d$)
- **Ceiling/Floor Bounds**: Sourced cost of debt ($K_d$) is bounded between $K_d = R_f + 0.01$ (floor, which is 8.12%) and $K_d = R_f + 0.05$ (ceiling, which is 12.12%).
- **Default Spread**: If the company's total debt is less than 5% of its total assets, we apply a default credit spread: $K_d = R_f + 0.02$.
- For Asian Paints, total debt (₹22.90B) is $7.54\%$ of total assets (₹303.71B), which is above the 5% threshold. Its calculated raw interest/debt cost is $9.91\%$. Since this is within the floor ($8.12\%$) and ceiling ($12.12\%$) bounds, the calculated cost of **9.91%** is applied directly.

### Tax Rate ($t$)
- Calculated as the 4-year average of $\text{Tax Provision} / \text{Pretax Income}$.
- For Asian Paints, this yields an effective tax rate of **26.06%**.

### Explicit Projections & WACC
- **Revenue Growth**: Based on historical 4-year CAGR. Capped between $5.0\%$ and $20.0\%$. For Asian Paints, this is **5.32%**.
- **Line Items**: EBIT, D&A, CapEx, and Net Working Capital changes are projected as historical 4-year averages relative to Revenue.
- **Terminal Growth ($g_{terminal}$)**: Capped at $\min(4.0\%, R_f - 1.0\%)$. For India, this is set to **4.00%**.
- **WACC**: Capped WACC is **13.20%**. 
- **WACC Invariant Assertion**: The engine strictly enforces `0.05 < wacc < 0.30` (using `raise ValueError` in production code) to fail loudly on unit-conversion errors.

---

## 2. Statistical Conventions
We use the sample standard deviation convention (`ddof=1`) everywhere statistical standard deviation appears (Moat Check #1 and Predictability Check #6).

### Volatility on YoY Growth Rates (Check #6)
- **Calculation**: Evaluates standard deviation on Year-over-Year revenue growth rates, rather than dispersion on revenue levels:
  `hist_growth_rates = [(hist_revenue[i] / hist_revenue[i-1] - 1.0) for i in range(1, len(hist_revenue))]`
  `hist_growth_std = np.std(hist_growth_rates, ddof=1)`
- **Sample Size Warning**: With only 3 YoY growth observations from a 4-year data slice, the sample standard deviation is highly noisy and sensitive to outliers. A single anomalous year (e.g. pandemic recovery or supply chain shock) can easily flip the predictability check verdict from pass to fail.
- **Roadmap Item**: Revisit the volatility threshold (currently 10.0%) when the data layer is upgraded to support 8–10 years of historical data.

---

## 3. Model Limitations
The calculated DCF intrinsic value (₹291.69) is significantly below the current market price of Asian Paints (₹2,657.80). This difference represents a structural model coverage gap:

1. **Depressed Historical Growth Window**: The historical 4-year window (2022–2025) starts from a high fiscal year 2022 base and spans a period of raw material inflation and post-pandemic demand normalization. This depresses the projected explicit growth rate to $5.32\%$, which understates the business's long-term normalized growth path.
2. **Elevated CapEx Period**: The historical CapEx/Revenue average ($5.92\%$) reflects an intense capacity expansion cycle. Applying this ratio to the projection period understates future Free Cash Flow generation by modeling perpetual high expansionary CapEx rather than lower maintenance CapEx.
3. **Terminal Growth Ceiling**: The $4.00\%$ terminal growth rate ceiling is too conservative for a premium consumer staple company in an emerging economy with long-term GDP growth expected at 6-7%.
4. **Treatment of Intrinsic Value**: The computed intrinsic value should be treated as a **strict conservative floor**, NOT a fair valuation estimate.
5. **Future Adjustments**: Subsequent phases should implement a 2-stage DCF growth model (allowing higher growth in years 1–5 before converging to terminal growth) and sector-aware/macro-aware terminal rates.

---

## 4. Buffett Lens Checks & Truthful Output

The verification-target hint of 6-7 / WAIT in the original prompt was a prior, not a fact — the truthful output supersedes it.

### Moat Check (Gross Margin Standard Deviation)
- **Result for Asian Paints**: The Gross Margin standard deviation over 4 years is **3.09%**. Since this is above the $3.0\%$ threshold, the check fails (❌).

### Predictability Check (YoY Growth Rate Volatility)
- **Result for Asian Paints**: The standard deviation of YoY growth rates is **11.90%**, which is above the $10.0\%$ threshold. Thus, the check fails (❌).

### FCF Margin Check
- **Result for Asian Paints**: The average FCF margin is **6.84%**, which is under the $10.0\%$ threshold. Thus, the check fails (❌).

### Score and Verdict
- **Total Buffett Score**: **4/8** (passing checks 2, 4, 5, 8; failing checks 1, 3, 6, 7).
- **Final Verdict**: **SKIP** (A score of 4/8 does not meet the 6/8 quality threshold, resulting in a SKIP recommendation). This is the honest and truthful output of the system under the specified rules.

---

## 5. v0 → v0.1 Migration
- In v0, reports were written to duplicate filenames (e.g. `output/asianpaints_report.md` with plural 's').
- In v0.1, the canonical file name has been unified to `{ticker_lowercase_no_suffix}_report.md` (e.g., `output/asianpaint_report.md`).
- As a build migration step, `output/asianpaints_report.md` has been deleted from the directory. The pytest exclusivity test (`test_no_duplicate_reports`) has been added to ensure that only a single report file is written per run.

---

## 6. v0.1 → v0.1.1 Changelog

- **Sector-aware industry mapping** (`TICKER_INDUSTRY_MAP` in `data/public.py`). Asian Paints now maps to `"Household Products"` (was `"Chemical (Specialty)"`). This affects the report's WACC table display tag only — see finding below.
- **Removed stale "5-year" docstring and vestigial slice** in `data/public.py` (`sorted_dates[-5:]` comment removed; authoritative 4-year slice at line 557+ unchanged).
- **Unified version label as `v0.1`** across `render.py`, `value.py`, `README.md`, and `tests/expected_report.md`.
- **Clarified that Damodaran industry levered beta is fallback only** (guardrail, not primary path).
- **Replaced hardcoded `range(4)`** with `range(len(hist_revenue))` in `lenses/buffett.py`.
- **Refactored sheet-selection** into `get_beta_sheet_name()` helper in `data/public.py` (single source of truth for both production lookup and category-string audit).
- **Added category-string audit** to guard against silent Damodaran category drift (see Section 7).

### Finding: Industry mapping is metadata-only in v0.1.1

The beta parsing code in `fetch_damodaran_data` uses a header-row scan with a 5-row lookback window (`range(max(0, ind_row_idx - 5), ind_row_idx)`). The actual header row in Damodaran's `betaGlobal.xls` `'Industry Averages'` sheet is at index 9, but the "Household Products" data row is at index 53. The 5-row window misses the header entirely, so `levered_idx` and `unlevered_idx` remain `None` and the code falls through to hardcoded defaults (levered=1.15, unlevered=0.95).

This means:
- `target_industry` and `industry_source` are correctly set and appear correctly in the report's WACC table.
- The actual beta **value** used in WACC (0.95) is unchanged from v0.1 — it is not sourced from Household Products; it is the Chemical (Specialty) hardcoded default.
- WACC (13.20%), intrinsic value (₹291.69), Buffett score (4/8), and verdict (SKIP) are identical to v0.1.

This is a **pre-existing v0.1 parsing bug**, not a v0.1.1 regression. Phase 2 must fix the beta extraction by reading with `header=9` and using exact column-name matching instead of the proximity-based header scan. Until then, `industry_unlevered_beta` always returns the hardcoded default regardless of mapping.

---

## 7. v0.1.1 Category Audit

Audit run on 2026-05-25 before code changes were committed. Validates all `TICKER_INDUSTRY_MAP` values against the Damodaran beta sheet that each ticker would actually use (per `get_beta_sheet_name()` logic).

```
  OK: ASIANPAINT.NS -> 'Household Products' found in sheet 'Industry Averages'
  OK: BERGEPAINT.NS -> 'Household Products' found in sheet 'Industry Averages'
  OK: PIDILITIND.NS -> 'Chemical (Diversified)' found in sheet 'Industry Averages'
  OK: HINDUNILVR.NS -> 'Household Products' found in sheet 'Industry Averages'
  OK: NESTLEIND.NS -> 'Food Processing' found in sheet 'Industry Averages'
  OK: ITC.NS -> 'Tobacco' found in sheet 'Industry Averages'
  OK: BRITANNIA.NS -> 'Food Processing' found in sheet 'Industry Averages'
  OK: HDFCBANK.NS -> 'Bank (Money Center)' found in sheet 'Industry Averages'
  OK: ICICIBANK.NS -> 'Bank (Money Center)' found in sheet 'Industry Averages'
  OK: BAJFINANCE.NS -> 'Financial Svcs. (Non-bank & Insurance)' found in sheet 'Industry Averages'
  OK: TCS.NS -> 'Software (System & Application)' found in sheet 'Industry Averages'
  OK: INFY.NS -> 'Software (System & Application)' found in sheet 'Industry Averages'
  OK: AAPL -> 'Computers/Peripherals' found in sheet 'Industry Averages'
  OK: MSFT -> 'Software (System & Application)' found in sheet 'Industry Averages'
  OK: DEFAULT 'Chemical (Specialty)' found in sheet 'Industry Averages' (India)
  OK: DEFAULT 'Chemical (Specialty)' found in sheet 'Industry Averages' (US)

OK - all 9 mapping values exist in their respective Damodaran sheets
```

Note: The cached `betaGlobal.xls` does not have separate emerging-markets/US sheets — it has a single `'Industry Averages'` sheet used for all tickers. The `get_beta_sheet_name()` helper falls through to the `'Industry Averages'` fallback for all current tickers. This is correct behavior given the current Damodaran global beta file structure.

---

## 7. v0.1.1 → v0.2 Changelog

- **Added qualitative ingestion layer:**
  - `data/documents.py` for PDF discovery from Drive-synced folder (`~/Sidwell-Drive/<TICKER>/`)
  - `analysis/qualitative.py` for Gemini-based structured extraction with 30-day TTL cache keyed on document hash
  - `analysis/prompts/qualitative_extraction.md` as the version-controlled Gemini prompt
- **Modified Buffett check #8** to be hybrid: hard deterministic blacklist AND soft LLM coherence signal. Both signals must pass. Defaults to hard-only when qualitative unavailable (v0.1.1 behavior).
- **Added `## 3.5 Qualitative Analysis`** section to the markdown report (forward guidance, risks, strategic themes, tone & coherence).
- **Gemini output cache** with 30-day TTL keyed on combined document hash. Cache invalidates automatically when document bytes change.
- **New `tests/test_qualitative.py`** with 5 mock-based tests (zero live API calls).
- **Updated `tests/test_snapshot.py`** to pass `mock_qualitative` fixture into both `evaluate_buffett_lens` and `render_markdown_report`.
- **Hand-edited `tests/expected_calculations.md`** (Section 6) and `tests/expected_report.md` (Section 3.5) to include qualitative section before running snapshot test.
- **Migrated from deprecated `google-generativeai` to `google-genai`** (new SDK, `google.genai.Client` pattern).
- **4 new hybrid check #8 tests** in `tests/test_buffett.py`.
- **4 new documents tests** in `tests/test_data.py`.

---

## 8. LLM Determinism Boundary

- Quantitative pipeline (DCF, Buffett checks 1-7) remains **pure deterministic Python**. Same inputs always produce same outputs.
- Only **check #8** and the **qualitative report section** depend on LLM output.
- Verdict may shift run-to-run for the same inputs if Gemini's coherence read drifts. This is the cost of incorporating qualitative judgment.
- **Mitigation:** The prompt is locked in `analysis/prompts/qualitative_extraction.md` and version-controlled. Any change to the prompt is a deliberate edit, tracked in git history.
- Report displays both hard and soft signals for check #8 so the user can see WHY a verdict shifted between runs.
- **Cache prevents drift for 30 days:** Once a set of documents has been analyzed, the result is cached by combined document hash. The LLM is only called when document bytes actually change (new or modified PDF).

---

## 9. Why "Free Equity Research" Was Dropped

Original v0.2 scope included scraping free equity research reports. After investigation, quality free equity research on Indian and US stocks barely exists — Moneycontrol/Trendlyne free tiers are retail-grade, broker research is paywalled, and aggregators have variable quality. Adding this would either fail to find sources or pollute the analysis with low-quality material. The four document types we already ingest (concall transcripts, IR decks, MD&A sections, annual reports) are the high-quality free corpus.

---

## 10. v0.2 Asian Paints Results

[Document the actual outputs from running `python value.py ASIANPAINT.NS` after placing at least one PDF in `~/Sidwell-Drive/ASIANPAINT.NS/`. Include: WACC, intrinsic value, all 8 Buffett checks with hybrid signal details for check #8, verdict, qualitative section contents. Whatever the pipeline produces is what goes here — no predictions, no anchoring on v0.1.1 results.]

**Awaiting user to place PDF in Drive folder to complete full-path verification.**
