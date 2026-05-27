import pytest
from lenses.blackstone import evaluate_blackstone_lens
from tests.fixture_company import (
    FIXTURE_INPUTS,
    _make_available_qualitative,
    _make_asianpaints_qualitative,
    _make_unavailable_qualitative
)

def test_blackstone_score_is_14_max():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {}}
    qual = _make_available_qualitative()
    res = evaluate_blackstone_lens(FIXTURE_INPUTS.copy(), dcf_res, qual)
    assert 0 <= res["score"] <= 14
    assert len(res["checks"]) == 14
    assert res["verdict"] in {"BUY", "WAIT", "WATCH", "SKIP"}

def test_blackstone_all_checks_have_required_keys():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {}}
    qual = _make_available_qualitative()
    res = evaluate_blackstone_lens(FIXTURE_INPUTS.copy(), dcf_res, qual)
    required_keys = {"name", "metric_name", "value", "threshold_str", "passed", "detail", "part"}
    for key, check in res["checks"].items():
        for k in required_keys:
            assert k in check, f"Check {key} missing key '{k}'"

def test_perfect_blackstone_pass():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Household Products"}}
    fin = FIXTURE_INPUTS.copy()
    
    fin["market_cap"] = 2e11  # Huge scale
    fin["revenue"] = [100.0, 110.0, 121.0, 133.1]
    fin["gross_profit"] = [45.0, 49.5, 54.45, 59.895]  # Stable GM > 35%
    fin["ebit"] = [25.0, 27.5, 30.25, 33.275]
    fin["fcf"] = [20.0, 22.0, 24.2, 26.62]  # High FCF
    fin["debt"] = [10.0, 10.0, 10.0, 10.0]  # Low debt
    fin["interest_expense"] = [1.0, 1.0, 1.0, 1.0] # High IC
    fin["cash"] = [50.0, 50.0, 50.0, 50.0]  # High cash ratio
    
    qual = _make_available_qualitative(
        sector_cycle="mid_cycle",
        holdability_verdict="holdable_20y"
    )
    qual.update({
        "structural_tailwind_signal": {"verdict": "tailwind"},
        "multi_product_engagement_signal": {"verdict": "multi_product_potential"}
    })
    
    res = evaluate_blackstone_lens(fin, dcf_res, qual)
    assert res["verdict"] == "BUY"

def test_phalippou_failure_skips():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Household Products"}}
    fin = FIXTURE_INPUTS.copy()
    
    fin["market_cap"] = 2e11
    fin["revenue"] = [100.0, 110.0, 121.0, 133.1]
    # Mess up GM stability to fail check 2
    fin["gross_profit"] = [45.0, 20.0, 54.45, 10.0]
    # Mess up YoY growth to fail check 3
    fin["revenue"] = [100.0, 50.0, 120.0, 60.0]
    
    fin["fcf"] = [20.0, 22.0, 24.2, 26.62] 
    fin["debt"] = [10.0, 10.0, 10.0, 10.0] 
    fin["interest_expense"] = [1.0, 1.0, 1.0, 1.0] 
    fin["cash"] = [50.0, 50.0, 50.0, 50.0] 
    
    qual = _make_available_qualitative(
        holdability_verdict="unclear" # Fails check 12
    )
    qual.update({
        "structural_tailwind_signal": {"verdict": "headwind"}, # Fails check 7
        "multi_product_engagement_signal": {"verdict": "single_product_only"} # Fails check 13
    })
    
    res = evaluate_blackstone_lens(fin, dcf_res, qual)
    assert res["checks"]["14_alpha_thesis"]["passed"] == False
    assert res["verdict"] == "SKIP"

def test_part_c_failure_skips():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Household Products"}}
    fin = FIXTURE_INPUTS.copy()
    
    # Check 8: Leverage high and IC low
    fin["debt"] = [5000.0, 5000.0, 5000.0, 5000.0]
    fin["interest_expense"] = [1000.0, 1000.0, 1000.0, 1000.0]
    fin["ebit"] = [10.0, 10.0, 10.0, 10.0]
    fin["depreciation"] = [1.0, 1.0, 1.0, 1.0]
    
    # Check 9: FCF negative
    fin["fcf"] = [-10.0, -10.0, -10.0, -10.0]
    
    # Check 10: Cash ratio poor
    fin["cash"] = [0.0, 0.0, 0.0, 0.0]
    fin["market_cap"] = 1.0
    
    qual = _make_available_qualitative()
    res = evaluate_blackstone_lens(fin, dcf_res, qual)
    # Part C checks 8, 9, 10 all fail
    assert res["checks"]["8_conservative_bs"]["passed"] == False
    assert res["checks"]["9_fcf_resilience"]["passed"] == False
    assert res["checks"]["10_stress_survival"]["passed"] == False
    assert res["verdict"] == "SKIP"

def test_asianpaints_actual():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Household Products"}}
    qual = _make_asianpaints_qualitative()
    res = evaluate_blackstone_lens(FIXTURE_INPUTS.copy(), dcf_res, qual)
    assert res["verdict"] == "BUY"

def test_unavailable_qualitative_graceful_degrade():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Household Products"}}
    qual = _make_unavailable_qualitative()
    res = evaluate_blackstone_lens(FIXTURE_INPUTS.copy(), dcf_res, qual)
    assert res["verdict"] in {"BUY", "WAIT", "WATCH", "SKIP"}
