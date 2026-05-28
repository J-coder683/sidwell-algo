# Investment Analysis Report: TMPV.NS
**Generated on**: May 28, 2026
**Valuation Engine**: Discounted Cash Flow (DCF)
**Investor Lenses**: Warren Buffett + Howard Marks + KKR + Blackstone + Apollo (v0.6)

> [!WARNING]
> **DCF COVERAGE GAP WARNING**: The computed DCF intrinsic value
> deviates significantly from the current market price (intrinsic
> at 26% of price).
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
| **Current Price** | ₹403.05 | Yahoo Finance |
| **Intrinsic Value (DCF)** | ₹103.34 | Sidwell DCF Engine |
| **Margin of Safety** | Trading at 3.9x intrinsic value (target ≤ 0.75x) | Current Discount to Intrinsic |
| **Buffett Score** | **6/14** | Buffett Lens (14 checks) |
| **Buffett Verdict** | **SKIP** ❌ | Buffett Lens Rules |
| **Marks Score** | **8/14** | Marks Lens (14 checks) |
| **Marks Verdict** | **SKIP** ❌ | Marks Lens Rules |
| **KKR Score** | **12/18** | KKR Lens (18 checks) |
| **KKR Verdict** | **SKIP** ❌ | KKR Lens Rules |
| **Blackstone Score** | **8/14** | Blackstone Lens (14 checks) |
| **Blackstone Verdict** | **SKIP** ❌ | Blackstone Lens Rules |
| **Apollo Score** | **8/16** | Apollo Lens (16 checks) |
| **Apollo Verdict** | **SKIP** ❌ | Apollo Lens Rules |

### Verdict Summary
> **Buffett**: **SKIP** — Does not meet enough Buffett criteria across business quality, management, and price.
> **Marks**: **SKIP** — Insufficient asymmetric edge under Marks framework.
> **KKR**: **SKIP** — Failed Part A pre-condition: not LBO-viable.
> **Blackstone**: **SKIP** — Failed Part C pre-condition: lacks Schwarzman downside protection (<2/3 passed).
> **Apollo**: **SKIP** — Failed Part E pre-condition: lacks above-average alpha thesis (Phalippou bar).

## 1. Company Snapshot
Historical financial statements over the last 4 years:

| Metric | 2023 | 2024 | 2025 | 2026 |
| :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹3,428.75B | ₹4,312.12B | ₹3,634.86B | ₹3,333.83B |
| Gross Margin (%) | 33.48% | 36.26% | 39.08% | 35.78% |
| EBIT | ₹136.19B | ₹360.23B | ₹323.55B | ₹12.04B |
| Free Cash Flow | ₹172.92B | ₹365.01B | ₹250.60B | ₹-232.41B |
| Total Debt | ₹1,366.13B | ₹1,098.12B | ₹740.04B | ₹791.09B |
| Stockholders Equity | ₹453.22B | ₹849.18B | ₹1,161.44B | ₹1,120.68B |

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
| **Target Levered Beta ($\beta$)** | 1.37 | Re-levered using actual D/E = 1.37 |
| **Cost of Equity ($K_e$)** | 15.88% | CAPM: $R_f + \beta \times ERP$ = 15.88% |
| **Cost of Debt ($K_d$)** | 8.12% | Calculated and floored to Rf + 1% (raw: 3.57%) |
| **Effective Tax Rate ($t$)** | 26.29% | 4-year historical average from filings |
| **Equity Weight ($W_e$)** | 65.23% | Market Cap / (Market Cap + Total Debt) |
| **Debt Weight ($W_d$)** | 34.77% | Total Debt / (Market Cap + Total Debt) |
| **Computed WACC** | **12.44%** | Weighted cost of capital = **12.44%** |

### 5-Year High-Growth Forecast (Stage 1)
Projections are based on historical averages relative to Revenue. Revenue growth is projected at **5.00%** (historical 4y CAGR capped between 5% and 20%).

