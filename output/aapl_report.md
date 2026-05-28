# Investment Analysis Report: AAPL
**Generated on**: May 29, 2026
**Valuation Engine**: Discounted Cash Flow (DCF)
**Investor Lenses**: Warren Buffett + Howard Marks + KKR + Blackstone + Apollo (v0.6)

## Executive Summary
| Metric | Value | Source / Detail |
| :--- | :--- | :--- |
| **Current Price** | $311.48 | Yahoo Finance |
| **Intrinsic Value (DCF)** | $100.21 | Sidwell DCF Engine |
| **Margin of Safety** | Trading at 3.1x intrinsic value (target ≤ 0.75x) | Current Discount to Intrinsic |
| **Buffett Score** | **10/14** | Buffett Lens (14 checks) |
| **Buffett Verdict** | **WAIT** ⏳ | Buffett Lens Rules |
| **Marks Score** | **8/14** | Marks Lens (14 checks) |
| **Marks Verdict** | **SKIP** ❌ | Marks Lens Rules |
| **KKR Score** | **13/18** | KKR Lens (18 checks) |
| **KKR Verdict** | **WATCH** 👀 | KKR Lens Rules |
| **Blackstone Score** | **13/14** | Blackstone Lens (14 checks) |
| **Blackstone Verdict** | **BUY** ✅ | Blackstone Lens Rules |
| **Apollo Score** | **8/16** | Apollo Lens (16 checks) |
| **Apollo Verdict** | **SKIP** ❌ | Apollo Lens Rules |

### Verdict Summary
> **Buffett**: **WAIT** — High-quality business that satisfies most Buffett criteria but lacks margin of safety. Set alert at buy-trigger price: ₹75.16 (75% of intrinsic value).
> **Marks**: **SKIP** — Insufficient asymmetric edge under Marks framework.
> **KKR**: **WATCH** — Mixed signals across strategic/timing checks; monitor for changes.
> **Blackstone**: **BUY** — High-conviction Blackstone target. Good business in a good neighborhood.
> **Apollo**: **SKIP** — Failed Part E pre-condition: lacks above-average alpha thesis (Phalippou bar).

## 1. Company Snapshot
Historical financial statements over the last 4 years:

| Metric | 2022 | 2023 | 2024 | 2025 |
| :--- | :--- | :--- | :--- | :--- |
| Revenue | $394.33B | $383.29B | $391.04B | $416.16B |
| Gross Margin (%) | 43.31% | 44.13% | 46.21% | 46.91% |
| EBIT | $119.44B | $114.30B | $123.22B | $133.05B |
| Free Cash Flow | $111.44B | $99.58B | $108.81B | $98.77B |
| Total Debt | $120.07B | $111.09B | $106.63B | $98.66B |
| Stockholders Equity | $50.67B | $62.15B | $56.95B | $73.73B |

## 2. DCF Valuation & WACC Sourcing
Every component of the Weighted Average Cost of Capital (WACC) is explicitly sourced and modeled below:

### WACC Components & Assumptions
| Component | Value | Source / Reference |
| :--- | :--- | :--- |
| **Risk-Free Rate ($R_f$)** | 4.50% | FRED Series: `DGS10` (US 10Y Treasury) |
| **Mature Market ERP** | 4.23% | Damodaran NYU Stern (Mature Equity Risk Premium) |
| **Country Risk Premium** | 0.00% | Damodaran NYU Stern (Country default spread adjusted) |
| **Total Equity Risk Premium** | 4.23% | Damodaran mature ERP + country premium = 4.23% |
| **Industry Unlevered Beta** | 1.42 | Damodaran 'Computers/Peripherals' (from Damodaran sheet) |
| **Target Levered Beta ($\beta$)** | 1.45 | Re-levered using actual D/E = 1.45 |
| **Cost of Equity ($K_e$)** | 10.61% | CAPM: $R_f + \beta \times ERP$ = 10.61% |
| **Cost of Debt ($K_d$)** | 5.50% | Calculated and floored to Rf + 1% (raw: 5.00%) |
| **Effective Tax Rate ($t$)** | 17.66% | 4-year historical average from filings |
| **Equity Weight ($W_e$)** | 97.91% | Market Cap / (Market Cap + Total Debt) |
| **Debt Weight ($W_d$)** | 2.09% | Total Debt / (Market Cap + Total Debt) |
| **Computed WACC** | **10.49%** | Weighted cost of capital = **10.49%** |

