import pytest
from lenses.buffett import evaluate_buffett_lens
from tests.fixture_company import _make_available_qualitative, _make_unavailable_qualitative


def get_perfect_financials():
    """Fixture company that passes all 14 Buffett checks."""
    return {
        "ticker": "PERFECT",
        "current_price": 50.0,
        "market_cap": 500.0,
        "shares_outstanding": 10.0,
        "years": ["2021-12-31", "2022-12-31", "2023-12-31", "2024-12-31"],
        # Revenue growing at exactly 6%
        "revenue": [106.0, 112.36, 119.1016, 126.2477],
        # Gross margin exactly 50% — stable → moat PASS
        "gross_profit": [53.0, 56.18, 59.5508, 63.1238],
        # EBIT margin 25%
        "ebit": [26.5, 28.09, 29.7754, 31.5619],
        "interest_expense": [1.0, 1.0, 1.0, 1.0],
        "tax_provision": [6.625, 7.0225, 7.4438, 7.8905],
        "pretax_income": [26.5, 28.09, 29.7754, 31.5619],
        "net_income": [19.875, 21.0675, 22.3315, 23.6714],
        "total_assets": [106.0, 112.36, 119.1016, 126.2477],
        "total_equity": [74.2, 78.652, 83.3711, 88.3734],
        # Cash > 50% of debt → liquidity PASS
        "cash": [31.8, 33.708, 35.7305, 37.8743],
        "debt": [10.0, 10.0, 10.0, 10.0],
        "capex": [5.3, 5.618, 5.9551, 6.3124],
        "depreciation": [2.12, 2.2472, 2.3820, 2.5250],
        "working_capital_change": [0.0, 0.0, 0.0, 0.0],
        "fcf": [21.2, 22.472, 23.8203, 25.2495],
        # v0.3 additional fields
        "insider_ownership": 0.10,           # > 5% → owner orientation hard PASS
        "stock_beta": 0.85,
        "trailing_pe": 18.0,
        "recommendation_mean": 3.0,
        "dividend_yield": 0.02,              # > 0 → capital returned
        "historical_shares": [10.0, 10.0, 10.0, 10.0],  # flat → anti-dilution PASS
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





# ---------------------------------------------------------------------------
# BUY / WAIT / SKIP verdict tests (no qualitative)
# ---------------------------------------------------------------------------

def test_buffett_lens_buy():
    """Perfect company at 50% of intrinsic, no qualitative → soft checks 11 & 14
    are N/A and excluded; scored 12/12 → BUY (ratio cutoff 12/14)."""
    financials = get_perfect_financials()
    dcf_res = get_perfect_dcf(100.0)

    res = evaluate_buffett_lens(financials, dcf_res)

    assert res["max_score"] == 12   # 11 (coherence) & 14 (holdability) excluded — no qualitative
    assert res["score"] == 12
    assert res["verdict"] == "BUY"


def test_buffett_lens_buy_full_data_scores_14():
    """With qualitative available and positive, all 14 checks fire → 14/14, BUY.
    Verifies the ratio cutoff reproduces the original absolute behavior on full data."""
    financials = get_perfect_financials()
    dcf_res = get_perfect_dcf(100.0)
    qualitative = _make_available_qualitative()

    res = evaluate_buffett_lens(financials, dcf_res, qualitative_results=qualitative)

    assert res["max_score"] == 14
    assert res["score"] == 14
    assert res["verdict"] == "BUY"


def test_buffett_lens_wait():
    """Perfect company but price > intrinsic → MoS fails → WAIT."""
    financials = get_perfect_financials()
    dcf_res = get_perfect_dcf(100.0)
    dcf_res["current_price"] = 90.0  # MoS fails

    res = evaluate_buffett_lens(financials, dcf_res)

    assert res["checks"]["12_margin_of_safety"]["passed"] is False
    assert res["score"] == 11       # 12 applicable (11 & 14 N/A), all pass except MoS
    assert res["max_score"] == 12
    assert res["verdict"] == "WAIT"


def test_buffett_lens_skip():
    """Ruin multiple checks → score < 10 → SKIP."""
    financials = get_perfect_financials()
    # Ruin moat: volatile gross margin
    financials["gross_profit"] = [10.0, 45.0, 10.0, 60.0]
    # Ruin FCF margin: < 10%
    financials["fcf"] = [1.0, 1.0, 1.0, 1.0]
    # Ruin balance sheet: excessive debt
    financials["debt"] = [200.0, 200.0, 200.0, 200.0]
    # Ruin ROE: low equity
    financials["total_equity"] = [10.0, 10.0, 10.0, 10.0]
    # Ruin anti-dilution: shares grew 20%
    financials["historical_shares"] = [10.0, 10.5, 11.5, 12.0]

    dcf_res = get_perfect_dcf(100.0)
    dcf_res["current_price"] = 95.0

    res = evaluate_buffett_lens(financials, dcf_res)

    assert res["verdict"] == "SKIP"
    assert res["score"] < res["max_score"] * 10 / 14   # below WATCH ratio


# ---------------------------------------------------------------------------
# Part B — Financial Health checks
# ---------------------------------------------------------------------------

def test_check7_liquidity_cushion_pass():
    """Cash > 50% of debt → check 7 passes."""
    financials = get_perfect_financials()
    # cash[-1] = 37.87, debt[-1] = 10.0 → ratio = 3.79 > 0.5
    dcf_res = get_perfect_dcf(100.0)

    res = evaluate_buffett_lens(financials, dcf_res)
    assert res["checks"]["7_liquidity_cushion"]["passed"] is True


def test_check7_liquidity_cushion_fail():
    """Cash < 50% of debt → check 7 fails."""
    financials = get_perfect_financials()
    financials["cash"] = [1.0, 1.0, 1.0, 1.0]   # tiny cash
    financials["debt"] = [100.0, 100.0, 100.0, 100.0]  # large debt
    dcf_res = get_perfect_dcf(100.0)

    res = evaluate_buffett_lens(financials, dcf_res)
    assert res["checks"]["7_liquidity_cushion"]["passed"] is False


# ---------------------------------------------------------------------------
# Part C — Management checks
# ---------------------------------------------------------------------------

def test_check8_anti_dilution_pass():
    """Flat share count → check 8 passes."""
    financials = get_perfect_financials()
    financials["historical_shares"] = [10.0, 10.0, 10.0, 10.0]
    dcf_res = get_perfect_dcf(100.0)

    res = evaluate_buffett_lens(financials, dcf_res)
    assert res["checks"]["8_anti_dilution"]["passed"] is True


def test_check8_anti_dilution_fail():
    """Share count grew 20% → check 8 fails."""
    financials = get_perfect_financials()
    financials["historical_shares"] = [10.0, 10.0, 11.0, 12.0]
    dcf_res = get_perfect_dcf(100.0)

    res = evaluate_buffett_lens(financials, dcf_res)
    assert res["checks"]["8_anti_dilution"]["passed"] is False


def test_check8_anti_dilution_no_data():
    """No share count data → defaults PASS."""
    financials = get_perfect_financials()
    financials["historical_shares"] = []
    dcf_res = get_perfect_dcf(100.0)

    res = evaluate_buffett_lens(financials, dcf_res)
    assert res["checks"]["8_anti_dilution"]["passed"] is True
    assert "defaulted PASS" in res["checks"]["8_anti_dilution"]["detail"]


def test_check9_capital_allocation_pass():
    """ROIC stable and dividend_yield > 0 → check 9 passes."""
    financials = get_perfect_financials()
    financials["dividend_yield"] = 0.02
    dcf_res = get_perfect_dcf(100.0)

    res = evaluate_buffett_lens(financials, dcf_res)
    assert res["checks"]["9_capital_allocation"]["passed"] is True


def test_check10_owner_orientation_hard_pass():
    """Insider ownership > 5% → check 10 passes regardless of soft."""
    financials = get_perfect_financials()
    financials["insider_ownership"] = 0.10
    dcf_res = get_perfect_dcf(100.0)
    qualitative = _make_unavailable_qualitative()

    res = evaluate_buffett_lens(financials, dcf_res, qualitative_results=qualitative)
    assert res["checks"]["10_owner_orientation"]["passed"] is True


def test_check10_owner_orientation_soft_pass():
    """Insider ownership < 5% but LLM says owner_oriented → check 10 passes."""
    financials = get_perfect_financials()
    financials["insider_ownership"] = 0.01  # < 5% → hard FAIL
    dcf_res = get_perfect_dcf(100.0)
    qualitative = _make_available_qualitative(owner_verdict="owner_oriented")

    res = evaluate_buffett_lens(financials, dcf_res, qualitative_results=qualitative)
    assert res["checks"]["10_owner_orientation"]["passed"] is True


def test_check10_owner_orientation_both_fail():
    """Insider < 5% AND LLM says management_class → check 10 fails."""
    financials = get_perfect_financials()
    financials["insider_ownership"] = 0.01
    dcf_res = get_perfect_dcf(100.0)
    qualitative = _make_available_qualitative(owner_verdict="management_class")

    res = evaluate_buffett_lens(financials, dcf_res, qualitative_results=qualitative)
    assert res["checks"]["10_owner_orientation"]["passed"] is False


def test_check11_mgmt_coherence_excluded_when_unavailable():
    """When qualitative unavailable, check 11 is N/A and excluded from the denominator."""
    financials = get_perfect_financials()
    dcf_res = get_perfect_dcf(100.0)
    qualitative = _make_unavailable_qualitative()

    res = evaluate_buffett_lens(financials, dcf_res, qualitative_results=qualitative)
    check11 = res["checks"]["11_mgmt_coherence"]
    assert check11["applicable"] is False
    assert check11["passed"] is False
    assert "excluded" in check11["detail"].lower()


def test_check11_mgmt_coherence_fails_on_incoherent():
    """When qualitative says incoherent, check 11 fails."""
    financials = get_perfect_financials()
    dcf_res = get_perfect_dcf(100.0)
    qualitative = _make_available_qualitative(coherence_verdict="incoherent")

    res = evaluate_buffett_lens(financials, dcf_res, qualitative_results=qualitative)
    assert res["checks"]["11_mgmt_coherence"]["passed"] is False


# ---------------------------------------------------------------------------
# Part D — Price & Holdability checks
# ---------------------------------------------------------------------------

def test_check13_blacklist_fail():
    """Ticker starting with BTC fails hard blacklist."""
    financials = get_perfect_financials()
    financials["ticker"] = "BTC-USD"
    dcf_res = get_perfect_dcf(100.0)

    res = evaluate_buffett_lens(financials, dcf_res)
    assert res["checks"]["13_hard_blacklist"]["passed"] is False


def test_check14_holdability_excluded_when_unavailable():
    """When qualitative unavailable, check 14 is N/A and excluded from the denominator."""
    financials = get_perfect_financials()
    dcf_res = get_perfect_dcf(100.0)
    qualitative = _make_unavailable_qualitative()

    res = evaluate_buffett_lens(financials, dcf_res, qualitative_results=qualitative)
    check14 = res["checks"]["14_holdability"]
    assert check14["applicable"] is False
    assert check14["passed"] is False


def test_check14_holdability_fails_on_not_holdable():
    """When qualitative says not_holdable_20y, check 14 fails."""
    financials = get_perfect_financials()
    dcf_res = get_perfect_dcf(100.0)
    qualitative = _make_available_qualitative(holdability_verdict="not_holdable_20y")

    res = evaluate_buffett_lens(financials, dcf_res, qualitative_results=qualitative)
    assert res["checks"]["14_holdability"]["passed"] is False


# ---------------------------------------------------------------------------
# Structural invariants
# ---------------------------------------------------------------------------

def test_score_is_14_max():
    financials = get_perfect_financials()
    dcf_res = get_perfect_dcf(100.0)
    qualitative = _make_available_qualitative()

    res = evaluate_buffett_lens(financials, dcf_res, qualitative_results=qualitative)
    assert 0 <= res["score"] <= 14


def test_verdict_in_valid_set():
    financials = get_perfect_financials()
    dcf_res = get_perfect_dcf(100.0)

    res = evaluate_buffett_lens(financials, dcf_res)
    assert res["verdict"] in {"BUY", "WAIT", "WATCH", "SKIP"}


def test_all_checks_have_required_keys():
    financials = get_perfect_financials()
    dcf_res = get_perfect_dcf(100.0)

    res = evaluate_buffett_lens(financials, dcf_res)
    required_keys = {"name", "metric_name", "value", "threshold_str", "passed", "detail", "part"}
    for key, check in res["checks"].items():
        for k in required_keys:
            assert k in check, f"Check {key} missing key '{k}'"


def test_14_checks_present():
    financials = get_perfect_financials()
    dcf_res = get_perfect_dcf(100.0)

    res = evaluate_buffett_lens(financials, dcf_res)
    assert len(res["checks"]) == 14
