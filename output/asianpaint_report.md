# Investment Analysis Report: ASIANPAINT.NS
**Generated on**: May 26, 2026
**Valuation Engine**: Discounted Cash Flow (DCF)
**Investor Lens**: Warren Buffett (v0.2.1)

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
| Understandable business | ✅ | Hard: PASS / Soft: PASS | Both signals must pass | Hard check: PASS (ticker not in avoided-sector blacklist). Soft check: PASS (LLM coherence verdict: coherent). The disclosures and statements from the management are highly coherent and align with reported financials. Management successfully reconciles the 5% gap between volume and value growth using transparent references to material deflation and product mix variations. Strategic investments, such as impairments on White Teak and regional launches, are directly addressed and align with their longer-term operational plans for profitability and market share protection. |

**Total Buffett Score**: **4/8**

## 3.5 Qualitative Analysis
Based on 1 document(s): 8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf. Model: `gemini-3.5-flash`.

### Forward Guidance
- **Q4 FY26** (volume): Management expects to maintain their current volume growth trajectory, targeting a volume growth band of 8% to 10% in the upcoming quarter. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_
- **Future periods** (margin): The company intends to maintain its PBDIT margin guidance within the 18% to 20% band, balancing brand investment and competitive pressures. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_
- **Next few quarters** (revenue): Realistically, value growth is projected to be around 5% to 6%, assuming the volume-value gap continues to hover at approximately 4% to 5%. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_

### Risk Callouts
- **competitive intensity**: Management expects high competitive intensity to continue with the entry of aggressive new players and the amalgamation of two existing players. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_
- **crude oil volatility**: Geopolitical uncertainties pose continuous risks of volatility in crude oil prices, which can quickly impact key raw material costs. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_
- **regulatory pressure on TiO2**: There is potential regulatory risk around key imported raw materials like titanium dioxide (TiO2), which could see upcoming structural movements. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_
- **home decor bottom-line distress**: The White Teak business faced bottom-line challenges, leading to an impairment loss of approximately Rs. 94 crores during the quarter. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_

### Strategic Themes
- **regionalization**: Asian Paints has scaled customized regional product portfolios and marketing strategies across 8 to 9 states to enhance localized customer brand equity. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_
- **backward integration**: Following the launch of its white cement plant, the company plans to progress to the next level of backward integration starting next fiscal year to drive cost efficiency. _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_
- **AI integration in services**: The company is deploying artificial intelligence for hyper-segmentation of customers and tracking execution quality via AI-driven Net Promoter Scores (NPS). _[8bc8c7dd-23d0-4cf2-bcdf-620769ed0d1a.pdf]_

### Tone & Coherence
- **Tone (current)**: confident
- **Tone (trajectory)**: stable
- **Coherence verdict**: coherent

_Management displays a high level of confidence in their market leadership, brand visibility, and structural initiatives like regional packaging and backward integration. They dismiss competitive pricing moves as artificial discounting and remain secure in their premium position. However, their tone is reasonably realistic and cautious concerning global crude volatilities, geopolitical disruptions, and the slower recovery cycle in domestic decorative paint spending._

_The disclosures and statements from the management are highly coherent and align with reported financials. Management successfully reconciles the 5% gap between volume and value growth using transparent references to material deflation and product mix variations. Strategic investments, such as impairments on White Teak and regional launches, are directly addressed and align with their longer-term operational plans for profitability and market share protection._

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