### 5-Year High-Growth Forecast (Stage 1)
Projections are based on historical averages relative to Revenue. Revenue growth is projected at **5.00%** (historical 4y CAGR capped between 5% and 20%).

| Metric | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | $436.97B | $458.82B | $481.76B | $505.85B | $531.14B |
| EBIT | $135.01B | $141.76B | $148.85B | $156.30B | $164.11B |
| Taxes | $23.84B | $25.03B | $26.28B | $27.60B | $28.98B |
| D&A | $12.63B | $13.26B | $13.92B | $14.62B | $15.35B |
| CapEx | $12.07B | $12.67B | $13.30B | $13.97B | $14.67B |
| NWC Change (CF) | $-7.08B | $-7.44B | $-7.81B | $-8.20B | $-8.61B |
| Free Cash Flow | $104.65B | $109.88B | $115.38B | $121.15B | $127.20B |
| Discount Factor | 1.1049 | 1.2207 | 1.3488 | 1.4902 | 1.6465 |
| PV of Cash Flow | $94.72B | $90.01B | $85.54B | $81.30B | $77.26B |

### 5-Year Fade Forecast (Stage 2) — growth fading from 5.00% to 3.00%

| Metric | Year 6 | Year 7 | Year 8 | Year 9 | Year 10 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | $555.57B | $578.90B | $600.90B | $621.33B | $639.97B |
| EBIT | $171.66B | $178.87B | $185.67B | $191.98B | $197.74B |
| Taxes | $30.31B | $31.58B | $32.78B | $33.90B | $34.91B |
| D&A | $16.05B | $16.73B | $17.36B | $17.96B | $18.49B |
| CapEx | $15.34B | $15.99B | $16.59B | $17.16B | $17.67B |
| NWC Change (CF) | $-9.01B | $-9.39B | $-9.74B | $-10.07B | $-10.38B |
| Free Cash Flow | $133.06B | $138.64B | $143.91B | $148.81B | $153.27B |
| Discount Factor | 1.8192 | 2.0099 | 2.2207 | 2.4536 | 2.7109 |
| PV of Cash Flow | $73.14B | $68.98B | $64.80B | $60.65B | $56.54B |

### Terminal Value
- Final fade year (Year 10) FCF: $153.27B
- Terminal growth (Gordon): 3.00%
- Sector mapping: SECTOR_TERMINAL_GROWTH lookup for (Computers/Peripherals, US)
- Terminal Value: $2,108.54B
- PV of Terminal Value (discounted from Year 10): $777.80B

### Valuation Bridge
- **PV of Explicit FCFs**: $752.94B
- **PV of Terminal Value (g = 3.00%)**: $777.80B
- **Enterprise Value**: $1,530.74B
- **Add: Cash & Equivalents**: $54.70B
- **Less: Total Debt**: $98.66B
- **Equity Value**: $1,486.78B
- **Shares Outstanding**: 14,837,000,000
- **Intrinsic Value per Share**: **$100.21**

## 3. Buffett Investor Lens
All 14 checks per Warren Buffett's framework across 4 Parts (frameworks/buffett.md):

### Part A — Business Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Durable competitive advantage (moat) | ✅ | 1.70% | < 3.0% | stdev = 1.70% < 3% |
| High return on invested capital | ✅ | 90.20% | > 15.0% | 4y avg = 90.20% > 15% |
| Strong free-cash-flow generation | ❌ | 0.26 / -0.11 | Margin > 10% & Growth > 0% | avg margin = 26.45%, FCF growth = -11.37% |
| Earnings predictability | ❌ | 0.05 / 0.05 | 5% < CAGR < 30% & YoY Growth StDev < 10.0% | Revenue CAGR = 5.00%, YoY Growth StDev = 4.61% |

