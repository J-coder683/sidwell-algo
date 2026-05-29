# Investment Analysis Report: RELIANCE.NS
**Generated on**: May 29, 2026
**Valuation Engine**: Discounted Cash Flow (DCF)
**Investor Lenses**: Warren Buffett + Howard Marks + KKR + Blackstone + Apollo (v0.6)

## Executive Summary
| Metric | Value | Source / Detail |
| :--- | :--- | :--- |
| **Current Price** | ₹1,350.00 | Yahoo Finance |
| **Intrinsic Value (DCF)** | ₹554.19 | Sidwell DCF Engine |
| **Margin of Safety** | Trading at 2.4x intrinsic value (target ≤ 0.75x) | Current Discount to Intrinsic |
| **Buffett Score** | **9/14** | Buffett Lens (14 checks) |
| **Buffett Verdict** | **SKIP** ❌ | Buffett Lens Rules |
| **Marks Score** | **9/14** | Marks Lens (14 checks) |
| **Marks Verdict** | **WAIT** ⏳ | Marks Lens Rules |
| **KKR Score** | **10/18** | KKR Lens (18 checks) |
| **KKR Verdict** | **SKIP** ❌ | KKR Lens Rules |
| **Blackstone Score** | **11/14** | Blackstone Lens (14 checks) |
| **Blackstone Verdict** | **BUY** ✅ | Blackstone Lens Rules |
| **Apollo Score** | **8/16** | Apollo Lens (16 checks) |
| **Apollo Verdict** | **SKIP** ❌ | Apollo Lens Rules |

### Verdict Summary
> **Buffett**: **SKIP** — Does not meet enough Buffett criteria across business quality, management, and price.
> **Marks**: **WAIT** — Risk architecture acceptable but MoS or multiple position inadequate. Set re-rating alert at 332.52 (60% of intrinsic = 40% MoS).
> **KKR**: **SKIP** — Failed Part A pre-condition: not LBO-viable.
> **Blackstone**: **BUY** — High-conviction Blackstone target. Good business in a good neighborhood.
> **Apollo**: **SKIP** — Failed Part E pre-condition: lacks above-average alpha thesis (Phalippou bar).

## 1. Company Snapshot
Historical financial statements over the last 4 years:

| Metric | 2023 | 2024 | 2025 | 2026 |
| :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹8,763.96B | ₹8,990.41B | ₹9,628.20B | ₹10,572.19B |
| Gross Margin (%) | 32.85% | 34.89% | 34.60% | 34.86% |
| EBIT | ₹1,423.18B | ₹1,624.98B | ₹1,655.98B | ₹1,789.49B |
| Free Cash Flow | ₹-167.70B | ₹212.12B | ₹410.79B | ₹700.23B |
| Total Debt | ₹4,516.64B | ₹3,507.19B | ₹3,743.13B | ₹3,980.00B |
| Stockholders Equity | ₹7,158.72B | ₹7,934.81B | ₹8,432.00B | ₹9,040.30B |

## 2. DCF Valuation & WACC Sourcing
Every component of the Weighted Average Cost of Capital (WACC) is explicitly sourced and modeled below:

### WACC Components & Assumptions
| Component | Value | Source / Reference |
| :--- | :--- | :--- |
| **Risk-Free Rate ($R_f$)** | 7.12% | FRED Series: `INDIRLTLT01STM` (India 10Y G-Sec) |
| **Mature Market ERP** | 4.23% | Damodaran NYU Stern (Mature Equity Risk Premium) |
| **Country Risk Premium** | 2.85% | Damodaran NYU Stern (Country default spread adjusted) |
| **Total Equity Risk Premium** | 7.08% | Damodaran mature ERP + country premium = 7.08% |
| **Industry Unlevered Beta** | 0.59 | Damodaran 'Oil/Gas (Integrated)' (hardcoded fallback (Damodaran lookup failed)) |
| **Target Levered Beta ($\beta$)** | 0.69 | Re-levered using actual D/E = 0.69 |
| **Cost of Equity ($K_e$)** | 12.02% | CAPM: $R_f + \beta \times ERP$ = 12.02% |
| **Cost of Debt ($K_d$)** | 8.12% | Calculated and floored to Rf + 1% (raw: 6.80%) |
| **Effective Tax Rate ($t$)** | 23.25% | 4-year historical average from filings |
| **Equity Weight ($W_e$)** | 82.12% | Market Cap / (Market Cap + Total Debt) |
| **Debt Weight ($W_d$)** | 17.88% | Total Debt / (Market Cap + Total Debt) |
| **Computed WACC** | **10.98%** | Weighted cost of capital = **10.98%** |

