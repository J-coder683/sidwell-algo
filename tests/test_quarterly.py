import os
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from data.scrapers.screener import fetch_screener_financials
from data.scrapers.stockanalysis import fetch_stockanalysis_financials
from analysis.quarterly import derive_quarterly_signals

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "screener_reliance_consolidated.html")

# 1. Test quarterly analysis helper
def test_quarterly_signals_insufficient_data():
    res = derive_quarterly_signals({})
    assert res["ttm_revenue"] is None
    
    res = derive_quarterly_signals({"periods": ["Q1"], "revenue": [100]})
    assert res["ttm_revenue"] is None

def test_quarterly_signals_math():
    quarterly = {
        "periods": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9"],
        "revenue": [100, 110, 120, 130, 140, 150, 160, 170, 180],
        "operating_profit": [10, 11, 12, 13, 14, 15, 16, 17, 18]
    }
    res = derive_quarterly_signals(quarterly)
    
    # Last 4 Q revenue: 150 + 160 + 170 + 180 = 660
    assert res["ttm_revenue"] == 660
    # Last 4 Q op profit: 15 + 16 + 17 + 18 = 66
    assert res["ttm_operating_profit"] == 66
    
    # latest_q_yoy_growth: q9 (180) vs q5 (140) => 40 / 140 = 28.57%
    assert abs(res["latest_q_yoy_growth"] - (180 - 140) / 140) < 1e-4
    
    # ttm_yoy_growth: [150+160+170+180]=660 vs [110+120+130+140]=500
    assert abs(res["ttm_yoy_growth"] - (660 - 500) / 500) < 1e-4

def test_seasonality_flag():
    # Seasonal: Q4 is huge
    quarterly = {
        "periods": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"],
        "revenue": [10, 10, 10, 70, 10, 10, 10, 70]
    }
    res = derive_quarterly_signals(quarterly)
    assert res["seasonality_flag"] is True
    
    # Non-seasonal
    quarterly_flat = {
        "periods": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"],
        "revenue": [25, 25, 25, 25, 25, 25, 25, 25]
    }
    res2 = derive_quarterly_signals(quarterly_flat)
    assert res2["seasonality_flag"] is False

# 2. Test screener.py quarterly parser
@patch("data.scrapers.screener.requests.get")
def test_screener_quarterly_parser(mock_get, monkeypatch):
    monkeypatch.setattr("data.scrapers.screener._resolve_screener_slug", lambda t: "RELIANCE")
    
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = html

    def mock_requests_get(url, *args, **kwargs):
        if "schedules" in url:
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {}
            return resp
        return mock_resp

    mock_get.side_effect = mock_requests_get

    with patch("data.scrapers.screener.cache.get_json", return_value=None), \
         patch("data.scrapers.screener.cache.set_json"):
        fin = fetch_screener_financials("RELIANCE.NS")
        
        assert "quarterly" in fin
        q = fin["quarterly"]
        assert len(q["periods"]) > 5
        assert q["revenue"][-1] > 0
        assert q["operating_profit"][-1] > 0
        assert q["net_income"][-1] > 0
        assert q["opm"][-1] is not None

@patch("data.scrapers.screener.requests.get")
def test_screener_quarterly_absent_safe(mock_get, monkeypatch):
    monkeypatch.setattr("data.scrapers.screener._resolve_screener_slug", lambda t: "TEST")
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '<html><body><section id="profit-loss"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody><tr><td>Sales +</td><td>100</td></tr></tbody></table></section><section id="balance-sheet"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section><section id="cash-flow"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section></body></html>'
    mock_get.return_value = mock_resp
    
    with patch("data.scrapers.screener.cache.get_json", return_value=None), \
         patch("data.scrapers.screener.cache.set_json"):
        fin = fetch_screener_financials("TEST.NS")
        assert "quarterly" not in fin

# 3. Test stockanalysis.py quarterly parser
@patch("data.scrapers.stockanalysis.requests.get")
def test_stockanalysis_quarterly_parser(mock_get):
    def mock_requests_get(url, *args, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        if "?p=quarterly" in url:
            mock_response.text = '''
                <table><thead><tr><th></th><th>Current</th><th>Mar 31, 2024</th><th>Dec 31, 2023</th><th>Sep 30, 2023</th></tr></thead>
                <tbody>
                <tr><td>Revenue</td><td>110</td><td>100</td><td>90</td><td>80</td></tr>
                <tr><td>Operating Income</td><td>11</td><td>10</td><td>9</td><td>8</td></tr>
                <tr><td>Net Income</td><td>5</td><td>4</td><td>3</td><td>2</td></tr>
                </tbody></table>
            '''
        elif "financials" in url:
            mock_response.text = '''
                <table><thead><tr><th></th><th>Current</th><th>FY 2023</th><th>FY 2022</th></tr></thead>
                <tbody><tr><td>Revenue</td><td>400</td><td>300</td><td>200</td></tr></tbody></table>
            '''
        else:
            mock_response.text = "<table></table>"
            
        return mock_response
        
    mock_get.side_effect = mock_requests_get
    
    with patch("data.scrapers.stockanalysis.cache.get_json", return_value=None), \
         patch("data.scrapers.stockanalysis.cache.set_json"):
        fin = fetch_stockanalysis_financials("TEST")
        
        assert "quarterly" in fin
        q = fin["quarterly"]
        assert q["periods"] == ["Sep 30, 2023", "Dec 31, 2023", "Mar 31, 2024"]
        assert q["revenue"] == [80, 90, 100]
        assert q["operating_profit"] == [8, 9, 10]
        assert q["net_income"] == [2, 3, 4]
        assert abs(q["opm"][0] - 0.1) < 1e-4
