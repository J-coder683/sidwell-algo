"""
Apollo Investor Lens

Implementation of the Apollo Global Management playbook for private credit / distressed evaluation.
"""

import numpy as np
from analysis import framework_parser
from lenses import _scoring

SECTOR_MEDIAN_EV_EBITDA = {
    "Household Products":                          16.0,
    "Food Processing":                             14.0,
    "Tobacco":                                     10.0,
    "Retail (Grocery and Food)":                   10.0,
    "Chemical (Diversified)":                      9.5,
    "Chemical (Specialty)":                        13.0,
    "Metals/Mining":                               7.0,
    "Software (System & Application)":             22.0,
    "Computers/Peripherals":                       15.0,
    "Financial Svcs. (Non-bank & Insurance)":      11.0,
    "Healthcare Services":                         13.0,
    "Hotel/Gaming":                                11.0,
    "Entertainment":                               12.0,
    "Media (TV/Film/Music/Publishing)":            11.0,
}

SECTOR_USE_PB_NOT_EV_EBITDA = {
    "Bank (Money Center)",
}

APOLLO_DOMAIN_SECTORS = {
    "Chemical (Diversified)",
    "Chemical (Specialty)",
    "Hotel/Gaming",
    "Metals/Mining",
    "Entertainment",
    "Media (TV/Film/Music/Publishing)",
    "Financial Svcs. (Non-bank & Insurance)",
    "Healthcare Services",
    "Retail (Grocery and Food)",
}

