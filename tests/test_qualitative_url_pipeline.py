from unittest.mock import patch, MagicMock, call, ANY
import pytest
import json

from analysis.qualitative import extract_qualitative, MAX_DOC_CHARS
from data import cache
from data.documents import discover_documents

MOCK_DOCUMENTS = [
    {"url": "https://fake.com/doc1.pdf", "type": "annual_report", "label": "Doc 1"},
    {"url": "https://fake.com/doc2.pdf", "type": "concall_transcript", "label": "Doc 2"},
    {"url": "https://fake.com/doc3.pdf", "type": "credit_rating", "label": "Doc 3"}
]

@pytest.fixture(autouse=True)
def mock_cache(monkeypatch):
    cache_store = {}
    def fake_get(key, ttl):
        return cache_store.get(key)
    def fake_set(key, val):
        cache_store[key] = val
    monkeypatch.setattr(cache, "get_json", fake_get)
    monkeypatch.setattr(cache, "set_json", fake_set)

@patch('analysis.qualitative.genai.Client')
@patch('analysis.qualitative.pdfplumber.open')
@patch('analysis.qualitative.requests.get')
def test_qualitative_fetches_pdf_in_memory_only(mock_get, mock_pdfplumber_open, mock_genai_client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
    
    mock_resp = MagicMock()
    mock_resp.content = b"fake pdf bytes"
    mock_get.return_value = mock_resp
    
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "fake text"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

    mock_client = MagicMock()
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"forward_guidance": []}'
    mock_model.generate_content.return_value = mock_response
    mock_client.models = mock_model
    mock_genai_client.return_value = mock_client

    result = extract_qualitative("MOCK", MOCK_DOCUMENTS[:1])
    
    assert result["status"] == "available"
    assert result["documents_used"] == ["Doc 1"]
    
    mock_get.assert_called_with("https://fake.com/doc1.pdf", timeout=30, headers=ANY)
    
    # Since we mock requests.get and pass BytesIO to pdfplumber.open, we didn't write to disk.

@patch('analysis.qualitative.genai.Client')
@patch('analysis.qualitative.pdfplumber.open')
@patch('analysis.qualitative.requests.get')
def test_qualitative_truncates_long_documents(mock_get, mock_pdfplumber_open, mock_genai_client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
    
    mock_resp = MagicMock()
    mock_resp.content = b"fake pdf bytes"
    mock_get.return_value = mock_resp
    
    # Make a document larger than MAX_DOC_CHARS (e.g., 250k)
    long_text = "A" * 250000
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = long_text
    mock_pdf.pages = [mock_page]
    mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

    mock_client = MagicMock()
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"forward_guidance": []}'
    mock_model.generate_content.return_value = mock_response
    mock_client.models = mock_model
    mock_genai_client.return_value = mock_client

    extract_qualitative("MOCK", MOCK_DOCUMENTS[:1])
    
    # Assert the prompt builder got truncated text
    prompt_call_args = mock_model.generate_content.call_args.kwargs['contents']
    
    # Head and tail should be present, middle should be truncated
    assert "...[TRUNCATED MIDDLE]..." in prompt_call_args
    # Length should be around 200k + length of truncation string
    assert len(prompt_call_args) < 210000

@patch('analysis.qualitative.genai.Client')
@patch('analysis.qualitative.pdfplumber.open')
@patch('analysis.qualitative.requests.get')
def test_qualitative_handles_individual_pdf_failure(mock_get, mock_pdfplumber_open, mock_genai_client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
    
    def side_effect_get(*args, **kwargs):
        if "doc2" in args[0]:
            raise Exception("Mock timeout")
        resp = MagicMock()
        resp.content = b"fake bytes"
        return resp
        
    mock_get.side_effect = side_effect_get
    
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "fake text"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

    mock_client = MagicMock()
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"forward_guidance": []}'
    mock_model.generate_content.return_value = mock_response
    mock_client.models = mock_model
    mock_genai_client.return_value = mock_client

    result = extract_qualitative("MOCK", MOCK_DOCUMENTS)
    
    # Doc 2 failed, so pipeline succeeds with Docs 1 and 3
    assert result["status"] == "available"
    assert "Doc 1" in result["documents_used"]
    assert "Doc 3" in result["documents_used"]
    assert "Doc 2" not in result["documents_used"]

@patch('analysis.qualitative.requests.get')
def test_qualitative_all_pdfs_fail_returns_unavailable(mock_get, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
    mock_get.side_effect = Exception("All fail")
    
    result = extract_qualitative("MOCK", MOCK_DOCUMENTS)
    
    assert result["status"] == "unavailable"
    assert "failed to fetch or parse" in result["reason"]
    assert result.get("forward_guidance") == []

@patch('analysis.qualitative.genai.Client')
@patch('analysis.qualitative.pdfplumber.open')
@patch('analysis.qualitative.requests.get')
def test_qualitative_url_hash_cache_key_stable_under_url_reorder(mock_get, mock_pdfplumber_open, mock_genai_client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
    
    mock_resp = MagicMock()
    mock_resp.content = b"fake bytes"
    mock_get.return_value = mock_resp
    
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "fake text"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

    mock_client = MagicMock()
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"forward_guidance": []}'
    mock_model.generate_content.return_value = mock_response
    mock_client.models = mock_model
    mock_genai_client.return_value = mock_client

    # Call with order 1
    extract_qualitative("MOCK", [MOCK_DOCUMENTS[0], MOCK_DOCUMENTS[1]])
    
    # Should only hit API once because the second call (reordered) hits the cache
    extract_qualitative("MOCK", [MOCK_DOCUMENTS[1], MOCK_DOCUMENTS[0]])
    
    assert mock_model.generate_content.call_count == 1

def test_us_ticker_returns_empty_doc_list_logs_info():
    docs = discover_documents("AAPL")
    assert docs == []