| Metric | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹3,500.52B | ₹3,675.55B | ₹3,859.32B | ₹4,052.29B | ₹4,254.91B |
| EBIT | ₹188.93B | ₹198.37B | ₹208.29B | ₹218.71B | ₹229.64B |
| Taxes | ₹49.67B | ₹52.16B | ₹54.77B | ₹57.50B | ₹60.38B |
| D&A | ₹227.95B | ₹239.35B | ₹251.32B | ₹263.88B | ₹277.08B |
| CapEx | ₹296.77B | ₹311.61B | ₹327.19B | ₹343.55B | ₹360.73B |
| NWC Change (CF) | ₹2.80B | ₹2.94B | ₹3.08B | ₹3.24B | ₹3.40B |
| Free Cash Flow | ₹73.23B | ₹76.89B | ₹80.74B | ₹84.77B | ₹89.01B |
| Discount Factor | 1.1244 | 1.2643 | 1.4216 | 1.5985 | 1.7973 |
| PV of Cash Flow | ₹65.13B | ₹60.82B | ₹56.79B | ₹53.03B | ₹49.52B |

### 5-Year Fade Forecast (Stage 2) — growth fading from 5.00% to 4.50%

| Metric | Year 6 | Year 7 | Year 8 | Year 9 | Year 10 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹4,463.40B | ₹4,677.64B | ₹4,897.49B | ₹5,122.77B | ₹5,353.30B |
| EBIT | ₹240.89B | ₹252.46B | ₹264.32B | ₹276.48B | ₹288.92B |
| Taxes | ₹63.34B | ₹66.38B | ₹69.50B | ₹72.69B | ₹75.97B |
| D&A | ₹290.65B | ₹304.60B | ₹318.92B | ₹333.59B | ₹348.60B |
| CapEx | ₹378.40B | ₹396.56B | ₹415.20B | ₹434.30B | ₹453.85B |
| NWC Change (CF) | ₹3.57B | ₹3.74B | ₹3.91B | ₹4.09B | ₹4.28B |
| Free Cash Flow | ₹93.37B | ₹97.85B | ₹102.45B | ₹107.17B | ₹111.99B |
| Discount Factor | 2.0209 | 2.2723 | 2.5551 | 2.8729 | 3.2303 |
| PV of Cash Flow | ₹46.20B | ₹43.06B | ₹40.10B | ₹37.30B | ₹34.67B |

### Terminal Value
- Final fade year (Year 10) FCF: ₹111.99B
- Terminal growth (Gordon): 4.50%
- Sector mapping: SECTOR_TERMINAL_GROWTH lookup for (Chemical (Specialty), India)
- Terminal Value: ₹1,473.72B
- PV of Terminal Value (discounted from Year 10): ₹456.21B

### Valuation Bridge
- **PV of Explicit FCFs**: ₹486.63B
- **PV of Terminal Value (g = 4.50%)**: ₹456.21B
- **Enterprise Value**: ₹942.84B
- **Add: Cash & Equivalents**: ₹228.80B
- **Less: Total Debt**: ₹791.09B
- **Equity Value**: ₹380.55B
- **Shares Outstanding**: 3,682,435,640
- **Intrinsic Value per Share**: **₹103.34**

## 3. Buffett Investor Lens
All 14 checks per Warren Buffett's framework across 4 Parts (frameworks/buffett.md):

### Part A — Business Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Durable competitive advantage (moat) | ✅ | 2.30% | < 3.0% | stdev = 2.30% < 3% |
| High return on invested capital | ❌ | 9.92% | > 15.0% | 4y avg = 9.92% <= 15% |
| Strong free-cash-flow generation | ❌ | 0.03 / -2.34 | Margin > 10% & Growth > 0% | avg margin = 3.36%, FCF growth = -234.40% |
| Earnings predictability | ❌ | 0.05 / 0.22 | 5% < CAGR < 30% & YoY Growth StDev < 10.0% | Revenue CAGR = 5.00%, YoY Growth StDev = 22.11% |

_Part A — Business Quality: **1/4 passed**_

