# Investment Analysis Report: TCS.NS
**Generated on**: May 28, 2026
**Valuation Engine**: Discounted Cash Flow (DCF)
**Investor Lenses**: Warren Buffett + Howard Marks + KKR + Blackstone + Apollo (v0.6)

## Executive Summary
| Metric | Value | Source / Detail |
| :--- | :--- | :--- |
| **Current Price** | ₹2,289.90 | Yahoo Finance |
| **Intrinsic Value (DCF)** | ₹1,391.88 | Sidwell DCF Engine |
| **Margin of Safety** | Trading at 1.6x intrinsic value (target ≤ 0.75x) | Current Discount to Intrinsic |
| **Buffett Score** | **13/14** | Buffett Lens (14 checks) |
| **Buffett Verdict** | **WAIT** ⏳ | Buffett Lens Rules |
| **Marks Score** | **8/14** | Marks Lens (14 checks) |
| **Marks Verdict** | **SKIP** ❌ | Marks Lens Rules |
| **KKR Score** | **14/18** | KKR Lens (18 checks) |
| **KKR Verdict** | **WATCH** 👀 | KKR Lens Rules |
| **Blackstone Score** | **14/14** | Blackstone Lens (14 checks) |
| **Blackstone Verdict** | **BUY** ✅ | Blackstone Lens Rules |
| **Apollo Score** | **9/16** | Apollo Lens (16 checks) |
| **Apollo Verdict** | **SKIP** ❌ | Apollo Lens Rules |

### Verdict Summary
> **Buffett**: **WAIT** — High-quality business that satisfies most Buffett criteria but lacks margin of safety. Set alert at buy-trigger price: ₹1043.91 (75% of intrinsic value).
> **Marks**: **SKIP** — Insufficient asymmetric edge under Marks framework.
> **KKR**: **WATCH** — Mixed signals across strategic/timing checks; monitor for changes.
> **Blackstone**: **BUY** — High-conviction Blackstone target. Good business in a good neighborhood.
> **Apollo**: **SKIP** — Failed Part E pre-condition: lacks above-average alpha thesis (Phalippou bar).

## 1. Company Snapshot
Historical financial statements over the last 4 years:

| Metric | 2023 | 2024 | 2025 | 2026 |
| :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹2,254.58B | ₹2,408.93B | ₹2,553.24B | ₹2,670.21B |
| Gross Margin (%) | 46.88% | 44.84% | 42.94% | 45.10% |
| EBIT | ₹576.86B | ₹627.75B | ₹661.27B | ₹667.14B |
| Free Cash Flow | ₹388.65B | ₹416.64B | ₹449.71B | ₹479.48B |
| Total Debt | ₹76.88B | ₹80.21B | ₹93.92B | ₹112.83B |
| Stockholders Equity | ₹904.24B | ₹904.89B | ₹947.56B | ₹1,072.40B |

## 2. DCF Valuation & WACC Sourcing
Every component of the Weighted Average Cost of Capital (WACC) is explicitly sourced and modeled below:

### WACC Components & Assumptions
| Component | Value | Source / Reference |
| :--- | :--- | :--- |
| **Risk-Free Rate ($R_f$)** | 7.12% | FRED Series: `INDIRLTLT01STM` (India 10Y G-Sec) |
| **Mature Market ERP** | 4.23% | Damodaran NYU Stern (Mature Equity Risk Premium) |
| **Country Risk Premium** | 2.18% | Damodaran NYU Stern (Country default spread adjusted) |
| **Total Equity Risk Premium** | 6.41% | Damodaran mature ERP + country premium = 6.41% |
| **Industry Unlevered Beta** | 1.30 | Damodaran 'Software (System & Application)' (from Damodaran sheet) |
| **Target Levered Beta ($\beta$)** | 1.31 | Re-levered using actual D/E = 1.31 |
| **Cost of Equity ($K_e$)** | 15.52% | CAPM: $R_f + \beta \times ERP$ = 15.52% |
| **Cost of Debt ($K_d$)** | 10.87% | Calculated: int_expense/debt = 10.87% |
| **Effective Tax Rate ($t$)** | 25.27% | 4-year historical average from filings |
| **Equity Weight ($W_e$)** | 98.66% | Market Cap / (Market Cap + Total Debt) |
| **Debt Weight ($W_d$)** | 1.34% | Total Debt / (Market Cap + Total Debt) |
| **Computed WACC** | **15.42%** | Weighted cost of capital = **15.42%** |

### 5-Year High-Growth Forecast (Stage 1)
Projections are based on historical averages relative to Revenue. Revenue growth is projected at **5.80%** (historical 4y CAGR capped between 5% and 20%).

