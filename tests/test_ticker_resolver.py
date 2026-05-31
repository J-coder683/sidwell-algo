import pytest
from unittest.mock import patch, MagicMock

from data import ticker_resolver
from data.ticker_resolver import (
    resolve_ticker_from_input,
    search_companies,
    get_local_index,
    _build_local_index,
    _looks_like_ticker,
    _normalize,
    _US_NAME_TO_TICKER,
)

@pytest.fixture
def mock_index():
    return {
        "Dual Listed Ltd": {"nse_symbol": "DUAL", "bse_code": "500100"},
        "BSE Only Ltd": {"bse_code": "500200"},
        "NSE Only Ltd": {"nse_symbol": "NSEONLY"},
    }

# --- OLD TESTS RESTORED ---

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


@patch("data.ticker_resolver.get_local_index", return_value={})
@patch("data.ticker_resolver.cache.get_json", return_value=None)
@patch("data.ticker_resolver.cache.set_json")
@patch("data.ticker_resolver._resolve_via_screener_search", return_value=None)
def test_resolve_us_name_hardcoded(mock_screener, mock_set_json, mock_get_json, mock_get_index):
    """Apple should hit the hardcoded map without any HTTP call."""
    ticker, source = resolve_ticker_from_input("Apple")
    assert ticker == "AAPL"
    assert source == "us_name_hardcoded"


@patch("data.ticker_resolver.get_local_index", return_value={})
@patch("data.ticker_resolver.cache.get_json", return_value=None)
@patch("data.ticker_resolver.cache.set_json")
@patch("data.ticker_resolver.requests.get")
def test_resolve_indian_name_via_screener(mock_get, mock_set_json, mock_get_json, mock_get_index):
    """Reliance should be resolved via screener.in search."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"name": "Reliance Industries Ltd", "url": "/company/RELIANCE/"}]
    mock_get.return_value = mock_resp
    
    ticker, source = resolve_ticker_from_input("Reliance")
    assert ticker == "RELIANCE.NS"
    assert source == "indian_name"


@patch("data.ticker_resolver.get_local_index", return_value={})
@patch("data.ticker_resolver.cache.get_json", return_value={"ticker": "AAPL", "source": "us_name_hardcoded"})
@patch("data.ticker_resolver.requests.get")
def test_resolve_uses_cache_on_second_call(mock_get, mock_get_json, mock_get_index):
    """Cached lookup should return immediately without HTTP."""
    ticker, source = resolve_ticker_from_input("Apple")
    assert ticker == "AAPL"
    mock_get.assert_not_called()


@patch("data.ticker_resolver.get_local_index", return_value={})
@patch("data.ticker_resolver.cache.get_json", return_value=None)
@patch("data.ticker_resolver.cache.set_json")
@patch("data.ticker_resolver.requests.get")
def test_resolve_unresolved_returns_input_uppercased(mock_get, mock_set_json, mock_get_json, mock_get_index):
    """If both regions fail, return uppercased input flagged as unresolved."""
    mock_screener_fail = MagicMock()
    mock_screener_fail.status_code = 200
    mock_screener_fail.json.return_value = []  # empty results
    
    mock_stockanalysis_fail = MagicMock()
    mock_stockanalysis_fail.status_code = 200
    mock_stockanalysis_fail.json.return_value = []
    
    mock_get.side_effect = [mock_screener_fail, mock_stockanalysis_fail]
    
    ticker, source = resolve_ticker_from_input("Zorglax 9000")
    assert ticker == "ZORGLAX 9000"
    assert source == "unresolved"

# --- NEW TESTS ---

@patch("data.ticker_resolver.get_local_index")
@patch("data.ticker_resolver._resolve_via_screener_search", return_value=None)
@patch("data.ticker_resolver._resolve_via_stockanalysis_search", return_value=None)
@patch("data.cache.get_json", return_value=None)
@patch("data.cache.set_json")
def test_resolve_ticker_offline(mock_set_json, mock_get_json, mock_stockanalysis, mock_screener, mock_get_index, mock_index):
    mock_get_index.return_value = mock_index
    
    # 1. Dual listed -> .NS
    ticker, source = resolve_ticker_from_input("Dual Listed Ltd")
    assert ticker == "DUAL.NS"
    assert source == "indian_name"
    
    # 2. BSE only -> .BO
    ticker, source = resolve_ticker_from_input("BSE Only Ltd")
    assert ticker == "500200.BO"
    assert source == "indian_name"
    
    # 3. NSE only -> .NS
    ticker, source = resolve_ticker_from_input("NSE Only Ltd")
    assert ticker == "NSEONLY.NS"
    assert source == "indian_name"


@patch("data.ticker_resolver.get_local_index")
@patch("data.ticker_resolver._resolve_via_screener_search", return_value=None)
def test_search_companies_offline(mock_screener, mock_get_index, mock_index):
    mock_get_index.return_value = mock_index
    
    # Search dual
    res = search_companies("dual")
    assert len(res) >= 1
    assert res[0][1] == "DUAL.NS"
    
    # Search bse only
    res = search_companies("bse only")
    assert len(res) >= 1
    assert res[0][1] == "500200.BO"
    
    # Search nse only
    res = search_companies("nse only")
    assert len(res) >= 1
    assert res[0][1] == "NSEONLY.NS"


@patch("data.ticker_resolver._build_local_index")
@patch("data.cache.get_json", return_value=None)
@patch("data.cache.set_json")
def test_get_local_index_partial_no_cache(mock_set_json, mock_get_json, mock_build):
    # Simulate a partial build: NSE succeeds, BSE fails
    mock_build.return_value = ({"NSE Only Ltd": {"nse_symbol": "NSEONLY"}}, {"nse": True, "bse": False})
    
    index = get_local_index()
    assert "NSE Only Ltd" in index
    # Assert cache.set_json was NOT called because it was partial
    mock_set_json.assert_not_called()
    
    # Simulate complete build
    mock_build.return_value = ({"NSE Only Ltd": {"nse_symbol": "NSEONLY"}}, {"nse": True, "bse": True})
    index = get_local_index()
    # Now it should be called
    mock_set_json.assert_called_once()
