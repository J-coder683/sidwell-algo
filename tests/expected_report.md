# Investment Analysis Report: FICTITIOUS.NS
**Generated on**: January 01, 2026
**Valuation Engine**: Discounted Cash Flow (DCF)
**Investor Lenses**: Warren Buffett + Howard Marks (v0.4)

## Executive Summary
| Metric | Value | Source / Detail |
| :--- | :--- | :--- |
| **Current Price** | ₹50.00 | Yahoo Finance |
| **Intrinsic Value (DCF)** | ₹29.20 | Sidwell DCF Engine |
| **Margin of Safety** | Trading at 1.7x intrinsic value (target ≤ 0.75x) | Current Discount to Intrinsic |
| **Buffett Score** | **13/14** | Buffett Lens (14 checks) |
| **Buffett Verdict** | **WAIT** ⏳ | Buffett Lens Rules |
| **Marks Score** | **11/14** | Marks Lens (14 checks) |
| **Marks Verdict** | **WAIT** ⏳ | Marks Lens Rules |

### Verdict Summary
> **Buffett**: **WAIT** — High-quality business that satisfies most Buffett criteria but lacks margin of safety. Set alert at buy-trigger price: ₹21.90 (75% of intrinsic value).
>
> **Marks**: **WAIT** — Risk architecture acceptable but MoS or multiple position inadequate. Set re-rating alert at 17.52 (60% of intrinsic = 40% MoS).

## 1. Company Snapshot
Historical financial statements over the last 4 years:

| Metric | 2022 | 2023 | 2024 | 2025 |
| :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹100.00 | ₹110.00 | ₹121.00 | ₹133.10 |
| Gross Margin (%) | 40.00% | 40.00% | 40.00% | 40.00% |
| EBIT | ₹20.00 | ₹22.00 | ₹24.20 | ₹26.62 |
| Free Cash Flow | ₹11.50 | ₹12.80 | ₹14.23 | ₹15.80 |
| Total Debt | ₹20.00 | ₹20.00 | ₹20.00 | ₹20.00 |
| Stockholders Equity | ₹60.00 | ₹66.00 | ₹72.60 | ₹79.86 |

## 2. DCF Valuation & WACC Sourcing
Every component of the Weighted Average Cost of Capital (WACC) is explicitly sourced and modeled below:

### WACC Components & Assumptions
| Component | Value | Source / Reference |
| :--- | :--- | :--- |
| **Risk-Free Rate ($R_f$)** | 6.00% | FRED Series: `INDIRLTLT01STM` (India 10Y G-Sec) |
| **Mature Market ERP** | 5.00% | Damodaran NYU Stern (Mature Equity Risk Premium) |
| **Country Risk Premium** | 2.00% | Damodaran NYU Stern (Country default spread adjusted) |
| **Total Equity Risk Premium** | 7.00% | Damodaran mature ERP + country premium = 7.00% |
| **Industry Unlevered Beta** | 0.90 | Damodaran 'Chemical (Specialty)' (hardcoded fallback (Damodaran lookup failed)) |
| **Target Levered Beta ($\beta$)** | 0.93 | Re-levered using actual D/E = 0.93 |
| **Cost of Equity ($K_e$)** | 12.49% | CAPM: $R_f + \beta \times ERP$ = 12.49% |
| **Cost of Debt ($K_d$)** | 10.00% | Calculated: int_expense/debt = 10.00% |
| **Effective Tax Rate ($t$)** | 25.00% | 4-year historical average from filings |
| **Equity Weight ($W_e$)** | 96.15% | Market Cap / (Market Cap + Total Debt) |
| **Debt Weight ($W_d$)** | 3.85% | Total Debt / (Market Cap + Total Debt) |
| **Computed WACC** | **12.30%** | Weighted cost of capital = **12.30%** |

### 5-Year High-Growth Forecast (Stage 1)
Projections are based on historical averages relative to Revenue. Revenue growth is projected at **10.00%** (historical 4y CAGR capped between 5% and 20%).

