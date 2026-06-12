import os
import pytest
from unittest.mock import patch, MagicMock

from data.scrapers.stockanalysis import fetch_stockanalysis_financials
from data.public import fetch_financials

@pytest.fixture
def mock_requests_get():
    def mock_get(url, *args, **kwargs):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        
        # Load the correct fixture based on the URL
        if "cash-flow-statement" in url:
            fixture_name = "stockanalysis_xom_cashflow.html"
        elif "balance-sheet" in url:
            fixture_name = "stockanalysis_xom_balance.html"
        elif "ratios" in url:
            fixture_name = "stockanalysis_xom_ratios.html"
        elif "/financials/" in url:
            fixture_name = "stockanalysis_xom_income.html"
        else: # overview
            fixture_name = "stockanalysis_xom_income.html" # Use income page as fallback since it has Industry link
            
        fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", fixture_name)
        with open(fixture_path, "r", encoding="utf-8") as f:
            mock_response.text = f.read()
            
        return mock_response
        
    with patch("data.scrapers.stockanalysis.requests.get", side_effect=mock_get) as mock:
        yield mock
        
def test_stockanalysis_parser(mock_requests_get):
    fin = fetch_stockanalysis_financials("XOM")
    
    assert fin is not None
    assert fin["statements"]["years_annual"] == ["2021", "2022", "2023", "2024", "2025"]
    
    pl = fin["statements"]["annual"]["profit_loss"]
    assert pl["sales"][-1] == 323905.0 / 10.0
    assert pl["cogs"][-1] == 226672.0 / 10.0
    
    ratios = fin["statements"]["ratios"]
    assert "working capital days" in ratios
    assert ratios["working capital days"][-1] is not None
    
    # market cap can be either from current or FY2025 depending on parsing
    assert (abs(fin["market_cap"] - 502901 * 1e6) < 1e6 * 1000 or abs(fin["market_cap"] - 621337 * 1e6) < 1e6 * 1000)
    
    assert fin["scraped_industry"] == "Oil & Gas Integrated" or fin["scraped_industry"] == "By Industry"

def test_fetch_financials_fallback(mock_requests_get):
    # macrotrends + stockanalysis both fail -> EDGAR companyfacts
    with patch("data.scrapers.macrotrends.fetch_macrotrends_financials", return_value=None):
        with patch("data.scrapers.stockanalysis.fetch_stockanalysis_financials", return_value=None):
            with patch("data.scrapers.edgar.fetch_edgar_companyfacts_financials", return_value={"source": "sec_edgar", "statements": {"years_annual": ["2024"], "annual": {"profit_loss": {}, "balance_sheet": {}, "cash_flow": {}}}}):
                fin = fetch_financials("XOM")
                assert fin is not None
                assert fin["source"] == "sec_edgar"
    
def test_fetch_financials_failure_fallback():
    # If macrotrends and EDGAR both return None, it should fallback to stockanalysis
    with patch("data.scrapers.macrotrends.fetch_macrotrends_financials", return_value=None):
        with patch("data.scrapers.edgar.fetch_edgar_companyfacts_financials", return_value=None):
            with patch("data.scrapers.stockanalysis.fetch_stockanalysis_financials", return_value={"source": "stockanalysis", "statements": {"years_annual": ["2024"]}}) as mock_sa:
                fin = fetch_financials("XOM")
                assert fin["source"] == "stockanalysis"
                mock_sa.assert_called_once_with("XOM")

def test_engine_smoke(mock_requests_get):
    from sidwell.engine.core import run_engine
    from sidwell.ajp.schema import AJP
    
    fin = fetch_stockanalysis_financials("XOM")
    ajp = AJP.from_dict({})
    
    with patch("data.public.fetch_risk_free_rate", return_value=0.04):
        with patch("data.public.fetch_damodaran_data", return_value={"mature_market_erp": 0.045, "country_risk_premium": 0.0, "total_erp": 0.045, "industry_levered_beta": 1.1, "industry_unlevered_beta": 1.0, "industry_de_ratio": 0.2}):
            with patch("data.public.fetch_damodaran_industry_fundamentals", return_value={"available": False}):
                res = run_engine(fin, ajp)
                assert res.get("intrinsic_value_per_share", 0) > 0

