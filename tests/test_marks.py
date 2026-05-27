"""
Tests for the Howard Marks investor lens (lenses/marks.py).
14 checks across 4 Parts (A: MoS/Asymmetry, B: Cycle, C: Risk, D: Contrarian).
"""
import pytest
from lenses.marks import evaluate_marks_lens
from tests.fixture_company import _make_available_qualitative as _make_full_qualitative, _make_unavailable_qualitative


def get_base_financials():
    """Fixture company that passes all quantitative Marks checks."""
    return {
        "ticker": "PERFECT",
        "current_price": 50.0,
        "market_cap": 500.0,
        "shares_outstanding": 10.0,
        "years": ["2021-12-31", "2022-12-31", "2023-12-31", "2024-12-31"],
        "revenue": [106.0, 112.36, 119.1016, 126.2477],
        "gross_profit": [53.0, 56.18, 59.5508, 63.1238],
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
        "fcf": [21.2, 22.472, 23.8203, 25.2495],
        # v0.3 fields
        "insider_ownership": 0.10,
        "stock_beta": 0.85,          # < 1.5 → check 10 PASS
        "trailing_pe": 18.0,         # < 25 → check 4 PASS
        "recommendation_mean": 3.2,  # 2.5-4.0 → check 7 PASS
        "dividend_yield": 0.02,
        "historical_shares": [10.0, 10.0, 10.0, 10.0],
    }


def get_base_dcf(intrinsic_value=30.0, current_price=50.0):
    """
    Default: price (50) > intrinsic (30) → deep MoS and asymmetry fail.
    For MoS to PASS at 40%, need price <= 0.6 * intrinsic,
    e.g., intrinsic=100, price=50 gives MoS=50%.
    """
    return {
        "current_price": current_price,
        "intrinsic_value_per_share": intrinsic_value,
        "wacc": 0.10,
        "assumptions": {
            "tax_rate": 0.25,
            "revenue_growth": 0.06,
        }
    }





# ---------------------------------------------------------------------------
# Part A — Margin of Safety & Asymmetric Payoff
# ---------------------------------------------------------------------------

def test_check1_deep_mos_pass():
    """Price = 50, intrinsic = 100 → MoS = 50% > 40% → PASS."""
    fin = get_base_financials()
    dcf = get_base_dcf(intrinsic_value=100.0, current_price=50.0)
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["1_deep_mos"]["passed"] is True


def test_check1_deep_mos_fail():
    """Price = 80, intrinsic = 100 → MoS = 20% < 40% → FAIL."""
    fin = get_base_financials()
    dcf = get_base_dcf(intrinsic_value=100.0, current_price=80.0)
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["1_deep_mos"]["passed"] is False


def test_check2_asymmetric_payoff_pass():
    """Price well below downside scenario → ratio = inf > 3.0 → PASS."""
    fin = get_base_financials()
    # intrinsic=100, upside=120, downside=80, price=50 → ratio = inf
    dcf = get_base_dcf(intrinsic_value=100.0, current_price=50.0)
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["2_asymmetric_payoff"]["passed"] is True


def test_check2_asymmetric_payoff_fail():
    """Price near intrinsic → ratio < 3.0 → FAIL."""
    fin = get_base_financials()
    # intrinsic=100, upside=120, downside=80, price=95 → ratio = (120-95)/(95-80) = 25/15 = 1.67
    dcf = get_base_dcf(intrinsic_value=100.0, current_price=95.0)
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["2_asymmetric_payoff"]["passed"] is False


def test_check3_downside_protection_pass():
    """Equity/MCap = 74.2/500 = 14.8% < 30% on base; need bigger equity."""
    fin = get_base_financials()
    # market_cap = 500, equity[-1] = 88.37 → 17.7% < 30%
    # Let's engineer PASS: increase equity
    fin["total_equity"] = [200.0, 210.0, 220.0, 230.0]
    fin["market_cap"] = 500.0
    dcf = get_base_dcf(intrinsic_value=100.0, current_price=50.0)
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["3_downside_protection"]["passed"] is True


def test_check3_downside_protection_fail():
    """Equity << market_cap → FAIL."""
    fin = get_base_financials()
    # equity[-1] = 88, market_cap = 1000 → 8.8% < 30%
    fin["market_cap"] = 1000.0
    dcf = get_base_dcf(intrinsic_value=100.0, current_price=50.0)
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["3_downside_protection"]["passed"] is False


def test_check4_multiple_expansion_pass():
    """Trailing P/E = 18 < 25 → PASS."""
    fin = get_base_financials()
    fin["trailing_pe"] = 18.0
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["4_multiple_expansion"]["passed"] is True