| Metric | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹2,825.13B | ₹2,989.04B | ₹3,162.46B | ₹3,345.94B | ₹3,540.07B |
| EBIT | ₹724.15B | ₹766.16B | ₹810.61B | ₹857.64B | ₹907.40B |
| Taxes | ₹183.02B | ₹193.64B | ₹204.88B | ₹216.76B | ₹229.34B |
| D&A | ₹59.55B | ₹63.01B | ₹66.67B | ₹70.53B | ₹74.63B |
| CapEx | ₹39.41B | ₹41.69B | ₹44.11B | ₹46.67B | ₹49.38B |
| NWC Change (CF) | ₹-48.53B | ₹-51.34B | ₹-54.32B | ₹-57.47B | ₹-60.81B |
| Free Cash Flow | ₹512.75B | ₹542.49B | ₹573.97B | ₹607.27B | ₹642.50B |
| Discount Factor | 1.1542 | 1.3322 | 1.5377 | 1.7748 | 2.0485 |
| PV of Cash Flow | ₹444.24B | ₹407.21B | ₹373.27B | ₹342.16B | ₹313.64B |

### 5-Year Fade Forecast (Stage 2) — growth fading from 5.80% to 5.00%

| Metric | Year 6 | Year 7 | Year 8 | Year 9 | Year 10 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹3,739.78B | ₹3,944.76B | ₹4,154.65B | ₹4,369.05B | ₹4,587.50B |
| EBIT | ₹958.59B | ₹1,011.13B | ₹1,064.93B | ₹1,119.89B | ₹1,175.88B |
| Taxes | ₹242.28B | ₹255.56B | ₹269.15B | ₹283.04B | ₹297.20B |
| D&A | ₹78.84B | ₹83.16B | ₹87.58B | ₹92.10B | ₹96.71B |
| CapEx | ₹52.17B | ₹55.03B | ₹57.95B | ₹60.94B | ₹63.99B |
| NWC Change (CF) | ₹-64.24B | ₹-67.76B | ₹-71.36B | ₹-75.04B | ₹-78.80B |
| Free Cash Flow | ₹678.75B | ₹715.95B | ₹754.05B | ₹792.96B | ₹832.61B |
| Discount Factor | 2.3644 | 2.7291 | 3.1500 | 3.6358 | 4.1965 |
| PV of Cash Flow | ₹287.06B | ₹262.34B | ₹239.38B | ₹218.10B | ₹198.41B |

### Terminal Value
- Final fade year (Year 10) FCF: ₹832.61B
- Terminal growth (Gordon): 5.00%
- Sector mapping: SECTOR_TERMINAL_GROWTH lookup for (Software (System & Application), India)
- Terminal Value: ₹8,388.42B
- PV of Terminal Value (discounted from Year 10): ₹1,998.93B

### Valuation Bridge
- **PV of Explicit FCFs**: ₹3,085.81B
- **PV of Terminal Value (g = 5.00%)**: ₹1,998.93B
- **Enterprise Value**: ₹5,084.74B
- **Add: Cash & Equivalents**: ₹64.05B
- **Less: Total Debt**: ₹112.83B
- **Equity Value**: ₹5,035.96B
- **Shares Outstanding**: 3,618,087,518
- **Intrinsic Value per Share**: **₹1,391.88**

## 3. Buffett Investor Lens
All 14 checks per Warren Buffett's framework across 4 Parts (frameworks/buffett.md):

### Part A — Business Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Durable competitive advantage (moat) | ✅ | 1.61% | < 3.0% | stdev = 1.61% < 3% |
| High return on invested capital | ✅ | 48.95% | > 15.0% | 4y avg = 48.95% > 15% |
| Strong free-cash-flow generation | ✅ | 0.18 / 0.23 | Margin > 10% & Growth > 0% | avg margin = 17.53%, FCF growth = 23.37% |
| Earnings predictability | ✅ | 0.06 / 0.01 | 5% < CAGR < 30% & YoY Growth StDev < 10.0% | Revenue CAGR = 5.80%, YoY Growth StDev = 1.14% |

_Part A — Business Quality: **4/4 passed**_

### Part B — Financial Health

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Conservative balance sheet | ✅ | 0.16 / 54.37 | Debt/EBITDA < 3x & Coverage > 5x | Debt/EBITDA = 0.16x, Int. Coverage = 54.37x |
| ROE without excess leverage | ✅ | 0.49 / 0.59 | ROE > 15% & Equity/Assets > 40% | 4y avg ROE = 48.62%, Equity/Assets = 58.80% |
| Liquidity cushion (Gibraltar test) | ✅ | 64050000000.00 / 112830000000.00 | Cash / Debt > 0.5x OR debt-free | Cash / Debt = 0.57x (> 0.5) |

