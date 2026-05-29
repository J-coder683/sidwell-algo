# Reference Models — Structure, Conventions & Feature Checklist

**Purpose.** Distilled reference for the five man-made / Cowork models used as the target standard for the Sidwell DCF v0.7 rebuild. Read this *before* opening the raw `.xlsx` files — it captures everything the rebuild needs about their structure and formatting so the agent rarely has to re-parse the binaries. Raw workbooks live in `reference/models/` and are only needed when pixel-exact format must be matched.

**How to use:** §1 is per-model reference (what each file is, sheet layout, features worth copying). §2 is the actionable distillation — formatting standards + the feature checklist that maps to the v0.7 plan (Workstream B). Build against §2; consult §1 when you need to see how a specific model did something.

---

## 1. The models

### 1.1 EasyJet — full 3-statement operating model `(reference for the integrated engine)`
**File:** `05-EasyJet-3-Statement-Model-Complete_Tele.xlsx` · single sheet `EasyJet` (~279 rows). Units: £ GBP millions, stated in the header. BIWS-style.

**Layout (single-sheet, top-to-bottom):**
- **Assumptions block** — company meta, periods, units, **scenario selector** (`Base / Downside / Extreme Downside`), % funding from debt, share price, last full historical year, most recent half-year.
- **Driver-based revenue build** — *not* a single growth rate. Available Seat Km (ASK) × YoY growth → Passenger Load Factor → Revenue Passenger Km (RPK); Passenger Revenue = RPK × yield; Ancillary Revenue = RPK × ancillary yield. Each driver has Base/Downside/Extreme rows.
- **Expense drivers** — fuel cost per tonne → implied tonnes → fuel expense per ASK; non-fuel opex per ASK; depreciation per ASK; right-of-use depreciation per ASK; amortisation; **operating-lease interest element** (ASC 842 / IFRS 16 lease treatment); effective tax rate.
- **Balance-sheet & CF drivers** — AR % LTM revenue, AP % LTM opex, deferred revenue % revenue, provisions, deferred taxes, **SBC % non-fuel opex**, CapEx per ASK, additions to ROU assets, dividends % net income, FX effects.
- **Income Statement** — revenue → opex (fuel, non-fuel, depreciation, ROU depreciation, amortisation) → operating profit → net finance charges (incl. lease interest) → PBT → tax → net income → basic EPS.
- **Statement of Financial Position** — current/non-current assets incl. **ROU assets** and goodwill; liabilities incl. operating-lease liabilities and total debt; equity; **`Balance Check` row** (must be zero).
- **Cash Flow Statement** — CFO (net income + non-cash add-backs incl. SBC, deferred tax; changes in operating assets/liabilities) → CFI (CapEx, ROU additions, intangibles, sale-and-leaseback proceeds) → CFF (issuances/repurchases, dividends, net debt proceeds, lease principal, repayments) → FX → net change → ending cash.
- **Debt & Equity schedule** — benchmark rate + spreads; interest on **beginning** balances (handles circularity); minimum-liquidity-per-seat test → additional funding required → debt/equity issued; **revolver with cash sweep** (beginning → borrowing required → repayment → ending); bond/finance-lease roll-forward.
- **Key metrics & ratios** — LTM EBITDA, net debt + leases, capital employed, **NOPAT, ROCE**, margins (operating/EBITDA/net), leverage (debt/EBITDA, net debt/EBITDA), coverage (EBITDA/interest), debt/equity.

**Copy:** scenario architecture; driver-based (units × price) revenue; full 3-statement with **balance check**; debt schedule with revolver/cash-sweep/min-liquidity and interest-on-beginning-balance; explicit lease treatment; ratios block.

---

### 1.2 STLD (Steel Dynamics) — institutional DCF `(reference for the DCF + bridge + WACC)`
**File:** `07-STLD-Valuation-DCF-Complete_.xlsx` · sheets: `STLD-DCF` (160×34), `WACC` (60×30), `Public-Comps` (43×40), `M&A-Comps` (26×9), `ValSum` (46×13), `ValGraph` (47×18). Units: $ USD millions.

