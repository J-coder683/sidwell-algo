import json
import pytest
from unittest.mock import patch, MagicMock

from analysis.qualitative import (
    extract_qualitative,
    MODEL_NAME,
    PROMPT_VERSION,
    _extract_html,
    _select_documents,
    _safe_json_loads,
)


def test_safe_json_loads_strict_and_lenient():
    assert _safe_json_loads('{"a": 1}') == {"a": 1}                    # strict path
    assert _safe_json_loads('{"a": 1,}') == {"a": 1}                   # trailing comma
    assert _safe_json_loads('{\n  // note\n  "a": [1, 2,]\n}') == {"a": [1, 2]}  # // line + trailing comma
    assert _safe_json_loads('{"u": "https://x.com/y"}') == {"u": "https://x.com/y"}  # URL // preserved

# All tests are OFFLINE: the OpenAI/DeepSeek client, PDF fetch (requests) and
# pdfplumber are mocked so the suite never makes a network or LLM call.


def _make_stream_chunks(content: str, n_chunks: int):
    """Split `content` into n streaming chunks shaped like the OpenAI SDK emits:
    each chunk has choices[0].delta.content. A trailing chunk with delta.content
    is None mimics the real finish marker — exercising _call_deepseek's None-skip."""
    chunks = []
    if content:
        n = max(1, min(n_chunks, len(content)))
        size = (len(content) + n - 1) // n
        for i in range(0, len(content), size):
            delta = MagicMock(); delta.content = content[i:i + size]
            choice = MagicMock(); choice.delta = delta
            ch = MagicMock(); ch.choices = [choice]
            chunks.append(ch)
    fin_delta = MagicMock(); fin_delta.content = None
    fin_choice = MagicMock(); fin_choice.delta = fin_delta
    fin = MagicMock(); fin.choices = [fin_choice]
    chunks.append(fin)
    return chunks


def _mock_openai(content: str, n_chunks: int = 3):
    """Build (OpenAI_class_mock, client_mock) whose
    client.chat.completions.create(..., stream=True) returns an iterable of chunks
    carrying `content` across choices[0].delta.content — the streaming shape
    _call_deepseek now reads. A list is used (re-iterable) rather than a generator."""
    chunks = _make_stream_chunks(content, n_chunks)
    client = MagicMock()
    client.chat.completions.create.return_value = chunks
    return MagicMock(return_value=client), client


_VALID_PAYLOAD = {
    "forward_guidance": [{"period": "FY27", "metric": "revenue",
                          "statement": "10% growth expected.", "source_doc": "test.pdf"}],
    "risk_callouts": [],
    "strategic_themes": [],
    "tone_assessment": {"current": "confident", "trajectory": "stable", "notes": "All good."},
    "coherence_assessment": {"verdict": "coherent", "reasoning": "Consistent story."},
}


def _mock_pdf(mock_pdfplumber, mock_get):
    """Wire requests.get + pdfplumber.open so document extraction succeeds."""
    mock_resp = MagicMock(); mock_resp.content = b"fake"
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp
    mock_pdf = MagicMock()
    mock_page = MagicMock(); mock_page.extract_text.return_value = "hello"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber.return_value.__enter__.return_value = mock_pdf


_DOCS = [{"url": "https://fake.com/test.pdf", "label": "test.pdf", "type": "concall_transcript"}]


# --- gating / no-call paths -------------------------------------------------

def test_no_documents_returns_unavailable():
    result = extract_qualitative("TEST.NS", [])
    assert result["status"] == "unavailable"
    assert "No documents" in result["reason"]
    assert result["forward_guidance"] == []
    assert "coherence_assessment" in result


@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative.pdfplumber.open")
def test_no_api_key_returns_unavailable(mock_pdfplumber, mock_get, monkeypatch):
    # Block BOTH key sources so the test is hermetic even on a dev box that has a
    # real DEEPSEEK_API_KEY in env or .streamlit/secrets.toml.
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    import streamlit as st
    monkeypatch.setattr(st, "secrets", {}, raising=False)  # {}.get(...) -> None
    _mock_pdf(mock_pdfplumber, mock_get)
    with patch("data.cache.get_json", return_value=None):
        result = extract_qualitative("TEST.NS", _DOCS)
    assert result["status"] == "unavailable"
    assert "DEEPSEEK" in result["reason"].upper()


# --- _call_deepseek internals (OpenAI client mocked) ------------------------