_Part B — Financial Health: **3/3 passed**_

### Part C — Management & Capital Allocation

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Anti-dilution discipline | ✅ | [4 values] | <= 2% growth over 4y | Share count growth (4y): -1.12% (threshold: <= +2%) |
| Capital allocation track record | ✅ | -0.018731447839557658 / True | ROIC not declining > 3pp AND capital returned | ROIC trend (latter-2y vs earlier-2y): -1.87pp; capital returned to shareholders: yes |
| Owner orientation | ✅ | 0.71795 / None | Insiders > 5% OR LLM = owner_oriented | Insider ownership: 71.80% (PASS at >5%). LLM owner-orientation: unavailable |
| Management coherence | ✅ | True | LLM coherence = coherent | Soft check: SKIPPED (qualitative unavailable); defaulted PASS |

_Part C — Management & Capital Allocation: **4/4 passed**_

### Part D — Margin of Safety & Holdability

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin of safety | ❌ | Trading at 1.6x intrinsic | > 25.0% | Trading at 1.6x intrinsic value (target ≤ 0.75x) (Price: 2289.90, Intrinsic: 1391.88) |
| Understandable business (hard blacklist) | ✅ | True | Ticker not BTC/ETH/COIN | Hard check: PASS (ticker not in avoided-sector blacklist) |
| Holdability (20-year test) | ✅ | N/A | LLM verdict = holdable_20y | Holdability check skipped (qualitative unavailable); defaulted PASS |

_Part D — Margin of Safety & Holdability: **2/3 passed**_

**Total Buffett Score**: **13/14**

## 3.1 Marks Investor Lens
All 14 checks per Howard Marks's risk-first framework (frameworks/marks.md):

### Part A — Margin of Safety & Asymmetric Payoff

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Deep margin of safety | ❌ | Trading at 1.6x intrinsic | > 40% | MoS = -64.52% (< 40% threshold) — Price 2289.90 vs Intrinsic 1391.88 |
| Asymmetric upside-to-downside payoff | ❌ | 0.000 | > 3.0x | Asymmetry ratio = 0.00 (< 3.0 threshold) |
| Downside protection (tangible book) | ❌ | 12.94% | > 30% | Equity/MCap = 12.94% (<= 30%) |
| Multiple expansion not exhausted | ✅ | 16.849 | < 25x (v0.3 placeholder; sector comp in v0.4) | Trailing P/E = 16.8x (< 25x) |

_Part A — Margin of Safety & Asymmetric Payoff: **1/4 passed**_

### Part B — Cycle Position

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Sector cycle position | ✅ | N/A | trough | early_recovery | mid_cycle | Cycle position unavailable; defaulted PASS (mid_cycle assumed) |
| Company earnings vs cyclical peak | ✅ | 100.00% | > 70% of peak | Latest NI / Peak NI = 100.0% |
| Sentiment — going against the crowd | ❌ | 2.116 | Mean rating 2.5-4.0 (mixed/cautious consensus) | Consensus rating mean: 2.12 (FAIL — Marks prefers 2.5-4.0 mixed/cautious; strong buy consensus is a contrarian caution signal) |

_Part B — Cycle Position: **2/3 passed**_

### Part C — Risk Architecture

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Capital structure resilience | ✅ | 0.16 / 54.37 | Debt/EBITDA < 4x AND Coverage > 4x | Debt/EBITDA = 0.16x, Coverage = 54.37x |
| FCF stability through downturn | ✅ | 388650000000.000 | All 4 years positive FCF | 4y FCF: [388650000000.0, 416640000000.0, 449710000000.0, 479480000000.0] |
| Volatility / beta | ✅ | 0.289 | < 1.5 | Beta = 0.29 (< 1.5) |
| No single-point failure mode | ✅ | 0 | <= 1 concentration/regulatory risk flagged | Concentration/regulatory risks identified: 0 |

_Part C — Risk Architecture: **4/4 passed**_

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
| EBITDA Scale | ✅ | 722740000000.000 | > ₹4.0B | Latest EBITDA passes scale check. |
| FCF Conversion | ✅ | 91.61% | > 60.00% | Average conversion is 91.6%. |
| Leverage Capacity | ✅ | 0.156 | < 3.0x | Leverage is 0.16x. |
| EBITDA Margin | ✅ | 27.07% | > 15.00% | Margin is 27.1%. |

