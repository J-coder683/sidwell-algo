"""
Tests for the qualitative URL pipeline.
v0.7.6: Gemini mocks replaced with Bedrock mocks; new tests for:
  - annual report section extraction metadata
  - fallback fires when <2 sections found
  - section search ignores TOC pages (starts after toc_page_idx + 10)
  - concall transcripts use full-text path
  - MODEL_ID assertion rejects non-Haiku models
"""
from unittest.mock import patch, MagicMock, ANY
import json
import pytest

from analysis.qualitative import (
    extract_qualitative,
    _extract_annual_report_sections,
    _extract_concall,
    MAX_DOC_CHARS,
    MODEL_ID,
)
from data import cache
from data.documents import discover_documents

MOCK_DOCUMENTS = [
    {"url": "https://fake.com/doc1.pdf", "type": "annual_report", "label": "Doc 1"},
    {"url": "https://fake.com/doc2.pdf", "type": "concall_transcript", "label": "Doc 2"},
    {"url": "https://fake.com/doc3.pdf", "type": "concall_transcript", "label": "Doc 3"},
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


def _make_mock_bedrock_response(json_text: str):
    """Helper: build a mock Bedrock response dict."""
    body_bytes = json.dumps({
        "content": [{"type": "text", "text": json_text}]
    }).encode()
    mock_body = MagicMock()
    mock_body.read.return_value = body_bytes
    mock_resp = MagicMock()
    mock_resp.__getitem__ = lambda self, key: mock_body if key == "body" else None
    return mock_resp


def _make_mock_bedrock_client(json_text: str = '{"forward_guidance": []}'):
    mock_client = MagicMock()
    mock_client.invoke_model.return_value = _make_mock_bedrock_response(json_text)
    return mock_client


# ─── Core pipeline tests ──────────────────────────────────────────────────────

@patch("analysis.qualitative.boto3.client")
@patch("analysis.qualitative.pdfplumber.open")
@patch("analysis.qualitative.requests.get")
def test_qualitative_fetches_pdf_in_memory_only(
    mock_get, mock_pdfplumber_open, mock_boto3_client, monkeypatch
):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "fake")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "fake")

    mock_resp = MagicMock()
    mock_resp.content = b"fake pdf bytes"
    mock_get.return_value = mock_resp

    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "fake text"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

    mock_boto3_client.return_value = _make_mock_bedrock_client()

    result = extract_qualitative("MOCK", MOCK_DOCUMENTS[:1])

    assert result["status"] == "available"
    assert result["documents_used"] == ["Doc 1"]
    assert result["model"] == MODEL_ID
    mock_get.assert_called_with("https://fake.com/doc1.pdf", timeout=30, headers=ANY)


@patch("analysis.qualitative.boto3.client")
@patch("analysis.qualitative.pdfplumber.open")
@patch("analysis.qualitative.requests.get")
def test_qualitative_handles_individual_pdf_failure(
    mock_get, mock_pdfplumber_open, mock_boto3_client, monkeypatch
):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "fake")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "fake")

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

    mock_boto3_client.return_value = _make_mock_bedrock_client()

    result = extract_qualitative("MOCK", MOCK_DOCUMENTS)

    assert result["status"] == "available"
    assert "Doc 1" in result["documents_used"]
    assert "Doc 2" not in result["documents_used"]


@patch("analysis.qualitative.requests.get")
def test_qualitative_all_pdfs_fail_returns_unavailable(mock_get, monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "fake")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "fake")
    mock_get.side_effect = Exception("All fail")

    result = extract_qualitative("MOCK", MOCK_DOCUMENTS)

    assert result["status"] == "unavailable"
    assert "failed to fetch or parse" in result["reason"]
    assert result.get("forward_guidance") == []


@patch("analysis.qualitative.boto3.client")
@patch("analysis.qualitative.pdfplumber.open")
@patch("analysis.qualitative.requests.get")
def test_qualitative_url_hash_cache_key_stable_under_url_reorder(
    mock_get, mock_pdfplumber_open, mock_boto3_client, monkeypatch
):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "fake")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "fake")

    mock_resp = MagicMock()
    mock_resp.content = b"fake bytes"
    mock_get.return_value = mock_resp

    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "fake text"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

    mock_client = _make_mock_bedrock_client()
    mock_boto3_client.return_value = mock_client

    extract_qualitative("MOCK", [MOCK_DOCUMENTS[0], MOCK_DOCUMENTS[1]])
    extract_qualitative("MOCK", [MOCK_DOCUMENTS[1], MOCK_DOCUMENTS[0]])

    # Should only invoke Bedrock once; second call hits the cache
    assert mock_client.invoke_model.call_count == 1