| Metric | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹146.41 | ₹161.05 | ₹177.16 | ₹194.87 | ₹214.36 |
| EBIT | ₹29.28 | ₹32.21 | ₹35.43 | ₹38.97 | ₹42.87 |
| Taxes | ₹7.32 | ₹8.05 | ₹8.86 | ₹9.74 | ₹10.72 |
| D&A | ₹4.39 | ₹4.83 | ₹5.31 | ₹5.85 | ₹6.43 |
| CapEx | ₹7.32 | ₹8.05 | ₹8.86 | ₹9.74 | ₹10.72 |
| NWC Change (CF) | ₹0.00 | ₹0.00 | ₹0.00 | ₹0.00 | ₹0.00 |
| Free Cash Flow | ₹19.03 | ₹20.94 | ₹23.03 | ₹25.33 | ₹27.87 |
| Discount Factor | 1.1230 | 1.2611 | 1.4161 | 1.5903 | 1.7858 |
| PV of Cash Flow | ₹16.95 | ₹16.60 | ₹16.26 | ₹15.93 | ₹15.60 |

### 5-Year Fade Forecast (Stage 2) — growth fading from 10.00% to 4.00%

| Metric | Year 6 | Year 7 | Year 8 | Year 9 | Year 10 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹233.22 | ₹250.95 | ₹267.01 | ₹280.89 | ₹292.13 |
| EBIT | ₹46.64 | ₹50.19 | ₹53.40 | ₹56.18 | ₹58.43 |
| Taxes | ₹11.66 | ₹12.55 | ₹13.35 | ₹14.04 | ₹14.61 |
| D&A | ₹7.00 | ₹7.53 | ₹8.01 | ₹8.43 | ₹8.76 |
| CapEx | ₹11.66 | ₹12.55 | ₹13.35 | ₹14.04 | ₹14.61 |
| NWC Change (CF) | ₹0.00 | ₹0.00 | ₹0.00 | ₹0.00 | ₹0.00 |
| Free Cash Flow | ₹30.32 | ₹32.62 | ₹34.71 | ₹36.52 | ₹37.98 |
| Discount Factor | 2.0054 | 2.2521 | 2.5290 | 2.8400 | 3.1892 |
| PV of Cash Flow | ₹15.12 | ₹14.49 | ₹13.73 | ₹12.86 | ₹11.91 |

### Terminal Value
- Final fade year (Year 10) FCF: ₹37.98
- Terminal growth (Gordon): 4.00%
- Sector mapping: SECTOR_TERMINAL_GROWTH lookup for (Chemical (Specialty), India)
- Terminal Value: ₹476.02
- PV of Terminal Value (discounted from Year 10): ₹149.26

### Valuation Bridge
- **PV of Explicit FCFs**: ₹149.44
- **PV of Terminal Value (g = 4.00%)**: ₹149.26
- **Enterprise Value**: ₹298.70
- **Add: Cash & Equivalents**: ₹13.31
- **Less: Total Debt**: ₹20.00
- **Equity Value**: ₹292.01
- **Shares Outstanding**: 10
- **Intrinsic Value per Share**: **₹29.20**

## 3. Buffett Investor Lens
All 14 checks per Warren Buffett's framework across 4 Parts (frameworks/buffett.md):

### Part A — Business Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Durable competitive advantage (moat) | ✅ | 0.00% | < 3.0% | stdev = 0.00% < 3% |
| High return on invested capital | ✅ | 22.26% | > 15.0% | 4y avg = 22.26% > 15% |
| Strong free-cash-flow generation | ✅ | 0.12 / 0.37 | Margin > 10% & Growth > 0% | avg margin = 11.69%, FCF growth = 37.42% |
| Earnings predictability | ✅ | 0.10 / 0.00 | 5% < CAGR < 30% & YoY Growth StDev < 10.0% | Revenue CAGR = 10.00%, YoY Growth StDev = 0.00% |

_Part A — Business Quality: **4/4 passed**_

### Part B — Financial Health

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Conservative balance sheet | ✅ | 0.65 / 13.31 | Debt/EBITDA < 3x & Coverage > 5x | Debt/EBITDA = 0.65x, Int. Coverage = 13.31x |
| ROE without excess leverage | ✅ | 0.23 / 0.60 | ROE > 15% & Equity/Assets > 40% | 4y avg ROE = 22.82%, Equity/Assets = 60.00% |
| Liquidity cushion (Gibraltar test) | ✅ | 13.31 / 20.00 | Cash / Debt > 0.5x OR debt-free | Cash / Debt = 0.67x (> 0.5) |

