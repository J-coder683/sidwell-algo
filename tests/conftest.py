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
            "sector_cycle": "mid_cycle",
            "company_cycle": "mid",
            "reasoning": "Capacity utilization mid-band; pricing actions modest; no signs of peak-cycle euphoria."
        },
        "variant_perception": {
            "consensus_view": "Market expects continued strong growth driven by premiumisation.",
            "company_view": "Management guides modest growth, citing cyclical headwinds and competitive intensity.",
            "variant_present": True,
            "specificity": "high",
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
