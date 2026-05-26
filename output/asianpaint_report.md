# Investment Analysis Report: ASIANPAINT.NS
**Generated on**: May 26, 2026
**Valuation Engine**: Discounted Cash Flow (DCF)
**Investor Lenses**: Warren Buffett + Howard Marks (v0.3)

> [!WARNING]
> **DCF COVERAGE GAP WARNING**: The computed DCF intrinsic value deviates significantly from the current market price.
> This indicates a potential DCF coverage gap. A simple 1-stage DCF model with a terminal growth ceiling may severely undervalue premium consumer staples 
> because historical CAGR may capture a depressed window, capacity expansion CapEx is elevated relative to normalized levels, 
> and the terminal growth ceiling is too conservative for high-quality consumer businesses. Treat this intrinsic value as a conservative floor, not a fair value.

## Executive Summary
| Metric | Value | Source / Detail |
| :--- | :--- | :--- |
| **Current Price** | ₹2,657.80 | Yahoo Finance |
| **Intrinsic Value (DCF)** | ₹291.69 | Sidwell DCF Engine |
| **Margin of Safety** | Trading at 9.1x intrinsic value (target ≤ 0.75x) | Current Discount to Intrinsic |
| **Buffett Score** | **8/14** | Buffett Lens (14 checks) |
| **Buffett Verdict** | **SKIP** ❌ | Buffett Lens Rules |
| **Marks Score** | **8/14** | Marks Lens (14 checks) |
| **Marks Verdict** | **SKIP** ❌ | Marks Lens Rules |

### Verdict Summary
> **Buffett**: **SKIP** — Does not meet enough Buffett criteria across business quality, management, and price.
>
> **Marks**: **SKIP** — Insufficient asymmetric edge under Marks framework.

## 1. Company Snapshot
Historical financial statements over the last 4 years:

| Metric | 2022 | 2023 | 2024 | 2025 |
| :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹289.41B | ₹343.89B | ₹353.95B | ₹338.15B |
| Gross Margin (%) | 36.50% | 38.22% | 43.00% | 42.06% |
| EBIT | ₹42.83B | ₹58.33B | ₹75.53B | ₹53.30B |
| Free Cash Flow | ₹4.36B | ₹27.48B | ₹36.08B | ₹25.94B |
| Total Debt | ₹15.87B | ₹19.33B | ₹24.74B | ₹22.90B |
| Stockholders Equity | ₹138.12B | ₹159.92B | ₹187.28B | ₹194.00B |

## 2. DCF Valuation & WACC Sourcing
Every component of the Weighted Average Cost of Capital (WACC) is explicitly sourced and modeled below:

### WACC Components & Assumptions
| Component | Value | Source / Reference |
| :--- | :--- | :--- |
| **Risk-Free Rate ($R_f$)** | 7.12% | FRED Series: `INDIRLTLT01STM` (India 10Y G-Sec) |
| **Mature Market ERP** | 4.23% | Damodaran NYU Stern (Mature Equity Risk Premium) |
| **Country Risk Premium** | 2.18% | Damodaran NYU Stern (Country default spread adjusted) |
| **Total Equity Risk Premium** | 6.41% | Damodaran mature ERP + country premium = 6.41% |
| **Industry Unlevered Beta** | 0.95 | Damodaran 'Household Products' (ticker-mapped) |
| **Target Levered Beta ($\beta$)** | 0.96 | Re-levered using actual D/E = 0.96 |
| **Cost of Equity ($K_e$)** | 13.25% | CAPM: $R_f + \beta \times ERP$ = 13.25% |
| **Cost of Debt ($K_d$)** | 9.91% | Calculated: int_expense/debt = 9.91% |
| **Effective Tax Rate ($t$)** | 26.06% | 4-year historical average from filings |
| **Equity Weight ($W_e$)** | 99.11% | Market Cap / (Market Cap + Total Debt) |
| **Debt Weight ($W_d$)** | 0.89% | Total Debt / (Market Cap + Total Debt) |
| **Computed WACC** | **13.20%** | Weighted cost of capital = **13.20%** |

### 5-Year Explicit Forecast Projections
Projections are based on historical averages relative to Revenue. Revenue growth is projected at **5.32%** (historical 4y CAGR capped between 5% and 20%).

