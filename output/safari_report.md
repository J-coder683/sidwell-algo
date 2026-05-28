# Investment Analysis Report: SAFARI.NS
**Generated on**: May 28, 2026
**Valuation Engine**: Discounted Cash Flow (DCF)
**Investor Lenses**: Warren Buffett + Howard Marks + KKR + Blackstone + Apollo (v0.6)

> [!WARNING]
> **DCF COVERAGE GAP WARNING**: The computed DCF intrinsic value
> deviates significantly from the current market price (intrinsic
> at 14% of price).
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
| **Current Price** | ₹1,525.00 | Yahoo Finance |
| **Intrinsic Value (DCF)** | ₹207.08 | Sidwell DCF Engine |
| **Margin of Safety** | Trading at 7.4x intrinsic value (target ≤ 0.75x) | Current Discount to Intrinsic |
| **Buffett Score** | **9/14** | Buffett Lens (14 checks) |
| **Buffett Verdict** | **SKIP** ❌ | Buffett Lens Rules |
| **Marks Score** | **6/14** | Marks Lens (14 checks) |
| **Marks Verdict** | **SKIP** ❌ | Marks Lens Rules |
| **KKR Score** | **11/18** | KKR Lens (18 checks) |
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
| Revenue | ₹12.08B | ₹15.47B | ₹17.72B | ₹20.47B |
| Gross Margin (%) | 40.61% | 45.02% | 45.68% | 47.11% |
| EBIT | ₹1.73B | ₹2.39B | ₹1.94B | ₹2.25B |
| Free Cash Flow | ₹3.20M | ₹1.06B | ₹-881.20M | ₹1.03B |
| Total Debt | ₹1.39B | ₹1.46B | ₹1.25B | ₹1.17B |
| Stockholders Equity | ₹4.26B | ₹8.23B | ₹9.53B | ₹11.15B |

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
| **Target Levered Beta ($\beta$)** | 0.99 | Re-levered using actual D/E = 0.99 |
| **Cost of Equity ($K_e$)** | 13.49% | CAPM: $R_f + \beta \times ERP$ = 13.49% |
| **Cost of Debt ($K_d$)** | 8.12% | Calculated and floored to Rf + 1% (raw: 7.39%) |
| **Effective Tax Rate ($t$)** | 23.33% | 4-year historical average from filings |
| **Equity Weight ($W_e$)** | 98.46% | Market Cap / (Market Cap + Total Debt) |
| **Debt Weight ($W_d$)** | 1.54% | Total Debt / (Market Cap + Total Debt) |
| **Computed WACC** | **13.37%** | Weighted cost of capital = **13.37%** |

### 5-Year High-Growth Forecast (Stage 1)
Projections are based on historical averages relative to Revenue. Revenue growth is projected at **19.21%** (historical 4y CAGR capped between 5% and 20%).

| Metric | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹24.40B | ₹29.09B | ₹34.68B | ₹41.34B | ₹49.27B |
| EBIT | ₹3.16B | ₹3.76B | ₹4.49B | ₹5.35B | ₹6.37B |
| Taxes | ₹736.28M | ₹877.70M | ₹1.05B | ₹1.25B | ₹1.49B |
| D&A | ₹786.22M | ₹937.23M | ₹1.12B | ₹1.33B | ₹1.59B |
| CapEx | ₹1.40B | ₹1.67B | ₹1.99B | ₹2.38B | ₹2.83B |
| NWC Change (CF) | ₹-1.27B | ₹-1.52B | ₹-1.81B | ₹-2.16B | ₹-2.57B |
| Free Cash Flow | ₹529.57M | ₹631.28M | ₹752.53M | ₹897.06M | ₹1.07B |
| Discount Factor | 1.1337 | 1.2854 | 1.4573 | 1.6522 | 1.8732 |
| PV of Cash Flow | ₹467.10M | ₹491.13M | ₹516.39M | ₹542.95M | ₹570.88M |

### 5-Year Fade Forecast (Stage 2) — growth fading from 19.21% to 4.50%

| Metric | Year 6 | Year 7 | Year 8 | Year 9 | Year 10 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹57.29B | ₹64.92B | ₹71.66B | ₹77.00B | ₹80.46B |
| EBIT | ₹7.41B | ₹8.40B | ₹9.27B | ₹9.96B | ₹10.41B |
| Taxes | ₹1.73B | ₹1.96B | ₹2.16B | ₹2.32B | ₹2.43B |
| D&A | ₹1.85B | ₹2.09B | ₹2.31B | ₹2.48B | ₹2.59B |
| CapEx | ₹3.29B | ₹3.73B | ₹4.12B | ₹4.43B | ₹4.63B |
| NWC Change (CF) | ₹-2.99B | ₹-3.39B | ₹-3.74B | ₹-4.02B | ₹-4.20B |
| Free Cash Flow | ₹1.24B | ₹1.41B | ₹1.56B | ₹1.67B | ₹1.75B |
| Discount Factor | 2.1237 | 2.4077 | 2.7297 | 3.0948 | 3.5088 |
| PV of Cash Flow | ₹585.44M | ₹585.18M | ₹569.74M | ₹539.92M | ₹497.66M |

