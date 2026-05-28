import os
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from data import public
from data.public import _find_column, _parse_damodaran_beta_sheet

@patch("data.public.get_fred_api_key")
@patch("data.public.Fred")
@patch("data.cache.get_json")
@patch("data.cache.set_json")
def test_fetch_risk_free_rate(mock_set_json, mock_get_json, mock_fred_class, mock_get_api_key):
    # Test cache hit
    mock_get_json.return_value = 4.25
    rate = public.fetch_risk_free_rate("AAPL")
    assert rate == 0.0425
    mock_fred_class.assert_not_called()
    
    # Test cache miss
    mock_get_json.return_value = None
    mock_get_api_key.return_value = "mock_key"
    
    # Mock FRED instance and series
    mock_fred_inst = MagicMock()
    mock_fred_class.return_value = mock_fred_inst
    mock_series = pd.Series([4.1, 4.2, 4.3])
    mock_fred_inst.get_series.return_value = mock_series
    
    rate = public.fetch_risk_free_rate("AAPL")
    assert rate == 0.043
    mock_set_json.assert_called_with("fred_DGS10.json", 4.3)

@patch("yfinance.Ticker")
@patch("data.cache.get_json")
@patch("data.cache.set_json")
def test_fetch_financials(mock_set_json, mock_get_json, mock_ticker_class):
    # Test cache hit
    mock_get_json.side_effect = [
        {"ticker": "MOCK.NS", "current_price": 10.0, "revenue": [100]}, # financials key
        {"current_price": 10.0} # price key
    ]
    res = public.fetch_financials("MOCK.NS")
    assert res["ticker"] == "MOCK.NS"
    assert res["current_price"] == 10.0
    mock_ticker_class.assert_not_called()
    
    # Test cache miss
    mock_get_json.side_effect = [None, None]
    
    # Mock yfinance Ticker return statements
    mock_ticker = MagicMock()
    mock_ticker_class.return_value = mock_ticker
    
    mock_ticker.info = {
        "currentPrice": 25.0,
        "marketCap": 250.0,
        "sharesOutstanding": 10.0
    }
    
    # Setup dataframes for financials
    cols = [pd.Timestamp("2021-12-31"), pd.Timestamp("2022-12-31"), pd.Timestamp("2023-12-31"), pd.Timestamp("2024-12-31")]
    
    mock_ticker.income_stmt = pd.DataFrame(
        data=[
            [82.64, 90.91, 100.0, 110.0],
            [41.32, 45.45, 50.0, 55.0],
            [12.40, 13.64, 15.0, 16.5],
            [0.0, 0.0, 0.0, 0.0],
            [3.12, 3.43, 3.77, 4.15],
            [12.40, 13.64, 15.0, 16.5],
            [9.28, 10.21, 11.22, 12.34]
        ],
        index=["Total Revenue", "Gross Profit", "EBIT", "Interest Expense", "Tax Provision", "Pretax Income", "Net Income"],
        columns=cols
    )
    mock_ticker.balance_sheet = pd.DataFrame(
        data=[
            [100.0, 100.0, 100.0, 100.0],
            [80.0, 80.0, 80.0, 80.0],
            [20.0, 20.0, 20.0, 20.0],
            [0.0, 0.0, 0.0, 0.0]
        ],
        index=["Total Assets", "Stockholders Equity", "Cash And Cash Equivalents", "Total Debt"],
        columns=cols
    )
    mock_ticker.cashflow = pd.DataFrame(
        data=[
            [8.40, 9.29, 10.22, 11.24],
            [-2.48, -2.73, -3.0, -3.3],
            [1.65, 1.82, 2.0, 2.2],
            [0.0, 0.0, 0.0, 0.0]
        ],
        index=["Operating Cash Flow", "Capital Expenditure", "Depreciation And Amortization", "Change In Working Capital"],
        columns=cols
    )
    
    res = public.fetch_financials("MOCK.NS")
    assert res["current_price"] == 25.0
    assert res["revenue"] == [82.64, 90.91, 100.0, 110.0]
    assert res["capex"] == [2.48, 2.73, 3.0, 3.3] # converted absolute value
    assert res["fcf"] == pytest.approx([5.92, 6.56, 7.22, 7.94]) # CFO - CapEx: 10.22 - 3.0 = 7.22, 11.24 - 3.3 = 7.94