| Metric | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 | Terminal Value |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹356.16B | ₹375.12B | ₹395.10B | ₹416.14B | ₹438.29B | - |
| EBIT | ₹61.32B | ₹64.58B | ₹68.02B | ₹71.64B | ₹75.46B | - |
| Taxes | ₹15.98B | ₹16.83B | ₹17.73B | ₹18.67B | ₹19.67B | - |
| D&A | ₹9.58B | ₹10.09B | ₹10.63B | ₹11.19B | ₹11.79B | - |
| CapEx | ₹16.54B | ₹17.42B | ₹18.34B | ₹19.32B | ₹20.35B | - |
| NWC Change (CF) | ₹-12.07B | ₹-12.72B | ₹-13.40B | ₹-14.11B | ₹-14.86B | - |
| Free Cash Flow | ₹26.31B | ₹27.71B | ₹29.18B | ₹30.74B | ₹32.37B | ₹366.06B |
| Discount Factor | 1.1320 | 1.2814 | 1.4505 | 1.6419 | 1.8586 | 1.8586 |
| PV of Cash Flow | ₹23.24B | ₹21.62B | ₹20.12B | ₹18.72B | ₹17.42B | ₹196.96B |

### Valuation Bridge
- **PV of Explicit FCFs**: ₹101.12B
- **PV of Terminal Value (g = 4.00%)**: ₹196.96B
- **Enterprise Value**: ₹298.07B
- **Add: Cash & Equivalents**: ₹4.45B
- **Less: Total Debt**: ₹22.90B
- **Equity Value**: ₹279.62B
- **Shares Outstanding**: 958,644,295
- **Intrinsic Value per Share**: **₹291.69**

## 3. Buffett Investor Lens
All 14 checks per Warren Buffett's framework across 4 Parts (frameworks/buffett.md):

### Part A — Business Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Durable competitive advantage (moat) | ❌ | 3.09% | < 3.0% | stdev = 3.09% >= 3% |
| High return on invested capital | ✅ | 23.04% | > 15.0% | 4y avg = 23.04% > 15% |
| Strong free-cash-flow generation | ❌ | 0.07 / 4.95 | Margin > 10% & Growth > 0% | avg margin = 6.84%, FCF growth = 495.22% |
| Earnings predictability | ❌ | 0.05 / 0.12 | 5% < CAGR < 30% & YoY Growth StDev < 10.0% | Revenue CAGR = 5.32%, YoY Growth StDev = 11.90% |

_Part A — Business Quality: **1/4 passed**_

### Part B — Financial Health

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Conservative balance sheet | ✅ | 0.36 / 23.48 | Debt/EBITDA < 3x & Coverage > 5x | Debt/EBITDA = 0.36x, Int. Coverage = 23.48x |
| ROE without excess leverage | ✅ | 0.24 / 0.64 | ROE > 15% & Equity/Assets > 40% | 4y avg ROE = 23.92%, Equity/Assets = 63.88% |
| Liquidity cushion (Gibraltar test) | ❌ | 4452800000.00 / 22902900000.00 | Cash / Debt > 0.5x OR debt-free | Cash / Debt = 0.19x (<= 0.5) |

_Part B — Financial Health: **2/3 passed**_

### Part C — Management & Capital Allocation

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Anti-dilution discipline | ✅ | [0 values] | <= 2% growth over 4y | Share count data unavailable; check defaulted PASS |
| Capital allocation track record | ❌ | -0.0012769063339250764 / False | ROIC not declining > 3pp AND capital returned | ROIC trend (latter-2y vs earlier-2y): -0.13pp; capital returned to shareholders: no |
| Owner orientation | ✅ | 0.0 / owner_oriented | Insiders > 5% OR LLM = owner_oriented | Insider ownership: 0.00% (FAIL at >5%). LLM owner-orientation: owner_oriented |
| Management coherence | ✅ | True | LLM coherence = coherent | Soft check: PASS (LLM coherence: coherent). The company's presentation and responses form a logical, unified strategy. They explain the volume-value gap coherently as a function of their deliberate dual-pronged approach to capture both premium luxury customers and lower-end economy upgrades, and the |

_Part C — Management & Capital Allocation: **3/4 passed**_

### Part D — Margin of Safety & Holdability

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin of safety | ❌ | Trading at 9.1x intrinsic | > 25.0% | Trading at 9.1x intrinsic value (target ≤ 0.75x) (Price: 2657.80, Intrinsic: 291.69) |
| Understandable business (hard blacklist) | ✅ | True | Ticker not BTC/ETH/COIN | Hard check: PASS (ticker not in avoided-sector blacklist) |
| Holdability (20-year test) | ✅ | holdable_20y | LLM verdict = holdable_20y | LLM holdability verdict: holdable_20y. The core paint and beautification business is highly resilient to 20-year technology disruptions as the underlying consumer need to protect and design physical spaces remains persistent. With a massive retail footprint of over 1.6 lakh outlets and continuous ex |

