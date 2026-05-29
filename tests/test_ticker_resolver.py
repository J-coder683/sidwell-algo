"""Tests for v0.7.5 ticker resolver."""
from unittest.mock import patch, MagicMock
import pytest
from data.ticker_resolver import (
    resolve_ticker_from_input,
    _looks_like_ticker,
    _normalize,
    _US_NAME_TO_TICKER,
)


def test_looks_like_ticker_indian_with_suffix():
    assert _looks_like_ticker("RELIANCE.NS") is True
    assert _looks_like_ticker("ASIANPAINT.BO") is True
    assert _looks_like_ticker("tcs.ns") is True  # lowercase still recognized as ticker


def test_looks_like_ticker_us_short_uppercase():
    assert _looks_like_ticker("AAPL") is True
    assert _looks_like_ticker("MSFT") is True
    assert _looks_like_ticker("BRK.B") is True


def test_looks_like_ticker_rejects_names():
    assert _looks_like_ticker("Apple") is False
    assert _looks_like_ticker("Reliance Industries") is False
    assert _looks_like_ticker("microsoft") is False  # lowercase + not all-caps
    assert _looks_like_ticker("") is False


def test_normalize_strips_and_lowers():
    assert _normalize("  Apple Inc.  ") == "apple inc"
    assert _normalize("J.P. Morgan") == "jp morgan"


def test_resolve_passthrough_for_ticker():
    ticker, source = resolve_ticker_from_input("AAPL")
    assert ticker == "AAPL"
    assert source == "ticker"


def test_resolve_passthrough_for_indian_ticker():
    ticker, source = resolve_ticker_from_input("RELIANCE.NS")
    assert ticker == "RELIANCE.NS"
    assert source == "ticker"


def test_resolve_us_name_hardcoded():
    """Apple should hit the hardcoded map without any HTTP call."""
    with patch("data.ticker_resolver.cache.get_json", return_value=None), \
         patch("data.ticker_resolver.cache.set_json"), \
         patch("data.ticker_resolver._resolve_via_screener_search", return_value=None):
        ticker, source = resolve_ticker_from_input("Apple")
        assert ticker == "AAPL"
        assert source == "us_name_hardcoded"


def test_resolve_indian_name_via_screener():
    """Reliance should be resolved via screener.in search."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"name": "Reliance Industries Ltd", "url": "/company/RELIANCE/"}]
    with patch("data.ticker_resolver.cache.get_json", return_value=None), \
         patch("data.ticker_resolver.cache.set_json"), \
         patch("data.ticker_resolver.requests.get", return_value=mock_resp):
        ticker, source = resolve_ticker_from_input("Reliance")
        assert ticker == "RELIANCE.NS"
        assert source == "indian_name"


def test_resolve_uses_cache_on_second_call():
    """Cached lookup should return immediately without HTTP."""
    with patch("data.ticker_resolver.cache.get_json", return_value={"ticker": "AAPL", "source": "us_name_hardcoded"}), \
         patch("data.ticker_resolver.requests.get") as mock_get:
        ticker, source = resolve_ticker_from_input("Apple")
        assert ticker == "AAPL"
        mock_get.assert_not_called()


def test_resolve_unresolved_returns_input_uppercased():
    """If both regions fail, return uppercased input flagged as unresolved."""
    mock_screener_fail = MagicMock()
    mock_screener_fail.status_code = 200
    mock_screener_fail.json.return_value = []  # empty results
    with patch("data.ticker_resolver.cache.get_json", return_value=None), \
         patch("data.ticker_resolver.cache.set_json"), \
         patch("data.ticker_resolver.requests.get", return_value=mock_screener_fail):
        ticker, source = resolve_ticker_from_input("Zorglax 9000")
        assert ticker == "ZORGLAX 9000"
        assert source == "unresolved"