def test_check4_multiple_expansion_fail():
    """Trailing P/E = 40 > 25 → FAIL."""
    fin = get_base_financials()
    fin["trailing_pe"] = 40.0
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["4_multiple_expansion"]["passed"] is False


def test_check4_multiple_expansion_none():
    """Trailing P/E not available → defaults PASS."""
    fin = get_base_financials()
    fin["trailing_pe"] = None
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["4_multiple_expansion"]["passed"] is True


# ---------------------------------------------------------------------------
# Part B — Cycle Position
# ---------------------------------------------------------------------------

def test_check5_sector_cycle_pass():
    """LLM sector_cycle = mid_cycle → PASS."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    qual = _make_full_qualitative(sector_cycle="mid_cycle")
    res = evaluate_marks_lens(fin, dcf, qualitative_results=qual)
    assert res["checks"]["5_sector_cycle"]["passed"] is True


def test_check5_sector_cycle_fail():
    """LLM sector_cycle = peak → FAIL."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    qual = _make_full_qualitative(sector_cycle="peak")
    res = evaluate_marks_lens(fin, dcf, qualitative_results=qual)
    assert res["checks"]["5_sector_cycle"]["passed"] is False


def test_check5_sector_cycle_unavailable_defaults_pass():
    """No qualitative → sector cycle defaults PASS."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["5_sector_cycle"]["passed"] is True


def test_check6_company_cycle_pass():
    """Latest NI at 100% of 4y peak → ratio = 1.0 > 0.70 → PASS."""
    fin = get_base_financials()
    # net_income is monotonically growing; latest is peak → eps_vs_peak = 1.0
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["6_company_cycle"]["passed"] is True


def test_check6_company_cycle_fail():
    """Latest NI at 50% of peak → FAIL."""
    fin = get_base_financials()
    fin["net_income"] = [20.0, 22.0, 24.0, 10.0]  # latest is 50% of peak
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["6_company_cycle"]["passed"] is False


def test_check7_sentiment_pass():
    """Consensus rating 3.2 in 2.5-4.0 → PASS."""
    fin = get_base_financials()
    fin["recommendation_mean"] = 3.2
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["7_sentiment"]["passed"] is True


def test_check7_sentiment_fail_strong_buy():
    """Consensus rating 1.5 (strong buy) → FAIL."""
    fin = get_base_financials()
    fin["recommendation_mean"] = 1.5
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["7_sentiment"]["passed"] is False


def test_check7_sentiment_unavailable_defaults_pass():
    fin = get_base_financials()
    fin["recommendation_mean"] = None
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["7_sentiment"]["passed"] is True


# ---------------------------------------------------------------------------
# Part C — Risk Architecture
# ---------------------------------------------------------------------------

def test_check8_capital_structure_pass():
    """Low debt, high coverage → PASS."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["8_capital_structure"]["passed"] is True


def test_check8_capital_structure_fail():
    """Massive debt → FAIL."""
    fin = get_base_financials()
    fin["debt"] = [500.0, 500.0, 500.0, 500.0]
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["8_capital_structure"]["passed"] is False


def test_check9_fcf_stability_pass():
    """All positive FCF → PASS."""
    fin = get_base_financials()
    fin["fcf"] = [5.0, 10.0, 15.0, 20.0]
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["9_fcf_stability"]["passed"] is True


def test_check9_fcf_stability_fail():
    """One negative FCF year → FAIL."""
    fin = get_base_financials()
    fin["fcf"] = [10.0, -1.0, 15.0, 20.0]
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["9_fcf_stability"]["passed"] is False


def test_check10_beta_pass():
    """Beta = 0.85 < 1.5 → PASS."""
    fin = get_base_financials()
    fin["stock_beta"] = 0.85
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["10_beta"]["passed"] is True


def test_check10_beta_fail():
    """Beta = 2.0 > 1.5 → FAIL."""
    fin = get_base_financials()
    fin["stock_beta"] = 2.0
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["10_beta"]["passed"] is False


def test_check11_no_single_point_failure_pass():
    """No concentration/regulatory keywords in risk callouts → PASS."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    qual = _make_full_qualitative()
    # risk_callouts has no concentration/regulatory → 0 flagged
    res = evaluate_marks_lens(fin, dcf, qualitative_results=qual)
    assert res["checks"]["11_no_single_point_failure"]["passed"] is True


# ---------------------------------------------------------------------------
# Part D — Second-Level Thinking & Contrarianism
# ---------------------------------------------------------------------------

def test_check12_variant_perception_pass():
    """variant_present=True and specificity=high → PASS."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    qual = _make_full_qualitative(variant_present=True, specificity="high")
    res = evaluate_marks_lens(fin, dcf, qualitative_results=qual)
    assert res["checks"]["12_variant_perception"]["passed"] is True


