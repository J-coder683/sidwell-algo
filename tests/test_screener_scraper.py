import os
import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock
from data.scrapers.screener import fetch_screener_financials, _to_screener_ticker

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "screener_reliance_consolidated.html")

def test_strip_ticker_suffix():
    assert _to_screener_ticker("ASIANPAINT.NS") == "ASIANPAINT"
    assert _to_screener_ticker("RELIANCE.BO") == "RELIANCE"
    assert _to_screener_ticker("TCS.NS") == "TCS"
    assert _to_screener_ticker("INFY") == "INFY"

@patch("data.scrapers.screener.requests.get")
def test_consolidated_url_404_falls_back_to_standalone(mock_get):
    # First call returns 404, second call returns 200 with minimal HTML
    mock_404 = MagicMock()
    mock_404.status_code = 404
    mock_404.raise_for_status.side_effect = Exception("404 Client Error")
    
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.text = '''
        <html><body>
        <section id="profit-loss"><table><thead><tr><th></th><th>Mar 2023</th><th>Mar 2024</th><th>Mar 2025</th><th>Mar 2026</th></tr></thead><tbody>
        <tr><td>Sales +</td><td>100</td><td>100</td><td>100</td><td>100</td></tr>
        </tbody></table></section>
        <section id="balance-sheet"><table><thead><tr><th></th><th>Mar 2023</th><th>Mar 2024</th><th>Mar 2025</th><th>Mar 2026</th></tr></thead><tbody>
        <tr><td>Total Assets</td><td>100</td><td>100</td><td>100</td><td>100</td></tr>
        </tbody></table></section>
        <section id="cash-flow"><table><thead><tr><th></th><th>Mar 2023</th><th>Mar 2024</th><th>Mar 2025</th><th>Mar 2026</th></tr></thead><tbody>
        <tr><td>Free Cash Flow</td><td>100</td><td>100</td><td>100</td><td>100</td></tr>
        </tbody></table></section>
        </body></html>
    '''
    
    mock_get.side_effect = [mock_404, mock_200]
    
    # We also need to patch cache so it actually fetches
    with patch("data.scrapers.screener.cache.get_json", return_value=None):
        with patch("data.scrapers.screener.cache.set_json"):
            res = fetch_screener_financials("SOME_SMALL_CAP.NS")
            assert res["ticker"] == "SOME_SMALL_CAP.NS"
            assert mock_get.call_count == 2
            assert "consolidated" in mock_get.call_args_list[0][0][0]
            assert "consolidated" not in mock_get.call_args_list[1][0][0]

@patch("data.scrapers.screener.requests.get")
def test_borrowings_parses_total_not_breakdown(mock_get):
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.text = '''
        <html><body>
        <section id="profit-loss"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        <section id="balance-sheet"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody>
        <tr><td>Borrowings +</td><td>1,500.50</td></tr>
        <tr class="stripe"><td>Long term Borrowings</td><td>1000</td></tr>
        <tr class="stripe"><td>Short term Borrowings</td><td>500.50</td></tr>
        </tbody></table></section>
        <section id="cash-flow"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        </body></html>
    '''
    mock_get.return_value = mock_200
    with patch("data.scrapers.screener.cache.get_json", return_value=None), \
         patch("data.scrapers.screener.cache.set_json"):
        res = fetch_screener_financials("TEST.NS")
        assert res["debt"][-1] == 1500.50 * 1e7

@patch("data.scrapers.screener.requests.get")
def test_comma_stripped_from_numeric(mock_get):
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.text = '''
        <html><body>
        <section id="profit-loss"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody>
        <tr><td>Sales +</td><td>1,500.50</td></tr>
        </tbody></table></section>
        <section id="balance-sheet"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        <section id="cash-flow"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        </body></html>
    '''
    mock_get.return_value = mock_200
    with patch("data.scrapers.screener.cache.get_json", return_value=None), \
         patch("data.scrapers.screener.cache.set_json"):
        res = fetch_screener_financials("TEST.NS")
        assert res["revenue"][-1] == 1500.50 * 1e7

@patch("data.scrapers.screener.requests.get")
def test_dash_returns_none(mock_get):
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.text = '''
        <html><body>
        <section id="profit-loss"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody>
        <tr><td>Interest</td><td>-</td></tr>
        </tbody></table></section>
        <section id="balance-sheet"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        <section id="cash-flow"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        </body></html>
    '''
    mock_get.return_value = mock_200
    with patch("data.scrapers.screener.cache.get_json", return_value=None), \
         patch("data.scrapers.screener.cache.set_json"):
        res = fetch_screener_financials("TEST.NS")
        assert res["interest_expense"][-1] is None

