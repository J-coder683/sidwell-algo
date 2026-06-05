"""
test_edgar_filings_text.py — Offline tests for fetch_edgar_filings_text.

All edgartools network calls are mocked; no network required.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_filing(md_and_a="MD&A text here", risk_factors="Risk text here",
                      business=None, filing_date="2024-11-01"):
    """Return a fake filing object whose obj() exposes structured sections."""
    tenk = MagicMock()
    tenk.management_discussion_and_analysis = md_and_a
    tenk.management_discussion = None          # ensure only one MD&A branch fires
    tenk.mda = None
    tenk.risk_factors = risk_factors
    tenk.business = business
    tenk.item_1 = None
    tenk.item_1a = None
    tenk.item_7 = None
    tenk.item_7a = None

    filing = MagicMock()
    filing.obj.return_value = tenk
    filing.filing_date = filing_date
    return filing


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@patch("data.scrapers.edgar.cache.set_json")
@patch("data.scrapers.edgar.cache.get_json", return_value=None)   # no cached hit
@patch("data.scrapers.edgar.set_identity")
@patch("data.scrapers.edgar.Company")
def test_fetch_edgar_filings_text_structured_sections(
    MockCompany, mock_set_identity, mock_cache_get, mock_cache_set
):
    """Happy-path: structured section accessors are available -> one doc returned."""
    fake_filing = _make_fake_filing()
    MockCompany.return_value.get_filings.return_value.latest.return_value = fake_filing

    from data.scrapers.edgar import fetch_edgar_filings_text
    result = fetch_edgar_filings_text("AAPL")

    assert len(result) == 1
    doc = result[0]
    assert "filename" in doc and "text" in doc
    assert "AAPL" in doc["filename"]
    assert "2024-11-01" in doc["filename"]
    assert "MD&A text here" in doc["text"]
    assert "Risk text here" in doc["text"]

    # Cache should have been written
    mock_cache_set.assert_called_once()


@patch("data.scrapers.edgar.cache.set_json")
@patch("data.scrapers.edgar.cache.get_json", return_value=None)
@patch("data.scrapers.edgar.set_identity")
@patch("data.scrapers.edgar.Company")
def test_fetch_edgar_filings_text_fallback_to_full_text(
    MockCompany, mock_set_identity, mock_cache_get, mock_cache_set
):
    """If obj() raises, fall back to filing.text() (truncated full text)."""
    fake_filing = MagicMock()
    fake_filing.obj.side_effect = Exception("section parsing failed")
    fake_filing.text.return_value = "Full 10-K text " * 1000   # ~15k chars
    fake_filing.filing_date = "2024-09-15"
    MockCompany.return_value.get_filings.return_value.latest.return_value = fake_filing

    from data.scrapers.edgar import fetch_edgar_filings_text
    result = fetch_edgar_filings_text("MSFT")

    assert len(result) == 1
    doc = result[0]
    assert "MSFT" in doc["filename"]
    assert "Full 10-K text" in doc["text"]
    assert len(doc["text"]) <= 200_000


@patch("data.scrapers.edgar.cache.set_json")
@patch("data.scrapers.edgar.cache.get_json", return_value=None)
@patch("data.scrapers.edgar.set_identity")
@patch("data.scrapers.edgar.Company")
def test_fetch_edgar_filings_text_no_filing_returns_empty(
    MockCompany, mock_set_identity, mock_cache_get, mock_cache_set
):
    """If latest() returns None (no 10-K on record), return []."""
    MockCompany.return_value.get_filings.return_value.latest.return_value = None

    from data.scrapers.edgar import fetch_edgar_filings_text
    result = fetch_edgar_filings_text("UNKNWN")

    assert result == []
    # Cache should still be written (empty list) to avoid repeat network hits
    mock_cache_set.assert_called_once()


@patch("data.scrapers.edgar.cache.set_json")
@patch("data.scrapers.edgar.cache.get_json", return_value=None)
@patch("data.scrapers.edgar.set_identity")
@patch("data.scrapers.edgar.Company")
def test_fetch_edgar_filings_text_company_raises_returns_empty(
    MockCompany, mock_set_identity, mock_cache_get, mock_cache_set
):
    """If Company() itself raises (network error, bad ticker), return []."""
    MockCompany.side_effect = Exception("network error")

    from data.scrapers.edgar import fetch_edgar_filings_text
    result = fetch_edgar_filings_text("BADINPUT")

    assert result == []
    mock_cache_set.assert_called_once()


@patch("data.scrapers.edgar.cache.get_json", return_value=[{"filename": "AAPL 10-K 2024-11-01", "text": "cached text"}])
def test_fetch_edgar_filings_text_uses_cache(mock_cache_get):
    """Cache hit: returns cached value immediately without touching edgartools."""
    from data.scrapers.edgar import fetch_edgar_filings_text
    with patch("data.scrapers.edgar.Company") as MockCompany:
        result = fetch_edgar_filings_text("AAPL")
        MockCompany.assert_not_called()

    assert len(result) == 1
    assert result[0]["text"] == "cached text"


@patch("data.scrapers.edgar.cache.set_json")
@patch("data.scrapers.edgar.cache.get_json", return_value=None)
@patch("data.scrapers.edgar.set_identity")
@patch("data.scrapers.edgar.Company")
def test_fetch_edgar_text_truncated_to_200k(
    MockCompany, mock_set_identity, mock_cache_get, mock_cache_set
):
    """Text output must never exceed 200 000 characters."""
    fake_filing = MagicMock()
    fake_filing.obj.side_effect = Exception("no sections")
    fake_filing.text.return_value = "X" * 300_000
    fake_filing.filing_date = "2024-01-01"
    MockCompany.return_value.get_filings.return_value.latest.return_value = fake_filing

    from data.scrapers.edgar import fetch_edgar_filings_text
    result = fetch_edgar_filings_text("BIGDOC")

    assert result
    assert len(result[0]["text"]) <= 200_000