### Terminal Value
- Final fade year (Year 10) FCF: ₹1.75B
- Terminal growth (Gordon): 4.50%
- Sector mapping: SECTOR_TERMINAL_GROWTH lookup for (Chemical (Specialty), India)
- Terminal Value: ₹20.56B
- PV of Terminal Value (discounted from Year 10): ₹5.86B

### Valuation Bridge
- **PV of Explicit FCFs**: ₹5.37B
- **PV of Terminal Value (g = 4.50%)**: ₹5.86B
- **Enterprise Value**: ₹11.23B
- **Add: Cash & Equivalents**: ₹84.90M
- **Less: Total Debt**: ₹1.17B
- **Equity Value**: ₹10.15B
- **Shares Outstanding**: 48,995,551
- **Intrinsic Value per Share**: **₹207.08**

## 3. Buffett Investor Lens
All 14 checks per Warren Buffett's framework across 4 Parts (frameworks/buffett.md):

### Part A — Business Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Durable competitive advantage (moat) | ✅ | 2.80% | < 3.0% | stdev = 2.80% < 3% |
| High return on invested capital | ✅ | 17.84% | > 15.0% | 4y avg = 17.84% > 15% |
| Strong free-cash-flow generation | ❌ | 0.02 / 320.62 | Margin > 10% & Growth > 0% | avg margin = 1.73%, FCF growth = 32062.50% |
| Earnings predictability | ✅ | 0.19 / 0.08 | 5% < CAGR < 30% & YoY Growth StDev < 10.0% | Revenue CAGR = 19.21%, YoY Growth StDev = 7.51% |

_Part A — Business Quality: **3/4 passed**_

### Part B — Financial Health

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Conservative balance sheet | ✅ | 0.39 / 26.13 | Debt/EBITDA < 3x & Coverage > 5x | Debt/EBITDA = 0.39x, Int. Coverage = 26.13x |
| ROE without excess leverage | ✅ | 0.20 / 0.77 | ROE > 15% & Equity/Assets > 40% | 4y avg ROE = 20.19%, Equity/Assets = 77.07% |
| Liquidity cushion (Gibraltar test) | ❌ | 84900000.00 / 1165500000.00 | Cash / Debt > 0.5x OR debt-free | Cash / Debt = 0.07x (<= 0.5) |

_Part B — Financial Health: **2/3 passed**_

### Part C — Management & Capital Allocation

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Anti-dilution discipline | ❌ | [4 values] | <= 2% growth over 4y | Share count growth (4y): +3.31% (threshold: <= +2%) |
| Capital allocation track record | ❌ | -0.07607559171980263 / True | ROIC not declining > 3pp AND capital returned | ROIC trend (latter-2y vs earlier-2y): -7.61pp; capital returned to shareholders: yes |
| Owner orientation | ✅ | 0.54758 / None | Insiders > 5% OR LLM = owner_oriented | Insider ownership: 54.76% (PASS at >5%). LLM owner-orientation: unavailable |
| Management coherence | ✅ | True | LLM coherence = coherent | Soft check: SKIPPED (qualitative unavailable); defaulted PASS |

_Part C — Management & Capital Allocation: **2/4 passed**_

### Part D — Margin of Safety & Holdability

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin of safety | ❌ | Trading at 7.4x intrinsic | > 25.0% | Trading at 7.4x intrinsic value (target ≤ 0.75x) (Price: 1525.00, Intrinsic: 207.08) |
| Understandable business (hard blacklist) | ✅ | True | Ticker not BTC/ETH/COIN | Hard check: PASS (ticker not in avoided-sector blacklist) |
| Holdability (20-year test) | ✅ | N/A | LLM verdict = holdable_20y | Holdability check skipped (qualitative unavailable); defaulted PASS |

_Part D — Margin of Safety & Holdability: **2/3 passed**_

**Total Buffett Score**: **9/14**

## 3.1 Marks Investor Lens
All 14 checks per Howard Marks's risk-first framework (frameworks/marks.md):

