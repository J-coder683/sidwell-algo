import pytest
from lenses.kkr import evaluate_kkr_lens
from tests.fixture_company import (
    FIXTURE_INPUTS, 
    _make_available_qualitative,
    _make_asianpaints_qualitative,
    _make_unavailable_qualitative
)

def test_kkr_score_is_18_max():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {}}
    qual = _make_available_qualitative()
    res = evaluate_kkr_lens(FIXTURE_INPUTS.copy(), dcf_res, qual)
    assert 0 <= res["score"] <= 18
    assert len(res["checks"]) == 18
    assert res["verdict"] in {"BUY", "WAIT", "WATCH", "SKIP"}

def test_kkr_all_checks_have_required_keys():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {}}
    qual = _make_available_qualitative()
    res = evaluate_kkr_lens(FIXTURE_INPUTS.copy(), dcf_res, qual)
    required_keys = {"name", "metric_name", "value", "threshold_str", "passed", "detail", "part"}
    for key, check in res["checks"].items():
        for k in required_keys:
            assert k in check, f"Check {key} missing key '{k}'"

def test_perfect_kkr_pass():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Chemical (Specialty)"}}
    fin = FIXTURE_INPUTS.copy()
    # Ensure EBITDA passes scale
    fin["ebit"] = [4e9, 4e9, 4e9, 5e9]
    fin["depreciation"] = [1e9, 1e9, 1e9, 1e9]
    fin["revenue"] = [10e9, 10e9, 10e9, 20e9]
    fin["fcf"] = [3e9, 3e9, 3e9, 3e9]
    fin["pretax_income"] = [3e9, 3e9, 3e9, 3e9]
    fin["tax_provision"] = [0.5e9, 0.5e9, 0.5e9, 0.5e9]
    fin["market_cap"] = 2e9
    fin["debt"] = [1e9, 1e9, 1e9, 1e9]
    fin["capex"] = [1.5e9, 1.5e9, 1.5e9, 1.5e9]
    fin["working_capital_change"] = [-2e9, -2e9, -2e9, -2e9]
    fin["gross_profit"] = [8e9, 8e9, 8e9, 18e9]
    
    qual = _make_available_qualitative(
        sector_cycle="mid_cycle",
        why_now_verdict="catalyst_present"
    )
    qual.update({
        "wc_optimization_signal": {"verdict": "high"},
        "ma_platform_potential": {"verdict": "high"},
        "mgmt_upgrade_potential": {"verdict": "high"},
        "workforce_stavros_fit": {"verdict": "mixed"},
        "willing_seller_signal": {"verdict": "willing_seller"}
    })
    
    res = evaluate_kkr_lens(fin, dcf_res, qual)
    assert res["verdict"] == "BUY"

def test_phalippou_failure_skips():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Chemical (Specialty)"}}
    fin = FIXTURE_INPUTS.copy()
    # Pass pre-condition Part A
    fin["ebit"] = [4e9, 4e9, 4e9, 5e9]
    fin["depreciation"] = [1e9, 1e9, 1e9, 1e9]
    fin["revenue"] = [10e9, 10e9, 10e9, 20e9]
    fin["fcf"] = [3e9, 3e9, 3e9, 3e9]
    fin["pretax_income"] = [3e9, 3e9, 3e9, 3e9]
    fin["tax_provision"] = [0.5e9, 0.5e9, 0.5e9, 0.5e9]
    fin["market_cap"] = 2e9
    fin["debt"] = [1e9, 1e9, 1e9, 1e9]
    fin["capex"] = [0.0, 0.0, 0.0, 0.0]
    fin["working_capital_change"] = [0.0, 0.0, 0.0, 0.0]
    fin["gross_profit"] = [10e9, 10e9, 10e9, 5.1e9]
    
    qual = _make_available_qualitative(
        sector_cycle="mid_cycle",
        why_now_verdict="catalyst_present"
    )
    # Fail qualitative levers (5, 7, 8, 9, 10, 16) to ensure sum < 4
    qual.update({
        "wc_optimization_signal": {"verdict": "unclear"},
        "ma_platform_potential": {"verdict": "unclear"},
        "mgmt_upgrade_potential": {"verdict": "unclear"},
        "workforce_stavros_fit": {"verdict": "poor"},
        "willing_seller_signal": {"verdict": "willing_seller"}
    })
    
    res = evaluate_kkr_lens(fin, dcf_res, qual)
    assert res["checks"]["18_alpha_thesis"]["passed"] == False
    assert res["verdict"] == "SKIP"

def test_part_a_failure_skips():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Chemical (Specialty)"}}
    fin = FIXTURE_INPUTS.copy()
    # Force EBITDA < threshold (e.g., 0)
    fin["ebit"] = [0.0, 0.0, 0.0, 0.0]
    fin["depreciation"] = [0.0, 0.0, 0.0, 0.0]
    qual = _make_available_qualitative()
    res = evaluate_kkr_lens(fin, dcf_res, qual)
    assert res["checks"]["1_ebitda_scale"]["passed"] == False
    assert res["verdict"] == "SKIP"

def test_asianpaints_actual():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Household Products"}}
    qual = _make_asianpaints_qualitative()
    res = evaluate_kkr_lens(FIXTURE_INPUTS.copy(), dcf_res, qual)
    assert res["verdict"] == "SKIP"

def test_unavailable_qualitative_graceful_degrade():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Household Products"}}
    qual = _make_unavailable_qualitative()
    res = evaluate_kkr_lens(FIXTURE_INPUTS.copy(), dcf_res, qual)
    assert res["verdict"] in {"BUY", "WAIT", "WATCH", "SKIP"}