_Part A — LBO Viability: **4/4 passed**_

### Part B — Operational Upside

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin Improvement Room | ❌ | 0.25 / 0.26 | Current < 95% of Peak | Already at/near peak margin. |
| Capex Optimization | ❌ | 0.02 / 0.00 | Optimization profile | Capex/Sales 1.6%, Growth share 0.0%. No obvious capex lever. |
| WC Optimization | ✅ | -6.74% | < -5% or qualitative | Quantitative pass. Qualitative: None. |
| M&A Platform Potential | ✅ | N/A | Qualitative high | Defaulted PASS (qualitative unavailable) |
| Mgmt / Ops Upgrade | ✅ | 20.11% | > 20% cost share | Opex share 20.1%. Qualitative: None. |
| Stavros Workforce Fit | ✅ | N/A | Frontline or mixed | Defaulted PASS (qualitative unavailable, assumed mixed) |

_Part B — Operational Upside: **4/6 passed**_

### Part C — Strategic Fit

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Sector Compatibility | ✅ | Software (System & Application) | In KKR Playbook | Software (System & Application) is in KKR playbook. |
| Willing Seller | ✅ | N/A | Positive catalyst | neutral default — qualitative unavailable; check counted as PASS |
| Regulatory Freedom | ✅ | Software (System & Application) | Not restricted | Clear. |

_Part C — Strategic Fit: **3/3 passed**_

### Part D — Cycle Timing & Returns

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Cycle Timing | ✅ | N/A | Not peak/late | Defaulted PASS (assumed mid_cycle) |
| 7-Year IRR | ❌ | 16.07% | > 18.00% | Entry mult 11.6x -> Exit mult 9.9x. |
| Dividend Recap | ✅ | 9.10% | CV < 35%, FCF > 0 | CV is 9.1%, min FCF 388650000000.0. |
| Why Now Catalyst | ❌ | N/A | Catalyst present | Defaulted FAIL (qualitative unavailable) |

_Part D — Cycle Timing & Returns: **2/4 passed**_

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
| Growing Market | ✅ | 5.80% | > 5% & upward | CAGR is 5.8%. |
| Durable Moat | ✅ | 0.02 / 0.45 | Stdev < 4pp & > 35% | Stdev 1.6pp, Mean 44.9%. |
| Recurring Revenue | ✅ | 0.011 | < 8pp | YoY growth stdev is 1.1pp. |
| No Concentration | ✅ | diversified | Diversified | Assumed diversified (public company baseline). |

_Part A — Good Business Filter: **4/4 passed**_

### Part B — Good Neighborhood (Thematic)

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Theme Alignment | ✅ | Software (System & Application) | Favored Theme | Software (System & Application) in themes. |
| Cycle Position | ✅ | N/A | Not peak/late | Defaulted PASS (assumed mid_cycle) |
| Structural Tailwind | ✅ | N/A | Tailwind/neutral | Defaulted PASS (assumed neutral) |

_Part B — Good Neighborhood (Thematic): **3/3 passed**_

### Part C — Downside Protection

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Conservative Balance Sheet | ✅ | 0.16 / 54.37 | <3.5x, >4x | Leverage 0.2x, Interest Coverage 54.4x. |
| FCF Resilience | ✅ | 388650000000.00 / 0.18 | >0, >6% | Min FCF 388650000000.0, Avg FCF Margin 17.5%. |
| Stress Survival | ✅ | 0.24 / 0.01 | Cash>1x OR Debt/MC<0.5 | Cash ratio 0.24x, Debt/Equity 1.4%. |

_Part C — Downside Protection: **3/3 passed**_

### Part D — Scale Fit & Hold Economics

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Blackstone-Scale Deal | ✅ | 8285057974272.000 | > ₹150B | Market cap is adequate. |
| 20-Year Core Viability | ✅ | N/A | Holdable 20y | Defaulted PASS (assumed holdable) |
| Multi-Product Engagement | ✅ | N/A | Multi-product | neutral default — qualitative unavailable; check counted as PASS |

_Part D — Scale Fit & Hold Economics: **3/3 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ✅ | 6 | >= 4 | 6 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **1/1 passed**_

**Total Blackstone Score**: **14/14**

## 3.4 Apollo Investor Lens
All 16 checks per Apollo's credit & complexity framework (frameworks/apollo.md):