_Part D — Margin of Safety & Holdability: **2/3 passed**_

**Total Buffett Score**: **8/14**

## 3.5 Qualitative Analysis
Based on 1 document(s): 8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf. Model: `gemini-3.5-flash`.

### Forward Guidance
- **Q4 FY2026** (volume): Management targets maintaining a volume growth momentum in the high single-digit range of 8% to 10% under current market conditions. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_
- **Q4 FY2026** (margin): Management expects to maintain their operating (PBDIT) margins within the established guidance band of 18% to 20%. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_
- **Next few quarters** (revenue): Management indicates that a value growth rate of 5% to 6% is a realistic expectation in the upcoming quarters, assuming a volume-value gap of 4% to 5% persists. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_

### Risk Callouts
- **Competitive Intensity**: The competitive landscape remains intense with the entry of new players and the amalgamation of two existing competitors, which may drive pricing pressure. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_
- **Raw Material Price Volatility**: Geopolitical uncertainties pose a risk to key raw material costs, as crude oil and Titanium Dioxide (TiO2) pricing structures remain highly volatile. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_
- **Shift in Discretionary Spending**: Changes in lifestyle patterns, such as destination weddings and increased travel, have temporarily deferred traditional home painting frequencies. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_

### Strategic Themes
- **Regionalization**: Management has customized product offerings and packaging for 8 to 9 states, driving localized brand equity and consumer connection. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_
- **B2B and Industrial Pivot**: Management is heavily capitalizing on the infrastructure boom and private capex through expanding industrial JVs and launching B2B digital service platforms. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_
- **Cost Efficiency & Backward Integration**: The company continues its backward integration journey, including a white cement plant, to generate structural cost advantages and preserve margins. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_

### Tone & Coherence
- **Tone (current)**: confident
- **Tone (trajectory)**: stable
- **Coherence verdict**: coherent

_Management exhibits strong confidence in their proprietary cost-saving models and technology-led service differentiation. Despite near-term challenges like a compressed festive period and muted retail demand, they remain highly optimistic about industrial coatings and B2B growth. They present a clear, steady strategy for defending market share against new competitive entrants without resorting to artificial pricing strategies._

_The company's presentation and responses form a logical, unified strategy. They explain the volume-value gap coherently as a function of their deliberate dual-pronged approach to capture both premium luxury customers and lower-end economy upgrades, and their cost-efficiency narrative aligns perfectly with their margin outperformance._

### Marks-Relevant Signals
- **Owner orientation**: owner_oriented — Management demonstrates an owner-oriented mindset by rejecting artificial channel-filling practices at quarter-ends to boost paper figures, calling them unproductive. Furthermore, they display exceptional candor by openly highlighting that their Home Decor business expansion has had 'limiting' progr
- **Holdability (20y)**: holdable_20y — The core paint and beautification business is highly resilient to 20-year technology disruptions as the underlying consumer need to protect and design physical spaces remains persistent. With a massive retail footprint of over 1.6 lakh outlets and continuous expansion into waterproofing and industri
- **Sector cycle**: late_cycle / Company cycle: mid — The retail decorative paint sector is in a late-cycle phase, characterized by mature real estate trends and a temporary postponement in discretionary home consumer painting cycles. However, the industrial and infrastructure sectors remain highly active. The company is in a mature mid-cycle phase, ag
- **Variant perception**: present=True, specificity=high. Consensus: 'The market consensus fears that aggressive well-funded new entrants will trigger a price war, significantly eroding Asian Paints' market share and ope'
- **Management humility**: humble — Management demonstrates humility by openly admitting past underperformance, such as the 'limiting' growth of the Home Decor segment and the direct impairment hits on White Teak. Rather than offering speculative multi-year forecasts or making bold macroeconomic assertions, they honestly declare that 
- **Why now**: normal_cycle — Normal cyclical volatility and entry of new competitive players.

## 3.6 Marks Investor Lens
All 14 checks per Howard Marks's risk-first framework across 4 Parts (frameworks/marks.md):