def test_find_column():
    cols = ["Industry Name", "Number of firms", "Beta", "D/E Ratio", "Effective Tax rate", "Unlevered beta", "Cash/Firm value", "Unlevered beta corrected for cash", "HiLo Risk"]
    
    assert _find_column(cols, ["unlevered beta", "unlevered_beta"]) == "Unlevered beta"
    assert _find_column(cols, ["average levered beta", "levered beta", "average beta", "beta"]) == "Beta"
    assert _find_column(cols, ["d/e ratio", "debt/equity", "d/e"]) == "D/E Ratio"

@patch("pandas.read_excel")
@patch("data.public.get_beta_sheet_name")
def test_parse_damodaran_beta_sheet(mock_get_sheet, mock_read_excel):
    mock_get_sheet.return_value = "Emerging Markets"
    
    # Mock dataframe with some data
    df = pd.DataFrame({
        "Industry Name": ["Advertising", "Aerospace/Defense", "Chemical (Specialty)", "Shoe"],
        "Number of firms": [50, 40, 100, 20],
        "Average Beta": [1.1, 1.2, 1.35, 0.9],
        "D/E Ratio": ["10.0%", "20.0%", "30.0%", "40.0%"],
        "Unlevered beta": [1.0, 1.1, 1.15, 0.8]
    })
    mock_read_excel.return_value = df
    
    res = _parse_damodaran_beta_sheet("dummy.xlsx", "Chemical (Specialty)", True)
    assert abs(res["industry_levered_beta"] - 1.35) < 1e-4
    assert abs(res["industry_unlevered_beta"] - 1.15) < 1e-4
    assert abs(res["industry_de_ratio"] - 0.3) < 1e-4
    
    # Exact match failure -> fallback to default
    res_fail = _parse_damodaran_beta_sheet("dummy.xlsx", "Chemical (Nonexistent)", True)
    assert res_fail["industry_unlevered_beta"] == 0.95
    assert res_fail["industry_levered_beta"] == 1.15

@patch("builtins.open", new_callable=MagicMock)
@patch("os.makedirs")
def test_single_report_written(mock_makedirs, mock_open):
    from reports.render import render_markdown_report
    
    financials = {
        "ticker": "ASIANPAINT.NS",
        "current_price": 2657.80,
        "market_cap": 2547884752896.0,
        "shares_outstanding": 958644295.0,
        "years": ["2022-03-31", "2023-03-31", "2024-03-31", "2025-03-31"],
        "revenue": [289413500000.0, 343887100000.0, 353954200000.0, 338151700000.0],
        "gross_profit": [105638100000.0, 131424200000.0, 152211200000.0, 142228100000.0],
        "ebit": [42831300000.0, 58332800000.0, 75529400000.0, 53300900000.0],
        "interest_expense": [954100000.0, 1444500000.0, 2051700000.0, 2270200000.0],
        "tax_provision": [11029100000.0, 14935000000.0, 17900800000.0, 13933600000.0],
        "pretax_income": [41877200000.0, 56888300000.0, 73477700000.0, 51030700000.0],
        "net_income": [30305700000.0, 41064500000.0, 54602300000.0, 36672300000.0],
        "total_assets": [229844500000.0, 257980000000.0, 299240900000.0, 303713700000.0],
        "total_equity": [138115600000.0, 159922300000.0, 187283000000.0, 193998100000.0],
        "cash": [6217200000.0, 5231000000.0, 8293400000.0, 4452800000.0],
        "debt": [15868400000.0, 19326200000.0, 24743800000.0, 22902900000.0],
        "capex": [5507000000.0, 14456100000.0, 24960800000.0, 18300700000.0],
        "depreciation": [8163600000.0, 8580200000.0, 8530000000.0, 10263400000.0],
        "working_capital_change": [-27952200000.0, -7721100000.0, 100500000.0, -5701800000.0],
        "fcf": [4357900000.0, 27478200000.0, 36075200000.0, 25938900000.0]
    }
    
    dcf_res = {
        "current_price": 2657.80,
        "market_cap": 2547884752896.0,
        "intrinsic_value_per_share": 291.69,
        "wacc": 0.1320,
        "enterprise_value": 298070000000.0,
        "equity_value": 279620000000.0,
        "pv_fcf": 101120000000.0,
        "pv_terminal_value": 196960000000.0,
        "terminal_value": 366060000000.0,
        "projections": [
            {"year": "Year 1", "revenue": 3.5e11, "ebit": 6.1e10, "tax": 1.5e10, "depreciation": 9.5e9, "capex": 1.6e10, "working_capital_change": -1.2e10, "fcf": 2.6e10, "discount_factor": 1.13, "pv_fcf": 2.3e10}
        ],
        "assumptions": {
            "revenue_growth": 0.0532,
            "tax_rate": 0.2606,
            "deprec_ratio": 0.02,
            "capex_ratio": 0.03,
            "nwc_ratio": 0.0,
            "terminal_growth_rate": 0.04,
            "risk_free_rate": 0.0712,
            "mature_market_erp": 0.0423,
            "country_risk_premium": 0.0218,
            "total_erp": 0.0641,
            "beta_unlevered": 0.95,
            "beta_levered": 0.96,
            "cost_of_equity": 0.1325,
            "cost_of_debt": 0.0991,
            "debt_source": "filings",
            "equity_weight": 0.99,
            "debt_weight": 0.01,
            "wacc": 0.1320,
            "shares_outstanding": 9.58e8,
            "latest_cash": 4.45e9,
            "latest_debt": 2.29e10
        }
    }
    
    buffett_res = {
        "ticker": "ASIANPAINT.NS",
        "score": 5,
        "verdict": "SKIP",
        "reason": "Skip",
        "checks": {
            "7_margin_of_safety": {
                "value": -8.11,
                "passed": False
            }
        }
    }
    
    # Mock checks dict for all 8 checks to avoid KeyError
    for c_id in ["1_moat", "2_roic", "3_fcf", "4_balance_sheet", "5_roe_leverage", "6_predictability", "7_margin_of_safety", "8_understandable"]:
        if c_id not in buffett_res["checks"]:
            buffett_res["checks"][c_id] = {}
        c = buffett_res["checks"][c_id]
        c.setdefault("name", c_id)
        c.setdefault("metric_name", c_id)
        c.setdefault("value", -8.11 if c_id == "7_margin_of_safety" else 1.0)
        c.setdefault("threshold_str", "> 25.0%" if c_id == "7_margin_of_safety" else "target")
        c.setdefault("passed", False if c_id == "7_margin_of_safety" else True)
        c.setdefault("detail", "detail")
            
    render_markdown_report(dcf_res, buffett_res, financials)
    
    # Assert that open was called exactly once to write a file
    # and it was called for the canonical report file.
    mock_open.assert_called_once()
    args, kwargs = mock_open.call_args
    filename = str(args[0])
    assert filename.replace("\\", "/").endswith("output/asianpaint_report.md")