### Part B — Financial Health

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Conservative balance sheet | ❌ | 3.69 / 0.43 | Debt/EBITDA < 3x & Coverage > 5x | Debt/EBITDA = 3.69x, Int. Coverage = 0.43x |
| ROE without excess leverage | ❌ | 0.35 / 0.29 | ROE > 15% & Equity/Assets > 40% | 4y avg ROE = 34.95%, Equity/Assets = 29.34% |
| Liquidity cushion (Gibraltar test) | ❌ | 228800000000.00 / 791090000000.00 | Cash / Debt > 0.5x OR debt-free | Cash / Debt = 0.29x (<= 0.5) |

_Part B — Financial Health: **0/3 passed**_

### Part C — Management & Capital Allocation

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Anti-dilution discipline | ✅ | [4 values] | <= 2% growth over 4y | Share count growth (4y): -3.85% (threshold: <= +2%) |
| Capital allocation track record | ❌ | -0.040087875065716094 / True | ROIC not declining > 3pp AND capital returned | ROIC trend (latter-2y vs earlier-2y): -4.01pp; capital returned to shareholders: yes |
| Owner orientation | ✅ | 0.44151002 / None | Insiders > 5% OR LLM = owner_oriented | Insider ownership: 44.15% (PASS at >5%). LLM owner-orientation: unavailable |
| Management coherence | ✅ | True | LLM coherence = coherent | Soft check: SKIPPED (qualitative unavailable); defaulted PASS |

_Part C — Management & Capital Allocation: **3/4 passed**_

### Part D — Margin of Safety & Holdability

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin of safety | ❌ | Trading at 3.9x intrinsic | > 25.0% | Trading at 3.9x intrinsic value (target ≤ 0.75x) (Price: 403.05, Intrinsic: 103.34) |
| Understandable business (hard blacklist) | ✅ | True | Ticker not BTC/ETH/COIN | Hard check: PASS (ticker not in avoided-sector blacklist) |
| Holdability (20-year test) | ✅ | N/A | LLM verdict = holdable_20y | Holdability check skipped (qualitative unavailable); defaulted PASS |

_Part D — Margin of Safety & Holdability: **2/3 passed**_

**Total Buffett Score**: **6/14**

## 3.1 Marks Investor Lens
All 14 checks per Howard Marks's risk-first framework (frameworks/marks.md):

### Part A — Margin of Safety & Asymmetric Payoff

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Deep margin of safety | ❌ | Trading at 3.9x intrinsic | > 40% | MoS = -290.02% (< 40% threshold) — Price 403.05 vs Intrinsic 103.34 |
| Asymmetric upside-to-downside payoff | ❌ | 0.000 | > 3.0x | Asymmetry ratio = 0.00 (< 3.0 threshold) |
| Downside protection (tangible book) | ✅ | 75.51% | > 30% | Equity/MCap = 75.51% (> 30%) |
| Multiple expansion not exhausted | ✅ | N/A | < 25x (v0.3 placeholder; sector comp in v0.4) | Trailing P/E unavailable; check defaulted PASS |

_Part A — Margin of Safety & Asymmetric Payoff: **2/4 passed**_

### Part B — Cycle Position

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Sector cycle position | ✅ | N/A | trough | early_recovery | mid_cycle | Cycle position unavailable; defaulted PASS (mid_cycle assumed) |
| Company earnings vs cyclical peak | ✅ | 100.00% | > 70% of peak | Latest NI / Peak NI = 100.0% |
| Sentiment — going against the crowd | ✅ | 2.815 | Mean rating 2.5-4.0 (mixed/cautious consensus) | Consensus rating mean: 2.81 (PASS — Marks prefers 2.5-4.0 mixed/cautious; strong buy consensus is a contrarian caution signal) |

_Part B — Cycle Position: **3/3 passed**_

### Part C — Risk Architecture

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Capital structure resilience | ❌ | 3.69 / 0.43 | Debt/EBITDA < 4x AND Coverage > 4x | Debt/EBITDA = 3.69x, Coverage = 0.43x |
| FCF stability through downturn | ❌ | -232410000000.000 | All 4 years positive FCF | 4y FCF: [172923300000.0, 365010000000.0, 250600000000.0, -232410000000.0] |
| Volatility / beta | ✅ | 0.775 | < 1.5 | Beta = 0.78 (< 1.5) |
| No single-point failure mode | ✅ | 0 | <= 1 concentration/regulatory risk flagged | Concentration/regulatory risks identified: 0 |