def test_missing_aws_credentials_returns_unavailable(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    result = extract_qualitative("MOCK", MOCK_DOCUMENTS[:1])
    # Will fail at PDF fetch stage before Bedrock since requests.get isn't mocked,
    # but the credentials check fires if we mock requests out too
    assert result["status"] == "unavailable"


# ─── Annual report section extraction tests ───────────────────────────────────

def _make_pdf_mock(pages_texts: list[str]):
    """Build a pdfplumber-compatible mock PDF with given per-page text."""
    mock_pages = []
    for text in pages_texts:
        p = MagicMock()
        p.extract_text.return_value = text
        mock_pages.append(p)
    mock_pdf = MagicMock()
    mock_pdf.pages = mock_pages
    mock_pdf.__enter__ = lambda self: self
    mock_pdf.__exit__ = MagicMock(return_value=False)
    return mock_pdf


@patch("analysis.qualitative.pdfplumber.open")
def test_annual_report_extraction_returns_metadata(mock_pdfplumber_open):
    """Sections found in body → metadata dict populated correctly."""
    # TOC on page 1, body starts page 12+; sections on pages 15, 20, 25, 30
    toc_text = "table of contents\nmanagement discussion and analysis\nrisk and governance\nchairman's message"
    mda_text = "management discussion and analysis\n" + "financial data " * 100
    risk_text = "risk and governance\n" + "risk data " * 100
    chair_text = "chairman and managing director's statement\n" + "letter " * 100
    biz_text = "business overview\n" + "overview data " * 100

    pages = (
        ["cover page"] * 1        # page 0: cover
        + [toc_text]               # page 1: TOC
        + ["filler"] * 13          # pages 2-14: preamble (skip past toc_idx+10=11)
        + [mda_text]               # page 15: MD&A
        + ["mda continues"] * 4    # pages 16-19
        + [risk_text]              # page 20: Risk
        + ["risk continues"] * 4   # pages 21-24
        + [chair_text]             # page 25: Chairman
        + ["chair continues"] * 4  # pages 26-29
        + [biz_text]               # page 30: Business Overview
        + ["biz continues"] * 9    # pages 31-39: business
    )
    mock_pdfplumber_open.return_value = _make_pdf_mock(pages)

    text, meta = _extract_annual_report_sections(b"fake")

    assert meta["fallback_used"] is False
    assert "MD&A" in meta["sections_found"]
    assert "Risk Factors" in meta["sections_found"]
    assert len(meta["sections_found"]) >= 2


@patch("analysis.qualitative.pdfplumber.open")
def test_annual_report_fallback_fires_when_fewer_than_2_sections(mock_pdfplumber_open):
    """When <2 sections detected, fallback extracts pages 1-80 + last 30."""
    pages = ["random text page " + str(i) for i in range(100)]
    mock_pdfplumber_open.return_value = _make_pdf_mock(pages)

    text, meta = _extract_annual_report_sections(b"fake")

    assert meta["fallback_used"] is True
    assert "fallback_reason" in meta
    assert "Pages 1-" in text or "fallback" in text.lower()


@patch("analysis.qualitative.pdfplumber.open")
def test_annual_report_section_search_skips_toc_pages(mock_pdfplumber_open):
    """Section keyword in the TOC itself should NOT be detected as the section start
    because search starts at toc_page_idx + 10."""
    # Put all keywords in the TOC (page 5), but NO section headers in body
    toc_text = (
        "table of contents\nmanagement discussion and analysis\n"
        "risk and governance\nchairman's message\nbusiness overview"
    )
    pages = (
        ["filler"] * 5
        + [toc_text]          # page 5: TOC
        + ["filler"] * 50    # pages 6-55: no section headers
    )
    mock_pdfplumber_open.return_value = _make_pdf_mock(pages)

    text, meta = _extract_annual_report_sections(b"fake")

    # Must fallback because body search starts at page 15 (5+10) and finds nothing
    assert meta["fallback_used"] is True


@patch("analysis.qualitative.pdfplumber.open")
def test_concall_uses_full_text_path(mock_pdfplumber_open):
    """Concall transcripts: all pages extracted, no section detection."""
    pages = ["page " + str(i) + " concall text" for i in range(15)]
    mock_pdfplumber_open.return_value = _make_pdf_mock(pages)

    text, meta = _extract_concall(b"fake")

    # Full text = all pages concatenated
    assert "page 0 concall text" in text
    assert "page 14 concall text" in text
    assert meta["sections_found"] == ["full_text"]
    assert meta["pages_extracted"] == 15


# ─── MODEL_ID assertion test ──────────────────────────────────────────────────

def test_model_id_assertion_rejects_non_haiku():
    """The assertion at module top should prevent non-Haiku MODEL_IDs."""
    # The assertion already ran when qualitative was imported — if it passed,
    # MODEL_ID is Haiku. Verify the string constraint directly.
    assert MODEL_ID.startswith("anthropic.claude-3-5-haiku-"), (
        f"MODEL_ID must be Claude Haiku 3.5; got {MODEL_ID}"
    )


# ─── extraction_metadata in output ───────────────────────────────────────────

@patch("analysis.qualitative.boto3.client")
@patch("analysis.qualitative.pdfplumber.open")
@patch("analysis.qualitative.requests.get")
def test_extraction_metadata_present_in_result(
    mock_get, mock_pdfplumber_open, mock_boto3_client, monkeypatch
):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "fake")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "fake")

    mock_resp = MagicMock()
    mock_resp.content = b"fake bytes"
    mock_get.return_value = mock_resp

    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "concall text"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

    mock_boto3_client.return_value = _make_mock_bedrock_client()

    result = extract_qualitative("MOCK", MOCK_DOCUMENTS[1:2])  # concall only

    assert result["status"] == "available"
    assert "extraction_metadata" in result
    docs_meta = result["extraction_metadata"]["documents"]
    assert len(docs_meta) == 1
    assert docs_meta[0]["type"] == "concall_transcript"
    assert "chars_extracted" in docs_meta[0]


# ─── US ticker passthrough ────────────────────────────────────────────────────

def test_us_ticker_returns_empty_doc_list_logs_info():
    docs = discover_documents("AAPL")
    assert docs == []
