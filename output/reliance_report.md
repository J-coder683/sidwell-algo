# Investment Analysis Report: RELIANCE.NS
**Generated on**: May 28, 2026
**Valuation Engine**: Discounted Cash Flow (DCF)
**Investor Lenses**: Warren Buffett + Howard Marks + KKR + Blackstone + Apollo (v0.6)

> [!WARNING]
> **DCF COVERAGE GAP WARNING**: The computed DCF intrinsic value
> deviates significantly from the current market price (intrinsic
> at -2% of price).
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
| **Current Price** | ₹1,352.00 | Yahoo Finance |
| **Intrinsic Value (DCF)** | ₹-23.88 | Sidwell DCF Engine |
| **Margin of Safety** | DCF produced non-positive intrinsic value — model failed | Current Discount to Intrinsic |
| **Buffett Score** | **9/14** | Buffett Lens (14 checks) |
| **Buffett Verdict** | **SKIP** ❌ | Buffett Lens Rules |
| **Marks Score** | **8/14** | Marks Lens (14 checks) |
| **Marks Verdict** | **SKIP** ❌ | Marks Lens Rules |
| **KKR Score** | **10/18** | KKR Lens (18 checks) |
| **KKR Verdict** | **SKIP** ❌ | KKR Lens Rules |
| **Blackstone Score** | **11/14** | Blackstone Lens (14 checks) |
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

| Metric | 2023 | 2024 | 2025 | 2026 |
| :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹8,778.35B | ₹9,010.64B | ₹9,646.93B | ₹10,572.19B |
| Gross Margin (%) | 23.46% | 25.13% | 29.22% | 29.40% |
| EBIT | ₹1,130.04B | ₹1,261.12B | ₹1,302.86B | ₹1,502.23B |
| Free Cash Flow | ₹-259.56B | ₹59.05B | ₹387.36B | ₹691.97B |
| Total Debt | ₹3,343.92B | ₹3,461.42B | ₹3,695.75B | ₹3,980.00B |
| Stockholders Equity | ₹7,158.72B | ₹7,934.81B | ₹8,432.00B | ₹9,040.30B |

## 2. DCF Valuation & WACC Sourcing
Every component of the Weighted Average Cost of Capital (WACC) is explicitly sourced and modeled below:

### WACC Components & Assumptions
| Component | Value | Source / Reference |
| :--- | :--- | :--- |
| **Risk-Free Rate ($R_f$)** | 7.12% | FRED Series: `INDIRLTLT01STM` (India 10Y G-Sec) |
| **Mature Market ERP** | 4.23% | Damodaran NYU Stern (Mature Equity Risk Premium) |
| **Country Risk Premium** | 2.18% | Damodaran NYU Stern (Country default spread adjusted) |
| **Total Equity Risk Premium** | 6.41% | Damodaran mature ERP + country premium = 6.41% |
| **Industry Unlevered Beta** | 0.98 | Damodaran 'Chemical (Specialty)' (hardcoded fallback (Damodaran lookup failed)) |
| **Target Levered Beta ($\beta$)** | 1.15 | Re-levered using actual D/E = 1.15 |
| **Cost of Equity ($K_e$)** | 14.46% | CAPM: $R_f + \beta \times ERP$ = 14.46% |
| **Cost of Debt ($K_d$)** | 8.12% | Calculated and floored to Rf + 1% (raw: 6.80%) |
| **Effective Tax Rate ($t$)** | 23.12% | 4-year historical average from filings |
| **Equity Weight ($W_e$)** | 82.13% | Market Cap / (Market Cap + Total Debt) |
| **Debt Weight ($W_d$)** | 17.87% | Total Debt / (Market Cap + Total Debt) |
| **Computed WACC** | **12.99%** | Weighted cost of capital = **12.99%** |

### 5-Year High-Growth Forecast (Stage 1)
Projections are based on historical averages relative to Revenue. Revenue growth is projected at **6.39%** (historical 4y CAGR capped between 5% and 20%).

