import pytest
from lenses.buffett import evaluate_buffett_lens

def get_perfect_financials():
    return {
        "ticker": "PERFECT",
        "current_price": 50.0,
        "market_cap": 500.0,
        "shares_outstanding": 10.0,
        "years": ["2021-12-31", "2022-12-31", "2023-12-31", "2024-12-31"],
        # Revenue growing at exactly 6%
        "revenue": [106.0, 112.36, 119.1016, 126.2477],
        # Gross margin exactly 50%
        "gross_profit": [53.0, 56.18, 59.5508, 63.1238],
        # EBIT margin 25%
        "ebit": [26.5, 28.09, 29.7754, 31.5619],
        "interest_expense": [1.0, 1.0, 1.0, 1.0],
        "tax_provision": [6.625, 7.0225, 7.4438, 7.8905],
        "pretax_income": [26.5, 28.09, 29.7754, 31.5619],
        "net_income": [19.875, 21.0675, 22.3315, 23.6714],
        "total_assets": [106.0, 112.36, 119.1016, 126.2477],
        "total_equity": [74.2, 78.652, 83.3711, 88.3734],
        "cash": [31.8, 33.708, 35.7305, 37.8743],
        "debt": [10.0, 10.0, 10.0, 10.0],
        "capex": [5.3, 5.618, 5.9551, 6.3124],
        "depreciation": [2.12, 2.2472, 2.3820, 2.5250],
        "working_capital_change": [0.0, 0.0, 0.0, 0.0],
        "fcf": [21.2, 22.472, 23.8203, 25.2495]
    }

def get_perfect_dcf(intrinsic_value=100.0):
    return {
        "current_price": 50.0,
        "intrinsic_value_per_share": intrinsic_value,
        "assumptions": {
            "tax_rate": 0.25,
            "revenue_growth": 0.06
        }
    }

def test_buffett_lens_buy():
    financials = get_perfect_financials()
    dcf_res = get_perfect_dcf(100.0)
    
    res = evaluate_buffett_lens(financials, dcf_res)
    
    assert res["score"] == 8
    assert res["verdict"] == "BUY"

def test_buffett_lens_wait():
    financials = get_perfect_financials()
    dcf_res = get_perfect_dcf(100.0)
    dcf_res["current_price"] = 90.0
    
    res = evaluate_buffett_lens(financials, dcf_res)
    
    assert res["score"] == 7
    assert res["verdict"] == "WAIT"

def test_buffett_lens_skip():
    financials = get_perfect_financials()
    # Intentionally ruin some checks to get a low score
    # Ruin Moat: Volatile Gross Margin
    financials["gross_profit"] = [10.0, 45.0, 10.0, 60.0]
    # Ruin FCF Growth: Negative growth
    financials["fcf"] = [30.0, 20.0, 15.0, 10.0]
    # Ruin Leverage: Extremely high debt
    financials["debt"] = [200.0, 200.0, 200.0, 200.0]
    # Ruin ROE & Leverage: Equity to Assets < 40% (Equity = 10, Assets = 126 -> 7.9%)
    financials["total_equity"] = [10.0, 10.0, 10.0, 10.0]
    
    dcf_res = get_perfect_dcf(100.0)
    dcf_res["current_price"] = 95.0
    
    res = evaluate_buffett_lens(financials, dcf_res)
    
    assert res["score"] < 6
    assert res["verdict"] == "SKIP"
