import numpy as np
from valuation.dcf import run_dcf_valuation

def get_base_mock_financials():
    return {
        "ticker": "TEST",
        "current_price": 10.0,
        "market_cap": 100.0,
        "shares_outstanding": 10.0,
        "years": ["2021-12-31", "2022-12-31", "2023-12-31", "2024-12-31"],
        # exactly 10% CAGR
        "revenue": [110.0, 121.0, 133.1, 146.41],
        "gross_profit": [55.0, 60.5, 66.55, 73.205],
        "ebit": [16.5, 18.15, 19.965, 21.9615],
        "interest_expense": [0.0, 0.0, 0.0, 0.0],
        # Tax Provision / Pretax Income = 25.17%
        "tax_provision": [4.15305, 4.56836, 5.02519, 5.52771],
        "pretax_income": [16.5, 18.15, 19.965, 21.9615],
        "net_income": [12.34695, 13.58164, 14.93981, 16.43379],
        "total_assets": [100.0, 100.0, 100.0, 100.0],
        "total_equity": [80.0, 80.0, 80.0, 80.0],
        "cash": [20.0, 20.0, 20.0, 20.0],
        "debt": [0.0, 0.0, 0.0, 0.0],
        "capex": [3.3, 3.63, 3.993, 4.3923], # exactly 3%
        "depreciation": [2.2, 2.42, 2.662, 2.9282], # exactly 2%
        "working_capital_change": [0.0, 0.0, 0.0, 0.0],
        "fcf": [11.24695, 12.37164, 13.60981, 14.96979]
    }

def get_base_mock_macro():
    return {
        "mature_market_erp": 0.05,
        "country_risk_premium": 0.0,
        "total_erp": 0.05,
        "industry_levered_beta": 1.0,
        "industry_unlevered_beta": 1.0,
        "industry_de_ratio": 0.0
    }

def test_wacc_calculation():
    financials = get_base_mock_financials()
    macro = get_base_mock_macro()
    rf = 0.04
    
    res = run_dcf_valuation(financials, macro, rf)
    
    # Debt is 0, so WACC should equal Cost of Equity (CAPM)
    # Ke = Rf + Beta * ERP = 0.04 + 1.0 * 0.05 = 0.09 (9%)
    assert abs(res["wacc"] - 0.09) < 1e-4
    assert abs(res["assumptions"]["cost_of_equity"] - 0.09) < 1e-4
    assert res["assumptions"]["equity_weight"] == 1.0
    assert res["assumptions"]["debt_weight"] == 0.0

def test_explicit_projections():
    financials = get_base_mock_financials()
    macro = get_base_mock_macro()
    rf = 0.04
    
    res = run_dcf_valuation(financials, macro, rf)
    projections = res["projections"]
    
    assert len(projections) == 5
    # Year 1 revenue should be 146.41 * 1.10 = 161.051
    assert abs(projections[0]["revenue"] - 161.051) < 1e-3
    # Year 1 EBIT = 161.051 * 15% = 24.15765
    assert abs(projections[0]["ebit"] - 24.15765) < 1e-3
    
    # Check that growth rate is correctly identified as 10%
    assert abs(res["assumptions"]["revenue_growth"] - 0.10) < 1e-4

def test_dcf_hand_calculation():
    # Known-answer hand calculation test
    # Inputs:
    # Revenue_0 = 146.41, Growth = 10% (0.10), EBIT Margin = 15%, Tax = 25.17%,
    # D&A Ratio = 2%, CapEx Ratio = 3%, NWC Change Ratio = 0%
    # Ke = 9%, Kd = 6% (Rf + 2% fallback), WACC = 9%
    # Terminal Growth = min(4%, Rf - 1%) = min(4%, 3%) = 3% (0.03)
    #
    # Explicit cash flows:
    # Year 1 FCF = Revenue_1 * [EBIT_margin*(1-t) + D&A_ratio - CapEx_ratio]
    #            = 161.051 * [0.15*(1-0.2517) + 0.02 - 0.03]
    #            = 161.051 * [0.112245 + 0.02 - 0.03]
    #            = 161.051 * [0.102245]
    #            = 16.46666
    # Present Value Factor for Year 1 = 1 / 1.09 = 0.917431
    # PV of FCF Year 1 = 16.46666 * 0.917431 = 15.1070
    #
    # Let's do the same for Years 2 to 5 growing at 10%:
    # FCF_t = FCF_1 * (1.10)^(t-1)
    # FCF = [16.46666, 18.11333, 19.92466, 21.91712, 24.10884]
    # Discount Factors = [1.09, 1.1881, 1.29503, 1.41158, 1.53862]
    # PV_FCFs = [15.10703, 15.24563, 15.38553, 15.52671, 15.66904]
    # Sum PV_FCFs = 76.93394
    #
    # Terminal Value:
    # TV = FCF_5 * (1 + g_terminal) / (WACC - g_terminal)
    #    = 24.10884 * (1.03) / (0.09 - 0.03)
    #    = 24.83211 / 0.06 = 413.8684
    # PV of TV = 413.8684 / 1.53862 = 268.9867
    #
    # Enterprise Value = PV_FCFs + PV_TV = 76.93394 + 268.9867 = 345.9206
    # Equity Value = EV + Cash - Debt = 345.9206 + 20 - 0 = 365.9206
    # Intrinsic Value per share = 365.9206 / 10 = 36.592
    
    financials = get_base_mock_financials()
    macro = get_base_mock_macro()
    rf = 0.04
    
    res = run_dcf_valuation(financials, macro, rf)
    
    assert abs(res["projections"][0]["fcf"] - 16.46666) < 1e-4
    assert abs(res["pv_fcf"] - 76.93394) < 1e-3
    assert abs(res["terminal_value"] - 413.8684) < 1e-2
    assert abs(res["pv_terminal_value"] - 268.9867) < 1e-2
    assert abs(res["enterprise_value"] - 345.9206) < 1e-2
    assert abs(res["equity_value"] - 365.9206) < 1e-2
    assert abs(res["intrinsic_value_per_share"] - 36.592) < 1e-2