**`STLD-DCF` structure:**
- **Assumptions & output header** — company/ticker/price, **diluted shares**, effective tax, WACC, last FY.
- **Current EV bridge (the complete one)** — Equity Value → (−) cash → (−) equity investments → (−) other non-core assets → (−) NOLs → (+) total debt → (+) **preferred stock** → (+) **noncontrolling interests** → (+) unfunded pension → (+) capital leases → (+) restructuring/other liabilities → **Enterprise Value**. *This is the bridge the v0.6 engine was missing.*
- **Segment revenue build** — net sales by segment (Steel / Metals Recycling / Fabrication / Other) driven by **shipments × average sales price per ton** per segment, plus inter-company eliminations; operating income & margin by segment.
- **FCF projection** — Revenue → EBIT (operating income) → (−) taxes excl. interest effect → NOPAT → (+) D&A → (+/−) deferred taxes → **itemized ΔNWC** (change in AR, inventory, other assets, AP, income-tax payable, accrued expenses) → (−) CapEx → **Unlevered FCF** → discount period → cumulative discount factor → PV of UFCF. EBITDA shown alongside.
- **Sensitivity** — two grids: **terminal EV/EBITDA multiple** and **terminal FCF growth rate**.

**`WACC` structure:**
- Assumptions: risk-free, ERP, pre-tax cost of debt, cost of preferred.
- **Comparable-companies unlevered beta** — peer set (X, NUE, CMC, AKS, WOR, RS), **unlever each peer's beta, take the median** asset beta.
- **Levered beta & WACC** for STLD under **current capital structure AND "optimal" capital structure**; cost of equity from comps (current / optimal) and from historical beta; WACC under each; **average of all methods**.

**Copy:** the **full EV→equity bridge incl. NCI/preferred/pension/leases/NOLs**; segment-level (volume × price) revenue; **itemized working capital**; unlever/relever beta from peers (Hamada) at current + target structure with method-averaging; dual-method terminal sensitivity.

---

### 1.3 JAZZ (Jazz Pharmaceuticals) — DCF + deep comps `(reference for comps tabs)`
**File:** `08-JAZZ-Valuation-DCF-Complete_.xlsx` · sheets: `JAZZ-DCF` (305×19), `H1-Results`, `WACC`, `ValGraph`, `ValSum` (79×14), `Public Comps`, `Public-Comps-Data` (95×59), `MA-Comps` (45×31), `Inputs`.

Same DCF spine as STLD, but the value-add to copy is the **comps layer**: a raw `Public-Comps-Data` sheet (wide, 59 cols — the data dump) feeding a clean `Public Comps` presentation sheet; a separate `MA-Comps` (precedent transactions); an `Inputs` sheet centralising hardcodes; `H1-Results` for interim actuals; and a `ValSum` / `ValGraph` football-field summary. This is the template for Phase 2 comps.

**Copy:** the **data-sheet → presentation-sheet split** for comps (raw pull separated from formatted output); precedent-transaction comps; centralised `Inputs` sheet; football-field `ValSum`/`ValGraph`.

---

### 1.4 Alphabet — clean modular UFCF DCF `(reference for modularity, scenarios, dilution)`
**File:** `2026_01_23-Alphabet-DCF.xlsx` · sheets: `Cover`, `DCF` (87×20), `WACC` (22×6), `Shares` (32×7), `IS - Historical`, `IS - Estimates`, `CFS - Historicals`, `CFS - Estimates`. Units: USD millions.

