"""
Tests for the qualitative analysis module. Zero live API calls — all Bedrock
interactions are mocked via unittest.mock.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from analysis.qualitative import extract_qualitative, _unavailable, MODEL_NAME, PROMPT_VERSION


def _make_bedrock_body(json_text):
    """v0.7.6.3: keep helper name but return Gemini response shape (mock with .text)."""
    from unittest.mock import MagicMock
    m = MagicMock()
    m.text = json_text
    return m



def test_no_documents_returns_unavailable():
    result = extract_qualitative("TEST.NS", [])
    assert result["status"] == "unavailable"
    assert "No documents" in result["reason"]
    assert "forward_guidance" in result
    assert result["forward_guidance"] == []
    assert "coherence_assessment" in result
    assert "owner_orientation_signal" in result
    assert "holdability_assessment" in result
    assert "cycle_position" in result
    assert "variant_perception" in result
    assert "management_humility" in result
    assert "why_now_signal" in result
    assert result["owner_orientation_signal"]["verdict"] is None
    assert result["variant_perception"]["variant_present"] is None


# ---------------------------------------------------------------------------
# 2. No AWS credentials → unavailable
# ---------------------------------------------------------------------------
@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative.pdfplumber.open")
def test_no_api_key_returns_unavailable(mock_pdfplumber, mock_get, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    mock_resp = MagicMock()
    mock_resp.content = b"fake"
    mock_get.return_value = mock_resp

    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "hello"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

    docs = [{"url": "https://fake.com/test.pdf", "label": "test.pdf", "type": "concall_transcript"}]

    with patch("analysis.qualitative.cache.get_json", return_value=None):
        result = extract_qualitative("TEST.NS", docs)

    assert result["status"] == "unavailable"
    assert "GEMINI" in result["reason"] or "Gemini" in result["reason"]


# ---------------------------------------------------------------------------
# 3. Bedrock raises exception → unavailable (graceful degrade)
# ---------------------------------------------------------------------------
@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative.pdfplumber.open")
def test_gemini_exception_returns_unavailable(mock_pdfplumber, mock_get, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    

    docs = [{"url": "https://fake.com/test.pdf", "label": "test.pdf", "type": "concall_transcript"}]

    mock_resp = MagicMock()
    mock_resp.content = b"fake"
    mock_get.return_value = mock_resp

    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "hello"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("Gemini quota exceeded")

    with patch("analysis.qualitative.cache.get_json", return_value=None), \
         patch("analysis.qualitative.genai.Client", return_value=mock_client):
        result = extract_qualitative("TEST.NS", docs)

    assert result["status"] == "unavailable"
    assert "Gemini" in result["reason"]


# ---------------------------------------------------------------------------
# 4. Bedrock returns valid JSON → parsed, cached, model field set
# ---------------------------------------------------------------------------
@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative.pdfplumber.open")
def test_gemini_valid_response_is_parsed_and_cached(mock_pdfplumber, mock_get, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    

    docs = [{"url": "https://fake.com/test.pdf", "label": "test.pdf", "type": "concall_transcript"}]

    mock_resp = MagicMock()
    mock_resp.content = b"fake"
    mock_get.return_value = mock_resp

    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "hello"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

    bedrock_payload = {
        "forward_guidance": [{"period": "FY27", "metric": "revenue",
                               "statement": "10% growth expected.", "source_doc": "test.pdf"}],
        "risk_callouts": [],
        "strategic_themes": [],
        "tone_assessment": {"current": "confident", "trajectory": "stable", "notes": "All good."},
        "coherence_assessment": {"verdict": "coherent", "reasoning": "Consistent story."}
    }

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _make_bedrock_body(json.dumps(bedrock_payload))

    written_cache = {}

    def fake_set_json(key, val):
        written_cache[key] = val

    with patch("analysis.qualitative.cache.get_json", return_value=None), \
         patch("analysis.qualitative.genai.Client", return_value=mock_client), \
         patch("analysis.qualitative.cache.set_json", side_effect=fake_set_json):
        result = extract_qualitative("TEST.NS", docs)

    assert result["status"] == "available"
    assert result["model"] == MODEL_NAME
    assert result["documents_used"] == ["test.pdf"]
    assert len(result["forward_guidance"]) == 1
    assert result["coherence_assessment"]["verdict"] == "coherent"
    assert "extraction_metadata" in result
    assert len(written_cache) == 1


# ---------------------------------------------------------------------------
# 5. Cache hit → Bedrock NOT called
# ---------------------------------------------------------------------------
def test_cache_hit_skips_gemini_call(monkeypatch):
    docs = [{"url": "https://fake.com/test.pdf", "label": "test.pdf", "type": "concall_transcript"}]

    cached_result = {
        "status": "available",
        "model": MODEL_NAME,
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
    mock_client.models.generate_content.assert_not_called()


# ---------------------------------------------------------------------------
# 6. PROMPT_VERSION in cache key
# ---------------------------------------------------------------------------
@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative.pdfplumber.open")
def test_cache_key_includes_prompt_version(mock_pdfplumber, mock_get, monkeypatch):
    """Cache key must include PROMPT_VERSION so schema changes invalidate old cache."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    

    docs = [{"url": "https://fake.com/test.pdf", "label": "test.pdf", "type": "concall_transcript"}]

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
        return None  # cache miss

    bedrock_payload = {"forward_guidance": [], "risk_callouts": [], "strategic_themes": [],
                       "tone_assessment": {"current": "confident", "trajectory": "stable", "notes": "OK."},
                       "coherence_assessment": {"verdict": "coherent", "reasoning": "Fine."}}
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _make_bedrock_body(json.dumps(bedrock_payload))

    with patch("analysis.qualitative.cache.get_json", side_effect=fake_get_json), \
         patch("analysis.qualitative.genai.Client", return_value=mock_client), \
         patch("analysis.qualitative.cache.set_json"):
        extract_qualitative("TEST.NS", docs)

    assert len(recorded_keys) == 1
    cache_key = recorded_keys[0]
    assert PROMPT_VERSION in cache_key, (
        f"Cache key '{cache_key}' does not include PROMPT_VERSION '{PROMPT_VERSION}'"
    )
