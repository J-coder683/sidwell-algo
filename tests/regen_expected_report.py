"""Generates tests/expected_report.md from the fixture pipeline. Run once after schema changes."""
from datetime import datetime
from pathlib import Path
from valuation.dcf import run_dcf_valuation
from lenses.buffett import evaluate_buffett_lens
from lenses.marks import evaluate_marks_lens
from reports.render import render_markdown_report
from tests.fixture_company import FIXTURE_INPUTS, FIXTURE_MACRO, FIXTURE_RISK_FREE_RATE
import shutil, os

MOCK_QUALITATIVE = {
    "status": "available",
    "model": "gemini-3.5-flash",
    "documents_used": ["fixture_concall.pdf"],
    "forward_guidance": [
        {"period": "FY27", "metric": "revenue",
         "statement": "Management expects 10% revenue growth driven by capacity expansion.",
         "source_doc": "fixture_concall.pdf"}
    ],
    "risk_callouts": [
        {"risk": "input cost volatility",
         "context": "Raw material prices remain a watchpoint.",
         "source_doc": "fixture_concall.pdf"}
    ],
    "strategic_themes": [
        {"theme": "premium product mix",
         "evidence": "Mix shift toward premium SKUs continues.",
         "source_doc": "fixture_concall.pdf"}
    ],
    "tone_assessment": {
        "current": "confident", "trajectory": "stable",
        "notes": "Management remained confident across the period, with a stable narrative."
    },
    "coherence_assessment": {
        "verdict": "coherent",
        "reasoning": "Numeric claims tie out across documents and strategy is consistent."
    },
    "owner_orientation_signal": {
        "verdict": "owner_oriented",
        "evidence": "Letter uses 'shareholders as partners' framing; admits two FY24 mis-allocations by name."
    },
    "holdability_assessment": {
        "verdict": "holdable_20y",
        "reasoning": "Demand category structurally enduring; no single-technology dependence identified in documents."
    },
    "cycle_position": {
        "sector_cycle": "mid_cycle", "company_cycle": "mid",
        "reasoning": "Capacity utilization mid-band; pricing actions modest; no signs of peak-cycle euphoria."
    },
    "variant_perception": {
        "consensus_view": "Market expects continued strong growth driven by premiumisation.",
        "company_view": "Management guides modest growth, citing cyclical headwinds and competitive intensity.",
        "variant_present": True, "specificity": "high",
        "notes": "Specific mechanism: regional capacity ramp ahead of demand normalization creates a timing variant that consensus models do not capture."
    },
    "management_humility": {
        "verdict": "humble",
        "evidence": "Management declines multi-year forecast; acknowledges raw material visibility limited to 2 quarters; references two past allocation errors by name."
    },
    "why_now_signal": {
        "verdict": "dislocation_present",
        "specific_event": "Post-Q3 FY26 commodity-cost shock has compressed multiples temporarily.",
        "notes": "Sector has de-rated 25% in trailing 12 months; entry timing favorable due to forced selling from FII redemptions, not fundamental deterioration."
    }
}

if __name__ == "__main__":
    financials = FIXTURE_INPUTS.copy()
    macro = FIXTURE_MACRO.copy()
    rf = FIXTURE_RISK_FREE_RATE

    dcf_res = run_dcf_valuation(financials, macro, rf)
    buffett_res = evaluate_buffett_lens(financials, dcf_res, qualitative_results=MOCK_QUALITATIVE)
    marks_res = evaluate_marks_lens(financials, dcf_res, qualitative_results=MOCK_QUALITATIVE)

    frozen_date = datetime(2026, 1, 1, 0, 0, 0)
    tmp_dir = Path("tests/_regen_tmp")
    report_path = render_markdown_report(
        dcf_res, buffett_res, financials,
        qualitative_results=MOCK_QUALITATIVE,
        marks_results=marks_res,
        generated_at=frozen_date,
        output_dir=tmp_dir
    )

    generated = report_path.read_text(encoding="utf-8")
    dest = Path("tests/expected_report.md")
    dest.write_text(generated, encoding="utf-8")

    # Cleanup temp dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"expected_report.md regenerated ({len(generated)} chars)")
    print(f"Buffett: {buffett_res['score']}/14 -> {buffett_res['verdict']}")
    print(f"Marks:   {marks_res['score']}/14 -> {marks_res['verdict']}")
