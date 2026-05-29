# Sidwell DCF Engine — v0.7 Rebuild Plan
**Repo:** `J-coder683/sidwell-algo` · **Target output:** institutional-grade, self-justifying DCF workbook
**Audience of this document:** Claude Code (which will translate it into an Antigravity implementation prompt — see §11)

---

## 0. TL;DR

Two workstreams, one architectural rule.

- **Workstream A — Justification & uncertainty layer.** Every number in the model carries a written rationale, a source tag, and a confidence flag. Numbers the engine cannot ground in a hard source are still emitted, but bracket-flagged (e.g. `[VERIFY: ER]`) so a human knows exactly what to check.
- **Workstream B — Output overhaul + mechanics fixes.** Make the workbook look and behave like the reference models (EasyJet 3-statement, STLD, Alphabet, Ascend): proper sheet structure, color coding, scenario switch, growth fade/convergence, dual terminal, full EV→equity bridge **including minority interest**, diluted share count, mid-year discounting.
- **The rule (non-negotiable):** **No LLM calls inside the engine.** Gemini runs *upstream* and produces a structured handoff file (the "Assumption Justification Pack", AJP). The engine is deterministic Python that ingests the AJP + the quantitative data it already pulls, then computes and renders. The AJP contract is what enforces the AI/engine separation.

---

## 1. Objective & non-negotiables

**Objective.** Move from a quantitative-only engine (single historical CAGR, flat drivers, EV − net debt) to a model that (a) justifies every input in writing against forensic-grade scrutiny, (b) flags everything it cannot source, and (c) is formatted and structured like a man-made institutional model.

**Non-negotiables:**
1. **Engine = deterministic.** No `gemini`, `openai`, `anthropic`, or any inference call in the engine package. Enforce with a CI lint that fails the build if those imports appear under the engine module path.
2. **AI is upstream only.** Gemini reads filings / earnings calls (already done for 3 quarters) and — later — ER/news, and writes the AJP. The engine never calls it; it reads the AJP file.
3. **Every output cell that is an input has a rationale + source tag.** No silent hardcodes.
4. **Unsourceable numbers are emitted, not omitted, and flagged in brackets.** A flagged number is better than a missing one; an unflagged guess is the failure mode we are killing.
5. **Backward compatibility of the math.** The valuation arithmetic must reconcile to a hand-check on at least one current ticker before merge.

---

## 2. Current state (v0.6) — what exists

The engine emits a 7-sheet workbook: `1_Cover`, `2_Assumptions`, `3_Stage1_Explicit`, `4_Stage2_Fade`, `5_Terminal`, `6_Valuation_Bridge`, `7_Sensitivity`.

Known limitations to fix:
- **Single growth rate** applied flat across both stages — `4_Stage2_Fade` does not actually fade (reuses Stage 1 rate).
- **Flat drivers** — EBIT margin, CapEx/Sales (default 5%), NWC/Sales (default 1%) held constant; not derived per company, not converging.
- **D&A pasted as hardcoded values**, decoupled from CapEx (no steady-state reconciliation).
- **Bridge is EV − net debt only** — no minority interest, no preferred, no associates/investments, no NOLs. Breaks on holdcos (BBTC mis-valued ~4x).
- **Raw share count** from Yahoo — no diluted/treasury-stock-method.
- **Single terminal method** (Gordon), no exit-multiple cross-check.
- **Full-year discounting** (`1/(1+WACC)^n`), no mid-year convention.
- **Source notes are generic** ("4-year historical average"); no per-number rationale, no confidence, no flags.
- **No 3-statement engine, no comps, no historical reconciliation.**

What is already sound and stays in the deterministic engine: FRED risk-free pull, Damodaran ERP/CRP + industry beta, CAPM cost of equity, historical tax-rate averaging, revenue base, market-cap-weighted WACC.

---

## 3. Target architecture: the AI ↔ engine wall

```
   ┌─────────────────────────┐        AJP (JSON/YAML)        ┌──────────────────────────┐
   │  GEMINI (upstream, AI)   │ ───────────────────────────▶ │  ENGINE (deterministic)   │
   │  • reads ARs + calls     │   one structured contract     │  • reads AJP + quant data  │
   │  • (later) ER + news     │                               │  • projects, discounts     │
   │  • assigns forward-look  │                               │  • builds bridge, WACC     │
   │    judgment numbers      │                               │  • renders xlsx + flags    │
   │  • writes rationale +    │                               │  • ZERO inference calls    │
   │    source + confidence   │                               └──────────────────────────┘
   └─────────────────────────┘
```

Gemini supplies **only** what the engine cannot derive mechanically: forward-looking judgment (growth path, margin path, terminal assumptions, scenario calibration) plus the **rationale text, source tag, and confidence flag for every input** — including the ones the engine itself computes (Gemini does not invent those values, it annotates them; see §5.3). The engine owns all arithmetic.

