# Expected Calculations - Snapshot Fixture Company

This document lists the step-by-step manual derivations and math formulas for the fictitious company snapshot tests to verify the correctness of the Sidwell engine.

## Inputs
- Ticker: `FICTITIOUS.NS`
- Current Price: `50.00`
- Shares Outstanding: `10.00`
- Market Cap: `500.00`
- Years: `["2022-12-31", "2023-12-31", "2024-12-31", "2025-12-31"]`
- Revenue: `[100.0, 110.0, 121.0, 133.1]` (10.00% YoY growth)
- Gross Profit: `[40.0, 44.0, 48.4, 53.24]` (40.00% Gross Margin)
- EBIT: `[20.0, 22.0, 24.2, 26.62]` (20.00% EBIT Margin)
- Interest Expense: `[2.0, 2.0, 2.0, 2.0]`
- Tax Provision: `[4.5, 5.0, 5.55, 6.155]` (25.00% of Pretax Income)
- Pretax Income: `[18.0, 20.0, 22.2, 24.62]`
- Net Income: `[13.5, 15.0, 16.65, 18.465]`
- Total Assets: `[100.0, 110.0, 121.0, 133.1]`
- Total Equity: `[60.0, 66.0, 72.6, 79.86]` (60.00% of Assets)
- Cash: `[10.0, 11.0, 12.1, 13.31]`
- Debt: `[20.0, 20.0, 20.0, 20.0]`
- CapEx: `[5.0, 5.5, 6.05, 6.655]` (5.00% of Revenue)
- Depreciation: `[3.0, 3.3, 3.63, 3.993]` (3.00% of Revenue)
- Working Capital Change: `[0.0, 0.0, 0.0, 0.0]`
- Free Cash Flow: `[11.5, 12.8, 14.23, 15.803]`

---

## 1. WACC Sourcing and CAPM
- Risk-Free Rate ($R_f$): `6.00%` (0.06)
- Mature Market ERP: `5.00%` (0.05)
- Country Risk Premium: `2.00%` (0.02)
- Total ERP: `mature_market_erp + country_risk_premium = 5.00% + 2.00% = 7.00%` (0.07)
- Industry Unlevered Beta: `0.90`
- Debt/Equity Ratio: `latest_debt / market_cap = 20.0 / 500.0 = 4.00%` (0.04)
- Average Tax Rate ($t$): `25.00%` (0.25)
- Target Levered Beta ($\beta$):
  $$\beta_{levered} = \beta_{unlevered} \times \left(1 + (1 - t) \times \frac{\text{Debt}}{\text{Equity}}\right)$$
  $$\beta_{levered} = 0.90 \times (1 + (1 - 0.25) \times 0.04) = 0.90 \times (1 + 0.03) = 0.927$$
- Cost of Equity ($K_e$):
  $$K_e = R_f + \beta \times \text{Total ERP}$$
  $$K_e = 0.06 + 0.927 \times 0.07 = 0.06 + 0.06489 = 12.489\%$$
- Cost of Debt ($K_d$):
  - Since `latest_debt = 20.0` is $\ge 5\%$ of `latest_assets = 133.1` (which is 6.655), raw interest/debt is calculated:
    $$\text{Raw } K_d = \frac{\text{interest\_expense}[-1]}{\text{latest\_debt}} = \frac{2.0}{20.0} = 10.00\%$$
  - Capped at `ceiling = Rf + 5% = 11.00%` and `floor = Rf + 1% = 7.00%`.
  - Since 10.00% is in-bounds, $K_d = 10.00\%$.
  - Debt source branch: `Calculated: int_expense/debt = 10.00%`
- Capital Weights:
  - Total Capital ($V$): `market_cap + latest_debt = 500.0 + 20.0 = 520.0`
  - Equity Weight ($W_e$): `500.0 / 520.0 = 96.1538%` (0.961538)
  - Debt Weight ($W_d$): `20.0 / 520.0 = 3.8462%` (0.038462)
- Weighted Average Cost of Capital (WACC):
  $$WACC = W_e \times K_e + W_d \times K_d \times (1 - t)$$
  $$WACC = 0.961538 \times 12.489\% + 0.038462 \times 10.00\% \times (1 - 0.25)$$
  $$WACC = 12.00865\% + 0.288465\% = 12.297115\% \approx 12.30\%$$

---

## 2. Projections (Explicit 5-Year Forecast)
Historical ratios as % of Revenue:
- EBIT Margin: `20.00%` (0.20)
- Tax Rate: `25.00%` (0.25)
- D&A Ratio: `3.00%` (0.03)
- CapEx Ratio: `5.00%` (0.05)
- Working Capital Change Ratio: `0.00%` (0.00)
- Net cash flow margin coefficient = `0.20 * (1 - 0.25) + 0.03 - 0.05 + 0.00 = 0.13` (13.00% of Revenue).
- Revenue growth rate: `10.00%` (0.10) (CAGR is exactly 10%, in the 5%-20% cap range).