| Metric | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹11,248.18B | ₹11,967.40B | ₹12,732.60B | ₹13,546.73B | ₹14,412.91B |
| EBIT | ₹1,534.92B | ₹1,633.06B | ₹1,737.48B | ₹1,848.57B | ₹1,966.77B |
| Taxes | ₹354.84B | ₹377.53B | ₹401.67B | ₹427.35B | ₹454.68B |
| D&A | ₹596.07B | ₹634.19B | ₹674.74B | ₹717.88B | ₹763.78B |
| CapEx | ₹1,663.69B | ₹1,770.07B | ₹1,883.25B | ₹2,003.67B | ₹2,131.78B |
| NWC Change (CF) | ₹59.37B | ₹63.16B | ₹67.20B | ₹71.50B | ₹76.07B |
| Free Cash Flow | ₹171.82B | ₹182.81B | ₹194.49B | ₹206.93B | ₹220.16B |
| Discount Factor | 1.1299 | 1.2768 | 1.4427 | 1.6301 | 1.8420 |
| PV of Cash Flow | ₹152.06B | ₹143.18B | ₹134.82B | ₹126.94B | ₹119.53B |

### 5-Year Fade Forecast (Stage 2) — growth fading from 6.39% to 4.50%

| Metric | Year 6 | Year 7 | Year 8 | Year 9 | Year 10 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹15,279.88B | ₹16,141.12B | ₹16,989.76B | ₹17,818.66B | ₹18,620.50B |
| EBIT | ₹2,085.08B | ₹2,202.60B | ₹2,318.41B | ₹2,431.52B | ₹2,540.94B |
| Taxes | ₹482.03B | ₹509.20B | ₹535.97B | ₹562.12B | ₹587.42B |
| D&A | ₹809.73B | ₹855.37B | ₹900.34B | ₹944.26B | ₹986.75B |
| CapEx | ₹2,260.01B | ₹2,387.40B | ₹2,512.92B | ₹2,635.52B | ₹2,754.12B |
| NWC Change (CF) | ₹80.65B | ₹85.19B | ₹89.67B | ₹94.04B | ₹98.28B |
| Free Cash Flow | ₹233.40B | ₹246.56B | ₹259.52B | ₹272.19B | ₹284.43B |
| Discount Factor | 2.0813 | 2.3518 | 2.6574 | 3.0027 | 3.3928 |
| PV of Cash Flow | ₹112.14B | ₹104.84B | ₹97.66B | ₹90.65B | ₹83.83B |

### Terminal Value
- Final fade year (Year 10) FCF: ₹284.43B
- Terminal growth (Gordon): 4.50%
- Sector mapping: SECTOR_TERMINAL_GROWTH lookup for (Chemical (Specialty), India)
- Terminal Value: ₹3,499.25B
- PV of Terminal Value (discounted from Year 10): ₹1,031.37B

### Valuation Bridge
- **PV of Explicit FCFs**: ₹1,165.65B
- **PV of Terminal Value (g = 4.50%)**: ₹1,031.37B
- **Enterprise Value**: ₹2,197.02B
- **Add: Cash & Equivalents**: ₹1,459.77B
- **Less: Total Debt**: ₹3,980.00B
- **Equity Value**: ₹-323.21B
- **Shares Outstanding**: 13,532,472,634
- **Intrinsic Value per Share**: **₹-23.88**

## 3. Buffett Investor Lens
All 14 checks per Warren Buffett's framework across 4 Parts (frameworks/buffett.md):

### Part A — Business Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Durable competitive advantage (moat) | ✅ | 2.98% | < 3.0% | stdev = 2.98% < 3% |
| High return on invested capital | ❌ | 9.20% | > 15.0% | 4y avg = 9.20% <= 15% |
| Strong free-cash-flow generation | ❌ | 0.02 / 3.67 | Margin > 10% & Growth > 0% | avg margin = 2.06%, FCF growth = 366.59% |
| Earnings predictability | ✅ | 0.06 / 0.04 | 5% < CAGR < 30% & YoY Growth StDev < 10.0% | Revenue CAGR = 6.39%, YoY Growth StDev = 3.51% |

_Part A — Business Quality: **2/4 passed**_

### Part B — Financial Health

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Conservative balance sheet | ✅ | 1.91 / 5.55 | Debt/EBITDA < 3x & Coverage > 5x | Debt/EBITDA = 1.91x, Int. Coverage = 5.55x |
| ROE without excess leverage | ❌ | 0.09 / 0.42 | ROE > 15% & Equity/Assets > 40% | 4y avg ROE = 8.82%, Equity/Assets = 41.50% |
| Liquidity cushion (Gibraltar test) | ❌ | 1459770000000.00 / 3980000000000.00 | Cash / Debt > 0.5x OR debt-free | Cash / Debt = 0.37x (<= 0.5) |