---

## 4. The Assumption Justification Pack (AJP) — the contract

A single file (`<TICKER>_AJP.json`) produced by the Gemini step and read by the engine. One entry per model input. Proposed schema:

```jsonc
{
  "meta": {
    "ticker": "BBTC.NS",
    "as_of": "2026-05-29",
    "gemini_run_id": "...",
    "sources_ingested": ["AR_FY25", "Q1FY26_call", "Q2FY26_call", "Q3FY26_call"],
    "is_holdco": true,                       // structural flag → triggers SOTP path / NCI handling
    "scenario_active": "BASE"
  },
  "assumptions": [
    {
      "driver_id": "stage1_revenue_growth",  // stable key the engine maps to a cell
      "value": 0.085,
      "unit": "ratio",
      "scenario": { "BEAR": 0.05, "BASE": 0.085, "BULL": 0.11 },
      "split": { "volume": 0.06, "price": 0.025 },   // optional; powers the volume/price defense
      "source_type": "MGMT_GUIDANCE",        // enum, see §5.3
      "confidence": "HIGH",                  // HIGH | MEDIUM | LOW | UNVERIFIED
      "verify_flag": null,                   // null | "ER" | "NEWS" | "EST"
      "rationale": "Mgmt guided 8–9% on Q3FY26 call (~12:04): ~6% volume on capacity adds, ~2.5% price from Jan tariff pass-through. Below 5-yr hist CAGR of 9.4% reflecting base effect.",
      "interrogation_refs": ["1.1", "1.2", "1.4"]   // maps to manual pillars/subtopics
    }
    // ... one object per input
  ]
}
```

**Engine behaviour on ingest, per assumption:**
- Write `value` to the input cell (formatted blue per §6.2).
- Write `"[<SOURCE_TAG>] <rationale>"` to the **Notes/Justification** column.
- If `verify_flag` is set **or** `confidence == "UNVERIFIED"`: append the bracket flag (e.g. ` [VERIFY: ER]`) to the cell's note **and** fill the cell yellow.
- If `scenario` is present, wire the three values into the scenario block so the switch in §6.3 toggles them.
- If a required `driver_id` is **missing** from the AJP: the engine falls back to its own computed value, tags it `[ENGINE-EST]`, sets confidence `LOW`, and flags `[VERIFY]`. **It never errors out and never silently inserts an unflagged number.**

A JSON schema file (`ajp.schema.json`) ships in the repo; the engine validates the AJP on load and writes a `validation_report` to the Sources sheet.

---

## 5. Workstream A — Justification & uncertainty layer

### 5.1 Justification schema mapped to the interrogation manual

Every input must, at minimum, answer the forensic question(s) for its pillar. The engine doesn't generate this prose — Gemini does — but the engine enforces that an `interrogation_refs` tag and a non-empty `rationale` exist for each input, and surfaces a coverage score.

| Manual pillar | Inputs it governs | What the rationale must contain |
|---|---|---|
| **1. Revenue & Growth** | revenue growth path, volume/price split, terminal share | volume-vs-price bifurcation; S-curve/decay logic; concentration/churn note; cyclicality stance |
| **2. Margins & Cost** | EBIT/EBITDA margin path, SBC treatment, R&D, capex/D&A convergence | fixed-vs-variable leverage basis; peer steady-state margin; SBC as real cost; ASC 842 / lease note |
| **3. Working Capital** | DSO/DIO/DPO, deferred rev, NWC/Sales, terminal NWC | per-line WC drivers; deferred-rev tethered to bookings not revenue; terminal NWC = TermRev × g × (NWC/Rev) |
| **4. WACC** | Rf, ERP, size/country premium, beta, Kd, weights | normalized vs spot Rf; Hamada unlever/relever math; premium justified by liquidity/idiosyncratic risk; synthetic-rating Kd |
| **5. Terminal Value** | g, exit multiple, reinvestment | g ≤ long-run nominal GDP; Gordon vs exit-multiple cross-check; reinvestment rate = g / RoNIC |

### 5.2 Source taxonomy & flag convention

`source_type` enum (drives the `[TAG]` prefix in the Notes column):

`FILING` · `EARNINGS_CALL` · `MGMT_GUIDANCE` · `SELL_SIDE_ER` · `NEWS` · `MACRO_FRED` · `DAMODARAN` · `PEER_COMPS` · `MARKET_CONVENTION` · `ENGINE_COMPUTED` · `ASSUMED`

Bracket flags appended to the note (and triggering yellow fill) when grounding is incomplete:
- `[VERIFY: ER]` — plausible but needs an equity-research figure to confirm.
- `[VERIFY: NEWS]` — depends on a recent event the engine couldn't see.
- `[EST]` — Gemini/engine estimate, no hard source; directional only.
- `[ENGINE-EST]` — AJP gave no value; engine fell back to its own computation.