**`DCF` structure:**
- **Assumptions / switches** at top — revenue, EBIT, WACC, TGR; cash-flow targets: **`D&A 2030 Target`, `CapEx 2030 Target`** (drivers *converge* to a steady-state target year — the fade mechanism v0.6 lacks).
- **Three scenario rows** for revenue and EBIT: `Conservative / Base (Street) / Optimistic`.
- Drivers as **% of sales**: D&A, CapEx, ΔNWC — each with its own % row.
- **DCF build:** Revenue (+ scenario rows) → EBIT (+ scenario rows) → taxes → **EBIAT** → (+) D&A → (−) CapEx → (−) ΔNWC → **UFCF** → PV of UFCF; explicit **`Discount Period`** row (supports mid-year); TV → PV of TV → **Enterprise Value → (+) Cash → (−) Debt → Equity Value → ÷ Share count → Implied price per share**.

**`WACC`** — compact CAPM: market cap & % equity, cost of equity (Rf + β × MRP), debt & % debt, after-tax cost of debt, total WACC.

**`Shares` (the one to copy for dilution):** full diluted share count via **treasury stock method** — basic shares + in-the-money exercisable options → total proceeds → shares repurchased → net dilutive options + RSUs + PSUs → **net diluted shares outstanding**; includes an options-outstanding schedule by tranche. *This replaces the v0.6 raw Yahoo share count.*

**IS/CFS historical + estimate sheets** feed the DCF (historicals and Street estimates kept separate).

**Copy:** modular sheet separation (DCF / WACC / Shares / statements); **scenario rows** in the DCF itself; **% -of-sales drivers with explicit target-year convergence**; **treasury-stock-method diluted share sheet**; clean EV→equity→per-share waterfall.

---

### 1.5 Ascend Telecom — Cowork-built model `(the quality bar a generated model can hit)`
**File:** `Ascend_Model.xlsx` · sheets: `Cover`, `Assumptions` (61×12), `Tower Derivation`, `Income Statement`, `Balance Sheet`, `Cash Flow`, `Tower Economics`, `DCF` (36×12), `Sensitivity`, `Reconciliation`, `Sources`. Units: INR crores.

**What it gets right (and is fully auto-generated):**
- **`Assumptions`** — single **scenario switch** (`Bear / Base / Bull` → `ACTIVE`), then grouped drivers: operational (towers × tenancy ratio → tenancies), revenue (**ARPS per tenant**, with explicit per-scenario growth rationale e.g. "+2.5% p.a., Kotak Indus ARPT trend"), margin, capex & D&A, working capital (**DSO/DPO days**), debt/interest/tax, and DCF inputs (Rf, ERP, beta, Ke, after-tax Kd, target D/cap, WACC, TGR, **exit EV/EBITDA multiple**).
- **3-statement core** — Income Statement / Balance Sheet / Cash Flow tabs.
- **`DCF`** — UFCF build (EBIT → tax → NOPAT → +D&A → −Capex → −ΔWC → UFCF); **`Period (mid-year)`** + discount factor → PV; **`TERMINAL VALUE` computed BOTH ways — Gordon AND exit-multiple — then averaged**; bridge to equity; implied EV/EBITDA cross-checks (FY26E/FY27E/FY30E).
- **`Tower Economics`** — per-unit economics & payback sensitivity; sourced to a named benchmark.
- **`Reconciliation`** — **ties every historical line item (IS/BS/CF/Capex) back to reported actuals** — the audit trail that proves the model isn't fabricated.
- **`Sources`** — explicit citations (Motilal Oswal, Kotak benchmarks).

**Copy:** the scenario-switch pattern; grouped, **rationale-annotated** assumptions; **mid-year** discounting; **dual terminal (Gordon + exit multiple) averaged**; **historical reconciliation tab**; explicit Sources sheet. This is the closest existing template to the v0.7 target.

---

## 2. Actionable distillation (build against this)

### 2.1 Formatting standards (apply to every sheet)

