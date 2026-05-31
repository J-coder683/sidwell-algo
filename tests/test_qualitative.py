import json
import pytest
from unittest.mock import patch, MagicMock

from analysis.qualitative import extract_qualitative, MODEL_NAME, PROMPT_VERSION

# --- OLD TESTS RESTORED AND ADAPTED ---

def test_no_documents_returns_unavailable():
    result = extract_qualitative("TEST.NS", [])
    assert result["status"] == "unavailable"
    assert "No documents" in result["reason"]
    assert "forward_guidance" in result
    assert result["forward_guidance"] == []
    assert "coherence_assessment" in result


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

    with patch("data.cache.get_json", return_value=None):
        result = extract_qualitative("TEST.NS", docs)

    assert result["status"] == "unavailable"
    assert "GEMINI" in result["reason"] or "Gemini" in result["reason"]


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

    with patch("data.cache.get_json", return_value=None), \
         patch("analysis.qualitative.genai.Client", return_value=mock_client):
        result = extract_qualitative("TEST.NS", docs)

    assert result["status"] == "unavailable"
    assert "Gemini error" in result["reason"]


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
        "status": "available",
        "forward_guidance": [{"period": "FY27", "metric": "revenue",
                               "statement": "10% growth expected.", "source_doc": "test.pdf"}],
        "risk_callouts": [],
        "strategic_themes": [],
        "tone_assessment": {"current": "confident", "trajectory": "stable", "notes": "All good."},
        "coherence_assessment": {"verdict": "coherent", "reasoning": "Consistent story."}
    }

    mock_client = MagicMock()
    # Mock the return value for Gemini response.text
    mock_resp_obj = MagicMock()
    mock_resp_obj.text = json.dumps(bedrock_payload)
    mock_client.models.generate_content.return_value = mock_resp_obj

    written_cache = {}

    def fake_set_json(key, val):
        written_cache[key] = val

    with patch("data.cache.get_json", return_value=None), \
         patch("analysis.qualitative.genai.Client", return_value=mock_client), \
         patch("data.cache.set_json", side_effect=fake_set_json):
        result = extract_qualitative("TEST.NS", docs)

    assert result["status"] == "available"
    assert result["model"] == MODEL_NAME
    assert result["documents_used"] == ["test.pdf"]
    assert len(result["forward_guidance"]) == 1
    assert result["coherence_assessment"]["verdict"] == "coherent"
    assert "extraction_metadata" in result
    assert len(written_cache) == 1


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

    with patch("data.cache.get_json", return_value=cached_result), \
         patch("analysis.qualitative.genai.Client", return_value=mock_client):
        result = extract_qualitative("TEST.NS", docs)

    assert result["status"] == "available"
    assert result["tone_assessment"]["current"] == "cautious"
    mock_client.models.generate_content.assert_not_called()


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

    bedrock_payload = {"status": "available", "forward_guidance": [], "risk_callouts": [], "strategic_themes": [],
                       "tone_assessment": {"current": "confident", "trajectory": "stable", "notes": "OK."},
                       "coherence_assessment": {"verdict": "coherent", "reasoning": "Fine."}}
    mock_client = MagicMock()
    mock_resp_obj = MagicMock()
    mock_resp_obj.text = json.dumps(bedrock_payload)
    mock_client.models.generate_content.return_value = mock_resp_obj

    with patch("data.cache.get_json", side_effect=fake_get_json), \
         patch("analysis.qualitative.genai.Client", return_value=mock_client), \
         patch("data.cache.set_json"):
        extract_qualitative("TEST.NS", docs)

    assert len(recorded_keys) == 1
    cache_key = recorded_keys[0]
    assert PROMPT_VERSION in cache_key, (
        f"Cache key '{cache_key}' does not include PROMPT_VERSION '{PROMPT_VERSION}'"
    )

# --- NEW TESTS ---

@patch("analysis.qualitative._call_gemini")
@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative._extract_annual_report_sections")
def test_extract_qualitative_skips_when_empty(mock_extract, mock_get, mock_call_gemini):
    # 1. documents == []
    res = extract_qualitative("TEST", [])
    assert res["status"] == "unavailable"
    assert "No documents found" in res["reason"]
    mock_call_gemini.assert_not_called()


@patch("analysis.qualitative._call_gemini")
@patch("analysis.qualitative.requests.get")
def test_extract_qualitative_skips_no_high_value(mock_get, mock_call_gemini):
    # 2. Only low-value documents
    docs = [
        {"url": "http://test.com/1", "type": "credit_rating", "label": "Credit Rating"},
        {"url": "http://test.com/2", "type": "unknown", "label": "Unknown"},
    ]
    res = extract_qualitative("TEST", docs)
    assert res["status"] == "unavailable"
    assert "Fewer than 1 high-value" in res["reason"]
    mock_call_gemini.assert_not_called()


@patch("analysis.qualitative._call_gemini")
@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative._extract_annual_report_sections")
def test_extract_qualitative_proceeds(mock_extract, mock_get, mock_call_gemini):
    # 3. Proceeds with high value doc
    docs = [
        {"url": "http://test.com/ar", "type": "annual_report", "label": "AR"},
    ]
    
    # Mock download success
    mock_resp = mock_get.return_value
    mock_resp.content = b"fake pdf content"
    mock_resp.raise_for_status.return_value = None
    
    mock_extract.return_value = ("Extracted text", {"sections_found": ["MD&A"]})
    
    # Mock gemini response
    mock_call_gemini.return_value = {"status": "available", "mock_field": "test"}
    
    # Also need to bypass cache
    with patch("data.cache.get_json", return_value=None):
        with patch("data.cache.set_json"):
            res = extract_qualitative("TEST", docs)
            
            assert res["status"] == "available"
            mock_call_gemini.assert_called_once()