### Part A — Margin of Safety & Asymmetric Payoff

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Deep margin of safety | ❌ | Trading at 7.4x intrinsic | > 40% | MoS = -636.44% (< 40% threshold) — Price 1525.00 vs Intrinsic 207.08 |
| Asymmetric upside-to-downside payoff | ❌ | 0.000 | > 3.0x | Asymmetry ratio = 0.00 (< 3.0 threshold) |
| Downside protection (tangible book) | ❌ | 14.92% | > 30% | Equity/MCap = 14.92% (<= 30%) |
| Multiple expansion not exhausted | ❌ | 44.565 | < 25x (v0.3 placeholder; sector comp in v0.4) | Trailing P/E = 44.6x (>= 25x) |

_Part A — Margin of Safety & Asymmetric Payoff: **0/4 passed**_

### Part B — Cycle Position

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Sector cycle position | ✅ | N/A | trough | early_recovery | mid_cycle | Cycle position unavailable; defaulted PASS (mid_cycle assumed) |
| Company earnings vs cyclical peak | ✅ | 95.42% | > 70% of peak | Latest NI / Peak NI = 95.4% |
| Sentiment — going against the crowd | ❌ | 1.000 | Mean rating 2.5-4.0 (mixed/cautious consensus) | Consensus rating mean: 1.00 (FAIL — Marks prefers 2.5-4.0 mixed/cautious; strong buy consensus is a contrarian caution signal) |

_Part B — Cycle Position: **2/3 passed**_

### Part C — Risk Architecture

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Capital structure resilience | ✅ | 0.39 / 26.13 | Debt/EBITDA < 4x AND Coverage > 4x | Debt/EBITDA = 0.39x, Coverage = 26.13x |
| FCF stability through downturn | ❌ | -881200000.000 | All 4 years positive FCF | 4y FCF: [3200000.0, 1056900000.0, -881200000.0, 1029200000.0] |
| Volatility / beta | ✅ | -0.456 | < 1.5 | Beta = -0.46 (< 1.5) |
| No single-point failure mode | ✅ | 0 | <= 1 concentration/regulatory risk flagged | Concentration/regulatory risks identified: 0 |

_Part C — Risk Architecture: **3/4 passed**_

