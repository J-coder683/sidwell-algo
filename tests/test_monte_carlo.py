import pytest
import numpy as np
from valuation.monte_carlo import run_monte_carlo
from valuation.dcf import run_dcf_valuation
from tests.test_dcf import get_base_mock_financials

@pytest.fixture
def base_dcf():
    fin = get_base_mock_financials()
    # Ensure current_price is set for probability calc
    fin["current_price"] = 100.0
    fin["market_cap"] = 1000.0
    
    macro = {
        "mature_market_erp": 0.05,
        "country_risk_premium": 0.0,
        "industry_unlevered_beta": 1.0,
        "target_industry": "Software"
    }
    rf = 0.04
    
    # Run a deterministic DCF to get the base results
    dcf_res = run_dcf_valuation(fin, macro, rf, overrides=None)
    return dcf_res, fin, macro, rf

def test_monte_carlo_determinism(base_dcf):
    dcf_res, fin, macro, rf = base_dcf
    
    # Run twice with the same seed
    mc1 = run_monte_carlo(dcf_res, fin, macro, rf, n=10, seed=42)
    mc2 = run_monte_carlo(dcf_res, fin, macro, rf, n=10, seed=42)
    
    assert mc1["applicable"] is True
    assert mc2["applicable"] is True
    
    # Must be exactly equal
    assert mc1["percentiles"]["p50"] == mc2["percentiles"]["p50"]
    assert mc1["mean"] == mc2["mean"]
    
def test_monte_carlo_different_seeds(base_dcf):
    dcf_res, fin, macro, rf = base_dcf
    
    mc1 = run_monte_carlo(dcf_res, fin, macro, rf, n=10, seed=42)
    mc2 = run_monte_carlo(dcf_res, fin, macro, rf, n=10, seed=99)
    
    assert mc1["applicable"] is True
    # They shouldn't be exactly the same
    assert mc1["mean"] != mc2["mean"]

def test_monte_carlo_ordering_and_prob(base_dcf):
    dcf_res, fin, macro, rf = base_dcf
    
    mc = run_monte_carlo(dcf_res, fin, macro, rf, n=20, seed=123)
    
    p10 = mc["percentiles"]["p10"]
    p25 = mc["percentiles"]["p25"]
    p50 = mc["percentiles"]["p50"]
    p75 = mc["percentiles"]["p75"]
    p90 = mc["percentiles"]["p90"]
    
    # Percentile ordering
    assert p10 <= p25 <= p50 <= p75 <= p90
    
    # Probability bounds
    prob = mc["prob_intrinsic_gt_price"]
    assert 0.0 <= prob <= 1.0

def test_monte_carlo_bank_filter(base_dcf):
    dcf_res, fin, macro, rf = base_dcf
    
    dcf_res_bank = dcf_res.copy()
    dcf_res_bank["not_applicable"] = True
    dcf_res_bank["not_applicable_reason"] = "Bank"
    
    mc = run_monte_carlo(dcf_res_bank, fin, macro, rf, n=10)
    assert mc["applicable"] is False
    assert "Bank" in mc["reason"]

def test_monte_carlo_non_positive_intrinsic(base_dcf):
    dcf_res, fin, macro, rf = base_dcf
    
    dcf_res_neg = dcf_res.copy()
    dcf_res_neg["intrinsic_value_per_share"] = -5.0
    
    mc = run_monte_carlo(dcf_res_neg, fin, macro, rf, n=10)
    assert mc["applicable"] is False
    assert "not positive" in mc["reason"]
