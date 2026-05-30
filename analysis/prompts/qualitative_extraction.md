# Qualitative Extraction Prompt v0.10

You are an investment analyst extracting structured insights from company
documents. Read all the documents provided below. Return ONLY a JSON object
matching the schema below — no preamble, no commentary, no markdown wrappers.

## Required JSON schema

{
  "forward_guidance": [
    {"period": "...", "metric": "revenue|margin|capex|volume|other",
     "statement": "verbatim or paraphrased, max 2 sentences",
     "source_doc": "filename"}
  ],
  "risk_callouts": [
    {"risk": "short label", "context": "what was said, max 2 sentences",
     "source_doc": "filename"}
  ],
  "strategic_themes": [
    {"theme": "short label", "evidence": "what was said, max 2 sentences",
     "source_doc": "filename"}
  ],
  "tone_assessment": {
    "current": "confident | cautious | defensive | evasive | inconsistent",
    "trajectory": "improving | stable | deteriorating | unclear",
    "notes": "one paragraph (3-5 sentences)"
  },
  "coherence_assessment": {
    "verdict": "coherent | incoherent",
    "reasoning": "one paragraph"
  },
  "owner_orientation_signal": {
    "verdict": "owner_oriented | management_class | unclear",
    "evidence": "one paragraph citing specific language patterns from the documents — partnership framing, candor about mistakes, long-term focus vs short-term metric games"
  },
  "holdability_assessment": {
    "verdict": "holdable_20y | uncertain | not_holdable_20y",
    "reasoning": "one paragraph. Holdable_20y = business model resilient to obvious 20-year disruption (durable customer need, hard to disintermediate). Not_holdable = single-technology or single-regulatory dependency that could shift in 20 years. Uncertain = mixed signals."
  },
  "cycle_position": {
    "sector_cycle": "trough | early_recovery | mid_cycle | late_cycle | peak",
    "company_cycle": "early | mid | late",
    "reasoning": "one paragraph identifying signals: capacity utilization, pricing trends, M&A activity in sector, demand commentary"
  },
  "variant_perception": {
    "consensus_view": "one sentence — what the market/analyst consensus believes about this company",
    "company_view": "one sentence — what management's actual outlook is",
    "variant_present": true,
    "specificity": "high | medium | low",
    "notes": "one paragraph. Variant present + high specificity means there is a clearly articulated non-consensus thesis with a specific operational/financial mechanism — not just 'AI tailwind.'"
  },
  "management_humility": {
    "verdict": "humble | hubristic | unclear",
    "evidence": "one paragraph citing specific examples: acknowledging uncertainty, refusing to give multi-year forecasts they can't defend, admitting past mistakes, NOT making bold macro predictions"
  },
  "why_now_signal": {
    "verdict": "dislocation_present | normal_cycle | catalyst_present | unclear",
    "specific_event": "one sentence — name the event creating opportunity: post-shock, post-distress, post-management-change, regulatory shift, or 'no specific dislocation'",
    "notes": "one paragraph elaborating"
  },
  "willing_seller_signal": {
    "verdict": "founder_succession | corporate_carveout | distress | unclear",
    "notes": "one sentence"
  },
  "ma_platform_potential": {
    "verdict": "high | low | unclear",
    "notes": "fragmented industry with roll-up opportunity"
  },
  "workforce_stavros_fit": {
    "verdict": "high_labor_intensity | low_labor_intensity | unclear",
    "notes": "one sentence"
  },
  "mgmt_upgrade_potential": {
    "verdict": "high | low | unclear",
    "notes": "one sentence"
  },
  "wc_optimization_signal": {
    "verdict": "high | low | unclear",
    "notes": "one sentence"
  },
  "structural_tailwind_signal": {
    "verdict": "present | absent | unclear",
    "notes": "one sentence"
  },
  "multi_product_engagement_signal": {
    "verdict": "high | low | unclear",
    "notes": "one sentence"
  },
  "chaos_dislocation_catalyst": {
    "verdict": "present | absent | unclear",
    "notes": "one sentence"
  },
  "fulcrum_security_signal": {
    "verdict": "present | absent | unclear",
    "notes": "one sentence"
  },
  "abf_credit_fit": {
    "verdict": "high | low | unclear",
    "notes": "one sentence"
  },
  "complexity_moat_signal": {
    "verdict": "high | low | unclear",
    "notes": "one sentence"
  },
  "permanent_hold_viable": {
    "verdict": "yes | no | unclear",
    "notes": "one sentence"
  },
  "covenant_control_potential": {
    "verdict": "high | low | unclear",
    "notes": "one sentence"
  },
  "ajp": {
    "meta": {
      "ticker": "BBTC.NS",
      "as_of": "2026-05-29",
      "currency": "INR_MM",
      "sources_ingested": ["list of filenames"],
      "fiscal_year_end_month": 3,
      "last_actual_fy": "FY2025",
      "is_holdco": true,
      "scenario_active": "BASE"
    },
    "assumptions": [
      {
        "driver_id": "stage1_revenue_growth",
        "value": 0.085,
        "unit": "ratio",
        "scenario": { "BEAR": 0.05, "BASE": 0.085, "BULL": 0.11 },
        "split": { "volume": 0.055, "price": 0.03 },
        "source_type": "MGMT_GUIDANCE",
        "confidence": "HIGH",
        "rationale": "Quote/paraphrase the specific guidance and the page/call timestamp.",
        "interrogation_refs": ["1.1"]
      }
      // HOW MANY TO OUTPUT:
      //  * ALWAYS output the SIX CORE drivers with your best document-grounded BASE
      //    value — an annual report plus three concalls always give enough to form a
      //    defensible view. Use "confidence" (HIGH/MEDIUM/LOW) to flag how firm it is,
      //    and the rationale to cite the evidence. The six core drivers are:
      //      stage1_revenue_growth, ebit_margin_target, capex_pct_sales_target,
      //      tax_rate, terminal_growth, exit_ev_ebitda_multiple
      //  * Output the OPTIONAL drivers ONLY when the documents disclose them; omit the
      //    rest (the engine then falls back to the company's own history — never guess
      //    on the optional ones).
      // Percentages are decimals (0.085 = 8.5%). Always include source_type, confidence
      // and a rationale citing specific evidence; give a scenario {BEAR,BASE,BULL} when
      // the framing supports a range.
      //
      // === DRIVER REFERENCE (the six core driver_ids named above are REQUIRED;
      //     everything else here is OPTIONAL — output only if disclosed) ===
      //
      // --- GROWTH & MARGINS ---
      //   stage1_revenue_growth   unit "ratio" — near-term (1-3y) growth. Add "split":{volume,price}
      //                           when management separates them (pricing power is a key signal).
      //                           (The engine fades this to terminal_growth over years 4-10.)
      //   ebit_margin_target      unit "ratio" — the operating-margin level they are steering to, the
      //                           DRIVER (mix / operating leverage / cost programme) and the timeline.
      //   da_rate_on_block        unit "ratio" — depreciation as a % of the net fixed-asset base, if guided.
      //   tax_rate                unit "ratio" — guided / normalized effective tax rate.
      //
      // --- INVESTMENT & WORKING CAPITAL ---
      //   capex_pct_sales_target  unit "ratio" — forward capex % of sales. If they signalled EXPANSION
      //                           (new plants/factories, capacity, a large project/order pipeline), set it
      //                           ABOVE the historical ratio and cite the plan, amount and timeline.
      //   dso_days / dio_days / dpo_days   unit "days" — receivable / inventory / payable terms, if discussed.
      //
      // --- TERMINAL VALUE & CAPITAL STRUCTURE ---
      //   terminal_growth         unit "ratio" — long-run growth, must be <= long-run nominal GDP.
      //   exit_ev_ebitda_multiple unit "x" — a DEFENSIBLE terminal EV/EBITDA exit multiple justified by the
      //                           company's quality and sector (do not leave it at a generic 10x).
      //   target_debt_to_cap      unit "ratio" — management's intended long-run debt / (debt + equity), if stated.
      //   pretax_cost_of_debt_override  unit "ratio" — only if they disclose their actual borrowing rate.
      //
      // --- EV -> EQUITY BRIDGE (only if the filings DISCLOSE these; values in INR_MM, source_type FILING) ---
      //   preferred_stock, unfunded_pension, nols
      //   (Cash, total debt, minority interest and investments are taken from the scraped balance
      //    sheet automatically — do NOT output those.)
      //
      // --- DILUTION (use the special fields, not "value") ---
      //   options_outstanding   add field "options_outstanding": [{ "shares": <count>, "strike_price": <Rs> }, ...]
      //   rsus_psus_outstanding unit "shares" — "value" = count of unvested RSUs/PSUs.
      //
      // --- HOLDCO / SUM-OF-THE-PARTS (only when meta.is_holdco = true) ---
      //   segments         add field "segments": [{ "name": "...", "valuation_method": "stake|consol",
      //                    "stake_pct": 0.51, "value_mm": <INR_MM> }, ...] for each listed/material stake.
      //   holdco_discount  unit "ratio" — the conglomerate discount management/analysts reference.
    ]
  }
}

## Rules

- Do NOT invent content not in the documents. Every item must trace to source documents.
- If a section has no findings, return an empty array (for list fields) or "unclear" / null (for verdict fields).
- Cite source documents by filename exactly as provided.
- Keep text fields concise. Max 2 sentences for items; max 5 sentences for paragraphs.
- Do NOT include any text outside the JSON object.
- The new verdicts (owner_orientation, holdability, cycle, etc.) may legitimately be "unclear" / "uncertain" — return that honestly rather than guessing.

## Documents

{documents_text}