def test_no_duplicate_reports(tmp_path, mock_financials):
    from reports.render import render_markdown_report
    
    dcf_res = {
        "current_price": 50.0,
        "market_cap": 500.0,
        "intrinsic_value_per_share": 27.02,
        "wacc": 0.1230,
        "enterprise_value": 276.94,
        "equity_value": 270.25,
        "pv_fcf": 81.35,
        "pv_terminal_value": 195.59,
        "terminal_value": 349.29,
        "projections": [
            {"year": "Year 1", "revenue": 146.41, "ebit": 29.28, "tax": 7.32, "depreciation": 4.39, "capex": 7.32, "working_capital_change": 0.00, "fcf": 19.03, "discount_factor": 1.1230, "pv_fcf": 16.95}
        ],
        "assumptions": {
            "revenue_growth": 0.10,
            "ebit_margin": 0.20,
            "tax_rate": 0.25,
            "deprec_ratio": 0.03,
            "capex_ratio": 0.05,
            "nwc_ratio": 0.00,
            "terminal_growth_rate": 0.04,
            "risk_free_rate": 0.06,
            "mature_market_erp": 0.05,
            "country_risk_premium": 0.02,
            "total_erp": 0.07,
            "beta_unlevered": 0.90,
            "beta_levered": 0.93,
            "cost_of_equity": 0.1249,
            "cost_of_debt": 0.10,
            "debt_source": "Calculated: int_expense/debt = 10.00%",
            "equity_weight": 0.9615,
            "debt_weight": 0.0385,
            "wacc": 0.1230,
            "shares_outstanding": 10.0,
            "latest_cash": 13.31,
            "latest_debt": 20.0
        }
    }
    
    buffett_res = {
        "ticker": "FICTITIOUS.NS",
        "score": 7,
        "verdict": "WAIT",
        "reason": "Wait",
        "checks": {}
    }
    for c_id in ["1_moat", "2_roic", "3_fcf", "4_balance_sheet", "5_roe_leverage", "6_predictability", "7_margin_of_safety", "8_understandable"]:
        buffett_res["checks"][c_id] = {
            "name": c_id, "metric_name": c_id, "value": 1.0, "threshold_str": "threshold", "passed": True, "detail": "detail"
        }
    
    render_markdown_report(dcf_res, buffett_res, mock_financials, output_dir=tmp_path)
    matches = list(tmp_path.glob("*_report.md"))
    assert len(matches) == 1, f"Expected exactly one report file, found: {matches}"


