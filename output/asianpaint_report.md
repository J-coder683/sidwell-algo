# Investment Analysis Report: ASIANPAINT.NS
**Generated on**: May 28, 2026
**Valuation Engine**: Discounted Cash Flow (DCF)
**Investor Lenses**: Warren Buffett + Howard Marks + KKR + Blackstone + Apollo (v0.5)

> [!WARNING]
> **DCF COVERAGE GAP WARNING**: The computed DCF intrinsic value
> deviates significantly from the current market price (intrinsic
> at 15% of price).
>
> Even this v0.4 2-stage DCF (Stage 1 high-growth + Stage 2 fade +
> sector-aware terminal) may understate premium businesses because:
> - Historical CapEx ratios may include expansionary capex that won't
>   recur indefinitely (a future v0.5+ refinement could fade capex
>   toward maintenance level in Stage 2)
> - DCF cannot capture brand premium, distribution moat, optionality
>   on adjacent categories, or India consumption-story re-rating
> - Market is willing to pay for sustained 15-20% earnings growth that
>   exceeds Damodaran's published sector terminal rates
>
> Treat this intrinsic value as a conservative floor anchor, not a
> fair-value estimate.

## Executive Summary
| Metric | Value | Source / Detail |
| :--- | :--- | :--- |
| **Current Price** | ₹2,671.90 | Yahoo Finance |
| **Intrinsic Value (DCF)** | ₹407.75 | Sidwell DCF Engine |
| **Margin of Safety** | Trading at 6.6x intrinsic value (target ≤ 0.75x) | Current Discount to Intrinsic |
| **Buffett Score** | **9/14** | Buffett Lens (14 checks) |
| **Buffett Verdict** | **SKIP** ❌ | Buffett Lens Rules |
| **Marks Score** | **7/14** | Marks Lens (14 checks) |
| **Marks Verdict** | **SKIP** ❌ | Marks Lens Rules |
| **KKR Score** | **14/18** | KKR Lens (18 checks) |
| **KKR Verdict** | **SKIP** ❌ | KKR Lens Rules |
| **Blackstone Score** | **13/14** | Blackstone Lens (14 checks) |
| **Blackstone Verdict** | **BUY** ✅ | Blackstone Lens Rules |
| **Apollo Score** | **8/16** | Apollo Lens (16 checks) |
| **Apollo Verdict** | **SKIP** ❌ | Apollo Lens Rules |

### Verdict Summary
> **Buffett**: **SKIP** — Does not meet enough Buffett criteria across business quality, management, and price.
> **Marks**: **SKIP** — Insufficient asymmetric edge under Marks framework.
> **KKR**: **SKIP** — Failed Part A pre-condition: not LBO-viable.
> **Blackstone**: **BUY** — High-conviction Blackstone target. Good business in a good neighborhood.
> **Apollo**: **SKIP** — Failed Part E pre-condition: lacks above-average alpha thesis (Phalippou bar).

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
| **Industry Unlevered Beta** | 0.74 | Damodaran 'Household Products' (from Damodaran sheet) |
| **Target Levered Beta ($\beta$)** | 0.75 | Re-levered using actual D/E = 0.75 |
| **Cost of Equity ($K_e$)** | 11.92% | CAPM: $R_f + \beta \times ERP$ = 11.92% |
| **Cost of Debt ($K_d$)** | 9.91% | Calculated: int_expense/debt = 9.91% |
| **Effective Tax Rate ($t$)** | 26.06% | 4-year historical average from filings |
| **Equity Weight ($W_e$)** | 99.11% | Market Cap / (Market Cap + Total Debt) |
| **Debt Weight ($W_d$)** | 0.89% | Total Debt / (Market Cap + Total Debt) |
| **Computed WACC** | **11.87%** | Weighted cost of capital = **11.87%** |

### 5-Year High-Growth Forecast (Stage 1)
Projections are based on historical averages relative to Revenue. Revenue growth is projected at **5.32%** (historical 4y CAGR capped between 5% and 20%).

