# Investment Analysis Report: PLTR
**Generated on**: May 29, 2026
**Valuation Engine**: Discounted Cash Flow (DCF)
**Investor Lenses**: Warren Buffett + Howard Marks + KKR + Blackstone + Apollo (v0.6)

> [!WARNING]
> **DCF COVERAGE GAP WARNING**: The computed DCF intrinsic value
> deviates significantly from the current market price (intrinsic
> at 3% of price).
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
| **Current Price** | $143.34 | Yahoo Finance |
| **Intrinsic Value (DCF)** | $4.14 | Sidwell DCF Engine |
| **Margin of Safety** | Trading at 34.6x intrinsic value (target ≤ 0.75x) | Current Discount to Intrinsic |
| **Buffett Score** | **9/14** | Buffett Lens (14 checks) |
| **Buffett Verdict** | **SKIP** ❌ | Buffett Lens Rules |
| **Marks Score** | **7/14** | Marks Lens (14 checks) |
| **Marks Verdict** | **SKIP** ❌ | Marks Lens Rules |
| **KKR Score** | **13/18** | KKR Lens (18 checks) |
| **KKR Verdict** | **WATCH** 👀 | KKR Lens Rules |
| **Blackstone Score** | **13/14** | Blackstone Lens (14 checks) |
| **Blackstone Verdict** | **BUY** ✅ | Blackstone Lens Rules |
| **Apollo Score** | **6/16** | Apollo Lens (16 checks) |
| **Apollo Verdict** | **SKIP** ❌ | Apollo Lens Rules |

### Verdict Summary
> **Buffett**: **SKIP** — Does not meet enough Buffett criteria across business quality, management, and price.
> **Marks**: **SKIP** — Insufficient asymmetric edge under Marks framework.
> **KKR**: **WATCH** — Mixed signals across strategic/timing checks; monitor for changes.
> **Blackstone**: **BUY** — High-conviction Blackstone target. Good business in a good neighborhood.
> **Apollo**: **SKIP** — Failed Part E pre-condition: lacks above-average alpha thesis (Phalippou bar).

## 1. Company Snapshot
Historical financial statements over the last 4 years:

| Metric | 2022 | 2023 | 2024 | 2025 |
| :--- | :--- | :--- | :--- | :--- |
| Revenue | $1.91B | $2.23B | $2.87B | $4.48B |
| Gross Margin (%) | 78.56% | 80.62% | 80.25% | 82.37% |
| EBIT | $-161.20M | $119.97M | $310.40M | $1.41B |
| Free Cash Flow | $183.71M | $697.07M | $1.14B | $2.10B |
| Total Debt | $249.40M | $229.39M | $239.22M | $229.34M |
| Stockholders Equity | $2.64B | $3.56B | $5.09B | $7.49B |

## 2. DCF Valuation & WACC Sourcing
Every component of the Weighted Average Cost of Capital (WACC) is explicitly sourced and modeled below:

### WACC Components & Assumptions
| Component | Value | Source / Reference |
| :--- | :--- | :--- |
| **Risk-Free Rate ($R_f$)** | 4.50% | FRED Series: `DGS10` (US 10Y Treasury) |
| **Mature Market ERP** | 4.23% | Damodaran NYU Stern (Mature Equity Risk Premium) |
| **Country Risk Premium** | 0.00% | Damodaran NYU Stern (Country default spread adjusted) |
| **Total Equity Risk Premium** | 4.23% | Damodaran mature ERP + country premium = 4.23% |
| **Industry Unlevered Beta** | 1.30 | Damodaran 'Software (System & Application)' (hardcoded fallback (Damodaran lookup failed)) |
| **Target Levered Beta ($\beta$)** | 1.30 | Re-levered using actual D/E = 1.30 |
| **Cost of Equity ($K_e$)** | 9.99% | CAPM: $R_f + \beta \times ERP$ = 9.99% |
| **Cost of Debt ($K_d$)** | 6.50% | Default: Rf + 2% (debt < 5% of total assets) |
| **Effective Tax Rate ($t$)** | 4.68% | 4-year historical average from filings |
| **Equity Weight ($W_e$)** | 99.94% | Market Cap / (Market Cap + Total Debt) |
| **Debt Weight ($W_d$)** | 0.06% | Total Debt / (Market Cap + Total Debt) |
| **Computed WACC** | **9.98%** | Weighted cost of capital = **9.98%** |

### 5-Year High-Growth Forecast (Stage 1)
Projections are based on historical averages relative to Revenue. Revenue growth is projected at **20.00%** (historical 4y CAGR capped between 5% and 20%).

