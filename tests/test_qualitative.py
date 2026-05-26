"""
Tests for the qualitative analysis module. Zero live API calls — all Gemini
interactions are mocked via unittest.mock.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from analysis.qualitative import extract_qualitative, _unavailable


# ---------------------------------------------------------------------------
# 1. No documents → unavailable
# ---------------------------------------------------------------------------
def test_no_documents_returns_unavailable():
    result = extract_qualitative("TEST.NS", [])
    assert result["status"] == "unavailable"
    assert "No documents" in result["reason"]
    # Schema keys present even when unavailable
    assert "forward_guidance" in result
    assert result["forward_guidance"] == []
    assert "coherence_assessment" in result


# ---------------------------------------------------------------------------
# 2. No API key → unavailable
# ---------------------------------------------------------------------------
def test_no_api_key_returns_unavailable():
    docs = [{"hash": "abc123", "filename": "test.pdf", "type": "transcript", "text": "hello"}]
    with patch("analysis.qualitative.cache.get_json", return_value=None), \
         patch("os.getenv", return_value=None):
        result = extract_qualitative("TEST.NS", docs)
    assert result["status"] == "unavailable"
    assert "GEMINI_API_KEY" in result["reason"]


# ---------------------------------------------------------------------------
# 3. Gemini raises exception → unavailable (graceful degrade)
# ---------------------------------------------------------------------------
def test_gemini_exception_returns_unavailable():
    docs = [{"hash": "abc123", "filename": "test.pdf", "type": "transcript", "text": "hello"}]

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("quota exceeded")

    with patch("analysis.qualitative.cache.get_json", return_value=None), \
         patch("os.getenv", return_value="fake_key"), \
         patch("analysis.qualitative.genai.Client", return_value=mock_client):
        result = extract_qualitative("TEST.NS", docs)

    assert result["status"] == "unavailable"
    assert "Gemini error" in result["reason"]
    assert "RuntimeError" in result["reason"]


# ---------------------------------------------------------------------------
# 4. Gemini returns valid JSON → parsed and cached
# ---------------------------------------------------------------------------
def test_gemini_valid_response_is_parsed_and_cached():
    docs = [{"hash": "abc123", "filename": "test.pdf", "type": "transcript", "text": "hello"}]

    gemini_payload = {
        "forward_guidance": [{"period": "FY27", "metric": "revenue",
                               "statement": "10% growth expected.", "source_doc": "test.pdf"}],
        "risk_callouts": [],
        "strategic_themes": [],
        "tone_assessment": {"current": "confident", "trajectory": "stable", "notes": "All good."},
        "coherence_assessment": {"verdict": "coherent", "reasoning": "Consistent story."}
    }

    mock_response = MagicMock()
    mock_response.text = json.dumps(gemini_payload)

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    written_cache = {}

    def fake_set_json(key, val):
        written_cache[key] = val

    with patch("analysis.qualitative.cache.get_json", return_value=None), \
         patch("os.getenv", return_value="fake_key"), \
         patch("analysis.qualitative.genai.Client", return_value=mock_client), \
         patch("analysis.qualitative.cache.set_json", side_effect=fake_set_json):
        result = extract_qualitative("TEST.NS", docs)

    assert result["status"] == "available"
    assert result["model"] == "gemini-1.5-flash"
    assert result["documents_used"] == ["test.pdf"]
    assert len(result["forward_guidance"]) == 1
    assert result["coherence_assessment"]["verdict"] == "coherent"
    # Confirm it was written to cache
    assert len(written_cache) == 1


# ---------------------------------------------------------------------------
# 5. Cache hit → Gemini NOT called
# ---------------------------------------------------------------------------
def test_cache_hit_skips_gemini_call():
    docs = [{"hash": "abc123", "filename": "test.pdf", "type": "transcript", "text": "hello"}]

    cached_result = {
        "status": "available",
        "model": "gemini-1.5-flash",
        "documents_used": ["test.pdf"],
        "forward_guidance": [],
        "risk_callouts": [],
        "strategic_themes": [],
        "tone_assessment": {"current": "cautious", "trajectory": "stable", "notes": "Fine."},
        "coherence_assessment": {"verdict": "coherent", "reasoning": "OK."}
    }

    mock_client = MagicMock()

    with patch("analysis.qualitative.cache.get_json", return_value=cached_result), \
         patch("analysis.qualitative.genai.Client", return_value=mock_client):
        result = extract_qualitative("TEST.NS", docs)

    assert result["status"] == "available"
    assert result["tone_assessment"]["current"] == "cautious"
    # Gemini was never called
    mock_client.models.generate_content.assert_not_called()