_Part B — Financial Health: **1/3 passed**_

### Part C — Management & Capital Allocation

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Anti-dilution discipline | ✅ | [4 values] | <= 2% growth over 4y | Share count growth (4y): +0.00% (threshold: <= +2%) |
| Capital allocation track record | ✅ | 0.0058913541378695505 / True | ROIC not declining > 3pp AND capital returned | ROIC trend (latter-2y vs earlier-2y): +0.59pp; capital returned to shareholders: yes |
| Owner orientation | ✅ | 0.51181 / None | Insiders > 5% OR LLM = owner_oriented | Insider ownership: 51.18% (PASS at >5%). LLM owner-orientation: unavailable |
| Management coherence | ✅ | True | LLM coherence = coherent | Soft check: SKIPPED (qualitative unavailable); defaulted PASS |

_Part C — Management & Capital Allocation: **4/4 passed**_

### Part D — Margin of Safety & Holdability

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin of safety | ❌ | Model failed | > 25.0% | DCF produced non-positive intrinsic value — model failed |
| Understandable business (hard blacklist) | ✅ | True | Ticker not BTC/ETH/COIN | Hard check: PASS (ticker not in avoided-sector blacklist) |
| Holdability (20-year test) | ✅ | N/A | LLM verdict = holdable_20y | Holdability check skipped (qualitative unavailable); defaulted PASS |

_Part D — Margin of Safety & Holdability: **2/3 passed**_

**Total Buffett Score**: **9/14**

## 3.1 Marks Investor Lens
All 14 checks per Howard Marks's risk-first framework (frameworks/marks.md):

### Part A — Margin of Safety & Asymmetric Payoff

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Deep margin of safety | ❌ | Model failed | > 40% | MoS = -100.00% (< 40% threshold) — Price 1352.00 vs Intrinsic -23.88 |
| Asymmetric upside-to-downside payoff | ❌ | 0.000 | > 3.0x | Asymmetry ratio = 0.00 (< 3.0 threshold) |
| Downside protection (tangible book) | ✅ | 49.41% | > 30% | Equity/MCap = 49.41% (> 30%) |
| Multiple expansion not exhausted | ✅ | 22.650 | < 25x (v0.3 placeholder; sector comp in v0.4) | Trailing P/E = 22.7x (< 25x) |

_Part A — Margin of Safety & Asymmetric Payoff: **2/4 passed**_

### Part B — Cycle Position

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Sector cycle position | ✅ | N/A | trough | early_recovery | mid_cycle | Cycle position unavailable; defaulted PASS (mid_cycle assumed) |
| Company earnings vs cyclical peak | ✅ | 100.00% | > 70% of peak | Latest NI / Peak NI = 100.0% |
| Sentiment — going against the crowd | ❌ | 1.312 | Mean rating 2.5-4.0 (mixed/cautious consensus) | Consensus rating mean: 1.31 (FAIL — Marks prefers 2.5-4.0 mixed/cautious; strong buy consensus is a contrarian caution signal) |

_Part B — Cycle Position: **2/3 passed**_

### Part C — Risk Architecture

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Capital structure resilience | ✅ | 1.91 / 5.55 | Debt/EBITDA < 4x AND Coverage > 4x | Debt/EBITDA = 1.91x, Coverage = 5.55x |
| FCF stability through downturn | ❌ | -259560000000.000 | All 4 years positive FCF | 4y FCF: [-259560000000.0, 59050000000.0, 387360000000.0, 691970000000.0] |
| Volatility / beta | ✅ | 0.244 | < 1.5 | Beta = 0.24 (< 1.5) |
| No single-point failure mode | ✅ | 0 | <= 1 concentration/regulatory risk flagged | Concentration/regulatory risks identified: 0 |

_Part C — Risk Architecture: **3/4 passed**_

