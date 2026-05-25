# Investment Analysis Report: ASIANPAINT.NS
**Generated on**: May 25, 2026
**Valuation Engine**: Discounted Cash Flow (DCF)
**Investor Lens**: Warren Buffett (v0.1)

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
| **Buffett Score** | **4/8** | Spec criteria checks passed |
| **Final Verdict** | **SKIP** ❌ | Buffett Lens Rules |

### Verdict Summary
> **SKIP** — Does not meet the quality or financial health standards of the Buffett framework. Skip.

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
All 8 checks per Warren Buffett's framework (distilled from annual letters):

| Check | Status | Value | Target Threshold | Description |
| :--- | :---: | :--- | :--- | :--- |
| Durable competitive advantage (moat) | ❌ | 3.09% | < 3.0% | stdev = 3.09% >= 3% |
| High return on invested capital | ✅ | 23.04% | > 15.0% | 4y avg = 23.04% > 15% |
| Strong free-cash-flow generation | ❌ | 6.84% / 495.22% | Margin > 10% & Growth > 0% | avg margin = 6.84%, FCF growth = 495.22% |
| Conservative balance sheet | ✅ | 0.36 / 23.48 | Debt/EBITDA < 3x & Coverage > 5x | Debt/EBITDA = 0.36x, Int. Coverage = 23.48x |
| ROE without excess leverage | ✅ | 23.92% / 63.88% | ROE > 15% & Equity/Assets > 40% | 4y avg ROE = 23.92%, Equity/Assets = 63.88% |
| Earnings predictability | ❌ | 5.32% / 11.90% | 5% < CAGR < 30% & YoY Growth StDev < 10.0% | Revenue CAGR = 5.32%, YoY Growth StDev = 11.90% |
| Margin of safety | ❌ | Trading at 9.1x intrinsic value (target ≤ 0.75x) | > 25.0% | Trading at 9.1x intrinsic value (target ≤ 0.75x) (Price: 2657.80, Intrinsic: 291.69) |
| Understandable business | ✅ | True | True | Business is within standard circle of competence |

**Total Buffett Score**: **4/8**

## 4. Margin-of-Safety Check
Current Stock Price: **₹2,657.80**
DCF Intrinsic Value: **₹291.69**
Required Margin of Safety: **25.00%** ( Graham & Dodd standard)
Computed Margin of Safety: Trading at 9.1x intrinsic value (target ≤ 0.75x)
### Status: [FAIL] ❌
The stock trades above the safety threshold. Trading at 9.1x intrinsic value is insufficient for investment under the Buffett framework.

## 5. Investment Verdict
**RECOMMENDATION: SKIP**

Does not meet the quality or financial health standards of the Buffett framework. Skip.
