# KKR Lens — The Operator-Buyer Framework

A working framework for analyzing any public company **the way KKR would**: not by quoting Henry Kravis interviews, but by applying the lens through which KKR's investment committee actually evaluates an LBO target.

## The KKR Worldview (the lens, not the citations)

KKR does not analyze companies the way a public-equity portfolio manager does. KKR analyzes them the way **a private buyer with a specific operational playbook and a 7-year hold horizon** does — where the entry price matters less than what can be done with the asset, and the question is always "would we want to take this private and build it?"

When KKR looks at a company, the investment committee is asking — in this order:

1. **Can we double EBITDA over a 7-year hold?** This is the threshold question. Per Bain's 2026 PE report, *"12 is the new 5"* — easy multiple expansion is gone, and meeting today's return hurdles requires EBITDA roughly to double over the hold period. The KKR investment committee will not approve a deal where 2× EBITDA growth isn't credible through a combination of organic operating improvement and bolt-on M&A. *"Anyone can lever a company financially or buy something in hopes that the economy or the market moves in the right direction…we've been creating our own luck since 1976."* (Josh Weisenbeck, KKR Industrials).

2. **Which value-creation levers actually apply here?** PE alpha doesn't come from one lever; it comes from stacking five or six of them. Margin improvement (operating efficiency, pricing discipline, SG&A optimization). Capex rationalization (throttling growth capex in early hold years, optimizing maintenance capex via Capstone playbook). Working capital compression (faster collection, leaner inventory, supplier terms). Bolt-on M&A (platform + acquisitions at 5-7× into 10-12× exit). Management and board upgrade (KKR's Rolodex of operating partners and sector-specialist CEOs). Workforce equity (Stavros / Ownership Works model). Dividend recap (post-stabilization debt-financed distributions that lock in returns). The KKR lens evaluates each lever as a distinct check, because a deal with only one lever working is generic PE — and the Phalippou data shows generic PE doesn't beat public equity net of fees.

3. **Do we have a playbook here?** KKR's edge is its sector-specific operational toolkits — institutionalized in KKR Capstone (their internal operating consultancy) and seven sector-specialist Americas private-equity teams. They invest where they have repeatable improvement methodologies. *"Industrials is one of the most cyclical of the seven sectors our Americas private equity team covers, and I think that makes value creation even more important."* No playbook = no deal, regardless of how good the company looks on screen.

4. **Is the workforce profile compatible with the Stavros employee-ownership model?** Pete Stavros (Co-Head of Global Private Equity) has institutionalized broad-based employee equity across 80+ portfolio companies. The thesis is concrete: at Ingersoll Rand, quit rates dropped 90% and engagement scores moved from the 19th to 91st percentile after employee equity was implemented. Companies with large frontline hourly workforces (industrials, manufacturing, services, logistics) are where this playbook generates measurable productivity gains.

5. **Is now the right entry moment?** KKR's macro discipline (Henry McVey's "regime change" framework) and Joe Bae's focus on deploying capital during market dislocations both apply. KKR avoided the 2021-2022 overdeployment that crippled the broader industry. *"We didn't make that mistake in '21 and '22…not because we're smarter, but we screwed that up before and we put processes in place not to do it again."* (Stavros). The lens explicitly checks for cycle position and specific entry catalysts.

6. **Will the seller actually sell, and what's the exit path?** A great LBO target that nobody can buy (family-controlled, hostile board, sovereign restriction) is not investable. KKR's preferred entry dynamics: corporate carve-outs (Capsugel from Pfizer), founder-family succession with no clear heir (Germany Mittelstand thesis), public-to-private at multiple compression, or partner-operator arrangements (Alliance Boots / Pessina).

7. **Does the deal-specific thesis clear the Phalippou bar?** This is the skeptic's check. Ludovic Phalippou's "An Inconvenient Fact" (2020) showed that **net returns to LPs across all PE funds roughly match public equity indices since 2006** — implied 11% p.a. The implication for any specific KKR deal: it must have **multiple operational edges working simultaneously** to justify the PE risk premium, illiquidity, and fee structure. A deal with one or two levers working is generic. KKR's track record (~20% net over 15 years per Stavros) is above-average specifically because they stack multiple levers per deal. The lens formalizes this with an explicit alpha-defensibility check.

This framework codifies that order: **LBO-able financials → multiple operational upside levers → workforce/playbook fit → cycle + seller dynamics → above-average alpha thesis vs the Phalippou bar**. A company that fails Part A (LBO viability) is not investable at any price under this lens. A company that passes A but only has one or two value-creation levers (Part B) fails the Phalippou defensibility check in Part E — it's a generic PE bet, not a KKR-edge deal.