| Element | Standard |
|---|---|
| **Input cells** | Blue font (`0,0,255`). Hardcoded values / scenario inputs only. |
| **Formulas** | Black font. No hardcodes inside formulas — reference assumption cells. |
| **Cross-sheet links** | Green font (`0,128,0`). |
| **Flagged / needs-check cells** | Yellow fill (`255,255,0`) — used by the v0.7 confidence-flag layer. |
| **Headers** | Always state units, e.g. `Revenue (₹ mm)`, `(₹ crores unless noted)`. |
| **Years** | Text strings (`"2026"`, not `2,026`). |
| **Percentages** | `0.0%`. **Multiples** | `0.0x`. **Currency** | `#,##0`. |
| **Negatives** | Parentheses `(123)`. **Zeros** | display as `-`. |
| **Notes/Justification column** | To the right of every assumption block (Ascend/STLD pattern). In v0.7 this is populated from the AJP with `[SOURCE_TAG] rationale [+ flag]`. |
| **Font** | One professional face throughout (Arial / Calibri). |
| **Errors** | Zero `#REF!/#DIV/0!/#VALUE!/#NAME?` on export — gate export on a recalc check. |

### 2.2 Feature checklist (maps to v0.7 plan, Workstream B §6)

| # | Feature | Seen in | v0.7 target |
|---|---|---|---|
| 1 | Scenario switch (Bear/Base/Bull) driving an ACTIVE column | EasyJet, Alphabet, Ascend | `2_Drivers_Scenarios` |
| 2 | Driver-based revenue (units × price), not a single CAGR | EasyJet, STLD, Ascend | `4_IS_Projection` |
| 3 | Growth **fade / convergence** to terminal; drivers glide to target-year levels | Alphabet (2030 targets) | `4_IS_Projection` |
| 4 | Itemized working capital (DSO/DIO/DPO; AR/Inv/AP) | STLD, EasyJet, Ascend | `5_FCF_DCF` |
| 5 | CapEx ↔ D&A steady-state reconciliation (stop pasting D&A) | STLD, Alphabet | `4`/`5` |
| 6 | UFCF build with **mid-year** discounting | Alphabet, Ascend | `5_FCF_DCF` |
| 7 | WACC from **comps unlevered beta, relevered** at current + target structure | STLD | `6_WACC` |
| 8 | **Synthetic-rating** cost of debt (coverage → spread → Kd) | (Damodaran method) | `6_WACC` |
| 9 | **Dual terminal**: Gordon + exit EV/EBITDA, cross-checked/averaged | STLD, Ascend | `7_Terminal` |
| 10 | **Terminal NWC reinvestment** = TermRev × g × (NWC/Rev) | (interrogation manual §3) | `7_Terminal` |
| 11 | **Full EV→equity bridge incl. NCI**, preferred, associates, pension, leases, NOLs | STLD | `8_Valuation_Bridge` |
| 12 | Holdco → SOTP/NAV path when `is_holdco` | (BBTC failure mode) | `8_Valuation_Bridge` |
| 13 | **Diluted** share count via treasury-stock method (+ RSUs/PSUs) | Alphabet (`Shares`) | `8`/`shares.py` |
| 14 | Sensitivity: WACC × g **and** WACC × exit multiple | STLD, Ascend | `9_Sensitivity` |
| 15 | **Historical reconciliation** tab tying model to reported actuals | Ascend | Phase 2 |
| 16 | Public + M&A comps, data-sheet/presentation-sheet split, football field | STLD, JAZZ | Phase 2 |
| 17 | Full 3-statement (BS + CFS) with **balance check** + debt/revolver schedule | EasyJet, Ascend | Phase 2 |
| 18 | Explicit **Sources** sheet with citations | Ascend, JAZZ (`Inputs`) | `10_Sources` |

### 2.3 The single biggest structural lesson

Every man-made model treats the company as an **operating entity built from drivers, valued with a complete bridge.** The v0.6 engine was effectively just the "DCF assumptions & output" block of one of these (Alphabet's `DCF` tab) with no engine underneath and an incomplete bridge — which is why a holdco like BBTC mis-valued ~4x (consolidated FCF over BBTC shares, **no NCI deduction**). Items **#11, #12, #13** are the non-negotiable correctness fixes; the rest are quality/credibility.
