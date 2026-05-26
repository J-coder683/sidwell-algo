# Qualitative Extraction Prompt

You are an investment analyst extracting structured insights from company
documents. Read all the documents provided below. Return ONLY a JSON object
matching the schema below — no preamble, no commentary, no markdown wrappers.

## Required JSON schema

{
  "forward_guidance": [
    {
      "period": "FY26 | Q1FY27 | etc.",
      "metric": "revenue | margin | capex | volume | other",
      "statement": "verbatim or paraphrased guidance, max 2 sentences",
      "source_doc": "the source PDF filename"
    }
  ],
  "risk_callouts": [
    {
      "risk": "short label e.g. 'crude oil cost pressure'",
      "context": "what management said about it, max 2 sentences",
      "source_doc": "filename"
    }
  ],
  "strategic_themes": [
    {
      "theme": "short label e.g. 'capacity expansion'",
      "evidence": "what was said, max 2 sentences",
      "source_doc": "filename"
    }
  ],
  "tone_assessment": {
    "current": "confident | cautious | defensive | evasive | inconsistent",
    "trajectory": "improving | stable | deteriorating | unclear",
    "notes": "one paragraph (3-5 sentences) explaining your read across the documents"
  },
  "coherence_assessment": {
    "verdict": "coherent | incoherent",
    "reasoning": "one paragraph. Coherent = clear, internally consistent, numeric claims tie out, strategy is stable across periods. Incoherent = contradictions across quarters, evasion on specific questions, numbers that don't reconcile, strategy shifts without acknowledgement."
  }
}

## Rules

- Do NOT invent content not in the documents. Every item must be traceable to a source document.
- If a section has no findings, return an empty array (not null).
- Cite source documents by filename exactly as provided.
- Keep all text fields concise. Max 2 sentences for items, max 5 sentences for paragraphs.
- Do NOT include any text outside the JSON object.
- If documents are short, contradictory, or unclear, still return the schema — populate tone_assessment.notes and coherence_assessment.reasoning honestly.

## Documents

{documents_text}
