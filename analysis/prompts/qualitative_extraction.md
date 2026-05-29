# Qualitative Extraction Prompt v0.5

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