# ---------------------------------------------------------------------------
# data/documents.py tests (v0.2)
# ---------------------------------------------------------------------------

from data.documents import discover_documents, _classify, _extract_text, get_drive_path
from pathlib import Path


def test_discover_documents_missing_folder_returns_empty(tmp_path, monkeypatch):
    """Non-existent ticker folder → empty list, no exception."""
    monkeypatch.setenv("SIDWELL_DRIVE_PATH", str(tmp_path))
    result = discover_documents("NOTEXIST.NS")
    assert result == []


def test_discover_documents_finds_pdfs(tmp_path, monkeypatch):
    """Folder with PDFs → list with correct length."""
    monkeypatch.setenv("SIDWELL_DRIVE_PATH", str(tmp_path))
    ticker_dir = tmp_path / "TEST.NS"
    ticker_dir.mkdir()

    # Create minimal "PDFs" (pdfplumber will fail gracefully on non-PDF bytes)
    (ticker_dir / "test_concall.pdf").write_bytes(b"%PDF fake")
    (ticker_dir / "test_deck.pdf").write_bytes(b"%PDF fake")

    # Mock _extract_text to avoid pdfplumber parsing real bytes
    with patch("data.documents._extract_text", return_value="extracted text"):
        result = discover_documents("TEST.NS")

    assert len(result) == 2
    filenames = [d["filename"] for d in result]
    assert "test_concall.pdf" in filenames
    assert "test_deck.pdf" in filenames
    assert all("hash" in d for d in result)
    assert all("text" in d for d in result)


def test_classify_all_keyword_types():
    """_classify correctly identifies each document type by keyword."""
    assert _classify("q4fy25_concall_transcript.pdf") == "transcript"
    assert _classify("investor_presentation_2025.pdf") == "investor_deck"
    assert _classify("annual_report_mda_section.pdf") == "mda"
    assert _classify("unknown_document.pdf") == "unknown"
    # Case insensitive
    assert _classify("EARNINGS_CALL_Q3.pdf") == "transcript"


def test_extract_text_failure_returns_empty_string(tmp_path):
    """_extract_text returns '' on any pdfplumber failure — no exception."""
    bad_pdf = tmp_path / "not_a_real.pdf"
    bad_pdf.write_bytes(b"this is not a valid PDF")
    result = _extract_text(bad_pdf)
    assert result == ""

@patch("data.public._fetch_financials_fmp")
def test_fetch_financials_us_dispatches_to_fmp(mock_fmp):
    mock_fmp.return_value = {"ticker": "AAPL"}
    res = public.fetch_financials("AAPL")
    assert res["ticker"] == "AAPL"
    mock_fmp.assert_called_once_with("AAPL")

@patch("data.public._fetch_financials_yfinance")
def test_fetch_financials_india_dispatches_to_yfinance(mock_yf):
    mock_yf.return_value = {"ticker": "ASIANPAINT.NS"}
    res = public.fetch_financials("ASIANPAINT.NS")
    assert res["ticker"] == "ASIANPAINT.NS"
    mock_yf.assert_called_once_with("ASIANPAINT.NS")