Projections relative to Revenue:
- **Year 1 (2026)**:
  - Revenue: `133.1 * 1.10 = 146.41`
  - EBIT: `146.41 * 0.20 = 29.282`
  - Taxes: `29.282 * 0.25 = 7.3205`
  - D&A: `146.41 * 0.03 = 4.3923`
  - CapEx: `146.41 * 0.05 = 7.3205`
  - NWC change: `0.00`
  - FCF: `146.41 * 0.13 = 19.0333`
  - Discount Factor: `(1 + WACC) ** 1 = 1.122971`
  - PV of FCF: `19.0333 / 1.122971 = 16.9490`
- **Year 2 (2027)**:
  - Revenue: `146.41 * 1.10 = 161.051`
  - EBIT: `32.2102`
  - Taxes: `8.05255`
  - D&A: `4.83153`
  - CapEx: `8.05255`
  - NWC change: `0.00`
  - FCF: `161.051 * 0.13 = 20.93663`
  - Discount Factor: `(1 + WACC) ** 2 = 1.261064`
  - PV of FCF: `20.93663 / 1.261064 = 16.6024`
- **Year 3 (2028)**:
  - Revenue: `161.051 * 1.10 = 177.1561`
  - EBIT: `35.43122`
  - Taxes: `8.857805`
  - D&A: `5.314683`
  - CapEx: `8.857805`
  - NWC change: `0.00`
  - FCF: `177.1561 * 0.13 = 23.030293`
  - Discount Factor: `(1 + WACC) ** 3 = 1.416139`
  - PV of FCF: `23.030293 / 1.416139 = 16.2627`
- **Year 4 (2029)**:
  - Revenue: `177.1561 * 1.10 = 194.87171`
  - EBIT: `38.974342`
  - Taxes: `9.7435855`
  - D&A: `5.8461513`
  - CapEx: `9.7435855`
  - NWC change: `0.00`
  - FCF: `194.87171 * 0.13 = 25.3333223`
  - Discount Factor: `(1 + WACC) ** 4 = 1.590284`
  - PV of FCF: `25.3333223 / 1.590284 = 15.9301`
- **Year 5 (2030)**:
  - Revenue: `194.87171 * 1.10 = 214.358881`
  - EBIT: `42.8717762`
  - Taxes: `10.71794405`
  - D&A: `6.43076643`
  - CapEx: `10.71794405`
  - NWC change: `0.00`
  - FCF: `214.358881 * 0.13 = 27.86665453`
  - Discount Factor: `(1 + WACC) ** 5 = 1.785842`
  - PV of FCF: `27.86665453 / 1.785842 = 15.6042`

Sum of PV of Explicit Cash Flows = `16.9490 + 16.6024 + 16.2627 + 15.9301 + 15.6042 = 81.3484`

---

## 3. Terminal Value (Gordon Growth)
- Terminal growth rate ($g_{terminal}$): `min(0.04, Rf - 0.01) = min(0.04, 0.05) = 4.00%` (0.04)
- Terminal Value (TV):
  $$TV = \frac{FCF_5 \times (1 + g_{terminal})}{WACC - g_{terminal}}$$
  $$TV = \frac{27.86665453 \times 1.04}{0.12297115 - 0.04} = \frac{28.9813207}{0.08297115} = 349.2939$$
- PV of Terminal Value:
  $$PV(TV) = \frac{TV}{(1 + WACC) ** 5} = \frac{349.2939}{1.785842} = 195.5906$$

---

## 4. Valuation Bridge
- Enterprise Value (EV) = PV of explicit FCFs + PV of TV = `81.3484 + 195.5906 = 276.9390`
- Add: latest Cash: `13.31`
- Less: latest Debt: `20.00`
- Equity Value = EV + Cash - Debt = `276.9390 + 13.31 - 20.00 = 270.2490`
- Shares Outstanding: `10.0`
- Intrinsic Value per Share: `270.2490 / 10 = 27.0249` $\approx$ `₹27.02`

---

## 5. Buffett Lens Checks
1. **Durable competitive advantage (moat)**:
   - `hist_gross_margins = [0.40, 0.40, 0.40, 0.40]`
   - `hist_gm_std = np.std(gross_margins, ddof=1) = 0.00%`
   - Target: `< 3.0%`. Status: **PASS** (value = 0.00%)
2. **High return on invested capital**:
   - ROIC = `EBIT * (1 - t) / (Equity + Debt - Cash)`
   - Year 1: `20.0 * 0.75 / (60.0 + 20.0 - 10.0) = 15.0 / 70.0 = 21.43%`
   - Year 2: `22.0 * 0.75 / (66.0 + 20.0 - 11.0) = 16.5 / 75.0 = 22.00%`
   - Year 3: `24.2 * 0.75 / (72.6 + 20.0 - 12.1) = 18.15 / 80.5 = 22.55%`
   - Year 4: `26.62 * 0.75 / (79.86 + 20.0 - 13.31) = 19.965 / 86.55 = 23.07%`
   - `hist_roic_avg`: `(21.43% + 22.00% + 22.55% + 23.07%) / 4 = 22.26%`
   - Target: `> 15.0%`. Status: **PASS**