| Metric | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹356.16B | ₹375.12B | ₹395.10B | ₹416.14B | ₹438.29B |
| EBIT | ₹61.32B | ₹64.58B | ₹68.02B | ₹71.64B | ₹75.46B |
| Taxes | ₹15.98B | ₹16.83B | ₹17.73B | ₹18.67B | ₹19.67B |
| D&A | ₹9.58B | ₹10.09B | ₹10.63B | ₹11.19B | ₹11.79B |
| CapEx | ₹16.54B | ₹17.42B | ₹18.34B | ₹19.32B | ₹20.35B |
| NWC Change (CF) | ₹-12.07B | ₹-12.72B | ₹-13.40B | ₹-14.11B | ₹-14.86B |
| Free Cash Flow | ₹26.31B | ₹27.71B | ₹29.18B | ₹30.74B | ₹32.37B |
| Discount Factor | 1.1187 | 1.2516 | 1.4002 | 1.5665 | 1.7525 |
| PV of Cash Flow | ₹23.51B | ₹22.14B | ₹20.84B | ₹19.62B | ₹18.47B |

### 5-Year Fade Forecast (Stage 2) — growth fading from 5.32% to 5.50%

| Metric | Year 6 | Year 7 | Year 8 | Year 9 | Year 10 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹461.79B | ₹486.70B | ₹513.13B | ₹541.17B | ₹570.93B |
| EBIT | ₹79.50B | ₹83.79B | ₹88.34B | ₹93.17B | ₹98.29B |
| Taxes | ₹20.72B | ₹21.84B | ₹23.02B | ₹24.28B | ₹25.62B |
| D&A | ₹12.42B | ₹13.09B | ₹13.80B | ₹14.56B | ₹15.36B |
| CapEx | ₹21.44B | ₹22.60B | ₹23.82B | ₹25.12B | ₹26.51B |
| NWC Change (CF) | ₹-15.66B | ₹-16.50B | ₹-17.40B | ₹-18.35B | ₹-19.36B |
| Free Cash Flow | ₹34.11B | ₹35.95B | ₹37.90B | ₹39.97B | ₹42.17B |
| Discount Factor | 1.9606 | 2.1934 | 2.4539 | 2.7453 | 3.0712 |
| PV of Cash Flow | ₹17.40B | ₹16.39B | ₹15.44B | ₹14.56B | ₹13.73B |

### Terminal Value
- Final fade year (Year 10) FCF: ₹42.17B
- Terminal growth (Gordon): 5.50%
- Sector mapping: SECTOR_TERMINAL_GROWTH lookup for (Household Products, India)
- Terminal Value: ₹697.90B
- PV of Terminal Value (discounted from Year 10): ₹227.24B

### Valuation Bridge
- **PV of Explicit FCFs**: ₹182.10B
- **PV of Terminal Value (g = 5.50%)**: ₹227.24B
- **Enterprise Value**: ₹409.34B
- **Add: Cash & Equivalents**: ₹4.45B
- **Less: Total Debt**: ₹22.90B
- **Equity Value**: ₹390.89B
- **Shares Outstanding**: 958,644,295
- **Intrinsic Value per Share**: **₹407.75**

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
| Anti-dilution discipline | ✅ | [4 values] | <= 2% growth over 4y | Share count growth (4y): -0.02% (threshold: <= +2%) |
| Capital allocation track record | ✅ | -0.0012769063339250764 / True | ROIC not declining > 3pp AND capital returned | ROIC trend (latter-2y vs earlier-2y): -0.13pp; capital returned to shareholders: yes |
| Owner orientation | ✅ | 0.52924 / None | Insiders > 5% OR LLM = owner_oriented | Insider ownership: 52.92% (PASS at >5%). LLM owner-orientation: unavailable |
| Management coherence | ✅ | True | LLM coherence = coherent | Soft check: SKIPPED (qualitative unavailable); defaulted PASS |

_Part C — Management & Capital Allocation: **4/4 passed**_

### Part D — Margin of Safety & Holdability

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin of safety | ❌ | Trading at 6.6x intrinsic | > 25.0% | Trading at 6.6x intrinsic value (target ≤ 0.75x) (Price: 2671.90, Intrinsic: 407.75) |
| Understandable business (hard blacklist) | ✅ | True | Ticker not BTC/ETH/COIN | Hard check: PASS (ticker not in avoided-sector blacklist) |
| Holdability (20-year test) | ✅ | N/A | LLM verdict = holdable_20y | Holdability check skipped (qualitative unavailable); defaulted PASS |