| Metric | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | $5.37B | $6.44B | $7.73B | $9.28B | $11.14B |
| EBIT | $528.47M | $634.17M | $761.00M | $913.20M | $1.10B |
| Taxes | $24.72M | $29.66M | $35.59M | $42.71M | $51.26M |
| D&A | $58.64M | $70.36M | $84.44M | $101.32M | $121.59M |
| CapEx | $53.40M | $64.08M | $76.90M | $92.28M | $110.74M |
| NWC Change (CF) | $-396.45M | $-475.74M | $-570.89M | $-685.06M | $-822.08M |
| Free Cash Flow | $112.54M | $135.05M | $162.06M | $194.47M | $233.36M |
| Discount Factor | 1.0998 | 1.2097 | 1.3304 | 1.4633 | 1.6094 |
| PV of Cash Flow | $102.32M | $111.64M | $121.81M | $132.90M | $145.00M |

### 5-Year Fade Forecast (Stage 2) — growth fading from 20.00% to 3.50%

| Metric | Year 6 | Year 7 | Year 8 | Year 9 | Year 10 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | $13.00B | $14.74B | $16.23B | $17.33B | $17.94B |
| EBIT | $1.28B | $1.45B | $1.60B | $1.71B | $1.76B |
| Taxes | $59.82M | $67.83M | $74.68M | $79.76M | $82.55M |
| D&A | $141.89M | $160.91M | $177.16M | $189.21M | $195.83M |
| CapEx | $129.23M | $146.54M | $161.35M | $172.32M | $178.35M |
| NWC Change (CF) | $-959.36M | $-1.09B | $-1.20B | $-1.28B | $-1.32B |
| Free Cash Flow | $272.34M | $308.83M | $340.02M | $363.14M | $375.85M |
| Discount Factor | 1.7701 | 1.9468 | 2.1412 | 2.3550 | 2.5901 |
| PV of Cash Flow | $153.85M | $158.63M | $158.80M | $154.20M | $145.11M |

### Terminal Value
- Final fade year (Year 10) FCF: $375.85M
- Terminal growth (Gordon): 3.50%
- Sector mapping: SECTOR_TERMINAL_GROWTH lookup for (Software (System & Application), US)
- Terminal Value: $6.00B
- PV of Terminal Value (discounted from Year 10): $2.32B

### Valuation Bridge
- **PV of Explicit FCFs**: $1.38B
- **PV of Terminal Value (g = 3.50%)**: $2.32B
- **Enterprise Value**: $3.70B
- **Add: Cash & Equivalents**: $7.18B
- **Less: Total Debt**: $229.34M
- **Equity Value**: $10.65B
- **Shares Outstanding**: 2,569,600,000
- **Intrinsic Value per Share**: **$4.14**

## 3. Buffett Investor Lens
All 14 checks per Warren Buffett's framework across 4 Parts (frameworks/buffett.md):

### Part A — Business Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Durable competitive advantage (moat) | ✅ | 1.56% | < 3.0% | stdev = 1.56% < 3% |
| High return on invested capital | ✅ | 143.47% | > 15.0% | 4y avg = 143.47% > 15% |
| Strong free-cash-flow generation | ✅ | 0.32 / 10.43 | Margin > 10% & Growth > 0% | avg margin = 31.93%, FCF growth = 1043.43% |
| Earnings predictability | ❌ | 0.20 / 0.20 | 5% < CAGR < 30% & YoY Growth StDev < 10.0% | Revenue CAGR = 20.00%, YoY Growth StDev = 20.21% |

_Part A — Business Quality: **3/4 passed**_

### Part B — Financial Health

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Conservative balance sheet | ✅ | 0.16 / 123.31 | Debt/EBITDA < 3x & Coverage > 5x | Debt/EBITDA = 0.16x, Int. Coverage = 123.31x |
| ROE without excess leverage | ❌ | 0.06 / 0.84 | ROE > 15% & Equity/Assets > 40% | 4y avg ROE = 5.63%, Equity/Assets = 84.13% |
| Liquidity cushion (Gibraltar test) | ✅ | 7177040000 / 229338000 | Cash / Debt > 0.5x OR debt-free | Cash / Debt = 31.29x (> 0.5) |

_Part B — Financial Health: **2/3 passed**_

### Part C — Management & Capital Allocation

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Anti-dilution discipline | ❌ | [4 values] | <= 2% growth over 4y | Share count growth (4y): +24.30% (threshold: <= +2%) |
| Capital allocation track record | ❌ | 2.480270737242893 / False | ROIC not declining > 3pp AND capital returned | ROIC trend (latter-2y vs earlier-2y): +248.03pp; capital returned to shareholders: no |
| Owner orientation | ✅ | 0.0 / None | Insiders > 5% OR LLM = owner_oriented | Insider ownership: 0.00% (FAIL at >5%). LLM owner-orientation: unavailable |
| Management coherence | ✅ | True | LLM coherence = coherent | Soft check: SKIPPED (qualitative unavailable); defaulted PASS |