_Part A — Business Quality: **2/4 passed**_

### Part B — Financial Health

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Conservative balance sheet | ✅ | 0.68 / 26.97 | Debt/EBITDA < 3x & Coverage > 5x | Debt/EBITDA = 0.68x, Int. Coverage = 26.97x |
| ROE without excess leverage | ❌ | 1.67 / 0.21 | ROE > 15% & Equity/Assets > 40% | 4y avg ROE = 167.39%, Equity/Assets = 20.52% |
| Liquidity cushion (Gibraltar test) | ✅ | 54697000000 / 98657000000 | Cash / Debt > 0.5x OR debt-free | Cash / Debt = 0.55x (> 0.5) |

_Part B — Financial Health: **2/3 passed**_

### Part C — Management & Capital Allocation

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Anti-dilution discipline | ✅ | [4 values] | <= 2% growth over 4y | Share count growth (4y): -8.10% (threshold: <= +2%) |
| Capital allocation track record | ✅ | 0.15793591806022234 / True | ROIC not declining > 3pp AND capital returned | ROIC trend (latter-2y vs earlier-2y): +15.79pp; capital returned to shareholders: yes |
| Owner orientation | ✅ | 0.0 / None | Insiders > 5% OR LLM = owner_oriented | Insider ownership: 0.00% (FAIL at >5%). LLM owner-orientation: unavailable |
| Management coherence | ✅ | True | LLM coherence = coherent | Soft check: SKIPPED (qualitative unavailable); defaulted PASS |

_Part C — Management & Capital Allocation: **4/4 passed**_

### Part D — Margin of Safety & Holdability

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin of safety | ❌ | Trading at 3.1x intrinsic | > 25.0% | Trading at 3.1x intrinsic value (target ≤ 0.75x) (Price: 311.48, Intrinsic: 100.21) |
| Understandable business (hard blacklist) | ✅ | True | Ticker not BTC/ETH/COIN | Hard check: PASS (ticker not in avoided-sector blacklist) |
| Holdability (20-year test) | ✅ | N/A | LLM verdict = holdable_20y | Holdability check skipped (qualitative unavailable); defaulted PASS |

_Part D — Margin of Safety & Holdability: **2/3 passed**_

**Total Buffett Score**: **10/14**

## 3.1 Marks Investor Lens
All 14 checks per Howard Marks's risk-first framework (frameworks/marks.md):

### Part A — Margin of Safety & Asymmetric Payoff

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Deep margin of safety | ❌ | Trading at 3.1x intrinsic | > 40% | MoS = -210.83% (< 40% threshold) — Price 311.48 vs Intrinsic 100.21 |
| Asymmetric upside-to-downside payoff | ❌ | 0.000 | > 3.0x | Asymmetry ratio = 0.00 (< 3.0 threshold) |
| Downside protection (tangible book) | ❌ | 1.60% | > 30% | Equity/MCap = 1.60% (<= 30%) |
| Multiple expansion not exhausted | ❌ | 37.664 | < 25x (v0.3 placeholder; sector comp in v0.4) | Trailing P/E = 37.7x (>= 25x) |

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
| Capital structure resilience | ✅ | 0.68 / 26.97 | Debt/EBITDA < 4x AND Coverage > 4x | Debt/EBITDA = 0.68x, Coverage = 26.97x |
| FCF stability through downturn | ✅ | 98767000000 | All 4 years positive FCF | 4y FCF: [111443000000, 99584000000, 108807000000, 98767000000] |
| Volatility / beta | ✅ | 1.060 | < 1.5 | Beta = 1.06 (< 1.5) |
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
| EBITDA Scale | ✅ | 144748000000 | > $200M | Latest EBITDA passes scale check. |
| FCF Conversion | ✅ | 103.78% | > 60.00% | Average conversion is 103.8%. |
| Leverage Capacity | ✅ | 0.682 | < 3.0x | Leverage is 0.68x. |
| EBITDA Margin | ✅ | 34.78% | > 15.00% | Margin is 34.8%. |

