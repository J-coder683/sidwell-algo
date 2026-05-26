import pytest
from tests.fixture_company import FIXTURE_INPUTS

@pytest.fixture
def mock_financials():
    return FIXTURE_INPUTS.copy()

@pytest.fixture
def mock_qualitative():
    return {
        "status": "available",
        "model": "gemini-1.5-flash",
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
        }
    }