_Part C — Risk Architecture: **2/4 passed**_

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
| EBITDA Scale | ✅ | 214570000000.000 | > ₹4.0B | Latest EBITDA passes scale check. |
| FCF Conversion | ✅ | 74.28% | > 60.00% | Average conversion is 74.3%. |
| Leverage Capacity | ❌ | 3.687 | < 3.0x | Leverage is 3.69x. |
| EBITDA Margin | ❌ | 6.44% | > 15.00% | Margin is 6.4%. |

_Part A — LBO Viability: **2/4 passed**_

### Part B — Operational Upside

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin Improvement Room | ✅ | 0.00 / 0.09 | Current < 95% of Peak | Margin compression exists. |
| Capex Optimization | ✅ | 0.11 / 0.44 | Optimization profile | Capex/Sales 10.9%, Growth share 44.2%. Optimization possible. |
| WC Optimization | ❌ | 0.90% | < -5% or qualitative | Quantitative fail. Qualitative: None. |
| M&A Platform Potential | ✅ | N/A | Qualitative high | Defaulted PASS (qualitative unavailable) |
| Mgmt / Ops Upgrade | ✅ | 35.42% | > 20% cost share | Opex share 35.4%. Qualitative: None. |
| Stavros Workforce Fit | ✅ | N/A | Frontline or mixed | Defaulted PASS (qualitative unavailable, assumed mixed) |

_Part B — Operational Upside: **5/6 passed**_

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
| 7-Year IRR | ❌ | 17.05% | > 18.00% | Entry mult 10.6x -> Exit mult 9.0x. |
| Dividend Recap | ❌ | 186.93% | CV < 35%, FCF > 0 | CV is 186.9%, min FCF -232410000000.0. |
| Why Now Catalyst | ❌ | N/A | Catalyst present | Defaulted FAIL (qualitative unavailable) |

_Part D — Cycle Timing & Returns: **1/4 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ✅ | 4 | >= 4 | 4 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **1/1 passed**_

**Total KKR Score**: **12/18**

## 3.3 Blackstone Investor Lens
All 14 checks per Blackstone's thematic framework (frameworks/blackstone.md):

### Part A — Good Business Filter

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Growing Market | ❌ | -0.93% | > 5% & upward | CAGR is -0.9%. |
| Durable Moat | ✅ | 0.02 / 0.36 | Stdev < 4pp & > 35% | Stdev 2.3pp, Mean 36.2%. |
| Recurring Revenue | ❌ | 0.221 | < 8pp | YoY growth stdev is 22.1pp. |
| No Concentration | ✅ | diversified | Diversified | Assumed diversified (public company baseline). |

_Part A — Good Business Filter: **2/4 passed**_

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
| Conservative Balance Sheet | ❌ | 3.69 / 0.43 | <3.5x, >4x | Leverage 3.7x, Interest Coverage 0.4x. |
| FCF Resilience | ❌ | -232410000000.00 / 0.04 | >0, >6% | Min FCF -232410000000.0, Avg FCF Margin 3.8%. |
| Stress Survival | ❌ | 0.69 / 0.53 | Cash>1x OR Debt/MC<0.5 | Cash ratio 0.69x, Debt/Equity 53.3%. |

_Part C — Downside Protection: **0/3 passed**_

### Part D — Scale Fit & Hold Economics

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Blackstone-Scale Deal | ✅ | 1484205588480.000 | > ₹150B | Market cap is adequate. |
| 20-Year Core Viability | ✅ | N/A | Holdable 20y | Defaulted PASS (assumed holdable) |
| Multi-Product Engagement | ✅ | N/A | Multi-product | neutral default — qualitative unavailable; check counted as PASS |

_Part D — Scale Fit & Hold Economics: **3/3 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ✅ | 4 | >= 4 | 4 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **1/1 passed**_

**Total Blackstone Score**: **8/14**

## 3.4 Apollo Investor Lens
All 16 checks per Apollo's credit & complexity framework (frameworks/apollo.md):

