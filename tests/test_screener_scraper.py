import os
import json
import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock
from data.scrapers.screener import fetch_screener_financials, _to_screener_ticker

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "screener_reliance_consolidated.html")

@pytest.fixture(autouse=True)
def mock_slug_resolver(monkeypatch):
    monkeypatch.setattr("data.scrapers.screener._resolve_screener_slug", lambda t: t.replace(".NS", "").replace(".BO", "").upper())

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
        # v0.7.4: parser still treats "-" as missing internally, but
        # fetch_screener_financials normalizes all None values to 0.0 at
        # output to prevent downstream DCF/lens crashes (NESTLEIND case).
        assert res["interest_expense"][-1] == 0.0

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

@patch("data.scrapers.screener.requests.get")
def test_extract_full_statements_structure(mock_get):
    """
    Test that the new statements dictionary is built properly:
    years_annual has all years, missing sections don't crash,
    and sub-rows are extracted if an expand button is found.
    """
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = html

    def mock_requests_get(url, *args, **kwargs):
        if "schedules" in url:
            resp = MagicMock()
            resp.status_code = 200
            # Return arbitrary mock data for any schedule request
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            parent = qs.get("parent", [""])[0]
            if parent == "Other Assets":
                resp.json.return_value = {
                    "Trade Receivables": {"Mar 2023": 100, "Mar 2024": 110},
                    "Inventory": {"Mar 2023": 50, "Mar 2024": 55}
                }
            elif parent == "Expenses":
                resp.json.return_value = {
                    "Employee Cost": {"Mar 2023": 20, "Mar 2024": 22}
                }
            else:
                resp.json.return_value = {f"{parent} sub 1": {"Mar 2024": 999}}
            return resp
        return mock_resp

    mock_get.side_effect = mock_requests_get

    with patch("data.scrapers.screener.cache.get_json", return_value=None), \
         patch("data.scrapers.screener.cache.set_json"):
        fin = fetch_screener_financials("RELIANCE.NS")

    assert "statements" in fin
    stmt = fin["statements"]

    # 1. Check years
    assert "years_annual" in stmt
    # Based on Reliance HTML, should have ~12 years
    assert len(stmt["years_annual"]) >= 8

    # 2. Check structure
    assert "annual" in stmt
    assert "profit_loss" in stmt["annual"]
    assert "balance_sheet" in stmt["annual"]
    assert "cash_flow" in stmt["annual"]

    # 3. Check ratio parsing (top ratios)
    assert "top_ratios" in stmt
    assert "market cap" in stmt["top_ratios"]

    # 4. Check sub-rows padded to len(years_annual)
    bs = stmt["annual"]["balance_sheet"]
    # We mocked "Trade Receivables"
    assert "trade receivables" in bs
    assert len(bs["trade receivables"]) == len(stmt["years_annual"])
    # The first few elements should be padded with None because the API mock only returned Mar 2023 and 2024
    assert bs["trade receivables"][-1] is None or bs["trade receivables"][-1] == 110

    # 5. Check no 1e7 multiplier for percent/ratios
    # Check return on equity
    if "ratios" in stmt and "return on equity" in stmt["ratios"]:
        roes = stmt["ratios"]["return on equity"]
        valid_roes = [r for r in roes if r is not None]
        if valid_roes:
            assert valid_roes[-1] < 1000  # i.e., not scaled by 1e7

@patch("data.scrapers.screener.requests.get")
def test_extract_full_statements_missing_sections(mock_get):
    """Missing sections should yield empty dicts, not crash."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '''
        <html><body>
        <section id="profit-loss"><table><thead><tr><th></th><th>Mar 2024</th></tr></thead><tbody>
        <tr><td>Sales</td><td>100</td></tr>
        </tbody></table></section>
        <section id="balance-sheet"><table><thead><tr><th></th><th>Mar 2024</th></tr></thead><tbody></tbody></table></section>
        <section id="cash-flow"><table><thead><tr><th></th><th>Mar 2024</th></tr></thead><tbody></tbody></table></section>
        </body></html>
    '''
    mock_get.return_value = mock_resp

    with patch("data.scrapers.screener.cache.get_json", return_value=None), \
         patch("data.scrapers.screener.cache.set_json"):
        fin = fetch_screener_financials("RELIANCE.NS")

    assert "statements" in fin
    assert fin["statements"]["ratios"] == {}
    assert fin["statements"]["quarters"] == []
    assert fin["statements"]["quarterly"]["profit_loss"] == {}
    assert fin["statements"]["shareholding"] == {}
    assert fin["statements"]["peers"] == []

@patch("data.scrapers.screener.requests.get")
def test_legacy_backward_compatibility(mock_get):
    """
    Test that the legacy keys exactly match the snapshot captured before the v0.7.8 changes.
    The test dumps the current output and compares legacy keys recursively.
    """
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    snapshot_path = os.path.join(os.path.dirname(__file__), "..", "legacy_snapshot.json")
    if not os.path.exists(snapshot_path):
        pytest.skip("legacy_snapshot.json not found, skipping backward compatibility test")
        
    with open(snapshot_path, "r", encoding="utf-8") as f:
        legacy_snapshot = json.load(f)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = html

    def mock_requests_get(url, *args, **kwargs):
        if "schedules" in url:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            parent = qs.get("parent", [""])[0].replace("+", " ")
            resp = MagicMock()
            resp.status_code = 200
            if parent == "Material Cost":
                resp.json.return_value = {"Raw Material Cost": {"Mar 2023": 100, "Mar 2024": 110, "Mar 2025": 120, "Mar 2026": 130}}
            elif parent == "Other Assets":
                resp.json.return_value = {"Cash Equivalents": {"Mar 2023": 50, "Mar 2024": 60, "Mar 2025": 70, "Mar 2026": 80}}
            elif parent == "Cash from Investing Activity":
                resp.json.return_value = {"Fixed assets purchased": {"Mar 2023": -200, "Mar 2024": -210, "Mar 2025": -220, "Mar 2026": -230}}
            elif parent == "Cash from Operating Activity":
                resp.json.return_value = {"Working capital changes": {"Mar 2023": -10, "Mar 2024": 10, "Mar 2025": -5, "Mar 2026": 15}}
            else:
                resp.json.return_value = {}
            return resp
        return mock_resp

    mock_get.side_effect = mock_requests_get

    with patch("data.scrapers.screener.cache.get_json", return_value=None), \
         patch("data.scrapers.screener.cache.set_json"):
        fin = fetch_screener_financials("RELIANCE.NS")

    # Assert legacy keys exactly match the snapshot
    for key, expected_val in legacy_snapshot.items():
        if key == "statements":
            continue
        actual_val = fin.get(key)
        assert actual_val == expected_val, f"Legacy mismatch on key: {key}. Expected: {expected_val}, Got: {actual_val}"