_Part D — Margin of Safety & Holdability: **2/3 passed**_

**Total Buffett Score**: **9/14**

## 3.1 Marks Investor Lens
All 14 checks per Howard Marks's risk-first framework (frameworks/marks.md):

### Part A — Margin of Safety & Asymmetric Payoff

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Deep margin of safety | ❌ | Trading at 6.6x intrinsic | > 40% | MoS = -555.27% (< 40% threshold) — Price 2671.90 vs Intrinsic 407.75 |
| Asymmetric upside-to-downside payoff | ❌ | 0.000 | > 3.0x | Asymmetry ratio = 0.00 (< 3.0 threshold) |
| Downside protection (tangible book) | ❌ | 7.57% | > 30% | Equity/MCap = 7.57% (<= 30%) |
| Multiple expansion not exhausted | ❌ | 66.416 | < 25x (v0.3 placeholder; sector comp in v0.4) | Trailing P/E = 66.4x (>= 25x) |

_Part A — Margin of Safety & Asymmetric Payoff: **0/4 passed**_

### Part B — Cycle Position

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Sector cycle position | ✅ | N/A | trough | early_recovery | mid_cycle | Cycle position unavailable; defaulted PASS (mid_cycle assumed) |
| Company earnings vs cyclical peak | ❌ | 67.16% | > 70% of peak | Latest NI / Peak NI = 67.2% |
| Sentiment — going against the crowd | ✅ | 2.706 | Mean rating 2.5-4.0 (mixed/cautious consensus) | Consensus rating mean: 2.71 (PASS — Marks prefers 2.5-4.0 mixed/cautious; strong buy consensus is a contrarian caution signal) |

_Part B — Cycle Position: **2/3 passed**_

### Part C — Risk Architecture

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Capital structure resilience | ✅ | 0.36 / 23.48 | Debt/EBITDA < 4x AND Coverage > 4x | Debt/EBITDA = 0.36x, Coverage = 23.48x |
| FCF stability through downturn | ✅ | 4357900000.000 | All 4 years positive FCF | 4y FCF: [4357900000.0, 27478200000.0, 36075200000.0, 25938900000.0] |
| Volatility / beta | ✅ | 0.284 | < 1.5 | Beta = 0.28 (< 1.5) |
| No single-point failure mode | ✅ | 0 | <= 1 concentration/regulatory risk flagged | Concentration/regulatory risks identified: 0 |

_Part C — Risk Architecture: **4/4 passed**_