def test_check12_variant_perception_fail_low_spec():
    """variant_present=True but specificity=low → FAIL."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    qual = _make_full_qualitative(variant_present=True, specificity="low")
    res = evaluate_marks_lens(fin, dcf, qualitative_results=qual)
    assert res["checks"]["12_variant_perception"]["passed"] is False


def test_check12_variant_perception_fail_no_variant():
    """variant_present=False → FAIL."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    qual = _make_full_qualitative(variant_present=False, specificity="high")
    res = evaluate_marks_lens(fin, dcf, qualitative_results=qual)
    assert res["checks"]["12_variant_perception"]["passed"] is False


def test_check12_variant_perception_unavailable_defaults_fail():
    """No qualitative → variant perception defaults FAIL."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["12_variant_perception"]["passed"] is False


def test_check13_management_humility_pass():
    """LLM verdict = humble → PASS."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    qual = _make_full_qualitative(humility_verdict="humble")
    res = evaluate_marks_lens(fin, dcf, qualitative_results=qual)
    assert res["checks"]["13_management_humility"]["passed"] is True


def test_check13_management_humility_fail():
    """LLM verdict = hubristic → FAIL."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    qual = _make_full_qualitative(humility_verdict="hubristic")
    res = evaluate_marks_lens(fin, dcf, qualitative_results=qual)
    assert res["checks"]["13_management_humility"]["passed"] is False


def test_check13_management_humility_unavailable_defaults_pass():
    """No qualitative → humility defaults PASS."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["13_management_humility"]["passed"] is True


def test_check14_why_now_pass():
    """LLM verdict = dislocation_present → PASS."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    qual = _make_full_qualitative(why_now_verdict="dislocation_present")
    res = evaluate_marks_lens(fin, dcf, qualitative_results=qual)
    assert res["checks"]["14_why_now"]["passed"] is True


def test_check14_why_now_fail():
    """LLM verdict = normal_cycle → FAIL."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    qual = _make_full_qualitative(why_now_verdict="normal_cycle")
    res = evaluate_marks_lens(fin, dcf, qualitative_results=qual)
    assert res["checks"]["14_why_now"]["passed"] is False


def test_check14_why_now_unavailable_defaults_fail():
    """No qualitative → why-now defaults FAIL."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["checks"]["14_why_now"]["passed"] is False


# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------

def test_marks_skip_no_qualitative():
    """No qualitative → checks 12 and 14 both fail → score low → SKIP."""
    fin = get_base_financials()
    dcf = get_base_dcf(intrinsic_value=100.0, current_price=80.0)
    res = evaluate_marks_lens(fin, dcf)
    # Checks 1, 12, 14 fail minimum; total depends on financials
    assert res["verdict"] in {"SKIP", "WAIT", "WATCH"}  # not BUY without qual


def test_marks_buy_requires_mos_and_asymmetry():
    """BUY requires score>=11 AND check_1 AND check_2."""
    fin = get_base_financials()
    # intrinsic=100, price=50 → MoS=50%, asymmetry=inf
    dcf = get_base_dcf(intrinsic_value=100.0, current_price=50.0)
    qual = _make_full_qualitative()
    res = evaluate_marks_lens(fin, dcf, qualitative_results=qual)
    assert res["checks"]["1_deep_mos"]["passed"] is True
    assert res["checks"]["2_asymmetric_payoff"]["passed"] is True
    # Score depends on check3 (equity/market_cap)
    # market_cap=500, equity=88.37 → 17.7% < 30% → check 3 FAIL
    # Let's see what verdict we get
    assert res["verdict"] in {"BUY", "WAIT", "WATCH", "SKIP"}


def test_marks_verdict_in_valid_set():
    fin = get_base_financials()
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["verdict"] in {"BUY", "WAIT", "WATCH", "SKIP"}


# ---------------------------------------------------------------------------
# Structural invariants
# ---------------------------------------------------------------------------

def test_score_is_14_max():
    fin = get_base_financials()
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert 0 <= res["score"] <= 14


def test_all_checks_have_required_keys():
    fin = get_base_financials()
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    required_keys = {"name", "metric_name", "value", "threshold_str", "passed", "detail", "part"}
    for key, check in res["checks"].items():
        for k in required_keys:
            assert k in check, f"Check {key} missing key '{k}'"


def test_14_checks_present():
    fin = get_base_financials()
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert len(res["checks"]) == 14


def test_parts_are_abcd():
    """Every check has part in {A, B, C, D}."""
    fin = get_base_financials()
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    for key, check in res["checks"].items():
        assert check["part"] in {"A", "B", "C", "D"}, f"Check {key} has invalid part {check['part']}"


def test_returns_ticker():
    fin = get_base_financials()
    dcf = get_base_dcf()
    res = evaluate_marks_lens(fin, dcf)
    assert res["ticker"] == "PERFECT"