_Part B — Financial Health: **3/3 passed**_

### Part C — Management & Capital Allocation

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Anti-dilution discipline | ✅ | [4 values] | <= 2% growth over 4y | Share count growth (4y): +0.00% (threshold: <= +2%) |
| Capital allocation track record | ✅ | 0.010928017051142658 / True | ROIC not declining > 3pp AND capital returned | ROIC trend (latter-2y vs earlier-2y): +1.09pp; capital returned to shareholders: yes |
| Owner orientation | ✅ | 0.1 / owner_oriented | Insiders > 5% OR LLM = owner_oriented | Insider ownership: 10.00% (PASS at >5%). LLM owner-orientation: owner_oriented |
| Management coherence | ✅ | True | LLM coherence = coherent | Soft check: PASS (LLM coherence: coherent). Numeric claims tie out across documents and strategy is consistent. |

_Part C — Management & Capital Allocation: **4/4 passed**_

### Part D — Margin of Safety & Holdability

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin of safety | ❌ | Trading at 1.7x intrinsic | > 25.0% | Trading at 1.7x intrinsic value (target ≤ 0.75x) (Price: 50.00, Intrinsic: 29.20) |
| Understandable business (hard blacklist) | ✅ | True | Ticker not BTC/ETH/COIN | Hard check: PASS (ticker not in avoided-sector blacklist) |
| Holdability (20-year test) | ✅ | holdable_20y | LLM verdict = holdable_20y | LLM holdability verdict: holdable_20y. Demand category structurally enduring; no single-technology dependence identified in documents. |

_Part D — Margin of Safety & Holdability: **2/3 passed**_

**Total Buffett Score**: **13/14**

## 3.5 Qualitative Analysis
Based on 1 document(s): fixture_concall.pdf. Model: `gemini-3.5-flash`.

### Forward Guidance
- **FY27** (revenue): Management expects 10% revenue growth driven by capacity expansion. _[fixture_concall.pdf]_

### Risk Callouts
- **input cost volatility**: Raw material prices remain a watchpoint. _[fixture_concall.pdf]_

### Strategic Themes
- **premium product mix**: Mix shift toward premium SKUs continues. _[fixture_concall.pdf]_

### Tone & Coherence
- **Tone (current)**: confident
- **Tone (trajectory)**: stable
- **Coherence verdict**: coherent

_Management remained confident across the period, with a stable narrative._

_Numeric claims tie out across documents and strategy is consistent._

### Marks-Relevant Signals
- **Owner orientation**: owner_oriented — Letter uses 'shareholders as partners' framing; admits two FY24 mis-allocations by name.
- **Holdability (20y)**: holdable_20y — Demand category structurally enduring; no single-technology dependence identified in documents.
- **Sector cycle**: mid_cycle / Company cycle: mid — Capacity utilization mid-band; pricing actions modest; no signs of peak-cycle euphoria.
- **Variant perception**: present=True, specificity=high. Consensus: 'Market expects continued strong growth driven by premiumisation.'
- **Management humility**: humble — Management declines multi-year forecast; acknowledges raw material visibility limited to 2 quarters; references two past allocation errors by name.
- **Why now**: dislocation_present — Post-Q3 FY26 commodity-cost shock has compressed multiples temporarily.

## 3.6 Marks Investor Lens
All 14 checks per Howard Marks's risk-first framework across 4 Parts (frameworks/marks.md):

### Part A — Margin of Safety & Asymmetric Payoff

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Deep margin of safety | ❌ | Trading at 1.7x intrinsic | > 40% | MoS = -71.23% (< 40% threshold) — Price 50.00 vs Intrinsic 29.20 |
| Asymmetric upside-to-downside payoff | ❌ | 0.000 | > 3.0x | Asymmetry ratio = 0.00 (< 3.0 threshold) |
| Downside protection (tangible book) | ❌ | 15.97% | > 30% | Equity/MCap = 15.97% (<= 30%) |
| Multiple expansion not exhausted | ✅ | 18.000 | < 25x (v0.3 placeholder; sector comp in v0.4) | Trailing P/E = 18.0x (< 25x) |

