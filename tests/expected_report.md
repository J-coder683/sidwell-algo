# Investment Analysis Report: FICTITIOUS.NS
**Generated on**: January 01, 2026
**Valuation Engine**: Discounted Cash Flow (DCF)
**Investor Lens**: Warren Buffett (v0.1)

## Executive Summary
| Metric | Value | Source / Detail |
| :--- | :--- | :--- |
| **Current Price** | ₹50.00 | Yahoo Finance |
| **Intrinsic Value (DCF)** | ₹27.02 | Sidwell DCF Engine |
| **Margin of Safety** | Trading at 1.9x intrinsic value (target ≤ 0.75x) | Current Discount to Intrinsic |
| **Buffett Score** | **7/8** | Spec criteria checks passed |
| **Final Verdict** | **WAIT** ⏳ | Buffett Lens Rules |

### Verdict Summary
> **WAIT** — High-quality business that satisfies key quality criteria, but currently lacks a sufficient margin of safety (current price 50.00 is higher than the target buy price of 20.27). Wait for a pullback.

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
| **Industry Unlevered Beta** | 0.90 | Damodaran 'Chemical (Specialty)' (default fallback) |
| **Target Levered Beta ($\beta$)** | 0.93 | Re-levered using actual D/E = 0.93 |
| **Cost of Equity ($K_e$)** | 12.49% | CAPM: $R_f + \beta \times ERP$ = 12.49% |
| **Cost of Debt ($K_d$)** | 10.00% | Calculated: int_expense/debt = 10.00% |
| **Effective Tax Rate ($t$)** | 25.00% | 4-year historical average from filings |
| **Equity Weight ($W_e$)** | 96.15% | Market Cap / (Market Cap + Total Debt) |
| **Debt Weight ($W_d$)** | 3.85% | Total Debt / (Market Cap + Total Debt) |
| **Computed WACC** | **12.30%** | Weighted cost of capital = **12.30%** |

### 5-Year Explicit Forecast Projections
Projections are based on historical averages relative to Revenue. Revenue growth is projected at **10.00%** (historical 4y CAGR capped between 5% and 20%).

| Metric | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 | Terminal Value |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Revenue | ₹146.41 | ₹161.05 | ₹177.16 | ₹194.87 | ₹214.36 | - |
| EBIT | ₹29.28 | ₹32.21 | ₹35.43 | ₹38.97 | ₹42.87 | - |
| Taxes | ₹7.32 | ₹8.05 | ₹8.86 | ₹9.74 | ₹10.72 | - |
| D&A | ₹4.39 | ₹4.83 | ₹5.31 | ₹5.85 | ₹6.43 | - |
| CapEx | ₹7.32 | ₹8.05 | ₹8.86 | ₹9.74 | ₹10.72 | - |
| NWC Change (CF) | ₹0.00 | ₹0.00 | ₹0.00 | ₹0.00 | ₹0.00 | - |
| Free Cash Flow | ₹19.03 | ₹20.94 | ₹23.03 | ₹25.33 | ₹27.87 | ₹349.29 |
| Discount Factor | 1.1230 | 1.2611 | 1.4161 | 1.5903 | 1.7858 | 1.7858 |
| PV of Cash Flow | ₹16.95 | ₹16.60 | ₹16.26 | ₹15.93 | ₹15.60 | ₹195.59 |

### Valuation Bridge
- **PV of Explicit FCFs**: ₹81.35
- **PV of Terminal Value (g = 4.00%)**: ₹195.59
- **Enterprise Value**: ₹276.94
- **Add: Cash & Equivalents**: ₹13.31
- **Less: Total Debt**: ₹20.00
- **Equity Value**: ₹270.25
- **Shares Outstanding**: 10
- **Intrinsic Value per Share**: **₹27.02**

## 3. Buffett Investor Lens
All 8 checks per Warren Buffett's framework (distilled from annual letters):

| Check | Status | Value | Target Threshold | Description |
| :--- | :---: | :--- | :--- | :--- |
| Durable competitive advantage (moat) | ✅ | 0.00% | < 3.0% | stdev = 0.00% < 3% |
| High return on invested capital | ✅ | 22.26% | > 15.0% | 4y avg = 22.26% > 15% |
| Strong free-cash-flow generation | ✅ | 11.69% / 37.42% | Margin > 10% & Growth > 0% | avg margin = 11.69%, FCF growth = 37.42% |
| Conservative balance sheet | ✅ | 0.65 / 13.31 | Debt/EBITDA < 3x & Coverage > 5x | Debt/EBITDA = 0.65x, Int. Coverage = 13.31x |
| ROE without excess leverage | ✅ | 22.82% / 60.00% | ROE > 15% & Equity/Assets > 40% | 4y avg ROE = 22.82%, Equity/Assets = 60.00% |
| Earnings predictability | ✅ | 10.00% / 0.00% | 5% < CAGR < 30% & YoY Growth StDev < 10.0% | Revenue CAGR = 10.00%, YoY Growth StDev = 0.00% |
| Margin of safety | ❌ | Trading at 1.9x intrinsic value (target ≤ 0.75x) | > 25.0% | Trading at 1.9x intrinsic value (target ≤ 0.75x) (Price: 50.00, Intrinsic: 27.02) |
| Understandable business | ✅ | Hard: PASS / Soft: PASS | Both signals must pass | Hard check: PASS (ticker not in avoided-sector blacklist). Soft check: PASS (LLM coherence verdict: coherent). Numeric claims tie out across documents and strategy is consistent. |

**Total Buffett Score**: **7/8**

## 3.5 Qualitative Analysis
Based on 1 document(s): fixture_concall.pdf. Model: `gemini-1.5-flash`.

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

## 4. Margin-of-Safety Check
Current Stock Price: **₹50.00**
DCF Intrinsic Value: **₹27.02**
Required Margin of Safety: **25.00%** ( Graham & Dodd standard)
Computed Margin of Safety: Trading at 1.9x intrinsic value (target ≤ 0.75x)
### Status: [FAIL] ❌
The stock trades above the safety threshold. Trading at 1.9x intrinsic value is insufficient for investment under the Buffett framework.

## 5. Investment Verdict
**RECOMMENDATION: WAIT**

High-quality business that satisfies key quality criteria, but currently lacks a sufficient margin of safety (current price 50.00 is higher than the target buy price of 20.27). Wait for a pullback.

**Action Item**: Set alert at buy-trigger price: **₹20.27** (75% of intrinsic value).
