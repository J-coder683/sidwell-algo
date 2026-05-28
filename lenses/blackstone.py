"""
Blackstone Investor Lens

Implementation of the Blackstone playbook for private equity evaluation.
"""

import numpy as np
from analysis import framework_parser

BLACKSTONE_FAVORED_THEMES = {
    "Computers/Peripherals",
    "Software (System & Application)",
    "Hotel/Gaming",
    "Household Products",
    "Food Processing",
    "Financial Svcs. (Non-bank & Insurance)",
}

def evaluate_blackstone_lens(financials: dict, dcf_results: dict, qualitative_results: dict = None) -> dict:
    checks = {}
    
    ticker = financials["ticker"]
    is_india = ticker.endswith(".NS") or ticker.endswith(".BO")
    
    rev_4y = financials["revenue"]
    ebit_4y = financials["ebit"]
    fcf_4y = financials["fcf"]
    gp_4y = financials["gross_profit"]
    debt = financials["debt"][-1]
    market_cap = financials["market_cap"]
    target_industry = dcf_results["assumptions"].get("target_industry", "Unknown")
    
    ebitda_4y = [ebit_4y[i] + financials["depreciation"][i] for i in range(4)]
    latest_ebitda = ebitda_4y[-1]
    latest_revenue = rev_4y[-1]
    
    if latest_revenue <= 0 or latest_ebitda <= 0:
        latest_ebitda = max(latest_ebitda, 1e-6)
        latest_revenue = max(latest_revenue, 1e-6)
        
    latest_cash = financials["cash"][-1]
    latest_interest = financials["interest_expense"][-1]
    
    q = qualitative_results or {}
    q_status = q.get("status", "unavailable")
    
    def _cagr(start, end, periods=3):
        if start <= 0 or end <= 0: return 0.0
        return (end / start) ** (1/periods) - 1
        
    rev_cagr_4y = _cagr(rev_4y[0], rev_4y[-1], 3)
    
    # --- PART A: Good Business Filter ---
    # 1. Large growing market
    pass_1 = rev_cagr_4y > 0.05 and max(rev_4y) > min(rev_4y)
    checks["1_large_growing_market"] = {
        "part": "A",
        "name": "Growing Market",
        "metric_name": "Revenue 4y CAGR",
        "value": rev_cagr_4y,
        "threshold_str": "> 5% & upward",
        "passed": pass_1,
        "detail": f"CAGR is {rev_cagr_4y*100:.1f}%."
    }
    
    # 2. Durable moat
    gm_4y = [gp_4y[i] / rev_4y[i] if rev_4y[i] > 0 else 0 for i in range(4)]
    gm_stdev = np.std(gm_4y, ddof=1) if len(gm_4y) > 1 else 0
    mean_gm = np.mean(gm_4y)
    sector_median_gm = 0.35 # Default
    pass_2 = gm_stdev < 0.04 and mean_gm > sector_median_gm
    checks["2_durable_moat"] = {
        "part": "A",
        "name": "Durable Moat",
        "metric_name": "GM Stability & Level",
        "value": (gm_stdev, mean_gm),
        "threshold_str": "Stdev < 4pp & > 35%",
        "passed": pass_2,
        "detail": f"Stdev {gm_stdev*100:.1f}pp, Mean {mean_gm*100:.1f}%."
    }
    
    # 3. Recurring revenue
    rev_yoy = [rev_4y[i] / rev_4y[i-1] - 1 for i in range(1, 4)] if rev_4y[0] > 0 else []
    rev_yoy_stdev = np.std(rev_yoy, ddof=1) if len(rev_yoy) > 1 else 0
    pass_3 = rev_yoy_stdev < 0.08
    checks["3_recurring_revenue"] = {
        "part": "A",
        "name": "Recurring Revenue",
        "metric_name": "YoY Growth Stdev",
        "value": rev_yoy_stdev,
        "threshold_str": "< 8pp",
        "passed": pass_3,
        "detail": f"YoY growth stdev is {rev_yoy_stdev*100:.1f}pp."
    }
    
    # 4. No concentration risk
    # Default to PASS as most large cap public companies are diversified
    pass_4 = True
    checks["4_no_concentration"] = {
        "part": "A",
        "name": "No Concentration",
        "metric_name": "Diversification",
        "value": "diversified",
        "threshold_str": "Diversified",
        "passed": pass_4,
        "detail": "Assumed diversified (public company baseline)."
    }
    
    # --- PART B: Good Neighborhood ---
    # 5. Theme alignment
    pass_5 = target_industry in BLACKSTONE_FAVORED_THEMES
    checks["5_theme_alignment"] = {
        "part": "B",
        "name": "Theme Alignment",
        "metric_name": "Industry",
        "value": target_industry,
        "threshold_str": "Favored Theme",
        "passed": pass_5,
        "detail": f"{target_industry} {'in' if pass_5 else 'not in'} themes."
    }
    
    # 6. Cycle position
    cyc_sig = q.get("cycle_position", {}).get("sector_cycle", "unclear")
    if q_status != "available":
        pass_6 = True
        det_6 = "Defaulted PASS (assumed mid_cycle)"
    else:
        pass_6 = cyc_sig in ["trough", "early_recovery", "mid_cycle", "unclear"]
        det_6 = f"Cycle: {cyc_sig}"
    checks["6_cycle_position"] = {
        "part": "B",
        "name": "Cycle Position",
        "metric_name": "Sector Cycle",
        "value": cyc_sig,
        "threshold_str": "Not peak/late",
        "passed": pass_6,
        "detail": det_6
    }
    
    # 7. Structural tailwind
    tw_sig = q.get("structural_tailwind_signal", {}).get("verdict", "unclear")
    if q_status != "available":
        pass_7 = True
        det_7 = "Defaulted PASS (assumed neutral)"
    else:
        pass_7 = tw_sig in ["tailwind", "neutral", "unclear"]
        det_7 = f"Tailwind: {tw_sig}"
    checks["7_structural_tailwind"] = {
        "part": "B",
        "name": "Structural Tailwind",
        "metric_name": "Tailwind",
        "value": tw_sig,
        "threshold_str": "Tailwind/neutral",
        "passed": pass_7,
        "detail": det_7
    }
    
    # --- PART C: Downside Protection (>=2/3 pre-condition) ---
    # 8. Conservative balance sheet
    lev = debt / latest_ebitda if latest_ebitda > 0 else 999.0
    ic = ebit_4y[-1] / latest_interest if latest_interest > 0 else 999.0
    pass_8 = lev < 3.5 and ic > 4.0
    checks["8_conservative_bs"] = {
        "part": "C",
        "name": "Conservative Balance Sheet",
        "metric_name": "Lev < 3.5x & IC > 4x",
        "value": (lev, ic),
        "threshold_str": "<3.5x, >4x",
        "passed": pass_8,
        "detail": f"Leverage {lev:.1f}x, Interest Coverage {ic:.1f}x."
    }
    
    # 9. Through-cycle FCF resilience
    min_fcf = min(fcf_4y)
    mean_fcf = np.mean(fcf_4y)
    mean_rev = np.mean(rev_4y)
    pass_9 = min_fcf > 0 and (mean_fcf > 0.06 * mean_rev)
    checks["9_fcf_resilience"] = {
        "part": "C",
        "name": "FCF Resilience",
        "metric_name": "Min FCF & Margin",
        "value": (min_fcf, mean_fcf / mean_rev if mean_rev > 0 else 0),
        "threshold_str": ">0, >6%",
        "passed": pass_9,
        "detail": f"Min FCF {min_fcf:.1f}, Avg FCF Margin {(mean_fcf / mean_rev if mean_rev > 0 else 0)*100:.1f}%."
    }
    
    # 10. Stress-test survival capacity
    cash_req = max(0.10 * latest_revenue, 0.5 * latest_interest * 4)
    cash_ratio = latest_cash / cash_req if cash_req > 0 else 999.0
    pass_10 = cash_ratio > 1.0 or (debt < 0.5 * market_cap)
    checks["10_stress_survival"] = {
        "part": "C",
        "name": "Stress Survival",
        "metric_name": "Cash or Equity Cushion",
        "value": (cash_ratio, debt / market_cap if market_cap > 0 else 999.0),
        "threshold_str": "Cash>1x OR Debt/MC<0.5",
        "passed": pass_10,
        "detail": f"Cash ratio {cash_ratio:.2f}x, Debt/Equity {(debt / market_cap if market_cap > 0 else 999.0)*100:.1f}%."
    }
    
    # --- PART D: Scale Fit & Hold ---
    # 11. Blackstone-scale
    threshold_cap = 1.5e11 if is_india else 5e9
    pass_11 = market_cap > threshold_cap
    checks["11_scale"] = {
        "part": "D",
        "name": "Blackstone-Scale Deal",
        "metric_name": "Market Cap",
        "value": market_cap,
        "threshold_str": f"> {'₹150B' if is_india else '$5B'}",
        "passed": pass_11,
        "detail": f"Market cap is {'adequate' if pass_11 else 'too small'}."
    }
    
    # 12. 20-year core viability
    ha_sig = q.get("holdability_assessment", {}).get("verdict", "unclear")
    if q_status != "available":
        pass_12 = True
        det_12 = "Defaulted PASS (assumed holdable)"
    else:
        pass_12 = ha_sig in ["holdable_20y", "unclear"]
        det_12 = f"Signal: {ha_sig}"
    checks["12_core_viability"] = {
        "part": "D",
        "name": "20-Year Core Viability",
        "metric_name": "Holdability",
        "value": ha_sig,
        "threshold_str": "Holdable 20y",
        "passed": pass_12,
        "detail": det_12
    }
    
    # 13. Multi-product engagement
    mp_sig = q.get("multi_product_engagement_signal", {}).get("verdict", "unclear")
    if q_status != "available" or mp_sig == "unclear":
        pass_13 = True
        det_13 = "neutral default — qualitative unavailable; check counted as PASS"
    else:
        pass_13 = mp_sig in ["multi_product_potential"]
        det_13 = f"Signal: {mp_sig}"
    checks["13_multi_product"] = {
        "part": "D",
        "name": "Multi-Product Engagement",
        "metric_name": "Engagement Potential",
        "value": mp_sig,
        "threshold_str": "Multi-product",
        "passed": pass_13,
        "detail": det_13
    }
    
    # --- PART E: Phalippou Defensibility ---
    # 14. Alpha thesis (levers: 2, 3, 5, 7, 12, 13)
    edge_passed = sum([pass_2, pass_3, pass_5, pass_7, pass_12, pass_13])
    pass_14 = edge_passed >= 4
    checks["14_alpha_thesis"] = {
        "part": "E",
        "name": "Above-Average Alpha",
        "metric_name": "Edge Levers Passed",
        "value": edge_passed,
        "threshold_str": ">= 4",
        "passed": pass_14,
        "detail": f"{edge_passed} of 6 levers passed."
    }
    
    # --- SCORING ---
    # =========================================================================
    # Inject framework_reasoning into every check (v0.6)
    # =========================================================================
    for check_id, check_dict in checks.items():
        check_num = int(check_id.split("_")[0])
        reasoning = framework_parser.get_reasoning("blackstone", check_num)
        if reasoning is None:
            raise ValueError(
                f"framework_reasoning missing for blackstone check {check_id} "
                f"(check_num={check_num}). Update analysis/framework_parser.py."
            )
        check_dict["framework_reasoning"] = reasoning

    score = sum(1 for c in checks.values() if c["passed"])
    
    precond_1 = sum([pass_8, pass_9, pass_10]) >= 2
    precond_2 = pass_14
    
    if not (precond_1 and precond_2):
        verdict = "SKIP"
        if not precond_1:
            reason = "Failed Part C pre-condition: lacks Schwarzman downside protection (<2/3 passed)."
        else:
            reason = "Failed Part E pre-condition: lacks above-average alpha thesis (Phalippou bar)."
    elif score >= 11:
        verdict = "BUY"
        reason = "High-conviction Blackstone target. Good business in a good neighborhood."
    elif score >= 9 and not pass_6:
        verdict = "WAIT"
        reason = "WAIT (wrong cycle moment). Protected and aligned but late cycle."
    elif score >= 9 and not pass_11:
        verdict = "WAIT"
        reason = "WAIT (sub-scale). Protected and aligned but too small."
    elif score >= 9:
        verdict = "WATCH"
        reason = "Mixed signals across thematic/scale checks; monitor."
    else:
        verdict = "SKIP"
        reason = "Too many failed checks for an investable thesis."
        
    return {
        "score": score,
        "max_score": 14,
        "verdict": verdict,
        "reason": reason,
        "checks": checks
    }
