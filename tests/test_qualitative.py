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
    # Core schema keys present even when unavailable
    assert "forward_guidance" in result
    assert result["forward_guidance"] == []
    assert "coherence_assessment" in result
    # v0.3 schema keys present even when unavailable
    assert "owner_orientation_signal" in result
    assert "holdability_assessment" in result
    assert "cycle_position" in result
    assert "variant_perception" in result
    assert "management_humility" in result
    assert "why_now_signal" in result
    assert result["owner_orientation_signal"]["verdict"] is None
    assert result["variant_perception"]["variant_present"] is None


# ---------------------------------------------------------------------------
# 2. No API key → unavailable
# ---------------------------------------------------------------------------
@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative.pdfplumber.open")
def test_no_api_key_returns_unavailable(mock_pdfplumber, mock_get):
    docs = [{"url": "https://fake.com/test.pdf", "label": "test.pdf", "type": "transcript"}]
    with patch("analysis.qualitative.cache.get_json", return_value=None), \
         patch("os.getenv", return_value=None):
        result = extract_qualitative("TEST.NS", docs)
    assert result["status"] == "unavailable"
    assert "GEMINI_API_KEY" in result["reason"]


# ---------------------------------------------------------------------------
# 3. Gemini raises exception → unavailable (graceful degrade)
# ---------------------------------------------------------------------------
@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative.pdfplumber.open")
def test_gemini_exception_returns_unavailable(mock_pdfplumber, mock_get):
    docs = [{"url": "https://fake.com/test.pdf", "label": "test.pdf", "type": "transcript"}]

    mock_resp = MagicMock()
    mock_resp.content = b"fake"
    mock_get.return_value = mock_resp
    
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "hello"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("quota exceeded")

    with patch("analysis.qualitative.cache.get_json", return_value=None), \
         patch("os.getenv", return_value="fake_key"), \
         patch("analysis.qualitative.genai.Client", return_value=mock_client):
        result = extract_qualitative("TEST.NS", docs)

    assert result["status"] == "unavailable"
    assert "Qualitative extraction failed" in result["reason"]


# ---------------------------------------------------------------------------
# 4. Gemini returns valid JSON → parsed and cached
# ---------------------------------------------------------------------------
@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative.pdfplumber.open")
def test_gemini_valid_response_is_parsed_and_cached(mock_pdfplumber, mock_get):
    docs = [{"url": "https://fake.com/test.pdf", "label": "test.pdf", "type": "transcript"}]

    mock_resp = MagicMock()
    mock_resp.content = b"fake"
    mock_get.return_value = mock_resp
    
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "hello"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

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
    assert result["model"] == "gemini-3.5-flash"
    assert result["documents_used"] == ["test.pdf"]
    assert len(result["forward_guidance"]) == 1
    assert result["coherence_assessment"]["verdict"] == "coherent"
    # Confirm it was written to cache
    assert len(written_cache) == 1


# ---------------------------------------------------------------------------
# 5. Cache hit → Gemini NOT called
# ---------------------------------------------------------------------------
def test_cache_hit_skips_gemini_call():
    docs = [{"url": "https://fake.com/test.pdf", "label": "test.pdf", "type": "transcript"}]

    cached_result = {
        "status": "available",
        "model": "gemini-3.5-flash",
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


# ---------------------------------------------------------------------------
# 6. PROMPT_VERSION in cache key
# ---------------------------------------------------------------------------
@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative.pdfplumber.open")
def test_cache_key_includes_prompt_version(mock_pdfplumber, mock_get):
    """Cache key must include PROMPT_VERSION so schema changes invalidate old cache."""
    from analysis.qualitative import PROMPT_VERSION
    docs = [{"url": "https://fake.com/test.pdf", "label": "test.pdf", "type": "transcript"}]

    mock_resp = MagicMock()
    mock_resp.content = b"fake"
    mock_get.return_value = mock_resp
    
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "hello"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

    recorded_keys = []

    def fake_get_json(key, ttl):
        recorded_keys.append(key)
        return None  # Cache miss

    gemini_payload = {
        "forward_guidance": [], "risk_callouts": [], "strategic_themes": [],
        "tone_assessment": {"current": "confident", "trajectory": "stable", "notes": "OK."},
        "coherence_assessment": {"verdict": "coherent", "reasoning": "Fine."},
        "owner_orientation_signal": {"verdict": "owner_oriented", "evidence": "Partners."},
        "holdability_assessment": {"verdict": "holdable_20y", "reasoning": "Durable."},
        "cycle_position": {"sector_cycle": "mid_cycle", "company_cycle": "mid", "reasoning": "Mid."},
        "variant_perception": {"consensus_view": "Bull.", "company_view": "Modest.",
                               "variant_present": True, "specificity": "high", "notes": "Specific."},
        "management_humility": {"verdict": "humble", "evidence": "No forecast."},
        "why_now_signal": {"verdict": "dislocation_present", "specific_event": "Shock.", "notes": "FII."},
    }
    mock_response = MagicMock()
    mock_response.text = json.dumps(gemini_payload)
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("analysis.qualitative.cache.get_json", side_effect=fake_get_json), \
         patch("os.getenv", return_value="fake_key"), \
         patch("analysis.qualitative.genai.Client", return_value=mock_client), \
         patch("analysis.qualitative.cache.set_json"):
        extract_qualitative("TEST.NS", docs)

    assert len(recorded_keys) == 1
    cache_key = recorded_keys[0]
    assert PROMPT_VERSION in cache_key, (
        f"Cache key '{cache_key}' does not include PROMPT_VERSION '{PROMPT_VERSION}'"
    )