### Part D — Second-Level Thinking & Contrarianism

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Variant perception | ❌ | False | variant_present=true AND specificity=high | Variant perception unavailable; defaulted FAIL |
| Management humility (knowing what you don't know) | ✅ | N/A | verdict = humble | Management humility check skipped; defaulted PASS |
| Patient opportunism (why now) | ❌ | N/A | verdict = dislocation_present | Why-now signal unavailable; defaulted FAIL |

_Part D — Second-Level Thinking & Contrarianism: **1/3 passed**_

**Total Marks Score**: **7/14**

## 3.2 KKR Investor Lens
All 18 checks per KKR's operating playbook framework (frameworks/kkr.md):

### Part A — LBO Viability

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| EBITDA Scale | ✅ | 63564300000.000 | > ₹4.0B | Latest EBITDA passes scale check. |
| FCF Conversion | ❌ | 55.06% | > 60.00% | Average conversion is 55.1%. |
| Leverage Capacity | ✅ | 0.360 | < 3.0x | Leverage is 0.36x. |
| EBITDA Margin | ✅ | 18.80% | > 15.00% | Margin is 18.8%. |

_Part A — LBO Viability: **3/4 passed**_

### Part B — Operational Upside

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin Improvement Room | ✅ | 0.16 / 0.21 | Current < 95% of Peak | Margin compression exists. |
| Capex Optimization | ✅ | 0.05 / 0.44 | Optimization profile | Capex/Sales 5.4%, Growth share 43.9%. Optimization possible. |
| WC Optimization | ✅ | -12.46% | < -5% or qualitative | Quantitative pass. Qualitative: None. |
| M&A Platform Potential | ✅ | N/A | Qualitative high | Defaulted PASS (qualitative unavailable) |
| Mgmt / Ops Upgrade | ✅ | 26.30% | > 20% cost share | Opex share 26.3%. Qualitative: None. |
| Stavros Workforce Fit | ✅ | N/A | Frontline or mixed | Defaulted PASS (qualitative unavailable, assumed mixed) |

_Part B — Operational Upside: **6/6 passed**_

### Part C — Strategic Fit

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Sector Compatibility | ✅ | Household Products | In KKR Playbook | Household Products is in KKR playbook. |
| Willing Seller | ✅ | N/A | Positive catalyst | neutral default — qualitative unavailable; check counted as PASS |
| Regulatory Freedom | ✅ | Household Products | Not restricted | Clear. |

_Part C — Strategic Fit: **3/3 passed**_

### Part D — Cycle Timing & Returns

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Cycle Timing | ✅ | N/A | Not peak/late | Defaulted PASS (assumed mid_cycle) |
| 7-Year IRR | ❌ | 16.06% | > 18.00% | Entry mult 40.7x -> Exit mult 34.6x. |
| Dividend Recap | ❌ | 57.52% | CV < 35%, FCF > 0 | CV is 57.5%, min FCF 4357900000.0. |
| Why Now Catalyst | ❌ | N/A | Catalyst present | Defaulted FAIL (qualitative unavailable) |

_Part D — Cycle Timing & Returns: **1/4 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ✅ | 5 | >= 4 | 5 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **1/1 passed**_

**Total KKR Score**: **14/18**

## 3.3 Blackstone Investor Lens
All 14 checks per Blackstone's thematic framework (frameworks/blackstone.md):

### Part A — Good Business Filter

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Growing Market | ✅ | 5.32% | > 5% & upward | CAGR is 5.3%. |
| Durable Moat | ✅ | 0.03 / 0.40 | Stdev < 4pp & > 35% | Stdev 3.1pp, Mean 39.9%. |
| Recurring Revenue | ❌ | 0.119 | < 8pp | YoY growth stdev is 11.9pp. |
| No Concentration | ✅ | diversified | Diversified | Assumed diversified (public company baseline). |

_Part A — Good Business Filter: **3/4 passed**_

### Part B — Good Neighborhood (Thematic)

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Theme Alignment | ✅ | Household Products | Favored Theme | Household Products in themes. |
| Cycle Position | ✅ | N/A | Not peak/late | Defaulted PASS (assumed mid_cycle) |
| Structural Tailwind | ✅ | N/A | Tailwind/neutral | Defaulted PASS (assumed neutral) |

_Part B — Good Neighborhood (Thematic): **3/3 passed**_

### Part C — Downside Protection

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Conservative Balance Sheet | ✅ | 0.36 / 23.48 | <3.5x, >4x | Leverage 0.4x, Interest Coverage 23.5x. |
| FCF Resilience | ✅ | 4357900000.00 / 0.07 | >0, >6% | Min FCF 4357900000.0, Avg FCF Margin 7.1%. |
| Stress Survival | ✅ | 0.13 / 0.01 | Cash>1x OR Debt/MC<0.5 | Cash ratio 0.13x, Debt/Equity 0.9%. |

_Part C — Downside Protection: **3/3 passed**_

### Part D — Scale Fit & Hold Economics

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Blackstone-Scale Deal | ✅ | 2561401683968.000 | > ₹150B | Market cap is adequate. |
| 20-Year Core Viability | ✅ | N/A | Holdable 20y | Defaulted PASS (assumed holdable) |
| Multi-Product Engagement | ✅ | N/A | Multi-product | neutral default — qualitative unavailable; check counted as PASS |

_Part D — Scale Fit & Hold Economics: **3/3 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ✅ | 5 | >= 4 | 5 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **1/1 passed**_

**Total Blackstone Score**: **13/14**

## 3.4 Apollo Investor Lens
All 16 checks per Apollo's credit & complexity framework (frameworks/apollo.md):

### Part A — Purchase Price & Capital Structure Entry

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Entry Valuation Discount | ❌ | 40.657 | < 12.8x EV/EBITDA or <0.70 P/B | EV/EBITDA is 40.7x. P/B is 13.20x. |
| Capital Structure Complexity | ❌ | 0.36 / 23.48 | Debt stress | Lev: 0.4x, IC: 23.5x. Clean. |
| FCF Serviceability | ✅ | 29.241 | >0 FCF, >1.5x Cov | Avg FCF 23462550000.0, Hyp Cov 29.2x. |
| Deployment Scale | ✅ | 2584304583968.000 | > ₹20B | EV is 2584304583968.0. |

_Part A — Purchase Price & Capital Structure Entry: **2/4 passed**_

### Part B — Chaos, Complexity, Credit Edge

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Chaos/Dislocation Catalyst | ❌ | N/A | Present | Defaulted FAIL (qualitative unavailable) |
| Fulcrum Security | ❌ | (0.360310740462807, 23.47850409655537, 111.83743910020128) | Hard or Soft Fulcrum | Qual: None. Hard signals: A=False, B=False. |
| ABF/Credit Fit | ❌ | N/A | Compatible | Defaulted FAIL (qualitative unavailable) |
| Complexity Moat | ❌ | 7.54% | >55% or High Qual | Debt/Assets 7.5%. Qual: None. |
| Domain Knowledge | ❌ | Household Products | In Apollo Playbook | Household Products not in playbook. |

_Part B — Chaos, Complexity, Credit Edge: **0/5 passed**_

### Part C — Athene Permanent Capital Fit

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| IG Credit Yield | ✅ | (0.18797569256638366, 0.360310740462807, 23.47850409655537) | Margin>12%, Lev<5x, IC>1.5x | Margin 18.8%, Lev 0.4x, IC 23.5x. |
| Long-Duration Stability | ✅ | 0.037 | < 4pp, > 0 avg | FCF Margin Stdev 3.7pp. |
| Hold-Without-Exit | ✅ | N/A | Viable | neutral default — qualitative unavailable; check counted as PASS |

_Part C — Athene Permanent Capital Fit: **3/3 passed**_

### Part D — Credit Downside Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Through-Cycle Credit Floor | ✅ | 42831300000.00 / 25.33 | Min EBIT>0, Cov>1.5x | Min EBIT 42831300000.0, Avg Cov 25.3x. |
| Tangible Collateral | ✅ | 97.34% | > 40% | Ratio 97.3%. |
| Covenant Control | ✅ | N/A | High/Mixed | Defaulted PASS (assumed mixed) |

_Part D — Credit Downside Quality: **3/3 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ❌ | 1 | >= 4 | 1 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **0/1 passed**_

**Total Apollo Score**: **8/16**

## 3.5 Qualitative Analysis
_Qualitative analysis unavailable: No documents found in Drive folder_

## 4. Margin-of-Safety Check
Current Stock Price: **₹2,671.90**
DCF Intrinsic Value: **₹407.75**
Required Margin of Safety: **25.00%** (Graham & Dodd standard — Buffett lens)
Computed Margin of Safety: Trading at 6.6x intrinsic value (target ≤ 0.75x)
### Status: [FAIL] ❌
The stock trades above the safety threshold. Trading at 6.6x intrinsic value is insufficient for investment under the Buffett framework.

## 5. Investment Verdict
**BUFFETT RECOMMENDATION: SKIP**

Does not meet enough Buffett criteria across business quality, management, and price.

**MARKS RECOMMENDATION: SKIP**

Insufficient asymmetric edge under Marks framework.

**KKR RECOMMENDATION: SKIP**

Failed Part A pre-condition: not LBO-viable.

**BLACKSTONE RECOMMENDATION: BUY**

High-conviction Blackstone target. Good business in a good neighborhood.

**APOLLO RECOMMENDATION: SKIP**

Failed Part E pre-condition: lacks above-average alpha thesis (Phalippou bar).

## 6. Quintuple-Lens Synthesis
Sidwell preserves all lens verdicts without collapsing them to a single recommendation.
The disagreement between lenses IS the insight.

| Lens | Score | Verdict |
| :--- | :---: | :---: |
| **Buffett** | 9/14 | **SKIP** ❌ |
| **Marks** | 7/14 | **SKIP** ❌ |
| **KKR** | 14/18 | **SKIP** ❌ |
| **Blackstone** | 13/14 | **BUY** ✅ |
| **Apollo** | 8/16 | **SKIP** ❌ |