_Part C — Management & Capital Allocation: **2/4 passed**_

### Part D — Margin of Safety & Holdability

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin of safety | ❌ | Trading at 34.6x intrinsic | > 25.0% | Trading at 34.6x intrinsic value (target ≤ 0.75x) (Price: 143.34, Intrinsic: 4.14) |
| Understandable business (hard blacklist) | ✅ | True | Ticker not BTC/ETH/COIN | Hard check: PASS (ticker not in avoided-sector blacklist) |
| Holdability (20-year test) | ✅ | N/A | LLM verdict = holdable_20y | Holdability check skipped (qualitative unavailable); defaulted PASS |

_Part D — Margin of Safety & Holdability: **2/3 passed**_

**Total Buffett Score**: **9/14**

## 3.1 Marks Investor Lens
All 14 checks per Howard Marks's risk-first framework (frameworks/marks.md):

### Part A — Margin of Safety & Asymmetric Payoff

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Deep margin of safety | ❌ | Trading at 34.6x intrinsic | > 40% | MoS = -3359.12% (< 40% threshold) — Price 143.34 vs Intrinsic 4.14 |
| Asymmetric upside-to-downside payoff | ❌ | 0.000 | > 3.0x | Asymmetry ratio = 0.00 (< 3.0 threshold) |
| Downside protection (tangible book) | ❌ | 2.03% | > 30% | Equity/MCap = 2.03% (<= 30%) |
| Multiple expansion not exhausted | ❌ | 161.056 | < 25x (v0.3 placeholder; sector comp in v0.4) | Trailing P/E = 161.1x (>= 25x) |

_Part A — Margin of Safety & Asymmetric Payoff: **0/4 passed**_

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
| Capital structure resilience | ✅ | 0.16 / 123.31 | Debt/EBITDA < 4x AND Coverage > 4x | Debt/EBITDA = 0.16x, Coverage = 123.31x |
| FCF stability through downturn | ✅ | 183710000 | All 4 years positive FCF | 4y FCF: [183710000, 697069000, 1141230000, 2100590000] |
| Volatility / beta | ❌ | 1.520 | < 1.5 | Beta = 1.52 (>= 1.5) |
| No single-point failure mode | ✅ | 0 | <= 1 concentration/regulatory risk flagged | Concentration/regulatory risks identified: 0 |

_Part C — Risk Architecture: **3/4 passed**_

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
| EBITDA Scale | ✅ | 1440165000 | > $200M | Latest EBITDA passes scale check. |
| FCF Conversion | ✅ | 245.30% | > 60.00% | Average conversion is 245.3%. |
| Leverage Capacity | ✅ | 0.159 | < 3.0x | Leverage is 0.16x. |
| EBITDA Margin | ✅ | 32.18% | > 15.00% | Margin is 32.2%. |

_Part A — LBO Viability: **4/4 passed**_

### Part B — Operational Upside

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin Improvement Room | ❌ | 0.32 / 0.32 | Current < 95% of Peak | Already at/near peak margin. |
| Capex Optimization | ❌ | 0.01 / 0.23 | Optimization profile | Capex/Sales 0.8%, Growth share 22.8%. No obvious capex lever. |
| WC Optimization | ✅ | -31.01% | < -5% or qualitative | Quantitative pass. Qualitative: None. |
| M&A Platform Potential | ✅ | N/A | Qualitative high | Defaulted PASS (qualitative unavailable) |
| Mgmt / Ops Upgrade | ✅ | 50.77% | > 20% cost share | Opex share 50.8%. Qualitative: None. |
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
| 7-Year IRR | ❌ | 16.04% | > 18.00% | Entry mult 255.9x -> Exit mult 217.5x. |
| Dividend Recap | ❌ | 78.94% | CV < 35%, FCF > 0 | CV is 78.9%, min FCF 183710000.0. |
| Why Now Catalyst | ❌ | N/A | Catalyst present | Defaulted FAIL (qualitative unavailable) |

_Part D — Cycle Timing & Returns: **1/4 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ✅ | 4 | >= 4 | 4 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **1/1 passed**_

**Total KKR Score**: **13/18**

## 3.3 Blackstone Investor Lens
All 14 checks per Blackstone's thematic framework (frameworks/blackstone.md):

### Part A — Good Business Filter

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Growing Market | ✅ | 32.92% | > 5% & upward | CAGR is 32.9%. |
| Durable Moat | ✅ | 0.02 / 0.80 | Stdev < 4pp & > 35% | Stdev 1.6pp, Mean 80.5%. |
| Recurring Revenue | ❌ | 0.202 | < 8pp | YoY growth stdev is 20.2pp. |
| No Concentration | ✅ | diversified | Diversified | Assumed diversified (public company baseline). |

