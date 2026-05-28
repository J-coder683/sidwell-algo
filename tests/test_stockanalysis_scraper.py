import pytest
import logging
from unittest.mock import patch, MagicMock
from data.scrapers.stockanalysis import _extract_dividend_yield, _resolve_sveltekit_node, fetch_stockanalysis_financials

def test_extract_dividend_yield():
    assert _extract_dividend_yield("$1.04 (0.33%)") == 0.0033
    assert _extract_dividend_yield("$3.20 (1.5%)") == 0.015
    assert _extract_dividend_yield("$0.00 (0.00%)") == 0.0
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
@patch("requests.get")
def test_fetch_stockanalysis_dispatches_via_cache(mock_get, mock_get_json):
    mock_get_json.side_effect = [{"revenue": [100]}, {"current_price": 150.0}]
    res = fetch_stockanalysis_financials("AAPL")
    assert res["current_price"] == 150.0
    assert res["revenue"] == [100]
    assert mock_get_json.call_count == 2
    mock_get.assert_not_called()

@patch("data.cache.get_json")
@patch("data.cache.set_json")
@patch("requests.get")
def test_stockanalysis_normalized_shape(mock_get, mock_set_json, mock_get_json):
    mock_get_json.return_value = None
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.ok = True
    
    mock_resp.json.return_value = {
        "nodes": [
            {"data": [{"financialData": 1}, 
                      {"datekey": 2, "revenue": 3, "grossProfit": 3, "operatingIncome": 3, "income_statement_provision_for_income_taxes": 3, "pretax": 3, "netIncome": 3, "sharesDiluted": 4, "epsDiluted": 5,
                       "assets": 3, "equity": 3, "totalcash": 3, "debt": 3,
                       "capex": 3, "cash_flow_statement_depreciation_and_amortization": 3, "changeInReceivables": 3, "fcf": 3,
                       "marketCap": 6, "peRatio": 6, "sharesOut": 6, "beta": 7, "quote": 8, "info": 9, "dividend": 10},
                      [11, 11, 11, 11, 11], [12, 12, 12, 12, 12], [13, 13, 13, 13, 13], [14, 14, 14, 14, 14], "100B", "1.5", {"p": 150.0}, {}, ".04 (0.33%)",
                      2025, 100, 10.0, 1.0
                      ]}
        ]
    }
    mock_get.return_value = mock_resp
    
    res = fetch_stockanalysis_financials("AAPL")
    assert "ticker" in res

@patch("data.cache.get_json")
@patch("data.cache.set_json")
@patch("requests.get")
def test_stockanalysis_capex_sign_flipped_to_positive(mock_get, mock_set_json, mock_get_json):
    mock_get_json.return_value = None
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.ok = True
    
    mock_resp.json.return_value = {
        "nodes": [
            {"data": [{"financialData": 1}, 
                      {"capex": 2, "sharesDiluted": 3, "epsDiluted": 3, "equity": 3},
                      [4, 5, 6, 7, 8], [9, 9, 9, 9, 9],
                      -25.5, -20.0, -15.0, -10.0, -5.0, 10, 1.0
                      ]}
        ]
    }
    mock_get.return_value = mock_resp
    
    res = fetch_stockanalysis_financials("AAPL")
    assert res["capex"] == [5.0, 10.0, 15.0, 20.0]

@patch("data.cache.get_json")
@patch("data.cache.set_json")
@patch("requests.get")
def test_stockanalysis_interest_expense_proxy_logs_warning(mock_get, mock_set_json, mock_get_json, caplog):
    mock_get_json.return_value = None
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.ok = True
    
    mock_resp.json.return_value = {
        "nodes": [
            {"data": [{"financialData": 1}, 
                      {"debt": 2, "sharesDiluted": 3, "epsDiluted": 3, "equity": 3},
                      [4, 4, 4, 4, 4], [5, 5, 5, 5, 5],
                      100, 10, 1.0
                      ]}
        ]
    }
    mock_get.return_value = mock_resp
    
    with caplog.at_level(logging.WARNING):
        res = fetch_stockanalysis_financials("AAPL")
        
    assert res["interest_expense"] == [5.0, 5.0, 5.0, 5.0]
    assert "interest_expense not available from stockanalysis.com" in caplog.text