### Part D — Second-Level Thinking & Contrarianism

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Variant perception | ❌ | False | variant_present=true AND specificity=high | Variant perception unavailable; defaulted FAIL |
| Management humility (knowing what you don't know) | ✅ | N/A | verdict = humble | Management humility check skipped; defaulted PASS |
| Patient opportunism (why now) | ❌ | N/A | verdict = dislocation_present | Why-now signal unavailable; defaulted FAIL |

_Part D — Second-Level Thinking & Contrarianism: **1/3 passed**_

**Total Marks Score**: **6/14**

## 3.2 KKR Investor Lens
All 18 checks per KKR's operating playbook framework (frameworks/kkr.md):

### Part A — LBO Viability

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| EBITDA Scale | ❌ | 2955700000.000 | > ₹4.0B | Latest EBITDA fails scale check. |
| FCF Conversion | ❌ | 18.94% | > 60.00% | Average conversion is 18.9%. |
| Leverage Capacity | ✅ | 0.394 | < 3.0x | Leverage is 0.39x. |
| EBITDA Margin | ❌ | 14.44% | > 15.00% | Margin is 14.4%. |

_Part A — LBO Viability: **1/4 passed**_

### Part B — Operational Upside

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin Improvement Room | ✅ | 0.11 / 0.15 | Current < 95% of Peak | Margin compression exists. |
| Capex Optimization | ❌ | 0.03 / 0.00 | Optimization profile | Capex/Sales 3.4%, Growth share 0.0%. No obvious capex lever. |
| WC Optimization | ✅ | -19.56% | < -5% or qualitative | Quantitative pass. Qualitative: None. |
| M&A Platform Potential | ✅ | N/A | Qualitative high | Defaulted PASS (qualitative unavailable) |
| Mgmt / Ops Upgrade | ✅ | 36.12% | > 20% cost share | Opex share 36.1%. Qualitative: None. |
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
| 7-Year IRR | ❌ | 16.07% | > 18.00% | Entry mult 25.7x -> Exit mult 21.8x. |
| Dividend Recap | ❌ | 307.52% | CV < 35%, FCF > 0 | CV is 307.5%, min FCF -881200000.0. |
| Why Now Catalyst | ❌ | N/A | Catalyst present | Defaulted FAIL (qualitative unavailable) |

_Part D — Cycle Timing & Returns: **1/4 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ✅ | 5 | >= 4 | 5 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **1/1 passed**_

**Total KKR Score**: **11/18**

## 3.3 Blackstone Investor Lens
All 14 checks per Blackstone's thematic framework (frameworks/blackstone.md):

### Part A — Good Business Filter

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Growing Market | ✅ | 19.21% | > 5% & upward | CAGR is 19.2%. |
| Durable Moat | ✅ | 0.03 / 0.45 | Stdev < 4pp & > 35% | Stdev 2.8pp, Mean 44.6%. |
| Recurring Revenue | ✅ | 0.075 | < 8pp | YoY growth stdev is 7.5pp. |
| No Concentration | ✅ | diversified | Diversified | Assumed diversified (public company baseline). |

_Part A — Good Business Filter: **4/4 passed**_

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
| Conservative Balance Sheet | ✅ | 0.39 / 26.13 | <3.5x, >4x | Leverage 0.4x, Interest Coverage 26.1x. |
| FCF Resilience | ❌ | -881200000.00 / 0.02 | >0, >6% | Min FCF -881200000.0, Avg FCF Margin 1.8%. |
| Stress Survival | ✅ | 0.04 / 0.02 | Cash>1x OR Debt/MC<0.5 | Cash ratio 0.04x, Debt/Equity 1.6%. |

_Part C — Downside Protection: **2/3 passed**_

### Part D — Scale Fit & Hold Economics

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Blackstone-Scale Deal | ❌ | 74718216192.000 | > ₹150B | Market cap is too small. |
| 20-Year Core Viability | ✅ | N/A | Holdable 20y | Defaulted PASS (assumed holdable) |
| Multi-Product Engagement | ✅ | N/A | Multi-product | neutral default — qualitative unavailable; check counted as PASS |

_Part D — Scale Fit & Hold Economics: **2/3 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ✅ | 5 | >= 4 | 5 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **1/1 passed**_

**Total Blackstone Score**: **11/14**

## 3.4 Apollo Investor Lens
All 16 checks per Apollo's credit & complexity framework (frameworks/apollo.md):

### Part A — Purchase Price & Capital Structure Entry

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Entry Valuation Discount | ❌ | 25.674 | < 10.4x EV/EBITDA or <0.70 P/B | EV/EBITDA is 25.7x. P/B is 6.70x. |
| Capital Structure Complexity | ❌ | 0.39 / 26.13 | Debt stress | Lev: 0.4x, IC: 26.1x. Clean. |
| FCF Serviceability | ✅ | 30.380 | >0 FCF, >1.5x Cov | Avg FCF 302025000.0, Hyp Cov 30.4x. |
| Deployment Scale | ✅ | 75883716192.000 | > ₹20B | EV is 75883716192.0. |

_Part A — Purchase Price & Capital Structure Entry: **2/4 passed**_

### Part B — Chaos, Complexity, Credit Edge

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Chaos/Dislocation Catalyst | ❌ | N/A | Present | Defaulted FAIL (qualitative unavailable) |
| Fulcrum Security | ❌ | (0.39432283384646616, 26.126596980255517, 64.1082936010296) | Hard or Soft Fulcrum | Qual: None. Hard signals: A=False, B=False. |
| ABF/Credit Fit | ❌ | N/A | Compatible | Defaulted FAIL (qualitative unavailable) |
| Complexity Moat | ❌ | 8.06% | >55% or High Qual | Debt/Assets 8.1%. Qual: None. |
| Domain Knowledge | ✅ | Chemical (Specialty) | In Apollo Playbook | Chemical (Specialty) in playbook. |

_Part B — Chaos, Complexity, Credit Edge: **1/5 passed**_

### Part C — Athene Permanent Capital Fit

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| IG Credit Yield | ✅ | (0.14439038211644245, 0.39432283384646616, 26.126596980255517) | Margin>12%, Lev<5x, IC>1.5x | Margin 14.4%, Lev 0.4x, IC 26.1x. |
| Long-Duration Stability | ❌ | 0.053 | < 4pp, > 0 avg | FCF Margin Stdev 5.3pp. |
| Hold-Without-Exit | ✅ | N/A | Viable | neutral default — qualitative unavailable; check counted as PASS |

_Part C — Athene Permanent Capital Fit: **2/3 passed**_

### Part D — Credit Downside Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Through-Cycle Credit Floor | ✅ | 1730100000.00 / 24.14 | Min EBIT>0, Cov>1.5x | Min EBIT 1730100000.0, Avg Cov 24.1x. |
| Tangible Collateral | ✅ | 99.71% | > 40% | Ratio 99.7%. |
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
Current Stock Price: **₹1,525.00**
DCF Intrinsic Value: **₹207.08**
Required Margin of Safety: **25.00%** (Graham & Dodd standard — Buffett lens)
Computed Margin of Safety: Trading at 7.4x intrinsic value (target ≤ 0.75x)
### Status: [FAIL] ❌
The stock trades above the safety threshold. Trading at 7.4x intrinsic value is insufficient for investment under the Buffett framework.

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
| **Marks** | 6/14 | **SKIP** ❌ |
| **KKR** | 11/18 | **SKIP** ❌ |
| **Blackstone** | 11/14 | **BUY** ✅ |
| **Apollo** | 8/16 | **SKIP** ❌ |