_Part A — LBO Viability: **4/4 passed**_

### Part B — Operational Upside

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Margin Improvement Room | ❌ | 0.32 / 0.32 | Current < 95% of Peak | Already at/near peak margin. |
| Capex Optimization | ❌ | 0.03 / 0.08 | Optimization profile | Capex/Sales 3.1%, Growth share 8.0%. No obvious capex lever. |
| WC Optimization | ✅ | -6.75% | < -5% or qualitative | Quantitative pass. Qualitative: None. |
| M&A Platform Potential | ✅ | N/A | Qualitative high | Defaulted PASS (qualitative unavailable) |
| Mgmt / Ops Upgrade | ❌ | 14.93% | > 20% cost share | Opex share 14.9%. Qualitative: None. |
| Stavros Workforce Fit | ✅ | N/A | Frontline or mixed | Defaulted PASS (qualitative unavailable, assumed mixed) |

_Part B — Operational Upside: **3/6 passed**_

### Part C — Strategic Fit

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Sector Compatibility | ✅ | Computers/Peripherals | In KKR Playbook | Computers/Peripherals is in KKR playbook. |
| Willing Seller | ✅ | N/A | Positive catalyst | neutral default — qualitative unavailable; check counted as PASS |
| Regulatory Freedom | ✅ | Computers/Peripherals | Not restricted | Clear. |

_Part C — Strategic Fit: **3/3 passed**_

### Part D — Cycle Timing & Returns

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Cycle Timing | ✅ | N/A | Not peak/late | Defaulted PASS (assumed mid_cycle) |
| 7-Year IRR | ❌ | 16.08% | > 18.00% | Entry mult 32.6x -> Exit mult 27.7x. |
| Dividend Recap | ✅ | 6.14% | CV < 35%, FCF > 0 | CV is 6.1%, min FCF 98767000000.0. |
| Why Now Catalyst | ❌ | N/A | Catalyst present | Defaulted FAIL (qualitative unavailable) |

_Part D — Cycle Timing & Returns: **2/4 passed**_

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
| Growing Market | ❌ | 1.81% | > 5% & upward | CAGR is 1.8%. |
| Durable Moat | ✅ | 0.02 / 0.45 | Stdev < 4pp & > 35% | Stdev 1.7pp, Mean 45.1%. |
| Recurring Revenue | ✅ | 0.046 | < 8pp | YoY growth stdev is 4.6pp. |
| No Concentration | ✅ | diversified | Diversified | Assumed diversified (public company baseline). |

_Part A — Good Business Filter: **3/4 passed**_

### Part B — Good Neighborhood (Thematic)

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Theme Alignment | ✅ | Computers/Peripherals | Favored Theme | Computers/Peripherals in themes. |
| Cycle Position | ✅ | N/A | Not peak/late | Defaulted PASS (assumed mid_cycle) |
| Structural Tailwind | ✅ | N/A | Tailwind/neutral | Defaulted PASS (assumed neutral) |

_Part B — Good Neighborhood (Thematic): **3/3 passed**_

### Part C — Downside Protection

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Conservative Balance Sheet | ✅ | 0.68 / 26.97 | <3.5x, >4x | Leverage 0.7x, Interest Coverage 27.0x. |
| FCF Resilience | ✅ | 98767000000 / 0.26413340661240564 | >0, >6% | Min FCF 98767000000.0, Avg FCF Margin 26.4%. |
| Stress Survival | ✅ | 1.31 / 0.02 | Cash>1x OR Debt/MC<0.5 | Cash ratio 1.31x, Debt/Equity 2.1%. |

_Part C — Downside Protection: **3/3 passed**_

### Part D — Scale Fit & Hold Economics

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Blackstone-Scale Deal | ✅ | 4621428760000.000 | > $5B | Market cap is adequate. |
| 20-Year Core Viability | ✅ | N/A | Holdable 20y | Defaulted PASS (assumed holdable) |
| Multi-Product Engagement | ✅ | N/A | Multi-product | neutral default — qualitative unavailable; check counted as PASS |

_Part D — Scale Fit & Hold Economics: **3/3 passed**_