@patch("data.public.requests.Session.get")
@patch("os.getenv")
@patch("data.cache.get_json")
@patch("data.cache.set_json")
def test_fmp_normalized_shape_matches_yfinance_shape(mock_set_json, mock_get_json, mock_getenv, mock_get):
    mock_getenv.return_value = "mock_fmp_key"
    mock_get_json.return_value = None
    
    # Mock all FMP endpoints
    def mock_fmp_responses(url, timeout=10):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        
        if "/profile" in url:
            mock_resp.json.return_value = [{"price": 100.0, "mktCap": 1000.0, "beta": 1.2, "lastDiv": 1.5, "dividendYield": 0.015}]
        elif "/income-statement" in url:
            mock_resp.json.return_value = [{"date": f"202{i}-12-31", "revenue": 100, "grossProfit": 50, "operatingIncome": 20, "interestExpense": 2, "incomeTaxExpense": 3, "incomeBeforeTax": 18, "netIncome": 15} for i in range(4, 0, -1)]
        elif "/balance-sheet-statement" in url:
            mock_resp.json.return_value = [{"totalAssets": 200, "totalStockholdersEquity": 100, "cashAndCashEquivalents": 50, "totalDebt": 30, "intangibleAssets": 10, "goodwill": 5} for i in range(4, 0, -1)]
        elif "/cash-flow-statement" in url:
            mock_resp.json.return_value = [{"capitalExpenditure": -10, "depreciationAndAmortization": 5, "changeInWorkingCapital": -2, "freeCashFlow": 15} for i in range(4, 0, -1)]
        elif "/key-metrics" in url:
            mock_resp.json.return_value = [{"weightedAverageShsOut": 10, "peRatio": 15.0} for i in range(4, 0, -1)]
        elif "/shares-float" in url:
            mock_resp.json.return_value = [{"insiderHolding": 5.0}]
        elif "/analyst-stock-recommendations" in url:
            mock_resp.json.return_value = [{"ratingScore": 2.5}]
        return mock_resp
        
    mock_get.side_effect = mock_fmp_responses
    
    fmp_res = public.fetch_financials("AAPL")
    
    # Run original yfinance test to get its shape
    with patch("yfinance.Ticker") as mock_ticker_class:
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.info = {"currentPrice": 25.0, "marketCap": 250.0, "sharesOutstanding": 10.0}
        cols = [pd.Timestamp(f"202{i}-12-31") for i in range(1, 5)]
        mock_ticker.income_stmt = pd.DataFrame([[100]*4]*7, index=["Total Revenue", "Gross Profit", "EBIT", "Interest Expense", "Tax Provision", "Pretax Income", "Net Income"], columns=cols)
        mock_ticker.balance_sheet = pd.DataFrame([[100]*4]*4, index=["Total Assets", "Stockholders Equity", "Cash And Cash Equivalents", "Total Debt"], columns=cols)
        mock_ticker.cashflow = pd.DataFrame([[100]*4]*4, index=["Operating Cash Flow", "Capital Expenditure", "Depreciation And Amortization", "Change In Working Capital"], columns=cols)
        
        yf_res = public._fetch_financials_yfinance("ASIANPAINT.NS")
        
    assert set(fmp_res.keys()) == set(yf_res.keys())

@patch("data.public.requests.Session.get")
@patch("os.getenv")
@patch("data.cache.get_json")
def test_fmp_429_surfaces_friendly_error(mock_get_json, mock_getenv, mock_get):
    mock_getenv.return_value = "mock_fmp_key"
    mock_get_json.return_value = None
    
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_get.return_value = mock_resp
    
    with pytest.raises(ValueError, match="FMP daily quota"):
        public.fetch_financials("AAPL")

@patch("data.public.requests.Session.get")
@patch("os.getenv")
@patch("data.cache.get_json")
@patch("data.cache.set_json")
def test_fmp_capex_sign_flipped_to_positive(mock_set_json, mock_get_json, mock_getenv, mock_get):
    mock_getenv.return_value = "mock_fmp_key"
    mock_get_json.return_value = None
    
    def mock_fmp_responses(url, timeout=10):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        if "/profile" in url:
            mock_resp.json.return_value = [{"price": 100.0, "mktCap": 1000.0}]
        elif "/income-statement" in url:
            mock_resp.json.return_value = [{"date": f"202{i}-12-31"} for i in range(4, 0, -1)]
        elif "/balance-sheet-statement" in url:
            mock_resp.json.return_value = [{}] * 4
        elif "/cash-flow-statement" in url:
            # FMP returns negative for outflows
            mock_resp.json.return_value = [{"capitalExpenditure": -25.5}] * 4
        elif "/key-metrics" in url:
            mock_resp.json.return_value = [{}] * 4
        elif "/shares-float" in url:
            mock_resp.json.return_value = []
        elif "/analyst-stock-recommendations" in url:
            mock_resp.json.return_value = []
        return mock_resp
        
    mock_get.side_effect = mock_fmp_responses
    
    res = public.fetch_financials("AAPL")
    assert all(cx == 25.5 for cx in res["capex"])

@patch("data.public.requests.Session.get")
@patch("os.getenv")
@patch("data.cache.get_json")
def test_fmp_403_legacy_endpoint_surfaces_clear_error(mock_get_json, mock_getenv, mock_get):
    mock_getenv.return_value = "mock_fmp_key"
    mock_get_json.return_value = None
    
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.text = "Legacy Endpoint"
    mock_get.return_value = mock_resp
    
    with pytest.raises(ValueError, match="FMP returned 403 Legacy Endpoint"):
        public.fetch_financials("AAPL")
