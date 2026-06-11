from reports.explain import build_check_explanation

def test_build_check_explanation_pass():
    check = {
        "name": "High return on invested capital",
        "threshold_str": "> 15.0%",
        "passed": True,
        "detail": "4y avg = 24.30% > 15%",
        "framework_reasoning": "ROIC > cost of capital sustainably is value creation."
    }
    res = build_check_explanation("2_roic", check)
    assert res["status"] == "pass"
    assert res["status_label"] == "PASSED"
    assert res["title"] == "2. High return on invested capital"
    assert res["what_why"] == "ROIC > cost of capital sustainably is value creation."
    assert res["finding"] == "4y avg = 24.30% > 15%"
    assert res["judgment"] == "Passed \u2014 the result clears the bar (> 15.0%)."

def test_build_check_explanation_fail():
    check = {
        "name": "Margin of safety",
        "threshold_str": "> 25.0%",
        "passed": False,
        "detail": "mos = 10.00%",
        "framework_reasoning": "Graham's 25% discount."
    }
    res = build_check_explanation("12_margin_of_safety", check)
    assert res["status"] == "fail"
    assert res["status_label"] == "REJECTED"
    assert res["judgment"] == "Rejected \u2014 the result misses the bar (> 25.0%)."

def test_build_check_explanation_na():
    check = {
        "name": "Margin of safety",
        "threshold_str": "> 25.0%",
        "passed": False,
        "applicable": False,
        "detail": "N/A \u2014 DCF not applicable to banks.",
        "framework_reasoning": "Graham's 25% discount."
    }
    res = build_check_explanation("12_margin_of_safety", check)
    assert res["status"] == "na"
    assert res["status_label"] == "NOT ASSESSED"
    assert res["judgment"] == "Not assessed \u2014 N/A \u2014 DCF not applicable to banks.; excluded from the score, so it neither helps nor hurts the verdict."

def test_build_check_explanation_already_numbered():
    check = {
        "name": "1. Moat",
        "passed": True,
    }
    res = build_check_explanation("1_moat", check)
    assert res["title"] == "1. Moat"