### Part A — Purchase Price & Capital Structure Entry

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Entry Valuation Discount | ❌ | 10.604 | < 10.4x EV/EBITDA or <0.70 P/B | EV/EBITDA is 10.6x. P/B is 1.32x. |
| Capital Structure Complexity | ✅ | 3.69 / 0.43 | Debt stress | Lev: 3.7x, IC: 0.4x. Complex/stressed. |
| FCF Serviceability | ✅ | 8.074 | >0 FCF, >1.5x Cov | Avg FCF 139030825000.0, Hyp Cov 8.1x. |
| Deployment Scale | ✅ | 2275295588480.000 | > ₹20B | EV is 2275295588480.0. |

_Part A — Purchase Price & Capital Structure Entry: **3/4 passed**_

### Part B — Chaos, Complexity, Credit Edge

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Chaos/Dislocation Catalyst | ❌ | N/A | Present | Defaulted FAIL (qualitative unavailable) |
| Fulcrum Security | ❌ | (3.6868620962855942, 0.42589317297488505, 1.8761526355787583) | Hard or Soft Fulcrum | Qual: None. Hard signals: A=False, B=False. |
| ABF/Credit Fit | ❌ | N/A | Compatible | Defaulted FAIL (qualitative unavailable) |
| Complexity Moat | ❌ | 20.71% | >55% or High Qual | Debt/Assets 20.7%. Qual: None. |
| Domain Knowledge | ✅ | Chemical (Specialty) | In Apollo Playbook | Chemical (Specialty) in playbook. |

_Part B — Chaos, Complexity, Credit Edge: **1/5 passed**_

### Part C — Athene Permanent Capital Fit

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| IG Credit Yield | ❌ | (0.06436141014988767, 3.6868620962855942, 0.42589317297488505) | Margin>12%, Lev<5x, IC>1.5x | Margin 6.4%, Lev 3.7x, IC 0.4x. |
| Long-Duration Stability | ❌ | 0.070 | < 4pp, > 0 avg | FCF Margin Stdev 7.0pp. |
| Hold-Without-Exit | ✅ | N/A | Viable | neutral default — qualitative unavailable; check counted as PASS |

_Part C — Athene Permanent Capital Fit: **1/3 passed**_

### Part D — Credit Downside Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Through-Cycle Credit Floor | ✅ | 12040000000.00 / 3.76 | Min EBIT>0, Cov>1.5x | Min EBIT 12040000000.0, Avg Cov 3.8x. |
| Tangible Collateral | ✅ | 71.48% | > 40% | Ratio 71.5%. |
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
Current Stock Price: **₹403.05**
DCF Intrinsic Value: **₹103.34**
Required Margin of Safety: **25.00%** (Graham & Dodd standard — Buffett lens)
Computed Margin of Safety: Trading at 3.9x intrinsic value (target ≤ 0.75x)
### Status: [FAIL] ❌
The stock trades above the safety threshold. Trading at 3.9x intrinsic value is insufficient for investment under the Buffett framework.

## 5. Investment Verdict
**BUFFETT RECOMMENDATION: SKIP**

Does not meet enough Buffett criteria across business quality, management, and price.

**MARKS RECOMMENDATION: SKIP**

Insufficient asymmetric edge under Marks framework.

**KKR RECOMMENDATION: SKIP**

Failed Part A pre-condition: not LBO-viable.

**BLACKSTONE RECOMMENDATION: SKIP**

Failed Part C pre-condition: lacks Schwarzman downside protection (<2/3 passed).

**APOLLO RECOMMENDATION: SKIP**

Failed Part E pre-condition: lacks above-average alpha thesis (Phalippou bar).

## 6. Quintuple-Lens Synthesis
Sidwell preserves all lens verdicts without collapsing them to a single recommendation.
The disagreement between lenses IS the insight.

| Lens | Score | Verdict |
| :--- | :---: | :---: |
| **Buffett** | 6/14 | **SKIP** ❌ |
| **Marks** | 8/14 | **SKIP** ❌ |
| **KKR** | 12/18 | **SKIP** ❌ |
| **Blackstone** | 8/14 | **SKIP** ❌ |
| **Apollo** | 8/16 | **SKIP** ❌ |