_Part A — Good Business Filter: **3/4 passed**_

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
| Conservative Balance Sheet | ✅ | 0.16 / 123.31 | <3.5x, >4x | Leverage 0.2x, Interest Coverage 123.3x. |
| FCF Resilience | ✅ | 183710000 / 0.35936684960738646 | >0, >6% | Min FCF 183710000.0, Avg FCF Margin 35.9%. |
| Stress Survival | ✅ | 16.04 / 0.00 | Cash>1x OR Debt/MC<0.5 | Cash ratio 16.04x, Debt/Equity 0.1%. |

_Part C — Downside Protection: **3/3 passed**_

### Part D — Scale Fit & Hold Economics

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Blackstone-Scale Deal | ✅ | 368326464000.000 | > $5B | Market cap is adequate. |
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
| Entry Valuation Discount | ❌ | 255.912 | < 17.6x EV/EBITDA or <0.70 P/B | EV/EBITDA is 255.9x. P/B is 49.27x. |
| Capital Structure Complexity | ❌ | 0.16 / 123.31 | Debt stress | Lev: 0.2x, IC: 123.3x. Clean. |
| FCF Serviceability | ✅ | 27.981 | >0 FCF, >1.5x Cov | Avg FCF 1030649750.0, Hyp Cov 28.0x. |
| Deployment Scale | ✅ | 368555802000.000 | > $500M | EV is 368555802000.0. |

_Part A — Purchase Price & Capital Structure Entry: **2/4 passed**_

### Part B — Chaos, Complexity, Credit Edge

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Chaos/Dislocation Catalyst | ❌ | N/A | Present | Defaulted FAIL (qualitative unavailable) |
| Fulcrum Security | ❌ | (0.159244253262647, 123.31318839442221, 1606.0420165868718) | Hard or Soft Fulcrum | Qual: None. Hard signals: A=False, B=False. |
| ABF/Credit Fit | ❌ | N/A | Compatible | Defaulted FAIL (qualitative unavailable) |
| Complexity Moat | ❌ | 2.58% | >55% or High Qual | Debt/Assets 2.6%. Qual: None. |
| Domain Knowledge | ❌ | Software (System & Application) | In Apollo Playbook | Software (System & Application) not in playbook. |

_Part B — Chaos, Complexity, Credit Edge: **0/5 passed**_

### Part C — Athene Permanent Capital Fit

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| IG Credit Yield | ✅ | (0.3217922220111944, 0.159244253262647, 123.31318839442221) | Margin>12%, Lev<5x, IC>1.5x | Margin 32.2%, Lev 0.2x, IC 123.3x. |
| Long-Duration Stability | ❌ | 0.162 | < 4pp, > 0 avg | FCF Margin Stdev 16.2pp. |
| Hold-Without-Exit | ✅ | N/A | Viable | neutral default — qualitative unavailable; check counted as PASS |

_Part C — Athene Permanent Capital Fit: **2/3 passed**_

### Part D — Credit Downside Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Through-Cycle Credit Floor | ❌ | -161201000 / 26.21190432586712 | Min EBIT>0, Cov>1.5x | Min EBIT -161201000.0, Avg Cov 26.2x. |
| Tangible Collateral | ✅ | 100.00% | > 40% | Ratio 100.0%. |
| Covenant Control | ✅ | N/A | High/Mixed | Defaulted PASS (assumed mixed) |

_Part D — Credit Downside Quality: **2/3 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ❌ | 1 | >= 4 | 1 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **0/1 passed**_

**Total Apollo Score**: **6/16**

## 3.5 Qualitative Analysis
_Qualitative analysis unavailable: No documents found in Drive folder_

## 4. Margin-of-Safety Check
Current Stock Price: **$143.34**
DCF Intrinsic Value: **$4.14**
Required Margin of Safety: **25.00%** (Graham & Dodd standard — Buffett lens)
Computed Margin of Safety: Trading at 34.6x intrinsic value (target ≤ 0.75x)
### Status: [FAIL] ❌
The stock trades above the safety threshold. Trading at 34.6x intrinsic value is insufficient for investment under the Buffett framework.

## 5. Investment Verdict
**BUFFETT RECOMMENDATION: SKIP**

Does not meet enough Buffett criteria across business quality, management, and price.

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
| **Buffett** | 9/14 | **SKIP** ❌ |
| **Marks** | 7/14 | **SKIP** ❌ |
| **KKR** | 13/18 | **WATCH** 👀 |
| **Blackstone** | 13/14 | **BUY** ✅ |
| **Apollo** | 6/16 | **SKIP** ❌ |
