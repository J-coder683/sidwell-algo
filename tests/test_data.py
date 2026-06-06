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
    mock_get_json.return_value = 4.25
    rate = public.fetch_risk_free_rate("AAPL")
    assert rate == 0.0425
    mock_fred_class.assert_not_called()
    
    mock_get_json.return_value = None
    mock_get_api_key.return_value = "mock_key"
    mock_fred_inst = MagicMock()
    mock_fred_class.return_value = mock_fred_inst
    mock_series = pd.Series([4.1, 4.2, 4.3])
    mock_fred_inst.get_series.return_value = mock_series
    
    rate = public.fetch_risk_free_rate("AAPL")
    assert rate == 0.043
    mock_set_json.assert_called_with("fred_DGS10.json", 4.3)

def test_find_column():
    cols = ["Industry Name", "Number of firms", "Beta", "D/E Ratio", "Effective Tax rate", "Unlevered beta", "Cash/Firm value", "Unlevered beta corrected for cash", "HiLo Risk"]
    
    assert _find_column(cols, ["unlevered beta", "unlevered_beta"]) == "Unlevered beta"
    assert _find_column(cols, ["average levered beta", "levered beta", "average beta", "beta"]) == "Beta"
    assert _find_column(cols, ["d/e ratio", "debt/equity", "d/e"]) == "D/E Ratio"

@patch("pandas.read_excel")
@patch("data.public.get_beta_sheet_name")
def test_parse_damodaran_beta_sheet(mock_get_sheet, mock_read_excel):
    mock_get_sheet.return_value = "Emerging Markets"
    
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
    
    res_fail = _parse_damodaran_beta_sheet("dummy.xlsx", "Chemical (Nonexistent)", True)
    assert res_fail["industry_unlevered_beta"] == 0.95
    assert res_fail["industry_levered_beta"] == 1.15


@patch("pandas.read_excel")
@patch("data.public.get_beta_sheet_name")
def test_levered_beta_not_conflated_with_unlevered(mock_get_sheet, mock_read_excel):
    """Regression: the real Damodaran betaGlobal.xls names the levered column 'Beta'
    (not 'Average Beta'), and 'Unlevered beta' contains the substring 'levered beta'.
    The old matcher (['average levered beta','levered beta','average beta']) skipped
    'Beta' and wrongly grabbed 'Unlevered beta', making levered == unlevered. The
    levered column must resolve to 'Beta' and stay distinct from the unlevered value."""
    mock_get_sheet.return_value = "Industry Averages"
    df = pd.DataFrame({
        "Industry Name": ["Retail (Special Lines)"],
        "Number of firms": [649],
        "Beta": [0.9604],                                  # <- real sheet's levered column name
        "D/E Ratio": [0.1836],
        "Effective Tax rate": [0.1692],
        "Unlevered beta": [0.8447],
        "Unlevered beta corrected for cash": [0.9036],     # must NOT be picked for either
    })
    mock_read_excel.return_value = df
    res = _parse_damodaran_beta_sheet("dummy.xls", "Retail (Special Lines)", False)
    assert abs(res["industry_levered_beta"] - 0.9604) < 1e-4, res
    assert abs(res["industry_unlevered_beta"] - 0.8447) < 1e-4, res
    assert res["industry_levered_beta"] != res["industry_unlevered_beta"]

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


from data.documents import discover_documents
from pathlib import Path

@patch("data.scrapers.edgar.fetch_edgar_financials")
def test_fetch_financials_us_dispatches_to_edgar(mock_edgar):
    mock_edgar.return_value = {"ticker": "AAPL"}
    res = public.fetch_financials("AAPL")
    assert res["ticker"] == "AAPL"
    mock_edgar.assert_called_once_with("AAPL")


@patch("data.scrapers.screener.fetch_screener_financials")
def test_fetch_financials_india_dispatches_to_screener(mock_scr):
    mock_scr.return_value = {"ticker": "RELIANCE.NS"}
    res = public.fetch_financials("RELIANCE.NS")
    assert res["ticker"] == "RELIANCE.NS"
    mock_scr.assert_called_once_with("RELIANCE.NS")


from data.public import get_industry_for_ticker, _normalize_sector_key, TICKER_INDUSTRY_MAP

def test_get_industry_scraped_industry_priority():
    financials = {'scraped_industry': 'Semiconductors'}
    ind, src = get_industry_for_ticker('MU', financials)
    assert ind == 'Semiconductor'
    assert src == 'scraped_industry'

def test_get_industry_scraped_sector_fallback():
    financials = {'scraped_industry': None, 'scraped_sector': 'Technology'}
    ind, src = get_industry_for_ticker('AAPL', financials)
    assert ind == 'Software (System & Application)'
    assert src == 'scraped_sector'

def test_get_industry_ticker_override_wins():
    TICKER_INDUSTRY_MAP['TEST_OVERRIDE'] = 'Chemical (Specialty)'
    financials = {'scraped_industry': 'Semiconductors'}
    ind, src = get_industry_for_ticker('TEST_OVERRIDE', financials)
    assert ind == 'Chemical (Specialty)'
    assert src == 'ticker_override'
    del TICKER_INDUSTRY_MAP['TEST_OVERRIDE']

def test_get_industry_default_fallback_logs_warning(caplog):
    financials = {'scraped_industry': 'unknown-industry'}
    ind, src = get_industry_for_ticker('UNKNOWN', financials)
    assert ind == 'Chemical (Specialty)'
    assert src == 'default'
    assert 'Unmapped sector for UNKNOWN' in caplog.text

def test_normalize_sector_key_handles_nbsp_and_case():
    assert _normalize_sector_key('Software—Infrastructure\xa0') == 'software-infrastructure'


def test_fetch_damodaran_signature_matches_callers():
    """Regression for v0.6.4.5: fetch_damodaran_data signature changed in v0.6.4.2
    to accept financials as second arg. Both value.py and app.py must call it correctly.
    This test asserts the signature contract so future drift breaks tests, not Streamlit Cloud."""
    import inspect
    from data.public import fetch_damodaran_data
    sig = inspect.signature(fetch_damodaran_data)
    params = list(sig.parameters.keys())
    assert 'financials' in params, (
        f"fetch_damodaran_data must accept 'financials' argument; got {params}"
    )
    assert len(params) == 2, (
        f"Expected exactly 2 params (ticker, financials), got {params}"
    )