### 5-Year High-Growth Forecast (Stage 1)
Projections are based on historical averages relative to Revenue. Revenue growth is projected at **6.45%** (historical 4y CAGR capped between 5% and 20%).

| Metric | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹11,254.33B | ₹11,980.49B | ₹12,753.50B | ₹13,576.39B | ₹14,452.38B |
| EBIT | ₹1,925.60B | ₹2,049.84B | ₹2,182.10B | ₹2,322.90B | ₹2,472.77B |
| Taxes | ₹447.70B | ₹476.59B | ₹507.34B | ₹540.07B | ₹574.92B |
| D&A | ₹597.27B | ₹635.81B | ₹676.83B | ₹720.50B | ₹766.99B |
| CapEx | ₹1,580.78B | ₹1,682.77B | ₹1,791.35B | ₹1,906.93B | ₹2,029.97B |
| NWC Change (CF) | ₹131.20B | ₹139.67B | ₹148.68B | ₹158.27B | ₹168.48B |
| Free Cash Flow | ₹625.59B | ₹665.96B | ₹708.93B | ₹754.67B | ₹803.36B |
| Discount Factor | 1.1098 | 1.2317 | 1.3670 | 1.5172 | 1.6838 |
| PV of Cash Flow | ₹563.68B | ₹540.67B | ₹518.60B | ₹497.42B | ₹477.12B |

### 5-Year Fade Forecast (Stage 2) — growth fading from 6.45% to 4.00%

| Metric | Year 6 | Year 7 | Year 8 | Year 9 | Year 10 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹15,314.00B | ₹16,151.88B | ₹16,956.39B | ₹17,717.81B | ₹18,426.52B |
| EBIT | ₹2,620.20B | ₹2,763.56B | ₹2,901.21B | ₹3,031.48B | ₹3,152.74B |
| Taxes | ₹609.20B | ₹642.53B | ₹674.53B | ₹704.82B | ₹733.01B |
| D&A | ₹812.72B | ₹857.18B | ₹899.88B | ₹940.29B | ₹977.90B |
| CapEx | ₹2,150.99B | ₹2,268.68B | ₹2,381.68B | ₹2,488.63B | ₹2,588.17B |
| NWC Change (CF) | ₹178.53B | ₹188.30B | ₹197.68B | ₹206.55B | ₹214.81B |
| Free Cash Flow | ₹851.26B | ₹897.83B | ₹942.55B | ₹984.88B | ₹1,024.27B |
| Discount Factor | 1.8687 | 2.0740 | 2.3018 | 2.5546 | 2.8351 |
| PV of Cash Flow | ₹455.53B | ₹432.91B | ₹409.49B | ₹385.54B | ₹361.28B |

### Terminal Value
- Final fade year (Year 10) FCF: ₹1,024.27B
- Terminal growth (Gordon): 4.00%
- Sector mapping: DEFAULT_TERMINAL_GROWTH_INDIA
- Terminal Value: ₹15,254.28B
- PV of Terminal Value (discounted from Year 10): ₹5,380.44B

### Valuation Bridge
- **PV of Explicit FCFs**: ₹4,642.23B
- **PV of Terminal Value (g = 4.00%)**: ₹5,380.44B
- **Enterprise Value**: ₹10,022.67B
- **Add: Cash & Equivalents**: ₹1,459.77B
- **Less: Total Debt**: ₹3,980.00B
- **Equity Value**: ₹7,502.44B
- **Shares Outstanding**: 13,537,548,148
- **Intrinsic Value per Share**: **₹554.19**

## 3. Buffett Investor Lens
All 14 checks per Warren Buffett's framework across 4 Parts (frameworks/buffett.md):

### Part A — Business Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Durable competitive advantage (moat) | ✅ | 0.98% | < 3.0% | stdev = 0.98% < 3% |
| High return on invested capital | ❌ | 11.29% | > 15.0% | 4y avg = 11.29% <= 15% |
| Strong free-cash-flow generation | ❌ | 0.03 / 5.18 | Margin > 10% & Growth > 0% | avg margin = 2.83%, FCF growth = 517.55% |
| Earnings predictability | ✅ | 0.06 / 0.04 | 5% < CAGR < 30% & YoY Growth StDev < 10.0% | Revenue CAGR = 6.45%, YoY Growth StDev = 3.65% |

