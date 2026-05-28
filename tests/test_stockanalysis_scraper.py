import pytest
from unittest.mock import patch, MagicMock
from data.scrapers.stockanalysis import _extract_dividend_yield, _resolve_sveltekit_node, fetch_stockanalysis_financials

def test_extract_dividend_yield():
    assert _extract_dividend_yield(".04 (0.33%)") == 0.0033
    assert _extract_dividend_yield(".20 (1.5%)") == 0.015
    assert _extract_dividend_yield(".00 (0.00%)") == 0.0
    assert _extract_dividend_yield(None) == 0.0
    assert _extract_dividend_yield("N/A") == 0.0
    assert _extract_dividend_yield("-") == 0.0

def test_resolve_sveltekit_node_base():
    data = [
        {"revenue": 1, "grossProfit": 2},
        [3, 4],
        [5, 6],
        100,
        200,
        50,
        100
    ]
    resolved = _resolve_sveltekit_node(data, 0)
    assert resolved["revenue"] == [100, 200]
    assert resolved["grossProfit"] == [50, 100]

@patch("data.cache.get_json")
def test_fetch_stockanalysis_dispatches_via_cache(mock_get_json):
    # Setup mock to return a dummy dict when checking cache
    mock_get_json.side_effect = [{"revenue": [100]}, {"current_price": 150.0}]
    
    res = fetch_stockanalysis_financials("AAPL")
    assert res["current_price"] == 150.0
    assert res["revenue"] == [100]
    # Verify cache get was called for financials and price
    assert mock_get_json.call_count == 2