@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative.pdfplumber.open")
def test_deepseek_exception_returns_unavailable(mock_pdfplumber, mock_get, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake")
    _mock_pdf(mock_pdfplumber, mock_get)
    cls, client = _mock_openai("")
    client.chat.completions.create.side_effect = RuntimeError("DeepSeek quota exceeded")
    with patch("data.cache.get_json", return_value=None), \
         patch("analysis.qualitative.OpenAI", cls):
        result = extract_qualitative("TEST.NS", _DOCS)
    assert result["status"] == "unavailable"
    assert "DeepSeek error" in result["reason"]


@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative.pdfplumber.open")
def test_deepseek_valid_response_is_parsed_and_cached(mock_pdfplumber, mock_get, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake")
    _mock_pdf(mock_pdfplumber, mock_get)
    cls, client = _mock_openai(json.dumps(_VALID_PAYLOAD))

    written_cache = {}
    with patch("data.cache.get_json", return_value=None), \
         patch("analysis.qualitative.OpenAI", cls), \
         patch("data.cache.set_json", side_effect=lambda k, v: written_cache.__setitem__(k, v)):
        result = extract_qualitative("TEST.NS", _DOCS)

    assert result["status"] == "available"
    assert result["model"] == MODEL_NAME
    assert result["documents_used"] == ["test.pdf"]
    assert len(result["forward_guidance"]) == 1
    assert result["coherence_assessment"]["verdict"] == "coherent"
    assert "extraction_metadata" in result
    assert len(written_cache) == 1


@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative.pdfplumber.open")
def test_streaming_assembles_chunks_and_emits_heartbeat(mock_pdfplumber, mock_get, monkeypatch):
    """Multi-chunk delta stream is reassembled into the full JSON, stream=True is
    requested, and the stream_cb heartbeat fires with the final char count."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake")
    _mock_pdf(mock_pdfplumber, mock_get)
    payload = json.dumps(_VALID_PAYLOAD)
    cls, client = _mock_openai(payload, n_chunks=5)

    seen = []
    with patch("data.cache.get_json", return_value=None), \
         patch("analysis.qualitative.OpenAI", cls), \
         patch("data.cache.set_json"):
        result = extract_qualitative("TEST.NS", _DOCS, stream_cb=lambda c: seen.append(c))

    assert result["status"] == "available"
    assert result["coherence_assessment"]["verdict"] == "coherent"  # full JSON reassembled
    _, kwargs = client.chat.completions.create.call_args
    assert kwargs.get("stream") is True
    assert seen and seen[-1] == len(payload)  # final heartbeat lands on the true total


def test_cache_hit_skips_deepseek_call(monkeypatch):
    cached_result = {
        "status": "available", "model": MODEL_NAME, "documents_used": ["test.pdf"],
        "forward_guidance": [], "risk_callouts": [], "strategic_themes": [],
        "tone_assessment": {"current": "cautious", "trajectory": "stable", "notes": "Fine."},
        "coherence_assessment": {"verdict": "coherent", "reasoning": "OK."},
    }
    cls, client = _mock_openai("{}")
    with patch("data.cache.get_json", return_value=cached_result), \
         patch("analysis.qualitative.OpenAI", cls):
        result = extract_qualitative("TEST.NS", _DOCS)
    assert result["status"] == "available"
    assert result["tone_assessment"]["current"] == "cautious"
    client.chat.completions.create.assert_not_called()


@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative.pdfplumber.open")
def test_cache_key_includes_prompt_version(mock_pdfplumber, mock_get, monkeypatch):
    """Cache key must include PROMPT_VERSION so schema changes invalidate old cache."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake")
    _mock_pdf(mock_pdfplumber, mock_get)
    cls, client = _mock_openai(json.dumps(_VALID_PAYLOAD))

    recorded_keys = []
    def fake_get_json(key, ttl):
        recorded_keys.append(key)
        return None

    with patch("data.cache.get_json", side_effect=fake_get_json), \
         patch("analysis.qualitative.OpenAI", cls), \
         patch("data.cache.set_json"):
        extract_qualitative("TEST.NS", _DOCS)

    assert len(recorded_keys) == 1
    assert PROMPT_VERSION in recorded_keys[0], (
        f"Cache key '{recorded_keys[0]}' does not include PROMPT_VERSION '{PROMPT_VERSION}'"
    )


# --- doc-gating (mock the LLM call directly) --------------------------------

@patch("analysis.qualitative._call_deepseek")
@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative._extract_annual_report_sections")
def test_extract_qualitative_skips_when_empty(mock_extract, mock_get, mock_call):
    res = extract_qualitative("TEST", [])
    assert res["status"] == "unavailable"
    assert "No documents found" in res["reason"]
    mock_call.assert_not_called()


@patch("analysis.qualitative._call_deepseek")
@patch("analysis.qualitative.requests.get")
def test_extract_qualitative_skips_no_high_value(mock_get, mock_call):
    docs = [
        {"url": "http://test.com/1", "type": "credit_rating", "label": "Credit Rating"},
        {"url": "http://test.com/2", "type": "unknown", "label": "Unknown"},
    ]
    res = extract_qualitative("TEST", docs)
    assert res["status"] == "unavailable"
    assert "Fewer than 1 high-value" in res["reason"]
    mock_call.assert_not_called()


@patch("analysis.qualitative._call_deepseek")
@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative._extract_annual_report_sections")
def test_extract_qualitative_proceeds(mock_extract, mock_get, mock_call):
    docs = [{"url": "http://test.com/ar", "type": "annual_report", "label": "AR"}]
    mock_resp = mock_get.return_value
    mock_resp.content = b"fake pdf content"
    mock_resp.raise_for_status.return_value = None
    mock_extract.return_value = ("Extracted text", {"sections_found": ["MD&A"]})
    mock_call.return_value = {"status": "available", "mock_field": "test"}

    with patch("data.cache.get_json", return_value=None), patch("data.cache.set_json"):
        res = extract_qualitative("TEST", docs)
    assert res["status"] == "available"
    mock_call.assert_called_once()


# --- HTML documents (credit ratings are HTML, not PDF) ----------------------

def test_extract_html_returns_visible_text():
    html = (b"<html><head><style>x{}</style></head><body>"
            b"<nav>menu</nav><p>Rated AAA / Stable by CRISIL.</p>"
            b"<script>bad()</script></body></html>")
    text, meta = _extract_html(html)
    assert "Rated AAA" in text
    assert "menu" not in text and "bad()" not in text   # nav + script stripped
    assert meta["sections_found"] == ["html_full"]


@patch("analysis.qualitative._call_deepseek")
@patch("analysis.qualitative._extract_annual_report_sections")
@patch("analysis.qualitative.requests.get")
def test_html_credit_rating_not_dropped(mock_get, mock_ar, mock_call):
    """An HTML credit-rating page must reach the model, not be dropped by pdfplumber."""
    def _get(url, **kw):
        r = MagicMock()
        r.content = (b"<html><body><p>Rating AAA stable</p></body></html>"
                     if "rating" in url else b"%PDF-1.4 fake annual report")
        r.raise_for_status.return_value = None
        return r
    mock_get.side_effect = _get
    mock_ar.return_value = ("AR text", {"sections_found": ["MD&A"]})
    mock_call.return_value = {"status": "available"}
    docs = [
        {"url": "http://x/ar.pdf", "type": "annual_report", "label": "AR"},
        {"url": "http://x/rating.html", "type": "credit_rating", "label": "Credit Rating"},
    ]
    with patch("data.cache.get_json", return_value=None), patch("data.cache.set_json"):
        res = extract_qualitative("TEST", docs)
    assert res["status"] == "available"
    assert "AR" in res["documents_used"] and "Credit Rating" in res["documents_used"]


# ---------------------------------------------------------------------------
# Historical-context injection tests
# ---------------------------------------------------------------------------

@patch("analysis.qualitative.requests.get")
@patch("analysis.qualitative.pdfplumber.open")
def test_historical_context_prepended_in_prompt(mock_pdfplumber, mock_get, monkeypatch):
    """The historical_context block must appear in the prompt BEFORE the documents."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake")
    _mock_pdf(mock_pdfplumber, mock_get)

    captured_prompts = []

    cls, client = _mock_openai(json.dumps(_VALID_PAYLOAD))
    # Intercept the prompt arg passed to client.chat.completions.create
    orig_create = client.chat.completions.create

    def _capture(*args, **kwargs):
        msgs = kwargs.get("messages", [])
        for m in msgs:
            if m.get("role") == "user":
                captured_prompts.append(m["content"])
        return orig_create(*args, **kwargs)

    client.chat.completions.create = _capture

    hist_block = "## Historical Financials (anchor your forecasts to these)\n| FY | Revenue |\n| Mar 2025 | 10,000 |"

    with patch("data.cache.get_json", return_value=None), \
         patch("analysis.qualitative.OpenAI", cls), \
         patch("data.cache.set_json"):
        extract_qualitative("TEST.NS", _DOCS, historical_context=hist_block)

    assert captured_prompts, "No user prompt was captured"
    prompt = captured_prompts[0]
    hist_pos = prompt.find("## Historical Financials")
    docs_pos = prompt.find("## Documents for")
    assert hist_pos != -1, "Historical context block not found in prompt"
    assert docs_pos != -1, "Documents section not found in prompt"
    assert hist_pos < docs_pos, (
        "Historical context must appear BEFORE the documents section in the prompt"
    )


# ---------------------------------------------------------------------------
# _select_documents — pure, offline (no network / DeepSeek needed)
# ---------------------------------------------------------------------------

_ANNUAL    = {"url": "http://x/ar.pdf",     "type": "annual_report",    "label": "AR"}
_CONCALL_A = {"url": "http://x/cc1.pdf",    "type": "concall_transcript","label": "Concall A"}
_CONCALL_B = {"url": "http://x/cc2.pdf",    "type": "concall_transcript","label": "Concall B"}
_RATING    = {"url": "http://x/r.html",     "type": "credit_rating",    "label": "Rating"}

_FULL_LIST = [_ANNUAL, _CONCALL_A, _CONCALL_B, _RATING]


def test_select_documents_with_research_returns_latest_concall_only():
    """has_research=True → only the first (newest) concall; discover returns newest-first."""
    result = _select_documents(_FULL_LIST, has_research=True)
    assert result == [_CONCALL_A], (
        f"Expected [_CONCALL_A], got {result}"
    )


def test_select_documents_without_research_returns_full_list():
    """has_research=False → all documents unchanged."""
    result = _select_documents(_FULL_LIST, has_research=False)
    assert result == _FULL_LIST


def test_select_documents_with_research_no_concall_returns_empty():
    """has_research=True but no concall present → empty list (research-only mode)."""
    docs_no_concall = [_ANNUAL, _RATING]
    result = _select_documents(docs_no_concall, has_research=True)
    assert result == []