### Part E — Defensibility vs Phalippou Bar

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Above-Average Alpha | ✅ | 6 | >= 4 | 6 of 6 levers passed. |

_Part E — Defensibility vs Phalippou Bar: **1/1 passed**_

**Total Blackstone Score**: **13/14**

## 3.4 Apollo Investor Lens
All 16 checks per Apollo's credit & complexity framework (frameworks/apollo.md):

### Part A — Purchase Price & Capital Structure Entry

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Entry Valuation Discount | ❌ | 32.609 | < 12.0x EV/EBITDA or <0.70 P/B | EV/EBITDA is 32.6x. P/B is 61.98x. |
| Capital Structure Complexity | ❌ | 0.68 / 26.97 | Debt stress | Lev: 0.7x, IC: 27.0x. Clean. |
| FCF Serviceability | ✅ | 19.395 | >0 FCF, >1.5x Cov | Avg FCF 104650250000.0, Hyp Cov 19.4x. |
| Deployment Scale | ✅ | 4720085760000.000 | > $500M | EV is 4720085760000.0. |

_Part A — Purchase Price & Capital Structure Entry: **2/4 passed**_

### Part B — Chaos, Complexity, Credit Edge

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Chaos/Dislocation Catalyst | ❌ | N/A | Present | Defaulted FAIL (qualitative unavailable) |
| Fulcrum Security | ❌ | (0.6815776383784232, 26.97223714485541, 46.843394386612204) | Hard or Soft Fulcrum | Qual: None. Hard signals: A=False, B=False. |
| ABF/Credit Fit | ❌ | N/A | Compatible | Defaulted FAIL (qualitative unavailable) |
| Complexity Moat | ❌ | 27.46% | >55% or High Qual | Debt/Assets 27.5%. Qual: None. |
| Domain Knowledge | ❌ | Computers/Peripherals | In Apollo Playbook | Computers/Peripherals not in playbook. |

_Part B — Chaos, Complexity, Credit Edge: **0/5 passed**_

### Part C — Athene Permanent Capital Fit

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| IG Credit Yield | ✅ | (0.3478173110887373, 0.6815776383784232, 26.97223714485541) | Margin>12%, Lev<5x, IC>1.5x | Margin 34.8%, Lev 0.7x, IC 27.0x. |
| Long-Duration Stability | ✅ | 0.021 | < 4pp, > 0 avg | FCF Margin Stdev 2.1pp. |
| Hold-Without-Exit | ✅ | N/A | Viable | neutral default — qualitative unavailable; check counted as PASS |

_Part C — Athene Permanent Capital Fit: **3/3 passed**_

### Part D — Credit Downside Quality

| Check | Status | Value | Threshold | Detail |
| :--- | :---: | :--- | :--- | :--- |
| Through-Cycle Credit Floor | ✅ | 114301000000 / 17.738369154893068 | Min EBIT>0, Cov>1.5x | Min EBIT 114301000000.0, Avg Cov 17.7x. |
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
Current Stock Price: **$311.48**
DCF Intrinsic Value: **$100.21**
Required Margin of Safety: **25.00%** (Graham & Dodd standard — Buffett lens)
Computed Margin of Safety: Trading at 3.1x intrinsic value (target ≤ 0.75x)
### Status: [FAIL] ❌
The stock trades above the safety threshold. Trading at 3.1x intrinsic value is insufficient for investment under the Buffett framework.

## 5. Investment Verdict
**BUFFETT RECOMMENDATION: WAIT**

High-quality business that satisfies most Buffett criteria but lacks margin of safety. Set alert at buy-trigger price: ₹75.16 (75% of intrinsic value).

**Action Item**: Set alert at buy-trigger price: **$75.16** (75% of intrinsic value).

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
| **Buffett** | 10/14 | **WAIT** ⏳ |
| **Marks** | 8/14 | **SKIP** ❌ |
| **KKR** | 13/18 | **WATCH** 👀 |
| **Blackstone** | 13/14 | **BUY** ✅ |
| **Apollo** | 8/16 | **SKIP** ❌ |