### Part A — Margin of Safety & Asymmetric Payoff

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Deep margin of safety | ❌ | Trading at 9.1x intrinsic | > 40% | MoS = -811.18% (< 40% threshold) — Price 2657.80 vs Intrinsic 291.69 |
| Asymmetric upside-to-downside payoff | ❌ | 0.000 | > 3.0x | Asymmetry ratio = 0.00 (< 3.0 threshold) |
| Downside protection (tangible book) | ❌ | 7.61% | > 30% | Equity/MCap = 7.61% (<= 30%) |
| Multiple expansion not exhausted | ✅ | N/A | < 25x (v0.3 placeholder; sector comp in v0.4) | Trailing P/E unavailable; check defaulted PASS |

_Part A — Margin of Safety & Asymmetric Payoff: **1/4 passed**_

### Part B — Cycle Position

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Sector cycle position | ❌ | late_cycle | trough | early_recovery | mid_cycle | LLM sector cycle: late_cycle. The retail decorative paint sector is in a late-cycle phase, characterized by mature real estate trends and a temporary postponement in discretionary home consumer painting cycles. However, the industrial and infrastructure sectors remain highly active. The company is i |
| Company earnings vs cyclical peak | ❌ | 67.16% | > 70% of peak | Latest NI / Peak NI = 67.2% |
| Sentiment — going against the crowd | ✅ | N/A | Mean rating 2.5-4.0 (mixed/cautious consensus) | Consensus rating unavailable; defaulted PASS |

_Part B — Cycle Position: **1/3 passed**_

### Part C — Risk Architecture

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Capital structure resilience | ✅ | 0.36 / 23.48 | Debt/EBITDA < 4x AND Coverage > 4x | Debt/EBITDA = 0.36x, Coverage = 23.48x |
| FCF stability through downturn | ✅ | 4357900000.000 | All 4 years positive FCF | 4y FCF: [4357900000.0, 27478200000.0, 36075200000.0, 25938900000.0] |
| Volatility / beta | ✅ | 1.000 | < 1.5 | Beta = 1.00 (< 1.5) |
| No single-point failure mode | ✅ | 0 | <= 1 concentration/regulatory risk flagged | Concentration/regulatory risks identified: 0 |

_Part C — Risk Architecture: **4/4 passed**_

### Part D — Second-Level Thinking & Contrarianism

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Variant perception | ✅ | True | variant_present=true AND specificity=high | Variant: True, Specificity: high. Consensus: 'The market consensus fears that aggressive well-funded new entrants will trigger a price war, significantly eroding Asian Paints' market share and operating margins.' | Company view: 'Management believes they can sustain high margins and defend their mar |
| Management humility (knowing what you don't know) | ✅ | humble | verdict = humble | LLM humility verdict: humble. Management demonstrates humility by openly admitting past underperformance, such as the 'limiting' growth of the Home Decor segment and the direct impairment hits on White Teak. Rather than offering speculative multi-year forecasts or making bold macroeconomic assertion |
| Patient opportunism (why now) | ❌ | normal_cycle | verdict = dislocation_present | Why-now: normal_cycle. Event: Normal cyclical volatility and entry of new competitive players.. The company's current environment reflects standard cyclical fluctuations rather than an asset distress or a unique regulatory dislocation. The muted growth was driven by normal seasonal shifts like a del |

_Part D — Second-Level Thinking & Contrarianism: **2/3 passed**_

**Total Marks Score**: **8/14**

## 4. Margin-of-Safety Check
Current Stock Price: **₹2,657.80**
DCF Intrinsic Value: **₹291.69**
Required Margin of Safety: **25.00%** (Graham & Dodd standard — Buffett lens)
Computed Margin of Safety: Trading at 9.1x intrinsic value (target ≤ 0.75x)
### Status: [FAIL] ❌
The stock trades above the safety threshold. Trading at 9.1x intrinsic value is insufficient for investment under the Buffett framework.

## 5. Investment Verdict
**BUFFETT RECOMMENDATION: SKIP**

Does not meet enough Buffett criteria across business quality, management, and price.

**MARKS RECOMMENDATION: SKIP**

Insufficient asymmetric edge under Marks framework.

## 6. Dual-Lens Synthesis
Sidwell preserves both lens verdicts without collapsing them to a single recommendation.
The disagreement between lenses IS the insight. See `frameworks/marks.md` section 'How This Lens Differs from Buffett' for design rationale.

| | Buffett | Marks |
| :--- | :---: | :---: |
| **Score** | 8/14 | 8/14 |
| **Verdict** | **SKIP** ❌ | **SKIP** ❌ |

**Pattern: Both SKIP/SKIP** — Monitor for change in conditions.