_Part A — Margin of Safety & Asymmetric Payoff: **1/4 passed**_

### Part B — Cycle Position

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Sector cycle position | ✅ | mid_cycle | trough | early_recovery | mid_cycle | LLM sector cycle: mid_cycle. Capacity utilization mid-band; pricing actions modest; no signs of peak-cycle euphoria. |
| Company earnings vs cyclical peak | ✅ | 100.00% | > 70% of peak | Latest NI / Peak NI = 100.0% |
| Sentiment — going against the crowd | ✅ | 3.200 | Mean rating 2.5-4.0 (mixed/cautious consensus) | Consensus rating mean: 3.20 (PASS — Marks prefers 2.5-4.0 mixed/cautious; strong buy consensus is a contrarian caution signal) |

_Part B — Cycle Position: **3/3 passed**_

### Part C — Risk Architecture

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Capital structure resilience | ✅ | 0.65 / 13.31 | Debt/EBITDA < 4x AND Coverage > 4x | Debt/EBITDA = 0.65x, Coverage = 13.31x |
| FCF stability through downturn | ✅ | 11.500 | All 4 years positive FCF | 4y FCF: [11.5, 12.8, 14.23, 15.8] |
| Volatility / beta | ✅ | 0.850 | < 1.5 | Beta = 0.85 (< 1.5) |
| No single-point failure mode | ✅ | 0 | <= 1 concentration/regulatory risk flagged | Concentration/regulatory risks identified: 0 |

_Part C — Risk Architecture: **4/4 passed**_

### Part D — Second-Level Thinking & Contrarianism

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Variant perception | ✅ | True | variant_present=true AND specificity=high | Variant: True, Specificity: high. Consensus: 'Market expects continued strong growth driven by premiumisation.' | Company view: 'Management guides modest growth, citing cyclical headwinds and competitive intensity.' |
| Management humility (knowing what you don't know) | ✅ | humble | verdict = humble | LLM humility verdict: humble. Management declines multi-year forecast; acknowledges raw material visibility limited to 2 quarters; references two past allocation errors by name. |
| Patient opportunism (why now) | ✅ | dislocation_present | verdict = dislocation_present | Why-now: dislocation_present. Event: Post-Q3 FY26 commodity-cost shock has compressed multiples temporarily.. Sector has de-rated 25% in trailing 12 months; entry timing favorable due to forced selling from FII redemptions, not fundamental deterioration. |

_Part D — Second-Level Thinking & Contrarianism: **3/3 passed**_

**Total Marks Score**: **11/14**

## 4. Margin-of-Safety Check
Current Stock Price: **₹50.00**
DCF Intrinsic Value: **₹29.20**
Required Margin of Safety: **25.00%** (Graham & Dodd standard — Buffett lens)
Computed Margin of Safety: Trading at 1.7x intrinsic value (target ≤ 0.75x)
### Status: [FAIL] ❌
The stock trades above the safety threshold. Trading at 1.7x intrinsic value is insufficient for investment under the Buffett framework.

## 5. Investment Verdict
**BUFFETT RECOMMENDATION: WAIT**

High-quality business that satisfies most Buffett criteria but lacks margin of safety. Set alert at buy-trigger price: ₹21.90 (75% of intrinsic value).

**Action Item**: Set alert at buy-trigger price: **₹21.90** (75% of intrinsic value).

**MARKS RECOMMENDATION: WAIT**

Risk architecture acceptable but MoS or multiple position inadequate. Set re-rating alert at 17.52 (60% of intrinsic = 40% MoS).

**Marks Action Item**: Set re-rating alert at **₹17.52** (60% of intrinsic = 40% MoS).

## 6. Dual-Lens Synthesis
Sidwell preserves both lens verdicts without collapsing them to a single recommendation.
The disagreement between lenses IS the insight. See `frameworks/marks.md` section 'How This Lens Differs from Buffett' for design rationale.

| | Buffett | Marks |
| :--- | :---: | :---: |
| **Score** | 13/14 | 11/14 |
| **Verdict** | **WAIT** ⏳ | **WAIT** ⏳ |

**Pattern: Both WAIT/WAIT** — Monitor for change in conditions.