The framing is critical: this lens evaluates public companies as **potential LBO targets**, not as public investments to hold passively. The output answers "would KKR want to take this private at the current price?" — not "is this a good public-market trade?"

---

## Framework: 18 Checks Across 5 Parts

Same conventions as `frameworks/buffett.md` and `frameworks/marks.md`:
- All standard deviations use `np.std(..., ddof=1)`.
- "Historical" = 4 years of data; "Latest" = most recent fiscal year.
- LLM-driven checks flagged with **(soft)**.

---

### Part A — LBO Viability (Checks 1–4)

These checks answer: *is the financial structure capable of supporting a KKR-scale LBO?* **Pre-conditions. All four must pass for the lens to even consider the company.**

#### 1. EBITDA scale (KKR-scale check size)
**Test:**
  - For US tickers: `latest_ebitda > $200M`
  - For India tickers (`.NS`/`.BO`): `latest_ebitda > ₹400cr` (~$48M)
**Logic:** KKR doesn't do small-cap. The Americas flagship is now ~$20B; the typical check size is $500M-$2B equity into businesses with $200M+ EBITDA. India is different — smaller market, lower thresholds, but the principle holds: scale matters because the operational improvement playbook has fixed costs (Capstone team support, board recruiting, M&A sourcing) that don't make sense for small-cap targets.
**Source:** Stavros Goldman Talks Dec 2025 (Americas flagship $20B vintage); Master Compendium Part 5.1.

#### 2. FCF conversion (debt-service capability)
**Test:** `mean(fcf_4y) / mean(ebit_after_tax_4y) > 0.60` where `ebit_after_tax = ebit × (1 - tax_rate)`
**Logic:** An LBO loads 4-6× EBITDA of debt onto the company; debt service requires real cash, not accounting earnings. KKR underwrites cash generation, not GAAP earnings. 60% conversion of after-tax EBIT into FCF is the threshold for KKR-style buyouts.
**Source:** Standard PE underwriting; Bain Global PE Report 2026 on "12 is the new 5."

#### 3. Leverage capacity (room to add LBO debt)
**Test:** `latest_debt / latest_ebitda < 3.0`
**Logic:** A KKR LBO typically targets 4-6× net debt / EBITDA at close. If the target is already at 3× pre-buyout, there isn't room to load the additional debt that makes the LBO math work. Companies with very low debt (Asian Paints at 0.36×) are ideal LBO targets — KKR can add 3-4 turns of leverage and the math becomes tractable.
**Source:** Standard LBO structure; KKR Capstone framework.

#### 4. EBITDA margin (operating cushion through cycles)
**Test:** `latest_ebitda_margin > 0.15`
**Logic:** An LBO must service its debt through cycle troughs. 15% EBITDA margin gives meaningful operating cushion before debt-service problems emerge.
**Source:** Capital Safety / Bettcher industrials playbook; Compendium Part 1.1 (RJR cash flow analysis).

---

### Part B — Operational Upside (Checks 5–10)

These checks answer: *which value-creation levers can KKR actually deploy at this company?* The Phalippou check in Part E later asks whether enough of these pass to justify the PE risk premium — but each check here is independent.

#### 5. Margin improvement room (not already best-in-class)
**Test:** `latest_ebit_margin < max(hist_ebit_margin_4y) × 0.95` (current margin is at least 5% below the 4y peak — meaning compression has occurred that operating improvement could reverse)
**Logic:** A company at its own all-time peak EBIT margin offers KKR limited upside. A company whose margin has compressed (input cost inflation, suboptimal pricing, operating bloat) is where KKR's playbook can capture step-changes via the Capstone team's sourcing/operations/pricing toolkit. Weisenbeck's Capsugel transformation is the canonical case.
**Source:** Josh Weisenbeck KKR Insights July 2024 (Capsugel from sleepy capsules to drug delivery platform).

#### 6. Capex optimization room (lifecycle-aware)
**Test (refined v0.5):**
  Decompose total capex into approximate maintenance and growth components:
  ```python
  maintenance_capex_proxy = latest_depreciation
  growth_capex_proxy = max(0, latest_capex - maintenance_capex_proxy)
  capex_to_sales = latest_capex / latest_revenue
  growth_share = growth_capex_proxy / latest_capex if latest_capex > 0 else 0
  ```
  Check passes if EITHER:
  - **(a) Growth-capex throttle path:** `growth_share > 0.30 AND capex_to_sales > 0.03` — meaningful growth capex KKR can throttle in early hold years to release FCF for delevering
  - **(b) High-maintenance optimization path:** `capex_to_sales > 0.06 AND revenue_cagr_4y < 0.10` — high total capex in a mature business where Capstone can optimize sourcing/efficiency
  - **(c) Light-asset mature path:** `0.02 <= capex_to_sales <= 0.06 AND revenue_cagr_4y < 0.10 AND latest_ebit_margin < 0.20` — modest capex, mature company, room for incremental discipline
  Check fails if: `capex_to_sales < 0.02` (asset-light, nothing material to optimize) OR (`growth_share < 0.20 AND capex_to_sales < 0.04` — minimal capex with no growth component to throttle)