3. **Strong free-cash-flow generation**:
   - `hist_fcf_margins` = `[11.50%, 11.64%, 11.76%, 11.87%]`
   - `hist_fcf_margin_avg` = `11.69%`
   - `hist_fcf_growth` = `(15.803 - 11.5) / 11.5 = 37.42%`
   - Target: `Margin > 10% & Growth > 0%`. Status: **PASS**
4. **Conservative balance sheet**:
   - `latest_ebitda = EBIT (26.62) + Depr (3.993) = 30.613`
   - `latest_debt = 20.0`
   - `latest_debt_to_ebitda = 20.0 / 30.613 = 0.65x`
   - `latest_interest_coverage = 26.62 / 2.0 = 13.31x`
   - Target: `Debt/EBITDA < 3x & Coverage > 5x`. Status: **PASS**
5. **ROE without excess leverage**:
   - `hist_roe` = `[13.5/60 = 22.50%, 15.0/66 = 22.73%, 16.65/72.6 = 22.93%, 18.465/79.86 = 23.12%]`
   - `hist_roe_avg` = `22.82%`
   - `latest_equity_to_assets = 79.86 / 133.1 = 60.00%`
   - Target: `ROE > 15% & Equity/Assets > 40%`. Status: **PASS**
6. **Earnings predictability**:
   - `hist_revenue_cagr = 10.00%`
   - `YoY growth rates = [10.00%, 10.00%, 10.00%]`
   - `hist_growth_std = 0.00%`
   - Target: `5% < CAGR < 30% & YoY Growth StDev < 10.0%`. Status: **PASS**
7. **Margin of safety**:
   - Intrinsic Value = `27.02`, Current Price = `50.00`
   - Target: `> 25.0%`. Status: **FAIL** (Trading at 1.9x intrinsic value (target ≤ 0.75x))
8. **Understandable business**:
   - Target: `True`. Status: **PASS**

**Total Buffett Score**: `7/8`
**Final Verdict**: `WAIT` (Quality business at wrong price. Alert when price drops to ₹20.27)

---

## 6. Qualitative Mock (Section 3.5 — v0.2)

The `mock_qualitative` pytest fixture (defined in `tests/conftest.py`) has
`status = "available"`, so the "available" branch of the renderer fires.

### Fixture values and what render.py produces from them

**Header line** (from `documents_used` and `model`):
```
Based on 1 document(s): fixture_concall.pdf. Model: `gemini-1.5-flash`.
```

**Forward Guidance** (1 item):
```
- **FY27** (revenue): Management expects 10% revenue growth driven by capacity expansion. _[fixture_concall.pdf]_
```

**Risk Callouts** (1 item):
```
- **input cost volatility**: Raw material prices remain a watchpoint. _[fixture_concall.pdf]_
```

**Strategic Themes** (1 item):
```
- **premium product mix**: Mix shift toward premium SKUs continues. _[fixture_concall.pdf]_
```

**Tone & Coherence header lines**:
```
- **Tone (current)**: confident
- **Tone (trajectory)**: stable
- **Coherence verdict**: coherent
```

**Tone notes paragraph** (italic, from `tone_assessment.notes`):
```
_Management remained confident across the period, with a stable narrative._
```

**Coherence reasoning paragraph** (italic, from `coherence_assessment.reasoning`):
```
_Numeric claims tie out across documents and strategy is consistent._
```

**Check #8 in the Buffett lens table** — with `mock_qualitative` having
`coherence_assessment.verdict = "coherent"`:
- `hard_pass = True` (FICTITIOUS.NS not in blacklist)
- `soft_pass = True` (verdict == "coherent")
- `check_8_passed = True`
- `value = (True, True)` → renders as `Hard: PASS / Soft: PASS`
- `detail` = "Hard check: PASS (ticker not in avoided-sector blacklist). Soft check: PASS (LLM coherence verdict: coherent). Numeric claims tie out across documents and strategy is consistent."

So the check #8 row in the Buffett table changes from v0.1.1 to v0.2 as follows:
```
Before: | Understandable business | ✅ | True | True | Business is within standard circle of competence |
After:  | Understandable business | ✅ | Hard: PASS / Soft: PASS | Both signals must pass | Hard check: PASS (ticker not in avoided-sector blacklist). Soft check: PASS (LLM coherence verdict: coherent). Numeric claims tie out across documents and strategy is consistent. |
```

Score remains 7/8 (check #8 still passes). Verdict remains WAIT.