_Part A — Business Quality: **2/4 passed**_

### Part B — Financial Health

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Conservative balance sheet | ✅ | 1.68 / 6.61 | Debt/EBITDA < 3x & Coverage > 5x | Debt/EBITDA = 1.68x, Int. Coverage = 6.61x |
| ROE without excess leverage | ❌ | 0.10 / 0.42 | ROE > 15% & Equity/Assets > 40% | 4y avg ROE = 10.14%, Equity/Assets = 41.50% |
| Liquidity cushion (Gibraltar test) | ❌ | 1459770000000.00 / 3980000000000.00 | Cash / Debt > 0.5x OR debt-free | Cash / Debt = 0.37x (<= 0.5) |

_Part B — Financial Health: **1/3 passed**_

### Part C — Management & Capital Allocation

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Anti-dilution discipline | ✅ | [4 values] | <= 2% growth over 4y | Share count growth (4y): +0.00% (threshold: <= +2%) |
| Capital allocation track record | ✅ | 0.007339123486534538 / True | ROIC not declining > 3pp AND capital returned | ROIC trend (latter-2y vs earlier-2y): +0.73pp; capital returned to shareholders: yes |
| Owner orientation | ✅ | 0.5 / None | Insiders > 5% OR LLM = owner_oriented | Insider ownership: 50.00% (PASS at >5%). LLM owner-orientation: unavailable |
| Management coherence | ✅ | True | LLM coherence = coherent | Soft check: SKIPPED (qualitative unavailable); defaulted PASS |

_Part C — Management & Capital Allocation: **4/4 passed**_

### Part D — Margin of Safety & Holdability

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin of safety | ❌ | Trading at 2.4x intrinsic | > 25.0% | Trading at 2.4x intrinsic value (target ≤ 0.75x) (Price: 1350.00, Intrinsic: 554.19) |
| Understandable business (hard blacklist) | ✅ | True | Ticker not BTC/ETH/COIN | Hard check: PASS (ticker not in avoided-sector blacklist) |
| Holdability (20-year test) | ✅ | N/A | LLM verdict = holdable_20y | Holdability check skipped (qualitative unavailable); defaulted PASS |

_Part D — Margin of Safety & Holdability: **2/3 passed**_

**Total Buffett Score**: **9/14**

## 3.1 Marks Investor Lens
All 14 checks per Howard Marks's risk-first framework (frameworks/marks.md):

### Part A — Margin of Safety & Asymmetric Payoff

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Deep margin of safety | ❌ | Trading at 2.4x intrinsic | > 40% | MoS = -143.60% (< 40% threshold) — Price 1350.00 vs Intrinsic 554.19 |
| Asymmetric upside-to-downside payoff | ❌ | 0.000 | > 3.0x | Asymmetry ratio = 0.00 (< 3.0 threshold) |
| Downside protection (tangible book) | ✅ | 49.47% | > 30% | Equity/MCap = 49.47% (> 30%) |
| Multiple expansion not exhausted | ✅ | 22.600 | < 25x (v0.3 placeholder; sector comp in v0.4) | Trailing P/E = 22.6x (< 25x) |

_Part A — Margin of Safety & Asymmetric Payoff: **2/4 passed**_

### Part B — Cycle Position

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Sector cycle position | ✅ | N/A | trough | early_recovery | mid_cycle | Cycle position unavailable; defaulted PASS (mid_cycle assumed) |
| Company earnings vs cyclical peak | ✅ | 100.00% | > 70% of peak | Latest NI / Peak NI = 100.0% |
| Sentiment — going against the crowd | ✅ | N/A | Mean rating 2.5-4.0 (mixed/cautious consensus) | Consensus rating unavailable; defaulted PASS |

_Part B — Cycle Position: **3/3 passed**_

### Part C — Risk Architecture

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Capital structure resilience | ✅ | 1.68 / 6.61 | Debt/EBITDA < 4x AND Coverage > 4x | Debt/EBITDA = 1.68x, Coverage = 6.61x |
| FCF stability through downturn | ❌ | -167700000000.000 | All 4 years positive FCF | 4y FCF: [-167700000000.0, 212120000000.0, 410790000000.0, 700230000000.0] |
| Volatility / beta | ✅ | 1.000 | < 1.5 | Beta = 1.00 (< 1.5) |
| No single-point failure mode | ✅ | 0 | <= 1 concentration/regulatory risk flagged | Concentration/regulatory risks identified: 0 |

