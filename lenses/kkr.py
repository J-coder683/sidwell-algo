"""
KKR Investor Lens

Implementation of the KKR playbook for private equity evaluation.
"""

import numpy as np
from analysis import framework_parser
from lenses import _scoring

KKR_PLAYBOOK_SECTORS = {
    "Household Products",
    "Chemical (Diversified)",
    "Chemical (Specialty)",
    "Food Processing",
    "Tobacco",
    "Financial Svcs. (Non-bank & Insurance)",
    "Software (System & Application)",
    "Computers/Peripherals",
}

INDIA_PE_RESTRICTED = {
    "Bank (Money Center)",
}

def evaluate_kkr_lens(financials: dict, dcf_results: dict, qualitative_results: dict = None) -> dict:
    checks = {}
    
    # Financial data extraction
    ticker = financials["ticker"]
    is_india = ticker.endswith(".NS") or ticker.endswith(".BO")
    
    rev_4y = financials["revenue"]
    ebit_4y = financials["ebit"]
    fcf_4y = financials["fcf"]
    tax_4y = financials["tax_provision"]
    pretax_4y = financials["pretax_income"]
    debt = financials["debt"][-1]
    market_cap = financials["market_cap"]
    target_industry = dcf_results["assumptions"].get("target_industry", "Unknown")
    
    # Calculate EBITDA
    ebitda_4y = [(ebit_4y[i] or 0.0) + (financials["depreciation"][i] or 0.0) for i in range(4)]
    latest_ebitda = ebitda_4y[-1]
    latest_revenue = rev_4y[-1]
    
    if latest_revenue <= 0 or latest_ebitda <= 0:
        # Avoid division by zero
        latest_ebitda = max(latest_ebitda, 1e-6)
        latest_revenue = max(latest_revenue, 1e-6)
        
    latest_ebitda_margin = latest_ebitda / latest_revenue
    latest_ebit_margin = ebit_4y[-1] / latest_revenue
    ebit_margin_4y = [(ebit_4y[i] or 0.0) / rev_4y[i] if rev_4y[i] and rev_4y[i] > 0 else 0 for i in range(4)]
    
    # Qualitative safe getters
    q = qualitative_results or {}
    q_status = q.get("status", "unavailable")
    
    # Helpers
    def _cagr(start, end, periods=3):
        if start <= 0 or end <= 0: return 0.0
        return (end / start) ** (1/periods) - 1
        
    rev_cagr_4y = _cagr(rev_4y[0], rev_4y[-1], 3)
    
    # --- PART A: LBO Viability ---
    # 1. EBITDA scale
    EBITDA_MIN = 4e9 if is_india else 200e6
    pass_1 = latest_ebitda > EBITDA_MIN
    checks["1_ebitda_scale"] = {
        "part": "A",
        "name": "EBITDA Scale",
        "metric_name": "Latest EBITDA",
        "value": latest_ebitda,
        "threshold_str": f"> {'₹4.0B' if is_india else '$200M'}",
        "passed": pass_1,
        "proximity": _scoring.proximity(latest_ebitda, EBITDA_MIN, "above"),
        "detail": f"Latest EBITDA {'passes' if pass_1 else 'fails'} scale check."
    }
    
    # 2. FCF conversion
    # mean(fcf_4y) / mean(ebit_after_tax_4y) > 0.60
    # Calculate effective tax rate per year
    tax_rates_4y = [(tax_4y[i] or 0.0) / pretax_4y[i] if pretax_4y[i] and pretax_4y[i] > 0 else 0.25 for i in range(4)]
    ebit_after_tax_4y = [ebit_4y[i] * (1 - tax_rates_4y[i]) for i in range(4)]
    mean_fcf = np.mean(fcf_4y)
    mean_eat = np.mean(ebit_after_tax_4y)
    fcf_conv = mean_fcf / mean_eat if mean_eat > 0 else 0
    FCF_CONV_MIN = 0.60
    pass_2 = fcf_conv > FCF_CONV_MIN
    checks["2_fcf_conversion"] = {
        "part": "A",
        "name": "FCF Conversion",
        "metric_name": "FCF / EBIT(1-t)",
        "value": fcf_conv,
        "threshold_str": "> 60.00%",
        "passed": pass_2,
        "proximity": _scoring.proximity(fcf_conv, FCF_CONV_MIN, "above"),
        "detail": f"Average conversion is {fcf_conv*100:.1f}%."
    }
    
    # 3. Leverage capacity
    lev = debt / latest_ebitda if latest_ebitda > 0 else 999.0
    LEV_MAX = 3.0
    pass_3 = lev < LEV_MAX
    checks["3_leverage_capacity"] = {
        "part": "A",
        "name": "Leverage Capacity",
        "metric_name": "Debt / EBITDA",
        "value": lev,
        "threshold_str": "< 3.0x",
        "passed": pass_3,
        "proximity": _scoring.proximity(lev, LEV_MAX, "below"),
        "detail": f"Leverage is {lev:.2f}x."
    }
    
    # 4. EBITDA margin
    EBITDA_MARGIN_MIN = 0.15
    pass_4 = latest_ebitda_margin > EBITDA_MARGIN_MIN
    checks["4_ebitda_margin"] = {
        "part": "A",
        "name": "EBITDA Margin",
        "metric_name": "EBITDA Margin",
        "value": latest_ebitda_margin,
        "threshold_str": "> 15.00%",
        "passed": pass_4,
        "proximity": _scoring.proximity(latest_ebitda_margin, EBITDA_MARGIN_MIN, "above"),
        "detail": f"Margin is {latest_ebitda_margin*100:.1f}%."
    }
    
    # --- PART B: Operational Upside ---
    # 5. Margin improvement room
    max_ebit_margin = max(ebit_margin_4y) if ebit_margin_4y else 0
    MARGIN_IMPROVEMENT_MAX = max_ebit_margin * 0.95
    pass_5 = latest_ebit_margin < MARGIN_IMPROVEMENT_MAX
    checks["5_margin_improvement"] = {
        "part": "B",
        "name": "Margin Improvement Room",
        "metric_name": "Current vs Peak EBIT Margin",
        "value": (latest_ebit_margin, max_ebit_margin),
        "threshold_str": "Current < 95% of Peak",
        "passed": pass_5,
        "proximity": _scoring.proximity(latest_ebit_margin, MARGIN_IMPROVEMENT_MAX, "below"),
        "detail": "Margin compression exists." if pass_5 else "Already at/near peak margin."
    }
    
    # 6. Capex optimization
    latest_capex = financials["capex"][-1]
    latest_deprec = financials["depreciation"][-1]
    maint_capex = latest_deprec
    growth_capex = max(0, latest_capex - maint_capex)
    capex_to_sales = latest_capex / latest_revenue
    growth_share = growth_capex / latest_capex if latest_capex > 0 else 0
    
    cond_a = growth_share > 0.30 and capex_to_sales > 0.03
    cond_b = capex_to_sales > 0.06 and rev_cagr_4y < 0.10
    cond_c = 0.02 <= capex_to_sales <= 0.06 and rev_cagr_4y < 0.10 and latest_ebit_margin < 0.20
    fail_cond = capex_to_sales < 0.02 or (growth_share < 0.20 and capex_to_sales < 0.04)
    pass_6 = (cond_a or cond_b or cond_c) and not fail_cond
    checks["6_capex_optimization"] = {
        "part": "B",
        "name": "Capex Optimization",
        "metric_name": "Capex/Sales & Growth Share",
        "value": (capex_to_sales, growth_share),
        "threshold_str": "Optimization profile",
        "passed": pass_6,
        "detail": f"Capex/Sales {capex_to_sales*100:.1f}%, Growth share {growth_share*100:.1f}%. " + ("Optimization possible." if pass_6 else "No obvious capex lever.")
    }
    
    # 7. Working capital optimization
    wc_change_4y = financials["working_capital_change"]
    sum_wc_change = sum(x if x is not None else 0 for x in wc_change_4y)
    mean_rev = np.mean(rev_4y)
    hard_7 = sum_wc_change < -0.05 * mean_rev
    
    wc_data = q.get("wc_optimization_signal", {}) or {}
    wc_sig = wc_data.get("verdict", "unclear")
    wc_conf = wc_data.get("confidence")
    wc_quote = (wc_data.get("evidence_quote") or "")[:300]
    # Soft branch only fires when confidence != 'low'
    soft_7 = wc_sig in ["high", "wc_optimization_available", "present"] and wc_conf != "low"
    pass_7 = hard_7 or soft_7
    wc_conf_str = f" (confidence: {wc_conf})" if wc_conf else ""
    wc_quote_str = f' Evidence: "{wc_quote}"' if wc_quote else ""
    checks["7_wc_optimization"] = {
        "part": "B",
        "name": "WC Optimization",
        "metric_name": "WC Change / Revenue",
        "value": sum_wc_change / mean_rev if mean_rev > 0 else 0,
        "threshold_str": "< -5% or qualitative",
        "passed": pass_7,
        "detail": f"Quantitative {'pass' if hard_7 else 'fail'}. Signal: {wc_sig}{wc_conf_str}.{wc_quote_str}"
    }
    
    # 8. M&A platform — excluded (N/A) when qualitative unavailable/unclear or low-confidence.
    ma_data = q.get("ma_platform_potential", {}) or {}
    ma_sig = ma_data.get("verdict")
    ma_conf = ma_data.get("confidence")
    ma_quote = (ma_data.get("evidence_quote") or "")[:300]
    ma_conf_str = f" (confidence: {ma_conf})" if ma_conf else ""
    ma_quote_str = f' Evidence: "{ma_quote}"' if ma_quote else ""
    pass_8, applic_8, det_8 = _scoring.resolve_soft(
        q_status, ma_sig, {"high", "platform_potential"},
        confidence=ma_conf,
        pass_detail=f"Signal: {ma_sig}{ma_conf_str}.{ma_quote_str}",
        fail_detail=f"Signal: {ma_sig}{ma_conf_str}.{ma_quote_str}",
    )
    checks["8_ma_platform"] = {
        "part": "B",
        "name": "M&A Platform Potential",
        "metric_name": "Platform Upside",
        "value": ma_sig,
        "threshold_str": "Qualitative high",
        "passed": pass_8,
        "applicable": applic_8,
        "detail": det_8
    }
    
    # 9. Operational revamp / Mgmt upgrade
    latest_gm = financials["gross_profit"][-1] / latest_revenue if latest_revenue > 0 else 0
    hard_9 = (latest_gm - latest_ebit_margin) > 0.20
    mgmt_data = q.get("mgmt_upgrade_potential", {}) or {}
    mgmt_sig = mgmt_data.get("verdict", "unclear")
    mgmt_conf = mgmt_data.get("confidence")
    mgmt_quote = (mgmt_data.get("evidence_quote") or "")[:300]
    # Soft branch only fires when confidence != 'low'
    soft_9 = mgmt_sig in ["high", "upgrade_available"] and mgmt_conf != "low"
    pass_9 = hard_9 or soft_9
    mgmt_conf_str = f" (confidence: {mgmt_conf})" if mgmt_conf else ""
    mgmt_quote_str = f' Evidence: "{mgmt_quote}"' if mgmt_quote else ""
    checks["9_mgmt_upgrade"] = {
        "part": "B",
        "name": "Mgmt / Ops Upgrade",
        "metric_name": "Cost Share > 20% or Qual",
        "value": latest_gm - latest_ebit_margin,
        "threshold_str": "> 20% cost share",
        "passed": pass_9,
        "detail": f"Opex share {(latest_gm - latest_ebit_margin)*100:.1f}%. Signal: {mgmt_sig}{mgmt_conf_str}.{mgmt_quote_str}"
    }
    
    # 10. Workforce fit — excluded (N/A) when qualitative unavailable/unclear or low-confidence.
    wf_data = q.get("workforce_stavros_fit", {}) or {}
    wf_sig = wf_data.get("verdict")
    wf_conf = wf_data.get("confidence")
    wf_quote = (wf_data.get("evidence_quote") or "")[:300]
    wf_conf_str = f" (confidence: {wf_conf})" if wf_conf else ""
    wf_quote_str = f' Evidence: "{wf_quote}"' if wf_quote else ""
    pass_10, applic_10, det_10 = _scoring.resolve_soft(
        q_status, wf_sig, {"high_labor_intensity", "frontline_heavy", "mixed"},
        confidence=wf_conf,
        pass_detail=f"Signal: {wf_sig}{wf_conf_str}.{wf_quote_str}",
        fail_detail=f"Signal: {wf_sig}{wf_conf_str}.{wf_quote_str}",
    )
    checks["10_workforce_fit"] = {
        "part": "B",
        "name": "Stavros Workforce Fit",
        "metric_name": "Labor Profile",
        "value": wf_sig,
        "threshold_str": "Frontline or mixed",
        "passed": pass_10,
        "applicable": applic_10,
        "detail": det_10
    }
    
    # --- PART C: Strategic Fit ---
    # 11. Sector compatibility
    pass_11 = target_industry in KKR_PLAYBOOK_SECTORS
    checks["11_sector_compatibility"] = {
        "part": "C",
        "name": "Sector Compatibility",
        "metric_name": "Industry",
        "value": target_industry,
        "threshold_str": "In KKR Playbook",
        "passed": pass_11,
        "detail": f"{target_industry} is {'in' if pass_11 else 'NOT in'} KKR playbook."
    }
    
    # 12. Willing seller — excluded (N/A) when qualitative unavailable/unclear or low-confidence.
    ws_data = q.get("willing_seller_signal", {}) or {}
    ws_sig = ws_data.get("verdict")
    ws_conf = ws_data.get("confidence")
    ws_quote = (ws_data.get("evidence_quote") or "")[:300]
    ws_conf_str = f" (confidence: {ws_conf})" if ws_conf else ""
    ws_quote_str = f' Evidence: "{ws_quote}"' if ws_quote else ""
    pass_12, applic_12, det_12 = _scoring.resolve_soft(
        q_status, ws_sig, {"founder_succession", "corporate_carveout", "distress", "willing_seller"},
        confidence=ws_conf,
        pass_detail=f"Signal: {ws_sig}{ws_conf_str}.{ws_quote_str}",
        fail_detail=f"Signal: {ws_sig}{ws_conf_str}.{ws_quote_str}",
    )
    checks["12_willing_seller"] = {
        "part": "C",
        "name": "Willing Seller",
        "metric_name": "Sale Catalyst",
        "value": ws_sig,
        "threshold_str": "Positive catalyst",
        "passed": pass_12,
        "applicable": applic_12,
        "detail": det_12
    }
    
    # 13. Regulatory blocker
    pass_13 = not (is_india and target_industry in INDIA_PE_RESTRICTED)
    checks["13_no_regulatory_blocker"] = {
        "part": "C",
        "name": "Regulatory Freedom",
        "metric_name": "Industry Blockers",
        "value": target_industry,
        "threshold_str": "Not restricted",
        "passed": pass_13,
        "detail": "Clear." if pass_13 else f"{target_industry} is restricted for control PE in India."
    }
    
    # --- PART D: Cycle Timing & Returns ---
    # 14. Cycle position — excluded (N/A) when qualitative unavailable/unclear or low-confidence.
    cyc_data = q.get("cycle_position", {}) or {}
    cyc_sig = cyc_data.get("sector_cycle")
    cyc_conf = cyc_data.get("confidence")
    cyc_quote = (cyc_data.get("evidence_quote") or "")[:300]
    cyc_conf_str = f" (confidence: {cyc_conf})" if cyc_conf else ""
    cyc_quote_str = f' Evidence: "{cyc_quote}"' if cyc_quote else ""
    pass_14, applic_14, det_14 = _scoring.resolve_soft(
        q_status, cyc_sig, {"trough", "early_recovery", "mid_cycle"},
        confidence=cyc_conf,
        pass_detail=f"Signal: {cyc_sig}{cyc_conf_str}.{cyc_quote_str}",
        fail_detail=f"Signal: {cyc_sig}{cyc_conf_str}.{cyc_quote_str}",
    )
    checks["14_cycle_position"] = {
        "part": "D",
        "name": "Cycle Timing",
        "metric_name": "Sector Cycle",
        "value": cyc_sig,
        "threshold_str": "Not peak/late",
        "passed": pass_14,
        "applicable": applic_14,
        "detail": det_14
    }
    
    # 15. 7-year IRR
    entry_ev = market_cap + debt
    entry_multiple = entry_ev / latest_ebitda if latest_ebitda > 0 else 999.0
    exit_ebitda_assumption = latest_ebitda * 2.0
    exit_multiple = max(8.0, entry_multiple * 0.85)
    exit_ev = exit_ebitda_assumption * exit_multiple
    exit_equity = exit_ev - (debt * 1.5)
    entry_equity = market_cap * 0.6
    
    irr_7y = 0.0
    if entry_equity > 0 and exit_equity > 0:
        irr_7y = (exit_equity / entry_equity) ** (1/7) - 1
        
    IRR_7Y_MIN = 0.18
    pass_15 = irr_7y > IRR_7Y_MIN
    checks["15_irr_feasibility"] = {
        "part": "D",
        "name": "7-Year IRR",
        "metric_name": "Proj IRR",
        "value": irr_7y,
        "threshold_str": "> 18.00%",
        "passed": pass_15,
        "proximity": _scoring.proximity(irr_7y, IRR_7Y_MIN, "above"),
        "detail": f"Entry mult {entry_multiple:.1f}x -> Exit mult {exit_multiple:.1f}x."
    }
    
    # 16. Dividend recap
    fcf_min = min(fcf_4y)
    fcf_cv = np.std(fcf_4y, ddof=1) / mean_fcf if mean_fcf > 0 else 999.0
    threshold_recap = 2e9 if is_india else 100e6
    pass_16 = (fcf_min > 0) and (fcf_cv < 0.35) and (latest_ebitda > threshold_recap)
    checks["16_dividend_recap"] = {
        "part": "D",
        "name": "Dividend Recap",
        "metric_name": "FCF Stability",
        "value": fcf_cv,
        "threshold_str": "CV < 35%, FCF > 0",
        "passed": pass_16,
        "detail": f"CV is {fcf_cv*100:.1f}%, min FCF {fcf_min:.1f}."
    }
    
    # 17. Why now — excluded (N/A) when qualitative unavailable/unclear or low-confidence.
    wn_data = q.get("why_now_signal", {}) or {}
    wn_sig = wn_data.get("verdict")
    wn_conf = wn_data.get("confidence")
    wn_quote = (wn_data.get("evidence_quote") or "")[:300]
    wn_conf_str = f" (confidence: {wn_conf})" if wn_conf else ""
    wn_quote_str = f' Evidence: "{wn_quote}"' if wn_quote else ""
    pass_17, applic_17, det_17 = _scoring.resolve_soft(
        q_status, wn_sig, {"catalyst_present", "dislocation_present"},
        confidence=wn_conf,
        pass_detail=f"Signal: {wn_sig}{wn_conf_str}.{wn_quote_str}",
        fail_detail=f"Signal: {wn_sig}{wn_conf_str}.{wn_quote_str}",
    )
    checks["17_why_now"] = {
        "part": "D",
        "name": "Why Now Catalyst",
        "metric_name": "Catalyst",
        "value": wn_sig,
        "threshold_str": "Catalyst present",
        "passed": pass_17,
        "applicable": applic_17,
        "detail": det_17
    }
    
    # --- PART E: Phalippou Bar ---
    # 18. Alpha thesis (levers: 5, 7, 8, 9, 10, 16). Proportional gate: when some
    # levers are N/A (soft signal unavailable), require >= ceil(4/6 * applicable).
    edge_levers = [
        (pass_5, True),            # margin improvement (quant)
        (pass_7, True),            # wc optimization (hybrid — always applicable)
        (pass_8, applic_8),        # M&A platform (soft)
        (pass_9, True),            # mgmt upgrade (hybrid — always applicable)
        (pass_10, applic_10),      # workforce fit (soft)
        (pass_16, True),           # dividend recap (quant)
    ]
    edge_passed, edge_n, edge_threshold, pass_18 = _scoring.proportional_gate(edge_levers)
    checks["18_alpha_thesis"] = {
        "part": "E",
        "name": "Above-Average Alpha",
        "metric_name": "Edge Levers Passed",
        "value": edge_passed,
        "threshold_str": f">= {edge_threshold} of {edge_n} applicable",
        "passed": pass_18,
        "detail": f"{edge_passed} of {edge_n} applicable levers passed (need {edge_threshold}; 2 N/A excluded)."
                  if edge_n < 6 else f"{edge_passed} of 6 levers passed (need {edge_threshold})."
    }
    
    # --- SCORING ---
    # =========================================================================
    # Inject framework_reasoning into every check (v0.6)
    # =========================================================================
    for check_id, check_dict in checks.items():
        check_num = int(check_id.split("_")[0])
        reasoning = framework_parser.get_reasoning("kkr", check_num)
        if reasoning is None:
            raise ValueError(
                f"framework_reasoning missing for kkr check {check_id} "
                f"(check_num={check_num}). Update analysis/framework_parser.py."
            )
        check_dict["framework_reasoning"] = reasoning

    # Exclude-from-denominator: soft checks with unavailable/unclear signals drop
    # out of both score and max_score. Verdict thresholds are ratio-based against
    # ORIG_MAX=18 (original 15/13 cutoffs). Preconditions are quant (1-4) and the
    # proportional Phalippou gate (18), so missing data does not auto-SKIP.
    ORIG_MAX = 18
    score, max_score = _scoring.tally(checks)

    precond_1 = all([pass_1, pass_2, pass_3, pass_4])
    precond_2 = pass_18

    if not (precond_1 and precond_2):
        verdict = "SKIP"
        if not precond_1:
            reason = "Failed Part A pre-condition: not LBO-viable."
        else:
            reason = "Failed Part E pre-condition: lacks above-average alpha thesis (Phalippou bar)."
    elif _scoring.meets(score, max_score, ORIG_MAX, 15):
        verdict = "BUY"
        reason = "High-conviction LBO target with strong alpha levers."
    elif _scoring.meets(score, max_score, ORIG_MAX, 13) and not pass_12:
        verdict = "WAIT"
        reason = "WAIT (seller not willing). Operationally sound but no deal available."
    elif _scoring.meets(score, max_score, ORIG_MAX, 13) and not pass_14:
        verdict = "WAIT"
        reason = "WAIT (wrong cycle moment). Better entry point required."
    elif _scoring.meets(score, max_score, ORIG_MAX, 13):
        verdict = "WATCH"
        reason = "Mixed signals across strategic/timing checks; monitor for changes."
    else:
        verdict = "SKIP"
        reason = "Too many failed checks for an investable thesis."

    return {
        "score": score,
        "max_score": max_score,
        "verdict": verdict,
        "reason": reason,
        "checks": checks
    }