def evaluate_apollo_lens(financials: dict, dcf_results: dict, qualitative_results: dict = None) -> dict:
    checks = {}
    
    ticker = financials["ticker"]
    is_india = ticker.endswith(".NS") or ticker.endswith(".BO")
    
    rev_4y = financials["revenue"]
    ebit_4y = financials["ebit"]
    fcf_4y = financials["fcf"]
    debt = financials["debt"][-1]
    market_cap = financials["market_cap"] or 0  # may be None (e.g. GOOGL on Cloud)
    target_industry = dcf_results["assumptions"].get("target_industry", "Unknown")
    
    ebitda_4y = [(ebit_4y[i] or 0.0) + (financials["depreciation"][i] or 0.0) for i in range(4)]
    latest_ebitda = ebitda_4y[-1]
    latest_revenue = rev_4y[-1]
    latest_total_assets = financials.get("total_assets", [0,0,0,0])[-1]
    latest_intangibles = financials.get("total_intangibles", [0,0,0,0])[-1]
    latest_goodwill = financials.get("goodwill", [0,0,0,0])[-1]
    bv_per_share = financials.get("book_value_per_share", 0.0)
    shares_outstanding = financials.get("historical_shares", [0,0,0,0])[-1]
    latest_price = market_cap / shares_outstanding if shares_outstanding > 0 else 0.0
    
    if latest_revenue <= 0 or latest_ebitda <= 0 or latest_total_assets <= 0:
        latest_ebitda = max(latest_ebitda, 1e-6)
        latest_revenue = max(latest_revenue, 1e-6)
        latest_total_assets = max(latest_total_assets, 1e-6)
        
    latest_interest = max(financials["interest_expense"][-1], 1e-6)
    
    q = qualitative_results or {}
    q_status = q.get("status", "unavailable")
    
    # --- PART A: Purchase Price & Capital Structure Entry ---
    # 1. Entry valuation discount
    entry_ev = market_cap + debt
    entry_ev_to_ebitda = entry_ev / latest_ebitda
    sector_ev_ebitda = SECTOR_MEDIAN_EV_EBITDA.get(target_industry, -1.0)
    
    if target_industry in SECTOR_USE_PB_NOT_EV_EBITDA:
        pb = latest_price / bv_per_share if bv_per_share > 0 else 999.0
        pass_1 = pb < 0.70
        val_metric = pb
        val_name = "Price/Book"
        val_thresh = "< 0.70x"
        val_det = f"P/B is {pb:.2f}x."
    else:
        pb = latest_price / bv_per_share if bv_per_share > 0 else 999.0
        if sector_ev_ebitda > 0:
            pass_ev = entry_ev_to_ebitda < (sector_ev_ebitda * 0.80)
        else:
            pass_ev = False # Fallback to fail if unmapped as per rules "Apollo Check 1 fallback: Default to FAIL if sector is unmapped."
            
        pass_pb = pb < 0.70
        pass_1 = pass_ev or pass_pb
        val_metric = entry_ev_to_ebitda
        val_name = "EV/EBITDA or P/B"
        val_thresh = f"< {sector_ev_ebitda*0.80:.1f}x EV/EBITDA or <0.70 P/B"
        val_det = f"EV/EBITDA is {entry_ev_to_ebitda:.1f}x. P/B is {pb:.2f}x."
        
    checks["1_entry_valuation"] = {
        "part": "A",
        "name": "Entry Valuation Discount",
        "metric_name": val_name,
        "value": val_metric,
        "threshold_str": val_thresh,
        "passed": pass_1,
        "detail": val_det
    }
    
    # 2. Capital structure complexity
    lev = debt / latest_ebitda if latest_ebitda > 0 else 0.0
    ic = ebit_4y[-1] / latest_interest if latest_interest > 0 else 999.0
    pass_2 = lev > 3.5 or ic < 3.0
    checks["2_capital_structure_complexity"] = {
        "part": "A",
        "name": "Capital Structure Complexity",
        "metric_name": "Lev > 3.5x or IC < 3.0x",
        "value": (lev, ic),
        "threshold_str": "Debt stress",
        "passed": pass_2,
        "detail": f"Lev: {lev:.1f}x, IC: {ic:.1f}x. {'Complex/stressed' if pass_2 else 'Clean'}."
    }
    
    # 3. FCF serviceability
    mean_fcf = np.mean(fcf_4y)
    mean_ebitda = np.mean(ebitda_4y)
    hyp_interest = max(debt * 0.07, latest_interest)
    hyp_cov = mean_ebitda / hyp_interest if hyp_interest > 0 else 999.0
    pass_3 = mean_fcf > 0 and hyp_cov > 1.5
    checks["3_fcf_serviceability"] = {
        "part": "A",
        "name": "FCF Serviceability",
        "metric_name": "FCF & Cov Floor",
        "value": hyp_cov,
        "threshold_str": ">0 FCF, >1.5x Cov",
        "passed": pass_3,
        "detail": f"Avg FCF {mean_fcf:.1f}, Hyp Cov {hyp_cov:.1f}x."
    }
    
    # 4. Capital deployment scale
    SCALE_MIN = 20e9 if is_india else 500e6
    pass_4 = entry_ev > SCALE_MIN
    checks["4_capital_deployment_scale"] = {
        "part": "A",
        "name": "Deployment Scale",
        "metric_name": "Enterprise Value",
        "value": entry_ev,
        "threshold_str": f"> {'₹20B' if is_india else '$500M'}",
        "passed": pass_4,
        "proximity": _scoring.proximity(entry_ev, SCALE_MIN, "above"),
        "detail": f"EV is {entry_ev:.1f}."
    }
    
    # --- PART B: Chaos, Complexity, Credit Edge ---
    # 5. Chaos / dislocation catalyst — excluded (N/A) when unavailable/unclear or low-confidence.
    ch_data = q.get("chaos_dislocation_catalyst", {}) or {}
    ch_sig = ch_data.get("verdict")
    ch_conf = ch_data.get("confidence")
    ch_quote = (ch_data.get("evidence_quote") or "")[:300]
    ch_conf_str = f" (confidence: {ch_conf})" if ch_conf else ""
    ch_quote_str = f' Evidence: "{ch_quote}"' if ch_quote else ""
    pass_5, applic_5, det_5 = _scoring.resolve_soft(
        q_status, ch_sig, {"present", "chaos_present", "dislocation_present"},
        confidence=ch_conf,
        pass_detail=f"Signal: {ch_sig}{ch_conf_str}.{ch_quote_str}",
        fail_detail=f"Signal: {ch_sig}{ch_conf_str}.{ch_quote_str}",
    )
    checks["5_chaos_catalyst"] = {
        "part": "B",
        "name": "Chaos/Dislocation Catalyst",
        "metric_name": "Dislocation",
        "value": ch_sig,
        "threshold_str": "Present",
        "passed": pass_5,
        "applicable": applic_5,
        "detail": det_5
    }
    
    # 6. Fulcrum security
    # Hybrid: hard conditions are always computable. Soft branch only fires when
    # confidence != 'low' (low-confidence cannot rescue a hard FAIL).
    hard_6_a = (lev > 5.0 and ic < 2.0)
    hard_6_b = market_cap < 0.30 * debt
    fl_data = q.get("fulcrum_security_signal", {}) or {}
    fl_sig = fl_data.get("verdict", "unclear")
    fl_conf = fl_data.get("confidence")
    fl_quote = (fl_data.get("evidence_quote") or "")[:300]
    # Soft branch only fires when confidence != 'low'
    soft_6 = fl_sig in ["present", "fulcrum_identified", "multi_tranche_complex"] and fl_conf != "low"
    pass_6 = hard_6_a or hard_6_b or soft_6
    fl_conf_str = f" (confidence: {fl_conf})" if fl_conf else ""
    fl_quote_str = f' Evidence: "{fl_quote}"' if fl_quote else ""
    checks["6_fulcrum_security"] = {
        "part": "B",
        "name": "Fulcrum Security",
        "metric_name": "Debt stress/Qual",
        "value": (lev, ic, market_cap / debt if debt > 0 else 999.0),
        "threshold_str": "Hard or Soft Fulcrum",
        "passed": pass_6,
        "detail": f"Signal: {fl_sig}{fl_conf_str}.{fl_quote_str} Hard: A={hard_6_a}, B={hard_6_b}."
    }
    
    # 7. ABF / private credit fit — excluded (N/A) when unavailable/unclear or low-confidence.
    abf_data = q.get("abf_credit_fit", {}) or {}
    abf_sig = abf_data.get("verdict")
    abf_conf = abf_data.get("confidence")
    abf_quote = (abf_data.get("evidence_quote") or "")[:300]
    abf_conf_str = f" (confidence: {abf_conf})" if abf_conf else ""
    abf_quote_str = f' Evidence: "{abf_quote}"' if abf_quote else ""
    pass_7, applic_7, det_7 = _scoring.resolve_soft(
        q_status, abf_sig, {"high", "abf_primary_opportunity", "direct_lending_opportunity"},
        confidence=abf_conf,
        pass_detail=f"Signal: {abf_sig}{abf_conf_str}.{abf_quote_str}",
        fail_detail=f"Signal: {abf_sig}{abf_conf_str}.{abf_quote_str}",
    )
    checks["7_abf_fit"] = {
        "part": "B",
        "name": "ABF/Credit Fit",
        "metric_name": "Credit Compatibility",
        "value": abf_sig,
        "threshold_str": "Compatible",
        "passed": pass_7,
        "applicable": applic_7,
        "detail": det_7
    }
    
    # 8. Complexity moat
    # Hybrid: hard condition always computable. Soft branch only fires when confidence != 'low'.
    debt_to_assets = debt / latest_total_assets
    hard_8 = debt_to_assets > 0.55
    cx_data = q.get("complexity_moat_signal", {}) or {}
    cx_sig = cx_data.get("verdict", "unclear")
    cx_conf = cx_data.get("confidence")
    cx_quote = (cx_data.get("evidence_quote") or "")[:300]
    # Soft branch only fires when confidence != 'low'
    soft_8 = cx_sig in ["high", "complexity_premium_available"] and cx_conf != "low"
    pass_8 = hard_8 or soft_8
    cx_conf_str = f" (confidence: {cx_conf})" if cx_conf else ""
    cx_quote_str = f' Evidence: "{cx_quote}"' if cx_quote else ""
    checks["8_complexity_moat"] = {
        "part": "B",
        "name": "Complexity Moat",
        "metric_name": "Debt/Assets or Qual",
        "value": debt_to_assets,
        "threshold_str": ">55% or High Qual",
        "passed": pass_8,
        "detail": f"Debt/Assets {debt_to_assets*100:.1f}%. Signal: {cx_sig}{cx_conf_str}.{cx_quote_str}"
    }
    
    # 9. Sector domain knowledge
    pass_9 = target_industry in APOLLO_DOMAIN_SECTORS
    checks["9_domain_knowledge"] = {
        "part": "B",
        "name": "Domain Knowledge",
        "metric_name": "Industry",
        "value": target_industry,
        "threshold_str": "In Apollo Playbook",
        "passed": pass_9,
        "detail": f"{target_industry} {'in' if pass_9 else 'not in'} playbook."
    }
    
    # --- PART C: Athene Permanent Capital Fit ---
    # 10. IG private credit yield generation
    latest_ebitda_margin = latest_ebitda / latest_revenue
    pass_10 = latest_ebitda_margin > 0.12 and lev < 5.0 and ic > 1.5
    checks["10_ig_yield"] = {
        "part": "C",
        "name": "IG Credit Yield",
        "metric_name": "Margin, Lev, IC",
        "value": (latest_ebitda_margin, lev, ic),
        "threshold_str": "Margin>12%, Lev<5x, IC>1.5x",
        "passed": pass_10,
        "detail": f"Margin {latest_ebitda_margin*100:.1f}%, Lev {lev:.1f}x, IC {ic:.1f}x."
    }
    
    # 11. Long-duration cash flow stability
    fcf_margins = [(fcf_4y[i] or 0.0) / rev_4y[i] if rev_4y[i] and rev_4y[i] > 0 else 0 for i in range(4)]
    fcf_margin_stdev = np.std(fcf_margins, ddof=1) if len(fcf_margins) > 1 else 0
    pass_11 = fcf_margin_stdev < 0.04 and mean_fcf > 0
    checks["11_cash_stability"] = {
        "part": "C",
        "name": "Long-Duration Stability",
        "metric_name": "FCF Margin Stdev",
        "value": fcf_margin_stdev,
        "threshold_str": "< 4pp, > 0 avg",
        "passed": pass_11,
        "detail": f"FCF Margin Stdev {fcf_margin_stdev*100:.1f}pp."
    }
    
    # 12. Hold-without-exit optionality — excluded (N/A) when unavailable/unclear or low-confidence.
    ph_data = q.get("permanent_hold_viable", {}) or {}
    ph_sig = ph_data.get("verdict")
    ph_conf = ph_data.get("confidence")
    ph_quote = (ph_data.get("evidence_quote") or "")[:300]
    ph_conf_str = f" (confidence: {ph_conf})" if ph_conf else ""
    ph_quote_str = f' Evidence: "{ph_quote}"' if ph_quote else ""
    pass_12, applic_12, det_12 = _scoring.resolve_soft(
        q_status, ph_sig, {"yes", "permanent_hold_viable"},
        confidence=ph_conf,
        pass_detail=f"Signal: {ph_sig}{ph_conf_str}.{ph_quote_str}",
        fail_detail=f"Signal: {ph_sig}{ph_conf_str}.{ph_quote_str}",
    )
    checks["12_hold_optionality"] = {
        "part": "C",
        "name": "Hold-Without-Exit",
        "metric_name": "Permanent Hold",
        "value": ph_sig,
        "threshold_str": "Viable",
        "passed": pass_12,
        "applicable": applic_12,
        "detail": det_12
    }
    
    # --- PART D: Credit Downside Quality ---
    # 13. Through-cycle credit floor
    min_ebit = min(ebit_4y)
    mean_ebit = np.mean(ebit_4y)
    avg_cov = mean_ebit / hyp_interest if hyp_interest > 0 else 999.0
    pass_13 = min_ebit > 0 and (avg_cov > 1.5 or ic > 2.5)
    checks["13_credit_floor"] = {
        "part": "D",
        "name": "Through-Cycle Credit Floor",
        "metric_name": "Min EBIT & Cov",
        "value": (min_ebit, avg_cov),
        "threshold_str": "Min EBIT>0, Cov>1.5x",
        "passed": pass_13,
        "detail": f"Min EBIT {min_ebit:.1f}, Avg Cov {avg_cov:.1f}x."
    }
    
    # 14. Tangible asset / collateral base
    tangible_assets = latest_total_assets - latest_intangibles - latest_goodwill
    tangible_ratio = tangible_assets / latest_total_assets
    TANGIBLE_RATIO_MIN = 0.40
    pass_14 = tangible_ratio > TANGIBLE_RATIO_MIN
    checks["14_collateral_base"] = {
        "part": "D",
        "name": "Tangible Collateral",
        "metric_name": "Tangible Ratio",
        "value": tangible_ratio,
        "threshold_str": "> 40%",
        "passed": pass_14,
        "proximity": _scoring.proximity(tangible_ratio, TANGIBLE_RATIO_MIN, "above"),
        "detail": f"Ratio {tangible_ratio*100:.1f}%."
    }
    
    # 15. Covenant control — excluded (N/A) when unavailable/unclear or low-confidence.
    cc_data = q.get("covenant_control_potential", {}) or {}
    cc_sig = cc_data.get("verdict")
    cc_conf = cc_data.get("confidence")
    cc_quote = (cc_data.get("evidence_quote") or "")[:300]
    cc_conf_str = f" (confidence: {cc_conf})" if cc_conf else ""
    cc_quote_str = f' Evidence: "{cc_quote}"' if cc_quote else ""
    pass_15, applic_15, det_15 = _scoring.resolve_soft(
        q_status, cc_sig, {"high", "covenant_rich_opportunity", "mixed"},
        confidence=cc_conf,
        pass_detail=f"Signal: {cc_sig}{cc_conf_str}.{cc_quote_str}",
        fail_detail=f"Signal: {cc_sig}{cc_conf_str}.{cc_quote_str}",
    )
    checks["15_covenant_control"] = {
        "part": "D",
        "name": "Covenant Control",
        "metric_name": "Control Potential",
        "value": cc_sig,
        "threshold_str": "High/Mixed",
        "passed": pass_15,
        "applicable": applic_15,
        "detail": det_15
    }
    
    # --- PART E: Phalippou Bar ---
    # 16. Apollo alpha thesis (levers: 5, 6, 7, 8, 9, 12). Proportional gate: when
    # some levers are N/A (soft signal unavailable), require >= ceil(4/6 * applicable).
    edge_levers = [
        (pass_5, applic_5),    # chaos (soft)
        (pass_6, True),        # fulcrum (hybrid — always applicable)
        (pass_7, applic_7),    # ABF (soft)
        (pass_8, True),        # complexity moat (hybrid — always applicable)
        (pass_9, True),        # domain knowledge (quant)
        (pass_12, applic_12),  # hold optionality (soft)
    ]
    edge_passed, edge_n, edge_threshold, pass_16 = _scoring.proportional_gate(edge_levers)
    checks["16_alpha_thesis"] = {
        "part": "E",
        "name": "Above-Average Alpha",
        "metric_name": "Edge Levers Passed",
        "value": edge_passed,
        "threshold_str": f">= {edge_threshold} of {edge_n} applicable",
        "passed": pass_16,
        "detail": (f"{edge_passed} of {edge_n} applicable levers passed (need {edge_threshold}; "
                   f"{6 - edge_n} N/A excluded)." if edge_n < 6
                   else f"{edge_passed} of 6 levers passed (need {edge_threshold}).")
    }
    
    # --- SCORING ---
    # =========================================================================
    # Inject framework_reasoning into every check (v0.6)
    # =========================================================================
    for check_id, check_dict in checks.items():
        check_num = int(check_id.split("_")[0])
        reasoning = framework_parser.get_reasoning("apollo", check_num)
        if reasoning is None:
            raise ValueError(
                f"framework_reasoning missing for apollo check {check_id} "
                f"(check_num={check_num}). Update analysis/framework_parser.py."
            )
        check_dict["framework_reasoning"] = reasoning

    # Exclude-from-denominator: soft checks with unavailable/unclear signals drop
    # out of both score and max_score. Verdict thresholds are ratio-based against
    # ORIG_MAX=16 (original 12/10 cutoffs). precond_2 uses the lever booleans, which
    # are False when N/A — and pass_6 (fulcrum) is always applicable, so missing soft
    # signals never auto-SKIP on their own.
    ORIG_MAX = 16
    score, max_score = _scoring.tally(checks)

    precond_1 = pass_16
    precond_2 = pass_5 or pass_6 or pass_7

    if not precond_1 or not precond_2:
        verdict = "SKIP"
        if not precond_1:
            reason = "Failed Part E pre-condition: lacks above-average alpha thesis (Phalippou bar)."
        else:
            reason = "Failed Part B pre-condition: no chaos, fulcrum, or ABF structural entry angle."
    elif _scoring.meets(score, max_score, ORIG_MAX, 12):
        verdict = "BUY"
        reason = "High-conviction Apollo deployment with structural edge and entry discount."
    elif _scoring.meets(score, max_score, ORIG_MAX, 10) and not pass_5:
        verdict = "WAIT"
        reason = "WAIT (no chaos catalyst yet). Good structure, wait for dislocation."
    elif _scoring.meets(score, max_score, ORIG_MAX, 10) and not pass_10 and not pass_11:
        verdict = "WAIT"
        reason = "WAIT (sub-Athene quality). Equity/opportunistic fit only."
    elif _scoring.meets(score, max_score, ORIG_MAX, 10):
        verdict = "WATCH"
        reason = "Mixed signals across edge checks; monitor."
    else:
        verdict = "SKIP"
        reason = "Too many failed checks. Generic credit/equity thesis."

    return {
        "score": score,
        "max_score": max_score,
        "verdict": verdict,
        "reason": reason,
        "checks": checks
    }