@patch("data.scrapers.screener.requests.get")
def test_crore_to_rupee_conversion(mock_get):
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.text = '''
        <html><body>
        <section id="profit-loss"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody>
        <tr><td>Sales +</td><td>1500</td></tr>
        </tbody></table></section>
        <section id="balance-sheet"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        <section id="cash-flow"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        </body></html>
    '''
    mock_get.return_value = mock_200
    with patch("data.scrapers.screener.cache.get_json", return_value=None), \
         patch("data.scrapers.screener.cache.set_json"):
        res = fetch_screener_financials("TEST.NS")
        assert res["revenue"][-1] == 1.5e10

@patch("data.scrapers.screener.requests.get")
def test_promoter_percent_maps_to_insider_ownership(mock_get):
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.text = '''
        <html><body>
        <section id="profit-loss"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        <section id="balance-sheet"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        <section id="cash-flow"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        <section id="shareholding"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody>
        <tr><td>Promoters +</td><td>53.6%</td></tr>
        </tbody></table></section>
        </body></html>
    '''
    mock_get.return_value = mock_200
    with patch("data.scrapers.screener.cache.get_json", return_value=None), \
         patch("data.scrapers.screener.cache.set_json"):
        res = fetch_screener_financials("TEST.NS")
        assert res["insider_ownership"] == 0.536

@patch("data.scrapers.screener.requests.get")
def test_capex_proxy_from_investing_activity(mock_get):
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.text = '''
        <html><body>
        <section id="profit-loss"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        <section id="balance-sheet"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        <section id="cash-flow"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody>
        <tr><td>Cash from Investing Activity +</td><td>-1000</td></tr>
        </tbody></table></section>
        </body></html>
    '''
    mock_get.return_value = mock_200
    with patch("data.scrapers.screener.cache.get_json", return_value=None), \
         patch("data.scrapers.screener.cache.set_json"):
        res = fetch_screener_financials("TEST.NS")
        assert res["capex"][-1] == 1e10

@patch("data.scrapers.screener.requests.get")
def test_working_capital_change_residual_method(mock_get):
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.text = '''
        <html><body>
        <section id="profit-loss"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody>
        <tr><td>Net Profit +</td><td>200</td></tr>
        <tr><td>Depreciation</td><td>50</td></tr>
        </tbody></table></section>
        <section id="balance-sheet"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        <section id="cash-flow"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody>
        <tr><td>Cash from Operating Activity +</td><td>300</td></tr>
        </tbody></table></section>
        </body></html>
    '''
    mock_get.return_value = mock_200
    with patch("data.scrapers.screener.cache.get_json", return_value=None), \
         patch("data.scrapers.screener.cache.set_json"):
        res = fetch_screener_financials("TEST.NS")
        # 300 - 200 - 50 = 50. 50 * 1e7 = 5e8
        assert res["working_capital_change"][-1] == 5e8

@patch("data.scrapers.screener.requests.get")
def test_fetch_screener_uses_cache_on_second_call(mock_get):
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.text = '''
        <html><body>
        <section id="profit-loss"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        <section id="balance-sheet"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        <section id="cash-flow"><table><thead><tr><th></th><th>Mar 2026</th></tr></thead><tbody></tbody></table></section>
        </body></html>
    '''
    mock_get.return_value = mock_200
    
    # We do NOT patch cache here. We want it to use the real cache mechanism in memory.
    # But since it writes to disk, we use patch to just mock the cache functions.
    cached_fin = {}
    cached_price = {}
    
    def mock_get_json(key, ttl):
        if "financials" in key: return cached_fin.get(key)
        if "price" in key: return cached_price.get(key)
        return None
        
    def mock_set_json(key, val):
        if "financials" in key: cached_fin[key] = val
        if "price" in key: cached_price[key] = val
        
    with patch("data.scrapers.screener.cache.get_json", side_effect=mock_get_json), \
         patch("data.scrapers.screener.cache.set_json", side_effect=mock_set_json):
        res1 = fetch_screener_financials("TEST.NS")
        assert mock_get.call_count == 1
        res2 = fetch_screener_financials("TEST.NS")
        assert mock_get.call_count == 1  # HTTP called only once