Rule of thumb encoded in the schema: **HIGH** = direct filing/guidance figure; **MEDIUM** = derived from filings + reasonable assumption; **LOW** = inferred from peers/market; **UNVERIFIED** = no source, must be checked. Anything below HIGH gets a flag.

### 5.3 Which numbers Gemini assigns vs. which the engine computes

Keep the split explicit so the wall is clean.

- **Engine computes (Gemini only annotates):** Rf (FRED), ERP/CRP + industry beta (Damodaran), CAPM Ke, historical tax rate, revenue base, historical driver averages, market-cap weights, **synthetic-rating cost of debt** (new — from interest coverage, deterministic), diluted share count (new — treasury stock method, deterministic), the full bridge arithmetic.
- **Gemini assigns (the "few but important" numbers not currently derived):** forward revenue growth *path* and volume/price split; margin *path* / target margin and its driver; terminal growth and exit multiple stance; scenario calibration (Bear/Base/Bull); convergence targets (capex→D&A, NWC tapering); holdco flag + segment splits for SOTP; any concentration/cyclicality adjustments.

---

## 6. Workstream B — Output overhaul + mechanics

### 6.1 Target workbook structure

Phase 1 (this rebuild):
1. `1_Cover` — ticker, date, price, intrinsic, upside, WACC, g, **confidence summary** (count of HIGH/MED/LOW/flagged inputs).
2. `2_Drivers_Scenarios` — scenario switch (BEAR/BASE/BULL) driving an ACTIVE column (model on EasyJet/Ascend).
3. `3_Assumptions_Justifications` — **the heart.** Each input: value (blue), source tag, rationale, confidence, flag. Grouped by the 5 pillars.
4. `4_IS_Projection` — revenue→EBIT→NOPAT build with fade/convergence (not flat).
5. `5_FCF_DCF` — UFCF build, mid-year discounting, PV.
6. `6_WACC` — comps beta unlever/relever (Hamada), current **and** target structure, synthetic-rating Kd.
7. `7_Terminal` — dual method (Gordon + exit EV/EBITDA), cross-check, terminal NWC reinvestment row.
8. `8_Valuation_Bridge` — EV → (+) cash → (−) debt → (−) minority interest → (−) preferred → (+) associates/investments → (−/+) NOLs → equity → ÷ **diluted** shares.
9. `9_Sensitivity` — WACC × g **and** WACC × exit multiple.
10. `10_Sources` — source list + AJP validation report + coverage score.