### Part A — Purchase Price & Capital Structure Entry

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Entry Valuation Discount | ✅ | 11.620 | < 17.6x EV/EBITDA or <0.70 P/B | EV/EBITDA is 11.6x. P/B is 7.73x. |
| Capital Structure Complexity | ❌ | 0.16 / 54.37 | Debt stress | Lev: 0.2x, IC: 54.4x. Clean. |
| FCF Serviceability | ✅ | 55.850 | >0 FCF, >1.5x Cov | Avg FCF 433620000000.0, Hyp Cov 55.8x. |
| Deployment Scale | ✅ | 8397887974272.000 | > ₹20B | EV is 8397887974272.0. |

_Part A — Purchase Price & Capital Structure Entry: **3/4 passed**_

### Part B — Chaos, Complexity, Credit Edge

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Chaos/Dislocation Catalyst | ❌ | N/A | Present | Defaulted FAIL (qualitative unavailable) |
| Fulcrum Security | ❌ | (0.15611423195063232, 54.37163814180929, 73.42956637660197) | Hard or Soft Fulcrum | Qual: None. Hard signals: A=False, B=False. |
| ABF/Credit Fit | ❌ | N/A | Compatible | Defaulted FAIL (qualitative unavailable) |
| Complexity Moat | ❌ | 6.19% | >55% or High Qual | Debt/Assets 6.2%. Qual: None. |
| Domain Knowledge | ❌ | Software (System & Application) | In Apollo Playbook | Software (System & Application) not in playbook. |

_Part B — Chaos, Complexity, Credit Edge: **0/5 passed**_

### Part C — Athene Permanent Capital Fit

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| IG Credit Yield | ✅ | (0.27066785009418737, 0.15611423195063232, 54.37163814180929) | Margin>12%, Lev<5x, IC>1.5x | Margin 27.1%, Lev 0.2x, IC 54.4x. |
| Long-Duration Stability | ✅ | 0.003 | < 4pp, > 0 avg | FCF Margin Stdev 0.3pp. |
| Hold-Without-Exit | ✅ | N/A | Viable | neutral default — qualitative unavailable; check counted as PASS |

_Part C — Athene Permanent Capital Fit: **3/3 passed**_

### Part D — Credit Downside Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Through-Cycle Credit Floor | ✅ | 576860000000.00 / 51.61 | Min EBIT>0, Cov>1.5x | Min EBIT 576860000000.0, Avg Cov 51.6x. |
| Tangible Collateral | ✅ | 89.91% | > 40% | Ratio 89.9%. |
| Covenant Control | ✅ | N/A | High/Mixed | Defaulted PASS (assumed mixed) |

_Part D — Credit Downside Quality: **3/3 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ❌ | 1 | >= 4 | 1 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **0/1 passed**_

**Total Apollo Score**: **9/16**

## 3.5 Qualitative Analysis
_Qualitative analysis unavailable: No documents found in Drive folder_

## 4. Margin-of-Safety Check
Current Stock Price: **₹2,289.90**
DCF Intrinsic Value: **₹1,391.88**
Required Margin of Safety: **25.00%** (Graham & Dodd standard — Buffett lens)
Computed Margin of Safety: Trading at 1.6x intrinsic value (target ≤ 0.75x)
### Status: [FAIL] ❌
The stock trades above the safety threshold. Trading at 1.6x intrinsic value is insufficient for investment under the Buffett framework.

## 5. Investment Verdict
**BUFFETT RECOMMENDATION: WAIT**

High-quality business that satisfies most Buffett criteria but lacks margin of safety. Set alert at buy-trigger price: ₹1043.91 (75% of intrinsic value).

**Action Item**: Set alert at buy-trigger price: **₹1,043.91** (75% of intrinsic value).

**MARKS RECOMMENDATION: SKIP**

Insufficient asymmetric edge under Marks framework.

**KKR RECOMMENDATION: WATCH**

Mixed signals across strategic/timing checks; monitor for changes.

**BLACKSTONE RECOMMENDATION: BUY**

High-conviction Blackstone target. Good business in a good neighborhood.

**APOLLO RECOMMENDATION: SKIP**

Failed Part E pre-condition: lacks above-average alpha thesis (Phalippou bar).

## 6. Quintuple-Lens Synthesis
Sidwell preserves all lens verdicts without collapsing them to a single recommendation.
The disagreement between lenses IS the insight.

| Lens | Score | Verdict |
| :--- | :---: | :---: |
| **Buffett** | 13/14 | **WAIT** ⏳ |
| **Marks** | 8/14 | **SKIP** ❌ |
| **KKR** | 14/18 | **WATCH** 👀 |
| **Blackstone** | 14/14 | **BUY** ✅ |
| **Apollo** | 9/16 | **SKIP** ❌ |