**Logic:** Capex is the most-cited PE lever but it's heterogeneous. Not every KKR portfolio company has 5%+ capex/sales — software-heavy businesses run at 1-2% and have nothing to optimize on the capex line. Conversely, capital-intensive cement or chemicals businesses at 8%+ have substantial optimization room. The check splits into three pass paths to capture different lifecycle stages:
  - (a) Growth-phase companies where growth capex (above depreciation) is large enough to throttle without killing the growth thesis. KKR's standard play in early hold years is to defer non-critical expansion, release FCF for debt paydown, then re-accelerate in mid-hold.
  - (b) Mature capital-intensive businesses where total capex is high enough that Capstone-driven sourcing improvements and facility efficiency yield material savings even without throttling.
  - (c) Mature companies with modest but non-trivial capex where there's room for incremental discipline.
  The fail conditions specifically exclude asset-light companies (nothing to operate on) and companies with both low total capex AND no growth component to throttle.
**Source:** Capstone team operational playbook; Weisenbeck on factory-floor Kaizen events; lifecycle calibration from Bain Global PE Report 2026.

#### 7. Working capital optimization potential (NEW — classic PE lever)
**Test:**
  - **Hard signal:** `sum(working_capital_change_4y) < -0.05 × mean(revenue_4y)` (company has cumulatively built up working capital by more than 5% of revenue over 4 years — indicates inefficiency to capture). Note: `working_capital_change` in yfinance cash flow statement uses cash-flow sign convention (negative = WC increase = inefficiency).
  - **OR soft signal (LLM-based):** Gemini judges from transcripts/MD&A whether management commentary mentions DSO/DPO/inventory turn issues, channel stuffing recovery, or supplier-term renegotiation opportunities. Returns `wc_optimization_available | already_optimized | unclear`. PASS if `wc_optimization_available`.
  Check passes if either signal indicates available WC optimization.
**Logic:** Working capital compression is one of the most reliable PE levers because it generates one-time cash without affecting reported income. Standard KKR Capstone moves: enforce shorter DSO (collection discipline), extend DPO (supplier-term renegotiation, often via volume leverage), reduce DIO (inventory turn improvement, lean/JIT implementation). For a company with $5B revenue and 15% working capital, compressing WC by 2 percentage points releases $100M of cash — material to LBO returns. The 4-year cumulative test captures companies that have been building inefficiency that KKR can reverse.
**Source:** Standard PE Capstone playbook; Weisenbeck KKR Insights on operational levers; Compendium Part 7.2 (Red Flags by category — inverse signal: companies WITHOUT WC discipline are LBO opportunities).
**Determinism note:** Soft component LLM-dependent. Defaults to using only the hard signal when qualitative unavailable.

#### 8. M&A platform potential (soft, LLM-based)
**Test (soft):** Gemini judges whether the company operates in a fragmented industry with consolidation upside, AND whether the company already has the infrastructure (M&A function, integration playbook, balance sheet headroom) to be a roll-up platform. Returns `platform_potential | bolt_on_only | not_applicable`. PASS if `platform_potential`.
**Logic:** KKR's value creation increasingly comes from bolt-on M&A within a platform thesis. Weisenbeck's Bettcher → Fortifi Food Processing transformation is canonical: acquire a platform, then 33 sites worldwide via bolt-ons. *"We don't just slap together a lot of companies and then try to sell the new entity right away."* The thesis requires fragmented industries (food processing, specialty distribution, healthcare services, industrial coatings, regional consumer brands) where bolt-on multiples are 5-7× EBITDA against platform multiples of 10-12×.
**Source:** Weisenbeck Bettcher / Fortifi case; Compendium Part 1.5 (Thoma Bravo / Vista buy-and-build math).
**Determinism note:** LLM-dependent. Defaults to PASS if no contraindicating evidence — KKR is willing to underwrite a platform thesis at entry if the sector is fragmented enough.

#### 9. Operational revamp + management/board upgrade potential (NEW — classic PE lever)
**Test:**
  - **Quantitative signal (cost optimization room):** `(latest_gross_margin - latest_ebit_margin) > 0.20` (operating costs >20% of revenue, indicating room to optimize SG&A, facility footprint, layers of management) OR `mean(roic_4y) < median industry ROIC` (proxy via Damodaran sector data — current management not extracting industry-typical returns from capital)
  - **OR soft signal (LLM-based):** Gemini judges whether management commentary suggests operational complacency, strategic drift, or governance concerns that KKR could remedy through CEO replacement, operating-partner installation, or board reconstruction. Returns `upgrade_available | management_best_in_class | unclear`. PASS if `upgrade_available`.
  Check passes if either signal flags meaningful upgrade potential.