### Part D — Second-Level Thinking & Contrarianism

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Variant perception | ❌ | False | variant_present=true AND specificity=high | Variant perception unavailable; defaulted FAIL |
| Management humility (knowing what you don't know) | ✅ | N/A | verdict = humble | Management humility check skipped; defaulted PASS |
| Patient opportunism (why now) | ❌ | N/A | verdict = dislocation_present | Why-now signal unavailable; defaulted FAIL |

_Part D — Second-Level Thinking & Contrarianism: **1/3 passed**_

**Total Marks Score**: **8/14**

## 3.2 KKR Investor Lens
All 18 checks per KKR's operating playbook framework (frameworks/kkr.md):

### Part A — LBO Viability

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| EBITDA Scale | ✅ | 2079110000000.000 | > ₹4.0B | Latest EBITDA passes scale check. |
| FCF Conversion | ❌ | 22.00% | > 60.00% | Average conversion is 22.0%. |
| Leverage Capacity | ✅ | 1.914 | < 3.0x | Leverage is 1.91x. |
| EBITDA Margin | ✅ | 19.67% | > 15.00% | Margin is 19.7%. |

_Part A — LBO Viability: **3/4 passed**_

### Part B — Operational Upside

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin Improvement Room | ❌ | 0.14 / 0.14 | Current < 95% of Peak | Already at/near peak margin. |
| Capex Optimization | ✅ | 0.12 / 0.53 | Optimization profile | Capex/Sales 11.6%, Growth share 53.1%. Optimization possible. |
| WC Optimization | ❌ | 2.42% | < -5% or qualitative | Quantitative fail. Qualitative: None. |
| M&A Platform Potential | ✅ | N/A | Qualitative high | Defaulted PASS (qualitative unavailable) |
| Mgmt / Ops Upgrade | ❌ | 15.20% | > 20% cost share | Opex share 15.2%. Qualitative: None. |
| Stavros Workforce Fit | ✅ | N/A | Frontline or mixed | Defaulted PASS (qualitative unavailable, assumed mixed) |

_Part B — Operational Upside: **3/6 passed**_

### Part C — Strategic Fit

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Sector Compatibility | ✅ | Chemical (Specialty) | In KKR Playbook | Chemical (Specialty) is in KKR playbook. |
| Willing Seller | ✅ | N/A | Positive catalyst | neutral default — qualitative unavailable; check counted as PASS |
| Regulatory Freedom | ✅ | Chemical (Specialty) | Not restricted | Clear. |

_Part C — Strategic Fit: **3/3 passed**_

### Part D — Cycle Timing & Returns

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Cycle Timing | ✅ | N/A | Not peak/late | Defaulted PASS (assumed mid_cycle) |
| 7-Year IRR | ❌ | 16.46% | > 18.00% | Entry mult 10.7x -> Exit mult 9.1x. |
| Dividend Recap | ❌ | 187.05% | CV < 35%, FCF > 0 | CV is 187.0%, min FCF -259560000000.0. |
| Why Now Catalyst | ❌ | N/A | Catalyst present | Defaulted FAIL (qualitative unavailable) |

_Part D — Cycle Timing & Returns: **1/4 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ❌ | 2 | >= 4 | 2 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **0/1 passed**_

**Total KKR Score**: **10/18**

## 3.3 Blackstone Investor Lens
All 14 checks per Blackstone's thematic framework (frameworks/blackstone.md):

### Part A — Good Business Filter

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Growing Market | ✅ | 6.39% | > 5% & upward | CAGR is 6.4%. |
| Durable Moat | ❌ | 0.03 / 0.27 | Stdev < 4pp & > 35% | Stdev 3.0pp, Mean 26.8%. |
| Recurring Revenue | ✅ | 0.035 | < 8pp | YoY growth stdev is 3.5pp. |
| No Concentration | ✅ | diversified | Diversified | Assumed diversified (public company baseline). |

_Part A — Good Business Filter: **3/4 passed**_

### Part B — Good Neighborhood (Thematic)

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Theme Alignment | ❌ | Chemical (Specialty) | Favored Theme | Chemical (Specialty) not in themes. |
| Cycle Position | ✅ | N/A | Not peak/late | Defaulted PASS (assumed mid_cycle) |
| Structural Tailwind | ✅ | N/A | Tailwind/neutral | Defaulted PASS (assumed neutral) |

_Part B — Good Neighborhood (Thematic): **2/3 passed**_

### Part C — Downside Protection

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Conservative Balance Sheet | ✅ | 1.91 / 5.55 | <3.5x, >4x | Leverage 1.9x, Interest Coverage 5.6x. |
| FCF Resilience | ❌ | -259560000000.00 / 0.02 | >0, >6% | Min FCF -259560000000.0, Avg FCF Margin 2.3%. |
| Stress Survival | ✅ | 1.38 / 0.22 | Cash>1x OR Debt/MC<0.5 | Cash ratio 1.38x, Debt/Equity 21.8%. |

_Part C — Downside Protection: **2/3 passed**_

### Part D — Scale Fit & Hold Economics

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Blackstone-Scale Deal | ✅ | 18295902175232.000 | > ₹150B | Market cap is adequate. |
| 20-Year Core Viability | ✅ | N/A | Holdable 20y | Defaulted PASS (assumed holdable) |
| Multi-Product Engagement | ✅ | N/A | Multi-product | neutral default — qualitative unavailable; check counted as PASS |

_Part D — Scale Fit & Hold Economics: **3/3 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ✅ | 4 | >= 4 | 4 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **1/1 passed**_

**Total Blackstone Score**: **11/14**

## 3.4 Apollo Investor Lens
All 16 checks per Apollo's credit & complexity framework (frameworks/apollo.md):

### Part A — Purchase Price & Capital Structure Entry

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Entry Valuation Discount | ❌ | 10.714 | < 10.4x EV/EBITDA or <0.70 P/B | EV/EBITDA is 10.7x. P/B is 2.02x. |
| Capital Structure Complexity | ❌ | 1.91 / 5.55 | Debt stress | Lev: 1.9x, IC: 5.6x. Clean. |
| FCF Serviceability | ✅ | 6.475 | >0 FCF, >1.5x Cov | Avg FCF 219705000000.0, Hyp Cov 6.5x. |
| Deployment Scale | ✅ | 22275902175232.000 | > ₹20B | EV is 22275902175232.0. |

_Part A — Purchase Price & Capital Structure Entry: **2/4 passed**_

### Part B — Chaos, Complexity, Credit Edge

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Chaos/Dislocation Catalyst | ❌ | N/A | Present | Defaulted FAIL (qualitative unavailable) |
| Fulcrum Security | ❌ | (1.9142806296925126, 5.551273049776431, 4.5969603455356784) | Hard or Soft Fulcrum | Qual: None. Hard signals: A=False, B=False. |
| ABF/Credit Fit | ❌ | N/A | Compatible | Defaulted FAIL (qualitative unavailable) |
| Complexity Moat | ❌ | 18.27% | >55% or High Qual | Debt/Assets 18.3%. Qual: None. |
| Domain Knowledge | ✅ | Chemical (Specialty) | In Apollo Playbook | Chemical (Specialty) in playbook. |

_Part B — Chaos, Complexity, Credit Edge: **1/5 passed**_

### Part C — Athene Permanent Capital Fit

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| IG Credit Yield | ✅ | (0.19665840284747058, 1.9142806296925126, 5.551273049776431) | Margin>12%, Lev<5x, IC>1.5x | Margin 19.7%, Lev 1.9x, IC 5.6x. |
| Long-Duration Stability | ❌ | 0.041 | < 4pp, > 0 avg | FCF Margin Stdev 4.1pp. |
| Hold-Without-Exit | ✅ | N/A | Viable | neutral default — qualitative unavailable; check counted as PASS |

_Part C — Athene Permanent Capital Fit: **2/3 passed**_

### Part D — Credit Downside Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Through-Cycle Credit Floor | ✅ | 1130040000000.00 / 4.66 | Min EBIT>0, Cov>1.5x | Min EBIT 1130040000000.0, Avg Cov 4.7x. |
| Tangible Collateral | ✅ | 79.45% | > 40% | Ratio 79.5%. |
| Covenant Control | ✅ | N/A | High/Mixed | Defaulted PASS (assumed mixed) |

_Part D — Credit Downside Quality: **3/3 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ❌ | 2 | >= 4 | 2 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **0/1 passed**_

**Total Apollo Score**: **8/16**

## 3.5 Qualitative Analysis
_Qualitative analysis unavailable: No documents found in Drive folder_

## 4. Margin-of-Safety Check
Current Stock Price: **₹1,352.00**
DCF Intrinsic Value: **₹-23.88**
Required Margin of Safety: **25.00%** (Graham & Dodd standard — Buffett lens)
Computed Margin of Safety: DCF produced non-positive intrinsic value — model failed
### Status: [FAIL] ❌
The stock trades above the safety threshold. A discount of -100.00% is insufficient for investment under the Buffett framework.

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
| **Marks** | 8/14 | **SKIP** ❌ |
| **KKR** | 10/18 | **SKIP** ❌ |
| **Blackstone** | 11/14 | **BUY** ✅ |
| **Apollo** | 8/16 | **SKIP** ❌ |