Phase 2 (later, flagged as out-of-scope for first PR): full Balance Sheet + Cash Flow with balance check and debt schedule; public + M&A comps; historical reconciliation tab (model Ascend's `Reconciliation`).

### 6.2 Formatting standards (match the reference models)

- **Color coding:** blue = hardcoded inputs; black = formulas; green = cross-sheet links; yellow fill = flagged/needs-check cells.
- **Units in every header** (e.g. "Revenue (₹ mm)"); years as text; multiples `0.0x`; percentages `0.0%`; negatives in parentheses; zeros as `-`.
- **Notes/Justification column** to the right of every assumption block, populated from the AJP per §4.
- **Font:** single professional face throughout (Arial/Calibri).
- **Zero formula errors** on export (`#REF!`, `#DIV/0!`, etc.) — gate the export on a recalc check.
- All assumptions as separate cells referenced by formula (no hardcodes inside formulas).

### 6.3 Mechanics upgrades

- **Growth fade / convergence:** Stage 1 explicit → Stage 2 *linearly decays* toward terminal g (Alphabet-style target-year convergence). Margins, CapEx/Sales, NWC/Sales each glide to a target by the final explicit year.
- **CapEx ↔ D&A reconciliation:** in steady state D&A converges toward CapEx; stop pasting D&A as independent values.
- **Itemized NWC** (Phase 1: at least AR/Inventory/AP via DSO/DIO/DPO; fall back to NWC/Sales only if data missing, flagged).
- **Dual terminal value:** Gordon **and** exit EV/EBITDA; show both, flag divergence > X%.
- **Terminal reinvestment:** hardcode `ΔNWC_terminal = TerminalRevenue × g × (NWC/Revenue)` so terminal FCF isn't inflated by a zeroed-out NWC change.
- **Mid-year convention:** discount periods 0.5, 1.5, … (toggleable).
- **Full bridge incl. minority interest:** structural fix; for `is_holdco == true`, route to an SOTP/NAV path (stake value + other segments − holdco net debt − holdco discount) instead of consolidated UFCF.
- **Diluted shares:** treasury-stock-method on options + RSUs/PSUs (model Alphabet's `Shares` sheet), deterministic.
- **Synthetic-rating cost of debt:** map interest-coverage ratio → spread → Kd (Damodaran synthetic-rating table), replacing naive int/debt.

---

## 7. Repo / module changes (`sidwell-algo`)

Suggested layout (Antigravity to confirm against actual repo):

```
sidwell/
  ajp/
    schema.py            # AJP dataclasses + ajp.schema.json validation
    loader.py            # load + validate AJP, fallback logic, flag handling
  engine/                # DETERMINISTIC ONLY — CI forbids inference imports here
    projections.py       # revenue/margin/driver paths with fade & convergence
    wacc.py              # Hamada unlever/relever, synthetic rating, dual structure
    terminal.py          # Gordon + exit multiple + terminal reinvestment
    bridge.py            # full EV→equity incl. NCI/preferred/associates; SOTP path
    shares.py            # treasury-stock-method diluted count
    fcf.py               # UFCF build, mid-year discounting
  render/
    workbook.py          # openpyxl writer: sheets, color coding, notes, flags
    formats.py           # number formats, fonts, fills
  tests/
    ...                  # see §8
  cli.py                 # run(ticker, ajp_path) -> xlsx
```

CI guard (example): a test that greps the `sidwell/engine/` tree for `import (anthropic|openai|google\.generativeai)` and fails if found.

---

## 8. Acceptance criteria & tests

1. **AI-wall test:** build fails if any inference import exists under `sidwell/engine/`.
2. **AJP validation:** malformed AJP → clear error; missing `driver_id` → engine falls back, flags `[ENGINE-EST]`, never crashes.
3. **Flag propagation:** an `UNVERIFIED` / `verify_flag` input produces a yellow cell + bracketed note. Unit-tested on a fixture AJP.
4. **No unflagged hardcodes:** every input cell has a non-empty Notes entry with a source tag. Test scans the rendered workbook.
5. **Zero formula errors** on export (recalc gate).
6. **Bridge correctness:** on a holdco fixture (BBTC), NCI is deducted / SOTP path taken; intrinsic value is sane vs. spot (no ~4x artifact).
7. **Math reconciliation:** one ticker hand-checked end-to-end; PV, TV, EV, equity, per-share match within rounding.
8. **Convergence:** Stage 2 growth strictly decays toward g; assert monotonic step-down.

---

## 9. Open design decision (decide before building)

A full integrated 3-statement model carries per-company judgment (segment splits, debt schedule, scenario calibration) that does not fully auto-generate the way the current single-rate engine does. **Recommended default:** ship Phase 1 (justification layer + formatting + mechanics fixes + bridge/dilution/dual-terminal) as a *fully automated* deterministic engine fed by the AJP; treat the full 3-statement BS/CFS + comps as Phase 2, and design the AJP schema now so it already has the fields Phase 2 needs (so no contract break later). Flag this choice to the user before Antigravity starts — it sets the PR scope.

---

## 10. Phasing summary

- **Phase 1 (this PR):** AJP contract + loader; justification/flag layer; formatting overhaul; fade/convergence; dual terminal + terminal reinvestment; full bridge incl. NCI + SOTP path; diluted shares; synthetic-rating Kd; mid-year; sensitivity (2 grids); tests.
- **Phase 2 (next):** full BS + CFS with balance check + debt schedule; public + M&A comps; historical reconciliation; news/ER ingestion feeding the AJP.

---

## 11. Instruction to Claude Code

Claude Code: using this document as the source of truth, produce a single implementation prompt for **Antigravity** that will modify the `sidwell-algo` repo to deliver **Phase 1** only. The Antigravity prompt must:

1. Open with the **non-negotiable AI/engine wall** (§1, §3) and the CI guard requirement (§7, §8.1) — state these first so they are not lost.
2. Specify the **AJP schema** (§4) as the integration contract, including the engine's fallback/flagging behaviour, and ask Antigravity to commit `ajp.schema.json` + a fixture `BBTC.NS_AJP.json` for tests.
3. Enumerate the **module changes** (§7) and the **workbook structure + formatting + mechanics** (§6) as concrete, checkable tasks.
4. Encode the **justification + flag requirements** (§5) — every input gets a tagged rationale; sub-HIGH confidence ⇒ bracket flag + yellow fill.
5. Restate the **acceptance criteria** (§8) as the definition of done, and instruct Antigravity to write those tests first (TDD).
6. Explicitly mark Phase 2 items (§10) as **out of scope** for this PR, while requiring the AJP schema to already carry Phase 2 fields.
7. Ask Antigravity to confirm the actual repo layout before refactoring, and to surface the §9 design decision to the user if repo reality conflicts with the assumed structure.

Keep the Antigravity prompt imperative, testable, and free of any instruction that would put an LLM call inside the engine.