**Logic:** KKR's distinctive edge here is its Rolodex of operating talent. Canonical cases: Rick Dreiling at Dollar General (recruited to revamp merchandising/operations), Stefano Pessina at Alliance Boots (sponsor-plus-operator structure), Frank Bisignano at First Data (recruited from JPMorgan to overhaul tech/culture). KKR can also reconstruct boards — installing industry-veteran chairs, sector-specialist independent directors, and operating partners with explicit performance mandates. The "operational revamp" piece includes the harder elements: SG&A optimization, layers-of-management reduction, facility consolidation, and yes — selective headcount reduction where layers are bloated. The test requires either quantitative evidence (margin gap, ROIC underperformance) OR qualitative signal that current leadership has room to improve. Companies whose current management is already top-quartile (high ROIC, clean execution, strong commentary discipline) are NOT KKR opportunities on this lever.
**Source:** Compendium Part 5.1 (Kravis lens — operational improvement as the real PE skill); Compendium Parts 2.2 (Hilton/Nassetta), 2.4 (Domino's/Brandon), 2.6 (Alliance Boots/Pessina); Weisenbeck on KKR's investment team being operationally-oriented (Kaizen requirement).
**Determinism note:** Quantitative path is deterministic when ROIC industry-comp data is available; otherwise relies on operating-cost-share calculation. Soft path LLM-dependent.

#### 10. Workforce fit for Stavros employee-ownership model (soft, LLM-based)
**Test (soft):** Gemini reads transcripts and MD&A for indicators of large frontline hourly workforce — manufacturing, logistics, services, retail with significant non-managerial headcount. Returns one of `frontline_heavy | mixed | knowledge_worker_heavy | unclear`. PASS if `frontline_heavy | mixed`; FAIL if `knowledge_worker_heavy` (pure software, asset management, financial services without large frontline workforce).
**Logic:** Stavros's Ownership Works model has been deployed at 80+ companies and produces measurable productivity gains (Ingersoll Rand: 90% quit rate reduction, engagement 19th → 91st percentile). The model requires a large frontline workforce to be impactful — companies with 80% knowledge workers benefit less from broad-based equity programs. *"Half of Americans earn an hourly wage…we don't talk about how stupid it is to compensate by hours instead of outcomes."* (Stavros).
**Source:** Pete Stavros Goldman Sachs Talks Dec 2025; Ownership Works publications; Compendium Part 5.1.
**Determinism note:** LLM-dependent. Defaults to `mixed` (PASS) when qualitative unavailable — most large-cap industrials/services have meaningful frontline headcount.

---

### Part C — Strategic Fit (Checks 11–13)

These checks answer: *does KKR specifically have an angle here, and can the deal mechanics work?*

#### 11. Sector compatibility with KKR playbook
**Test:** `target_industry in KKR_PLAYBOOK_SECTORS`
**Logic:** KKR has institutional playbooks in: Industrials, Healthcare services, Financial services (carry-out/specialty, not control banks), Technology Growth (separate fund), Consumer/Retail, Energy/Power, Real Assets / Infrastructure. Outside these areas — pure software (Thoma Bravo / Vista territory), distressed credit (Apollo / Oaktree territory), pure venture (Sequoia / a16z territory) — KKR is not the natural buyer. The `KKR_PLAYBOOK_SECTORS` list lives alongside the existing `SECTOR_TERMINAL_GROWTH` in `valuation/dcf.py`.

```python
KKR_PLAYBOOK_SECTORS = {
    "Household Products",                # Industrials-adjacent consumer
    "Chemical (Diversified)",
    "Chemical (Specialty)",
    "Food Processing",
    "Tobacco",
    # NOT: Bank (Money Center) — sovereign restrictions
    "Financial Svcs. (Non-bank & Insurance)",
    "Software (System & Application)",   # Core KKR flagship playbook (e.g., BMC, Epicor, Cloudera)
    "Computers/Peripherals",
}
```
**Source:** Stavros Dec 2025 on Americas PE seven sectors; KKR Annual Reports for sector strategy.

#### 12. Willing-seller / public-to-private feasibility (soft, LLM-based)
**Test (soft):** Gemini judges whether the company has indicators of seller willingness or take-private feasibility:
  - Family/founder succession concerns mentioned in transcripts
  - Conglomerate parent signaling divestiture interest
  - Low insider ownership AND board activism pressure
  - Low public-market sponsorship (depressed multiple, weak analyst coverage)
  - Promoter pledge / stake-sale signals (India context)
Returns `willing_seller | strategic_holdout | unclear`. PASS if `willing_seller`; FAIL if `strategic_holdout`.
**Logic:** The most analytically sound LBO is unbuyable if the seller won't sell. Asian Paints is canonical: family-controlled, no take-private signal, strong public-market premium — even if everything else worked, no deal exists.
**Source:** Compendium Part 7.1 question #4; Stavros Dec 2025.
**Determinism note:** LLM-dependent. Defaults to `unclear` (neutral, neither PASS nor FAIL) when qualitative unavailable.

#### 13. No regulatory blocker
**Test:** Hard sector blacklist for control PE:
  - **India**: Banks (RBI caps single-investor ownership/voting rights typically at 10-20%, blocking control buyouts), Defence (FDI cap 74%), Insurance (FDI cap 74% with conditions), regulated infrastructure with single-license dependence
  - **US**: Defense primes (CFIUS scrutiny), regulated utilities (PUC review), broadcast/media (FCC limits)
```python
INDIA_PE_RESTRICTED = {
    "Bank (Money Center)",
}
is_india = ticker.endswith(".NS") or ticker.endswith(".BO")
check_13_passes = not (is_india and target_industry in INDIA_PE_RESTRICTED)
```
**Logic:** Some sectors are simply not investable for control PE due to regulatory restrictions on ownership concentration or foreign control.
**Source:** SEBI Indian banking ownership norms; RBI policy framework.

---

### Part D — Cycle Timing & Returns (Checks 14–17)

These checks answer: *why now, what's the return math, and can we extract interim distributions?*

#### 14. Cycle position (entry timing)
**Test (soft, LLM-based):** Gemini reads transcripts and MD&A for sector cycle position. Returns one of `trough | early_recovery | mid_cycle | late_cycle | peak`. PASS if `trough | early_recovery | mid_cycle`; FAIL if `late_cycle | peak`.
**Logic:** KKR is a buy-and-build PE shop, not a distressed shop. They want to enter at favorable cycle positions where they can grow EBITDA through both operating improvement (cycle-independent) AND cyclical recovery (cycle-dependent). Late-cycle and peak entries compress forward returns even with great execution.
**Source:** Stavros Dec 2025; Master Compendium Part 7.6; Henry McVey KKR outlooks.
**Determinism note:** LLM-dependent. Defaults to PASS (assume `mid_cycle`) when qualitative unavailable.

#### 15. 7-year IRR feasibility (the math sanity check)
**Test:** Projected 7-year IRR at base case > 18%.
Simplified estimator (v0.6+ should add full LBO model in `valuation/lbo.py`):
```python
entry_ev = market_cap + latest_debt
entry_multiple = entry_ev / latest_ebitda
exit_ebitda_assumption = latest_ebitda × 2.0  # "12 is the new 5"
exit_multiple = max(8.0, entry_multiple × 0.85)
exit_ev = exit_ebitda_assumption × exit_multiple
exit_equity = exit_ev - latest_debt × 1.5
entry_equity = market_cap × 0.6
irr_7y = (exit_equity / entry_equity) ** (1/7) - 1
check_15_passes = irr_7y > 0.18
```
**Logic:** A KKR LBO needs to clear ~20% gross IRR at the deal level. The simplified estimator embeds "12 is the new 5" (EBITDA doubles), conservative exit multiple, and standard 40% takeover premium. Companies at very high entry multiples (Asian Paints at ~50× P/E) typically fail because exit multiple compression overwhelms EBITDA growth.
**Source:** Bain Global PE Report 2026; standard LBO underwriting math.
**Calibration note (v0.5 placeholder):** Deliberate approximation. v0.6+ should add proper LBO model with explicit debt schedule, sources & uses, fees, and waterfall economics.

#### 16. Dividend recap potential (NEW — interim return extraction)
**Test:**
  All three sub-conditions must hold:
  - `min(fcf_4y) > 0` (FCF positive every year — predictable cash for additional debt service)
  - `stdev(fcf_4y) / mean(fcf_4y) < 0.35` (FCF stability — coefficient of variation under 35%; less than ~one-third volatility)
  - For US: `latest_ebitda > $100M`; for India: `latest_ebitda > ₹200cr` (deal size meaningful enough that 1-2× EBITDA recap debt yields a material dividend in absolute terms)
**Logic:** Post-stabilization (typically 2-3 years into the hold), KKR can take on additional debt and pay itself a dividend, locking in returns regardless of exit outcome. Standard recap: company at 4-5× total leverage post-LBO can raise to 6-7× and distribute the proceeds. This requires FCF stability (debt-service confidence) and meaningful scale (so the absolute recap dividend is material). A company with $200M EBITDA supporting 1.5× recap debt = $300M dividend; at 60% equity sponsor split, that's ~$180M back to LPs before exit — a substantial interim distribution. Companies with cyclical or volatile FCF are NOT recap candidates because the additional debt would not be reliably serviceable through troughs.
**Source:** Standard PE financial engineering; Buffett's 2014 letter discusses critique of recap practice ("re-leverage with new borrowings…they typically use part of the proceeds to pay a huge dividend that drives equity sharply downward, sometimes even to a negative figure") — useful counter-context for when recap is appropriate vs aggressive.

#### 17. "Why now" / specific entry catalyst (soft, LLM-based)
**Test (soft):** Gemini judges whether there is a specific catalyst making *now* the entry moment. Returns `catalyst_present | normal_cycle | unclear`. PASS if `catalyst_present` with specific event named (corporate divestiture, regulatory shift, founder succession event, sector inflection, take-private window opening, competitor exiting); FAIL otherwise.
**Logic:** KKR is more flexible than Marks here. Marks requires *dislocation* (post-shock, distressed). KKR accepts *catalyst* (anything that creates a willing-seller or favorable-entry dynamic). *"Why now"* must be answerable in one specific sentence.
**Source:** Master Compendium Part 7.6; KKR India travel notes (Feb 2024, Feb 2026) for examples of identified India-specific catalysts.
**Determinism note:** LLM-dependent. Defaults to FAIL when qualitative unavailable.

---

### Part E — Defensibility vs the Phalippou Bar (Check 18)

This Part answers: *does the deal-specific thesis have enough KKR-edge characteristics to justify the PE risk premium that Phalippou's data challenges?* **This is the skeptic's check.**

#### 18. Above-average PE alpha thesis (NEW — Phalippou meta-check)
**Test (meta-check across Part B):**
```python
kkr_edge_checks_passed = sum([
    check_5_passed,   # margin improvement room
    check_7_passed,   # working capital optimization
    check_8_passed,   # M&A platform potential
    check_9_passed,   # operational revamp + mgmt/board upgrade
    check_10_passed,  # workforce fit for Stavros equity
    check_16_passed,  # dividend recap potential
])
check_18_passes = kkr_edge_checks_passed >= 4  # at least 4 of 6 KKR alpha levers must work
```
Note: Check 6 (capex) is intentionally NOT included — capex optimization is table-stakes for every LBO, not an above-average edge.

**Logic:** Ludovic Phalippou's "An Inconvenient Fact: Private Equity Returns & The Billionaire Factory" (2020) demonstrated that **average net returns to LPs across all PE funds since 2006 roughly match public equity indices** — implied ~11% p.a. The big-four PE firms (presumably including KKR) deliver net MoMs in the 1.54-1.67 range, and the broader industry sits at 1.55-1.63 MoM. These are *not* materially above public-equity benchmarks once you adjust for risk and illiquidity.

KKR's track record (per Stavros Dec 2025: ~20% net over 15 years, several hundred bps above competitors) is above-average specifically *because* they stack multiple value-creation levers per deal. The implication for any specific deal under consideration: if only one or two of KKR's edge levers work (margin room only, or M&A only), the deal is generic PE and won't differentiably beat the public-equity benchmark net of fees. KKR's lens should require **at least 4 of 6 alpha levers** working to justify the underwrite.

This is not a hypothetical bar — it's the empirical floor. A deal that passes everything else in the framework but fails this check is one where KKR would generate roughly market-equivalent returns net of fees, which is not a deal worth taking the PE risk premium for.

**Source:** Ludovic Phalippou, "An Inconvenient Fact: Private Equity Returns & The Billionaire Factory" (2020), Said Business School, University of Oxford. In `knowledge/New additions/An-Inconvenient-Fact.md`. Also Stavros Dec 2025 transcript ("hundreds and hundreds, in some cases a thousand basis points of return over the last 15 years relative above our most significant competitors") — the explicit acknowledgment that being above-average is a function of repeatable above-average lever-stacking, not luck.

**Calibration note:** The 4-of-6 threshold is calibrated against the median PE deal. A deal at 2-of-6 is below-average; 3-of-6 is roughly median; 4+/-6 is above-average. KKR (and any sophisticated buyer) should not write checks at the median bar given the fee structure and illiquidity costs.

---

## Scoring & Verdict Logic

```
score = sum of checks 1–18 that pass (max 18)

PRE-CONDITION 1: Part A all 4 must pass (LBO viability is non-negotiable).
PRE-CONDITION 2: Check 18 must pass (Phalippou defensibility).
If either pre-condition fails: verdict = "SKIP" regardless of other checks.

VERDICT (after pre-conditions):
  if score >= 15:                                    "BUY"
  elif score >= 13 and not check_12_passes:          "WAIT (seller not willing)"
  elif score >= 13 and not check_14_passes:          "WAIT (wrong cycle moment)"
  elif score >= 13:                                  "WATCH"
  else:                                              "SKIP"
```

**Calibration notes:**
- Two pre-conditions (Part A all-pass + Check 18 pass) reflect that LBO viability and above-average alpha are non-negotiable. KKR will not write a check that fails either.
- BUY (15+/18) means: LBO-viable, multiple Part B levers working, sector fit, willing seller, right cycle, IRR math clears, defensible vs Phalippou bar. High-conviction KKR target.
- WAIT semantic preserved: LBO-able and alpha-defensible, but wrong seller dynamics or wrong cycle moment. Set watchlist on either condition.
- WATCH: mixed signals across Part B/C/D; not a clear KKR target but worth monitoring.
- SKIP: failed Part A (not LBO-able), failed Check 18 (generic PE thesis without enough KKR edge), or too many other failed checks.

**Critical scoring rule (no methodology hacking):** Same rule as Buffett and Marks lenses. The verdict is whatever the math produces. Do not tune thresholds — including the 4-of-6 in Check 18 — toward a desired outcome on any specific ticker.

---

## How This Lens Differs from Buffett and Marks

| Dimension | Buffett | Marks | **KKR** |
|-----------|---------|-------|---------|
| **First question** | Is this a great business I can hold forever? | What's the downside, and is it survivable? | **Can we double EBITDA over 7 years and stack ≥4 value-creation levers?** |
| **Hold horizon** | 10–20+ years ("forever") | Until value is realized | **5–7 years (or 20 for Core vehicle)** |
| **Source of returns** | Compounding at high ROIC | Mispricing close on entry | **Operating improvement + bolt-on M&A + leverage + recap** |
| **Price discipline** | 25% MoS | 40% MoS | **Implicit via 7-year IRR > 18%** |
| **Workforce relevance** | Capital allocation by mgmt | Risk architecture | **Frontline workforce for Stavros equity program** |
| **Cycle awareness** | Largely ignores | Cycle position is primary | **Cycle position matters but secondary to operational thesis** |
| **Who is the seller?** | Doesn't matter (we buy from market) | Doesn't matter (we buy from market) | **Critical — must be willing-seller, not strategic-holdout** |
| **Critical counter-test** | Margin of safety | Asymmetric payoff + cycle | **Phalippou defensibility — must stack ≥4 of 6 alpha levers** |
| **Lens applicability** | Any public quality compounder | Any mispriced security | **Public-to-private candidates with operational upside** |

**Implication for composite verdict (Phase 5+):** This is the third operational lens. Patterns to expect:

- **Buffett BUY + KKR SKIP**: Quality compounder at fair price, but family-controlled or no operational upside. Asian Paints is canonical.
- **KKR BUY + Buffett SKIP**: Operationally improvable company with willing seller and good LBO math, but moat/predictability fail Buffett's quality bars. Typical industrials carve-out.
- **Marks BUY + KKR SKIP**: Mispriced distressed name with deep MoS but no operational improvement path KKR has a playbook for. Marks would trade; KKR would let Apollo or Oaktree have it.
- **All three BUY**: Extraordinarily rare. Quality compounder + cyclical opportunity + LBO viability + willing seller + ≥4 alpha levers. Historically: Hilton (post-GFC 2009), Bharti Tele-Ventures (Warburg 1999).
- **All three SKIP**: Premium business at peak valuation, family-controlled, no catalyst, no dislocation, only 1-2 alpha levers. Asian Paints in 2026 currently fits this pattern.

The composite verdict logic from `marks.md` extends naturally: preserve all three verdicts side-by-side in the report.

---

## Output Format (each check in the report)

```
PART A — LBO Viability (pre-condition; all 4 must pass)
[✅/❌] 1. EBITDA scale                       pass: ₹X.XB > ₹4.0B threshold
[✅/❌] 2. FCF conversion                     pass: 4y avg = 67% > 60%
[✅/❌] 3. Leverage capacity                  pass: Debt/EBITDA = 0.36x < 3.0x
[✅/❌] 4. EBITDA margin                      pass: 18.4% > 15%

PART B — Operational Upside
[✅/❌] 5. Margin improvement room            fail: at 4y peak (no compression to reverse)
[✅/❌] 6. Capex optimization (lifecycle)     pass: 5.4% capex/sales w/ 35% growth share
[✅/❌] 7. Working capital optimization       fail: WC already efficient (no buildup over 4y)
[✅/❌] 8. M&A platform potential             pass: platform_potential via LLM
[✅/❌] 9. Operational revamp + mgmt upgrade  fail: current management top-quartile execution
[✅/❌] 10. Workforce fit (Stavros)            pass: frontline_heavy via LLM

PART C — Strategic Fit
[✅/❌] 11. Sector compatibility               pass: Household Products in KKR_PLAYBOOK_SECTORS
[✅/❌] 12. Willing-seller dynamic             fail: family-controlled, no signal
[✅/❌] 13. No regulatory blocker              pass: not in INDIA_PE_RESTRICTED

PART D — Cycle Timing & Returns
[✅/❌] 14. Cycle position                     fail: late_cycle per qualitative
[✅/❌] 15. 7-year IRR feasibility             fail: estimated IRR = 11% < 18%
[✅/❌] 16. Dividend recap potential           pass: stable FCF, scale, leverage room
[✅/❌] 17. "Why now" catalyst                 fail: normal_cycle, no specific event

PART E — Defensibility vs Phalippou Bar (pre-condition)
[✅/❌] 18. Above-average PE alpha thesis      fail: only 3 of 6 alpha levers (5❌, 7❌, 8✅, 9❌, 10✅, 16✅)

PART A (LBO viability):           4/4 PASS ✅ (pre-condition met)
PART B (operational upside):      3/6 passed
PART C (strategic fit):           2/3 passed
PART D (timing & returns):        1/4 passed   ← weakness here
PART E (Phalippou defensibility): 0/1 PASS — pre-condition FAILED ❌

TOTAL: 10/18
VERDICT: SKIP — fails Phalippou defensibility pre-condition. Only 3 of 6
operational alpha levers active. Even with LBO viability, this is a
median-PE-deal at best — won't beat public equity net of fees per
Phalippou's data on average PE returns. Specifically: no margin
compression to reverse (Asian Paints already best-in-class operator),
working capital already efficient, current management already top-quartile.
KKR's edge stack doesn't apply to this name.
```

The Asian Paints pattern under this lens is particularly instructive: Part A (LBO viability) passes cleanly because the financials are pristine, but Part E fails precisely because the company is already so well-run that there's no operational alpha for KKR to add. **This is the case where "great company" and "great PE target" diverge** — and the Phalippou check formalizes the divergence.

---

## Sources for Further Encoding

**Primary (KKR's own writing and interviews):**
- KKR Annual Reports 2024-2026 (in `knowledge/Reports/KKR/`) — Henry Kravis + Joe Bae shareholder letters
- Pete Stavros, Goldman Sachs Talks at GS interview (Dec 2025) — *the* canonical statement of current KKR PE worldview, including Ownership Works, culture, geographic priorities (in `knowledge/New additions/kkr pete stravos.md`)
- Josh Weisenbeck, "Value Creation in Private Equity: Making Our Own Luck" (July 2024, KKR Insights) — Industrials value-creation playbook with Capsugel and Bettcher cases
- "Staying on Course in Private Equity" (KKR Insights) — cycle discipline
- KKR mid-year and annual outlooks 2024-2026 — Henry McVey macro/regime views
- "Thoughts from the Road: India" (Feb 2024, Feb 2026) — India-specific thesis

**Adjacent (PE strategy and case studies):**
- Bryan Burrough & John Helyar, *Barbarians at the Gate* (1989/2003) — canonical KKR/RJR case
- Master Investment Compendium Part 5.1 (Henry Kravis lens), Part 1.1 (RJR), Part 1.3 (Carve-outs), Part 2.1 (RJR win), Part 2.2 (Hilton/Blackstone — operator-recruitment case relevant cross-reference), Part 2.4 (Domino's/Bain — brand reset case), Part 2.6 (Alliance Boots/Pessina — sponsor-plus-operator model), Part 7 (personal screening framework)
- Bain Global Private Equity Report 2026 — *"12 is the new 5"* frame

**Critical/academic counterweight (now operationalized in Check 18):**
- Ludovic Phalippou, "An Inconvenient Fact: Private Equity Returns & The Billionaire Factory" (2020), Said Business School, Oxford. In `knowledge/New additions/An-Inconvenient-Fact.md`. The empirical foundation for Check 18's "4 of 6 alpha levers" threshold. Phalippou's data: PE net MoMs 1.51-1.67 across big four firms, 1.55-1.63 across the broader industry — implying ~11% p.a. net to LPs, matching public-equity indices since 2006. The implication: any specific PE deal must have multiple alpha levers stacked to outperform net of fees.

**Operationalization references:**
- Ownership Works non-profit publications (Stavros's policy work) — operational details of broad-based employee equity programs
- KKR Capstone team published case studies (where available)
- DealRoom historic largest-LBO data (cross-reference for deal-size calibration)

**Buffett counter-perspective (useful for Check 16 calibration):**
- Buffett 2014 letter on PE recap practice — provides the skeptic's view of dividend recapitalizations as value extraction vs value creation. The lens uses recap potential as a positive signal (KKR can extract returns) but is honest that Buffett would view aggressive recaps negatively. Useful context.
