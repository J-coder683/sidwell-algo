import numpy as np
from valuation.dcf import run_dcf_valuation, get_terminal_growth

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
    
    assert len(projections) == 10
    # Year 1 revenue should be 146.41 * 1.10 = 161.051
    assert abs(projections[0]["revenue"] - 161.051) < 1e-3
    # Year 1 EBIT = 161.051 * 15% = 24.15765
    assert abs(projections[0]["ebit"] - 24.15765) < 1e-3
    
    # Check that growth rate is correctly identified as 10%
    assert abs(res["assumptions"]["revenue_growth"] - 0.10) < 1e-4

def test_get_terminal_growth():
    # Known sectors
    assert abs(get_terminal_growth("Household Products", True, 0.08) - 0.055) < 1e-4
    assert abs(get_terminal_growth("Household Products", False, 0.08) - 0.030) < 1e-4
    assert abs(get_terminal_growth("Software (System & Application)", True, 0.08) - 0.050) < 1e-4
    
    # Unmapped sectors
    assert abs(get_terminal_growth("Random Unmapped", True, 0.08) - 0.040) < 1e-4
    assert abs(get_terminal_growth("Random Unmapped", False, 0.08) - 0.025) < 1e-4
    
    # Cap at Rf - 1%
    assert abs(get_terminal_growth("Household Products", True, 0.06) - 0.05) < 1e-4
    assert abs(get_terminal_growth("Tobacco", False, 0.02) - 0.01) < 1e-4

def test_degenerate_fade_case():
    financials = get_base_mock_financials()
    # Force history to 2.5% CAGR so it matches US terminal
    financials["revenue"] = [100.0, 102.5, 105.0625, 107.689] # ~2.5% CAGR
    # But wait, proj_growth is capped at 5% floor! So it will be 5%.
    # If growth is 5%, and we want g_terminal to be 5%, we can set Rf = 0.06, India mapped to Food Processing (5%).
    macro = get_base_mock_macro()
    macro["target_industry"] = "Food Processing" # 5% terminal in India
    financials["ticker"] = "TEST.NS" # India
    rf = 0.06
    
    res = run_dcf_valuation(financials, macro, rf)
    projs = res["projections"]
    assert len(projs) == 10
    
    # Stage 1 should be 5%, terminal is 5%, so Stage 2 should also be 5%
    for p in projs:
        assert abs(p["year_growth"] - 0.05) < 1e-4

def test_dcf_hand_calculation():
    # Known-answer hand calculation test for 2-stage DCF
    # Inputs:
    # Revenue_0 = 146.41, Growth = 10% (0.10), EBIT Margin = 15%, Tax = 25.17%,
    # D&A Ratio = 2%, CapEx Ratio = 3%, NWC Change Ratio = 0%
    # Ke = 9%, Kd = 6% (Rf + 2% fallback), WACC = 9%
    # Target industry default = "Chemical (Specialty)", is_india = False -> Terminal Growth = 0.025 (2.5%)
    # Rf = 0.04 -> cap is 0.03, so 0.025 is used.
    #
    # FCF effective margin = EBIT*(1-t) + D&A - CapEx = 0.15*(1-0.2517) + 0.02 - 0.03 = 0.102245
    #
    # explicit revenues:
    # Stage 1 (Y1-Y5): 10%
    # Stage 2 (Y6-Y10) fade:
    # Y6: 10% - (10%-2.5%)*0.2 = 8.5%
    # Y7: 10% - (10%-2.5%)*0.4 = 7.0%
    # Y8: 10% - (10%-2.5%)*0.6 = 5.5%
    # Y9: 10% - (10%-2.5%)*0.8 = 4.0%
    # Y10: 10% - (10%-2.5%)*1.0 = 2.5%
    #
    # Sum PV_FCFs (Years 1-10) = 150.1045
    # Terminal Value = Y10_FCF * (1 + 0.025) / (0.09 - 0.025) = 31.47752 * 1.025 / 0.065 = 496.3763
    # PV of TV = 496.3763 / 1.09^10 = 209.6747
    # Enterprise Value = 150.1045 + 209.6747 = 359.7792
    # Equity Value = 359.7792 + 20 - 0 = 379.7792
    # Intrinsic Value per share = 37.978
    
    financials = get_base_mock_financials()
    macro = get_base_mock_macro()
    rf = 0.04
    
    res = run_dcf_valuation(financials, macro, rf)
    
    assert abs(res["projections"][0]["fcf"] - 16.46666) < 1e-4
    # Check fade rates
    assert abs(res["projections"][5]["year_growth"] - 0.085) < 1e-4
    assert abs(res["projections"][9]["year_growth"] - 0.025) < 1e-4
    
    assert abs(res["pv_fcf"] - 150.1045) < 1e-2
    assert abs(res["terminal_value"] - 496.3763) < 1e-2
    assert abs(res["pv_terminal_value"] - 209.6747) < 1e-2
    assert abs(res["enterprise_value"] - 359.7792) < 1e-2
    assert abs(res["equity_value"] - 379.7792) < 1e-2
    assert abs(res["intrinsic_value_per_share"] - 37.978) < 1e-2