_Part C — Risk Architecture: **3/4 passed**_

### Part D — Second-Level Thinking & Contrarianism

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Variant perception | ❌ | False | variant_present=true AND specificity=high | Variant perception unavailable; defaulted FAIL |
| Management humility (knowing what you don't know) | ✅ | N/A | verdict = humble | Management humility check skipped; defaulted PASS |
| Patient opportunism (why now) | ❌ | N/A | verdict = dislocation_present | Why-now signal unavailable; defaulted FAIL |

_Part D — Second-Level Thinking & Contrarianism: **1/3 passed**_

**Total Marks Score**: **9/14**

## 3.2 KKR Investor Lens
All 18 checks per KKR's operating playbook framework (frameworks/kkr.md):

### Part A — LBO Viability

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| EBITDA Scale | ✅ | 2366370000000.000 | > ₹4.0B | Latest EBITDA passes scale check. |
| FCF Conversion | ❌ | 23.19% | > 60.00% | Average conversion is 23.2%. |
| Leverage Capacity | ✅ | 1.682 | < 3.0x | Leverage is 1.68x. |
| EBITDA Margin | ✅ | 22.38% | > 15.00% | Margin is 22.4%. |

_Part A — LBO Viability: **3/4 passed**_

### Part B — Operational Upside

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin Improvement Room | ✅ | 0.17 / 0.18 | Current < 95% of Peak | Margin compression exists. |
| Capex Optimization | ✅ | 0.12 / 0.53 | Optimization profile | Capex/Sales 11.5%, Growth share 52.7%. Optimization possible. |
| WC Optimization | ❌ | 4.49% | < -5% or qualitative | Quantitative fail. Qualitative: None. |
| M&A Platform Potential | ✅ | N/A | Qualitative high | Defaulted PASS (qualitative unavailable) |
| Mgmt / Ops Upgrade | ❌ | 17.93% | > 20% cost share | Opex share 17.9%. Qualitative: None. |
| Stavros Workforce Fit | ✅ | N/A | Frontline or mixed | Defaulted PASS (qualitative unavailable, assumed mixed) |

_Part B — Operational Upside: **4/6 passed**_

### Part C — Strategic Fit

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Sector Compatibility | ❌ | Oil/Gas (Integrated) | In KKR Playbook | Oil/Gas (Integrated) is NOT in KKR playbook. |
| Willing Seller | ✅ | N/A | Positive catalyst | neutral default — qualitative unavailable; check counted as PASS |
| Regulatory Freedom | ✅ | Oil/Gas (Integrated) | Not restricted | Clear. |

_Part C — Strategic Fit: **2/3 passed**_

### Part D — Cycle Timing & Returns

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Cycle Timing | ✅ | N/A | Not peak/late | Defaulted PASS (assumed mid_cycle) |
| 7-Year IRR | ❌ | 16.48% | > 18.00% | Entry mult 9.4x -> Exit mult 8.0x. |
| Dividend Recap | ❌ | 126.16% | CV < 35%, FCF > 0 | CV is 126.2%, min FCF -167700000000.0. |
| Why Now Catalyst | ❌ | N/A | Catalyst present | Defaulted FAIL (qualitative unavailable) |

_Part D — Cycle Timing & Returns: **1/4 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ❌ | 3 | >= 4 | 3 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **0/1 passed**_

**Total KKR Score**: **10/18**

## 3.3 Blackstone Investor Lens
All 14 checks per Blackstone's thematic framework (frameworks/blackstone.md):

### Part A — Good Business Filter

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Growing Market | ✅ | 6.45% | > 5% & upward | CAGR is 6.5%. |
| Durable Moat | ❌ | 0.01 / 0.34 | Stdev < 4pp & > 35% | Stdev 1.0pp, Mean 34.3%. |
| Recurring Revenue | ✅ | 0.036 | < 8pp | YoY growth stdev is 3.6pp. |
| No Concentration | ✅ | diversified | Diversified | Assumed diversified (public company baseline). |

_Part A — Good Business Filter: **3/4 passed**_

### Part B — Good Neighborhood (Thematic)

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Theme Alignment | ❌ | Oil/Gas (Integrated) | Favored Theme | Oil/Gas (Integrated) not in themes. |
| Cycle Position | ✅ | N/A | Not peak/late | Defaulted PASS (assumed mid_cycle) |
| Structural Tailwind | ✅ | N/A | Tailwind/neutral | Defaulted PASS (assumed neutral) |

_Part B — Good Neighborhood (Thematic): **2/3 passed**_

### Part C — Downside Protection

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Conservative Balance Sheet | ✅ | 1.68 / 6.61 | <3.5x, >4x | Leverage 1.7x, Interest Coverage 6.6x. |
| FCF Resilience | ❌ | -167700000000.00 / 0.03 | >0, >6% | Min FCF -167700000000.0, Avg FCF Margin 3.0%. |
| Stress Survival | ✅ | 1.38 / 0.22 | Cash>1x OR Debt/MC<0.5 | Cash ratio 1.38x, Debt/Equity 21.8%. |

_Part C — Downside Protection: **2/3 passed**_

### Part D — Scale Fit & Hold Economics

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Blackstone-Scale Deal | ✅ | 18275690000000.000 | > ₹150B | Market cap is adequate. |
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
| Entry Valuation Discount | ❌ | 9.405 | < -0.8x EV/EBITDA or <0.70 P/B | EV/EBITDA is 9.4x. P/B is 2.02x. |
| Capital Structure Complexity | ❌ | 1.68 / 6.61 | Debt stress | Lev: 1.7x, IC: 6.6x. Clean. |
| FCF Serviceability | ✅ | 7.639 | >0 FCF, >1.5x Cov | Avg FCF 288860000000.0, Hyp Cov 7.6x. |
| Deployment Scale | ✅ | 22255690000000.000 | > ₹20B | EV is 22255690000000.0. |

_Part A — Purchase Price & Capital Structure Entry: **2/4 passed**_

### Part B — Chaos, Complexity, Credit Edge

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Chaos/Dislocation Catalyst | ❌ | N/A | Present | Defaulted FAIL (qualitative unavailable) |
| Fulcrum Security | ❌ | (1.6819009706850576, 6.612800709508148, 4.591881909547738) | Hard or Soft Fulcrum | Qual: None. Hard signals: A=False, B=False. |
| ABF/Credit Fit | ❌ | N/A | Compatible | Defaulted FAIL (qualitative unavailable) |
| Complexity Moat | ❌ | 18.27% | >55% or High Qual | Debt/Assets 18.3%. Qual: None. |
| Domain Knowledge | ❌ | Oil/Gas (Integrated) | In Apollo Playbook | Oil/Gas (Integrated) not in playbook. |

_Part B — Chaos, Complexity, Credit Edge: **0/5 passed**_

### Part C — Athene Permanent Capital Fit

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| IG Credit Yield | ✅ | (0.22382968902375006, 1.6819009706850576, 6.612800709508148) | Margin>12%, Lev<5x, IC>1.5x | Margin 22.4%, Lev 1.7x, IC 6.6x. |
| Long-Duration Stability | ✅ | 0.036 | < 4pp, > 0 avg | FCF Margin Stdev 3.6pp. |
| Hold-Without-Exit | ✅ | N/A | Viable | neutral default — qualitative unavailable; check counted as PASS |

_Part C — Athene Permanent Capital Fit: **3/3 passed**_

### Part D — Credit Downside Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Through-Cycle Credit Floor | ✅ | 1423180000000.00 / 5.83 | Min EBIT>0, Cov>1.5x | Min EBIT 1423180000000.0, Avg Cov 5.8x. |
| Tangible Collateral | ✅ | 100.00% | > 40% | Ratio 100.0%. |
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
Current Stock Price: **₹1,350.00**
DCF Intrinsic Value: **₹554.19**
Required Margin of Safety: **25.00%** (Graham & Dodd standard — Buffett lens)
Computed Margin of Safety: Trading at 2.4x intrinsic value (target ≤ 0.75x)
### Status: [FAIL] ❌
The stock trades above the safety threshold. Trading at 2.4x intrinsic value is insufficient for investment under the Buffett framework.

## 5. Investment Verdict
**BUFFETT RECOMMENDATION: SKIP**

Does not meet enough Buffett criteria across business quality, management, and price.

**MARKS RECOMMENDATION: WAIT**

Risk architecture acceptable but MoS or multiple position inadequate. Set re-rating alert at 332.52 (60% of intrinsic = 40% MoS).

**Marks Action Item**: Set re-rating alert at **₹332.52** (60% of intrinsic = 40% MoS).

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
| **Marks** | 9/14 | **WAIT** ⏳ |
| **KKR** | 10/18 | **SKIP** ❌ |
| **Blackstone** | 11/14 | **BUY** ✅ |
| **Apollo** | 8/16 | **SKIP** ❌ |
