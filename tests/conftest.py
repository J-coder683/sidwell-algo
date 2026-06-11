import pytest
from tests.fixture_company import FIXTURE_INPUTS

@pytest.fixture
def mock_financials():
    return FIXTURE_INPUTS.copy()

@pytest.fixture
def mock_qualitative():
    """
    Full v0.3 qualitative fixture. Engineered so all 9 new fields are populated
    and produce clean PASS on every soft check in both lenses.
    v0.12: confidence='high' and evidence_quote added to all verdict-bearing signals.
    """
    return {
        "status": "available",
        "model": "gemini-3.5-flash",
        "documents_used": ["fixture_concall.pdf"],
        "forward_guidance": [
            {
                "period": "FY27",
                "metric": "revenue",
                "statement": "Management expects 10% revenue growth driven by capacity expansion.",
                "source_doc": "fixture_concall.pdf"
            }
        ],
        "risk_callouts": [
            {
                "risk": "input cost volatility",
                "context": "Raw material prices remain a watchpoint.",
                "source_doc": "fixture_concall.pdf"
            }
        ],
        "strategic_themes": [
            {
                "theme": "premium product mix",
                "evidence": "Mix shift toward premium SKUs continues.",
                "source_doc": "fixture_concall.pdf"
            }
        ],
        "tone_assessment": {
            "current": "confident",
            "trajectory": "stable",
            "notes": "Management remained confident across the period, with a stable narrative."
        },
        "coherence_assessment": {
            "verdict": "coherent",
            "reasoning": "Numeric claims tie out across documents and strategy is consistent.",
            "evidence_quote": "Revenue and EBITDA guidance reconcile to filings within 2% [fixture_concall.pdf]",
            "confidence": "high",
        },
        "owner_orientation_signal": {
            "verdict": "owner_oriented",
            "evidence": "Letter uses 'shareholders as partners' framing; admits two FY24 mis-allocations by name.",
            "evidence_quote": "We treat our shareholders as long-term partners [fixture_concall.pdf]",
            "confidence": "high",
        },
        "holdability_assessment": {
            "verdict": "holdable_20y",
            "reasoning": "Demand category structurally enduring; no single-technology dependence identified in documents.",
            "evidence_quote": "Category demand is structural, driven by urbanization not discretionary spending [fixture_concall.pdf]",
            "confidence": "high",
        },
        "cycle_position": {
            "sector_cycle": "mid_cycle",
            "company_cycle": "mid",
            "reasoning": "Capacity utilization mid-band; pricing actions modest; no signs of peak-cycle euphoria.",
            "evidence_quote": "Utilization at 72%, pricing flat for two quarters [fixture_concall.pdf]",
            "confidence": "high",
        },
        "variant_perception": {
            "consensus_view": "Market expects continued strong growth driven by premiumisation.",
            "company_view": "Management guides modest growth, citing cyclical headwinds and competitive intensity.",
            "variant_present": True,
            "specificity": "high",
            "notes": "Specific mechanism: regional capacity ramp ahead of demand normalization creates a timing variant that consensus models do not capture.",
            "evidence_quote": "We guide 8-10% volume growth vs Street's 15% [fixture_concall.pdf]",
            "confidence": "high",
        },
        "management_humility": {
            "verdict": "humble",
            "evidence": "Management declines multi-year forecast; acknowledges raw material visibility limited to 2 quarters; references two past allocation errors by name.",
            "evidence_quote": "We cannot give you a 3-year number with integrity [fixture_concall.pdf]",
            "confidence": "high",
        },
        "why_now_signal": {
            "verdict": "dislocation_present",
            "specific_event": "Post-Q3 FY26 commodity-cost shock has compressed multiples temporarily.",
            "notes": "Sector has de-rated 25% in trailing 12 months; entry timing favorable due to forced selling from FII redemptions, not fundamental deterioration.",
            "evidence_quote": "Sector de-rated 25% in 12 months on input cost fears [fixture_concall.pdf]",
            "confidence": "high",
        },
        "structural_tailwind_signal": {
            "verdict": "tailwind",
            "notes": "Urbanization driving structural demand.",
            "evidence_quote": "Urbanization will drive category growth for decades [fixture_concall.pdf]",
            "confidence": "high",
        },
        "multi_product_engagement_signal": {
            "verdict": "multi_product_potential",
            "notes": "Adjacent categories identified.",
            "evidence_quote": "Expanding into adjacent home improvement categories [fixture_concall.pdf]",
            "confidence": "high",
        },
        "chaos_dislocation_catalyst": {
            "verdict": "chaos_present",
            "notes": "Sector dislocation from FII selling.",
            "evidence_quote": "FII redemptions have created forced selling in the sector [fixture_concall.pdf]",
            "confidence": "high",
        },
        "fulcrum_security_signal": {
            "verdict": "fulcrum_identified",
            "notes": "Senior secured first-charge.",
            "evidence_quote": "Senior lenders hold first charge over fixed assets [fixture_concall.pdf]",
            "confidence": "high",
        },
        "abf_credit_fit": {
            "verdict": "abf_primary_opportunity",
            "notes": "Asset-backed structure available.",
            "evidence_quote": "Fixed assets provide tangible collateral for ABF structure [fixture_concall.pdf]",
            "confidence": "high",
        },
        "complexity_moat_signal": {
            "verdict": "high",
            "notes": "Multi-jurisdiction licensing.",
            "evidence_quote": "Multi-state regulatory approvals create a meaningful barrier [fixture_concall.pdf]",
            "confidence": "high",
        },
        "covenant_control_potential": {
            "verdict": "covenant_rich_opportunity",
            "notes": "Bank-funded with maintenance covenants.",
            "evidence_quote": "Primarily bank-funded with quarterly maintenance covenants [fixture_concall.pdf]",
            "confidence": "high",
        },
    }

