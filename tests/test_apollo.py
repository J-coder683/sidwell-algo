import pytest
from lenses.apollo import evaluate_apollo_lens
from tests.fixture_company import (
    FIXTURE_INPUTS,
    _make_available_qualitative,
    _make_asianpaints_qualitative,
    _make_unavailable_qualitative
)

def test_apollo_score_is_16_max():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {}}
    qual = _make_available_qualitative()
    res = evaluate_apollo_lens(FIXTURE_INPUTS.copy(), dcf_res, qual)
    assert 0 <= res["score"] <= 16
    assert len(res["checks"]) == 16
    assert res["verdict"] in {"BUY", "WAIT", "WATCH", "SKIP"}

def test_apollo_all_checks_have_required_keys():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {}}
    qual = _make_available_qualitative()
    res = evaluate_apollo_lens(FIXTURE_INPUTS.copy(), dcf_res, qual)
    required_keys = {"name", "metric_name", "value", "threshold_str", "passed", "detail", "part"}
    for key, check in res["checks"].items():
        for k in required_keys:
            assert k in check, f"Check {key} missing key '{k}'"

def test_perfect_apollo_pass():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Chemical (Specialty)"}}
    fin = FIXTURE_INPUTS.copy()
    # Meet scaling, valuation, capital complexity, and FCF thresholds
    fin["market_cap"] = 2e10
    fin["debt"] = [1.5e11, 1.5e11, 1.5e11, 1.5e11]  # High debt for complexity/stress
    fin["ebit"] = [2e9, 2e9, 2e9, 2e9]
    fin["depreciation"] = [1e9, 1e9, 1e9, 1e9]
    fin["fcf"] = [1e9, 1e9, 1e9, 1e9]
    fin["interest_expense"] = [5e8, 5e8, 5e8, 5e8] 
    fin["total_assets"] = [3e11, 3e11, 3e11, 3e11]
    fin["total_intangibles"] = [0, 0, 0, 0]
    fin["goodwill"] = [0, 0, 0, 0]
    fin["revenue"] = [10e9, 10e9, 10e9, 10e9]
    fin["book_value_per_share"] = 100.0
    fin["historical_shares"] = [1e8, 1e8, 1e8, 1e8] # Price = 200, P/B = 2.0. Entry EV / EBITDA < Sector * 0.8
    # EV = 1.7e11, EBITDA = 3e9, EV/EBITDA = 56... Wait, to pass Check 1 we need EV/EBITDA < Sector(13.0)*0.8=10.4
    # So EV must be < 31e9. Let's adjust debt to 1e10.
    fin["debt"] = [1e10, 1e10, 1e10, 1e10]
    # To pass check 2 (complexity), lev > 3.5 or ic < 3.0. 
    # Lev = 10e9 / 3e9 = 3.3x. ic = 2e9 / 5e8 = 4.0. We need lev > 3.5. Debt = 11e9.
    fin["debt"] = [11e9, 11e9, 11e9, 11e9]
    # Now EV = 3.1e10. EV/EBITDA = 10.33x. Sector=13.0. 13*0.8=10.4. Passes Check 1!
    
    qual = _make_available_qualitative()
    qual.update({
        "chaos_dislocation_catalyst": {"verdict": "chaos_present"},
        "fulcrum_security_signal": {"verdict": "fulcrum_identified"},
        "abf_credit_fit": {"verdict": "abf_primary_opportunity"},
        "complexity_moat_signal": {"verdict": "high"},
        "permanent_hold_viable": {"verdict": "yes"},
        "covenant_control_potential": {"verdict": "high"}
    })
    
    res = evaluate_apollo_lens(fin, dcf_res, qual)
    assert res["verdict"] == "BUY"

def test_phalippou_failure_skips():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Chemical (Specialty)"}}
    fin = FIXTURE_INPUTS.copy()
    # Force pass pre-condition 1 (B) by passing check 5
    qual = _make_available_qualitative()
    qual.update({
        "chaos_dislocation_catalyst": {"verdict": "chaos_present"},  # Pass 5
        "fulcrum_security_signal": {"verdict": "none"},               # Fail 6
        "abf_credit_fit": {"verdict": "none"},                        # Fail 7
        "complexity_moat_signal": {"verdict": "none"},                # Fail 8
        "permanent_hold_viable": {"verdict": "none"}                  # Fail 12
    })
    fin["total_assets"] = [3e11, 3e11, 3e11, 3e11]
    fin["debt"] = [1000, 1000, 1000, 1000] # Fail 8 Hard (debt/assets < 0.55)
    
    # We also need to fail Check 9 (Domain Knowledge). Change industry.
    dcf_res["assumptions"]["target_industry"] = "Random Sector"
    
    res = evaluate_apollo_lens(fin, dcf_res, qual)
    assert res["checks"]["16_alpha_thesis"]["passed"] == False
    assert res["verdict"] == "SKIP"

def test_no_chaos_no_fulcrum_no_abf_skips():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Chemical (Specialty)"}}
    fin = FIXTURE_INPUTS.copy()
    # Fails 5, 6, 7.
    qual = _make_available_qualitative()
    qual.update({
        "chaos_dislocation_catalyst": {"verdict": "none"},
        "fulcrum_security_signal": {"verdict": "none"},
        "abf_credit_fit": {"verdict": "none"},
    })
    # Fail hard 6
    fin["debt"] = [1.0, 1.0, 1.0, 1.0]
    fin["market_cap"] = 100.0
    
    res = evaluate_apollo_lens(fin, dcf_res, qual)
    # Pre-condition 2: pass 5, 6, or 7.
    assert res["checks"]["5_chaos_catalyst"]["passed"] == False
    assert res["checks"]["6_fulcrum_security"]["passed"] == False
    assert res["checks"]["7_abf_fit"]["passed"] == False
    assert res["verdict"] == "SKIP"

def test_asianpaints_actual():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Chemical (Specialty)"}}
    qual = _make_asianpaints_qualitative()
    res = evaluate_apollo_lens(FIXTURE_INPUTS.copy(), dcf_res, qual)
    assert res["verdict"] == "SKIP"

def test_unavailable_qualitative_graceful_degrade():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Chemical (Specialty)"}}
    qual = _make_unavailable_qualitative()
    res = evaluate_apollo_lens(FIXTURE_INPUTS.copy(), dcf_res, qual)
    assert res["verdict"] in {"BUY", "WAIT", "WATCH", "SKIP"}

def test_sector_not_in_lookup_fails_check_1():
    dcf_res = {"current_price": 50.0, "intrinsic_value_per_share": 100.0, "assumptions": {"target_industry": "Alien Technology"}}
    fin = FIXTURE_INPUTS.copy()
    # Make PB high so it fails the PB fallback
    fin["market_cap"] = 10000.0
    fin["historical_shares"] = [1.0, 1.0, 1.0, 1.0]
    fin["book_value_per_share"] = 1.0 # PB = 10000.0
    qual = _make_available_qualitative()
    res = evaluate_apollo_lens(fin, dcf_res, qual)
    assert res["checks"]["1_entry_valuation"]["passed"] == False
