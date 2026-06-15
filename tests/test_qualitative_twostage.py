import json
import os
from unittest.mock import patch, MagicMock
from analysis.qualitative import extract_qualitative, MODEL_NAME

_DOCS = [{"url": "http://example.com/ar.pdf", "type": "annual_report", "label": "AR"}]
_TICKER = "TEST"

def _mock_req():
    r = MagicMock()
    r.content = b"fake pdf content"
    return r

@patch("analysis.qualitative.QUALITATIVE_MODE", "two_stage")
@patch("analysis.qualitative._extract_generic", return_value=("fake text", {"sections_found": [], "fallback_used": False}))
@patch("analysis.qualitative.requests.get", return_value=_mock_req())
@patch("analysis.qualitative.cache.get_json", return_value=None)
@patch("analysis.qualitative.cache.set_json")
@patch("analysis.qualitative._call_stage1")
@patch("analysis.qualitative._call_stage2")
@patch("analysis.qualitative._call_deepseek")
def test_two_stage_orchestrator(mock_deepseek, mock_stage2, mock_stage1, mock_set_json, mock_get_json, mock_req, mock_extract):
    """Verify that stage 1 and stage 2 are called when QUALITATIVE_MODE == 'two_stage'."""
    
    mock_stage1.return_value = {
        "status": "available",
        "evidence_pack": {"governance_and_rpt": "No issues"},
        "forward_guidance": [{"period": "FY26"}]
    }
    
    # Mock stage 2 returning lens specific results
    def side_effect_stage2(lens, evidence_pack, ticker, historical_context):
        if lens == "buffett":
            return {"owner_orientation_signal": {"verdict": "owner_oriented"}}
        elif lens == "marks":
            return {"cycle_position": {"sector_cycle": "trough"}}
        return {}
    mock_stage2.side_effect = side_effect_stage2

    result = extract_qualitative(
        ticker=_TICKER,
        documents=_DOCS,
        lenses_to_run=["buffett", "marks"]
    )
    
    assert mock_stage1.called
    assert mock_stage2.call_count == 2
    assert not mock_deepseek.called
    
    assert result["status"] == "available"
    assert result["forward_guidance"] == [{"period": "FY26"}]
    assert result["owner_orientation_signal"]["verdict"] == "owner_oriented"
    assert result["cycle_position"]["sector_cycle"] == "trough"
    
    # Check unselected lenses remain empty
    assert result["chaos_dislocation_catalyst"]["verdict"] is None

@patch("analysis.qualitative.QUALITATIVE_MODE", "two_stage")
@patch("analysis.qualitative._extract_generic", return_value=("fake text", {"sections_found": [], "fallback_used": False}))
@patch("analysis.qualitative.requests.get", return_value=_mock_req())
@patch("analysis.qualitative.cache.get_json", return_value=None)
@patch("analysis.qualitative.cache.set_json")
@patch("analysis.qualitative._call_stage1")
@patch("analysis.qualitative._call_stage2")
@patch("analysis.qualitative._call_deepseek")
def test_two_stage_fallback(mock_deepseek, mock_stage2, mock_stage1, mock_set_json, mock_get_json, mock_req, mock_extract):
    """Verify that if two-stage fails, it falls back to monolithic."""
    
    mock_stage1.side_effect = Exception("Stage 1 crash")
    
    mock_deepseek.return_value = {
        "status": "available",
        "forward_guidance": [{"period": "Fallback"}],
        "chaos_dislocation_catalyst": {"verdict": "present"}
    }
    
    result = extract_qualitative(
        ticker=_TICKER,
        documents=_DOCS,
    )
    
    assert mock_stage1.called
    assert mock_deepseek.called
    
    assert result["status"] == "available"
    assert result["forward_guidance"] == [{"period": "Fallback"}]

