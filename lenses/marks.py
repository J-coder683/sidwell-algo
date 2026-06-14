"""
Howard Marks Investor Lens — Risk-First Framework
Implements 14 checks across 4 Parts per frameworks/marks.md.

Part A (1-4):  Margin of Safety & Asymmetric Payoff
Part B (5-7):  Cycle Position
Part C (8-11): Risk Architecture (pre-conditions)
Part D (12-14): Second-Level Thinking & Contrarianism (LLM-driven)
"""
import logging
from analysis import framework_parser
from lenses import _scoring

logger = logging.getLogger("sidwell.lenses.marks")


def evaluate_marks_lens(
    financials: dict,
    dcf_results: dict,
    qualitative_results: dict = None,
    ddm_results: dict = None,
) -> dict:
    """
    Evaluates a company through Howard Marks's risk-first framework.

    financials: dict from public.fetch_financials (v0.3+)
    dcf_results: dict from dcf.run_dcf_valuation
    qualitative_results: optional dict from analysis.qualitative (v0.2+)
    ddm_results: optional dict from a bank valuation model (DDM/excess-returns,
        not yet built). When it supplies an intrinsic value it takes precedence
        over the DCF, which lets the valuation-dependent checks (#1 deep MoS and
        #2 asymmetric payoff) auto-activate for banks once that model lands.

    Returns a dict with check details, score, verdict, and reason.
    Same interface as evaluate_buffett_lens.
    """
    hist_revenue = financials["revenue"]
    if len(hist_revenue) != 4:
        raise ValueError(f"Expected 4 years of historical data, got {len(hist_revenue)}")

    hist_fcf = financials["fcf"]
    hist_ebit = financials["ebit"]
    hist_interest_expense = financials["interest_expense"]
    hist_net_income = financials["net_income"]
    hist_total_equity = financials["total_equity"]
    hist_depreciation = financials["depreciation"]

    latest_debt = financials["debt"][-1]
    latest_ebitda = hist_ebit[-1] + hist_depreciation[-1]
    market_cap = financials.get("market_cap", 0)
    current_price = dcf_results["current_price"]
    # Prefer a bank valuation (DDM/excess-returns) intrinsic value if present;
    # fall back to the DCF. For banks today both are None → the two valuation-
    # dependent checks (1 deep MoS, 2 asymmetric payoff) are marked N/A and
    # excluded from the denominator.
    intrinsic_value = (ddm_results or {}).get("intrinsic_value_per_share")
    if intrinsic_value is None:
        intrinsic_value = dcf_results.get("intrinsic_value_per_share")

    checks = {}

    # =========================================================================
    # PART A — Margin of Safety & Asymmetric Payoff (Checks 1-4)
    # =========================================================================

    # Checks 1 and 2 both derive from the valuation intrinsic value. When no
    # valuation model applies (banks have no DCF and no DDM yet), intrinsic_value
    # is None: mark both N/A (applicable=False) so they are excluded from the
    # denominator. They auto-activate once ddm_results supplies an intrinsic value.
    valuation_available = intrinsic_value is not None

    # 1. Deep margin of safety (40%, deeper than Buffett's 25%)
    # Test: (intrinsic - price) / intrinsic > 0.40
    if not valuation_available:
        checks["1_deep_mos"] = {
            "name": "Deep margin of safety",
            "metric_name": "MoS (Marks 40% threshold)",
            "value": None,
            "threshold_str": "> 40%",
            "passed": False,
            "applicable": False,
            "detail": "N/A — DCF not applicable to banks; awaiting DDM/excess-returns model.",
            "part": "A",
        }
    else:
        if intrinsic_value > 0:
            mos = (intrinsic_value - current_price) / intrinsic_value
        else:
            mos = -1.0
        MOS_MIN = 0.40
        check_1_passed = mos > MOS_MIN
        checks["1_deep_mos"] = {
            "name": "Deep margin of safety",
            "metric_name": "MoS (Marks 40% threshold)",
            "value": mos,
            "threshold_str": "> 40%",
            "passed": check_1_passed,
            "proximity": _scoring.proximity(mos, MOS_MIN, "above"),
            "detail": (
                f"MoS = {mos*100:+.2f}% > 40%"
                if check_1_passed
                else (
                    f"MoS = {mos*100:+.2f}% (< 40% threshold) — "
                    f"Price {current_price:.2f} vs Intrinsic {intrinsic_value:.2f}"
                )
            ),
            "part": "A",
        }

    # 2. Asymmetric upside-to-downside payoff (3:1)
    # Placeholder per spec: +-20% bands on intrinsic value; tighten in v0.4.
    # Test: (upside - price) / (price - downside) > 3.0
    if not valuation_available:
        checks["2_asymmetric_payoff"] = {
            "name": "Asymmetric upside-to-downside payoff",
            "metric_name": "Upside/Downside ratio (+-20% bands, placeholder)",
            "value": None,
            "threshold_str": "> 3.0x",
            "passed": False,
            "applicable": False,
            "detail": "N/A — DCF not applicable to banks; awaiting DDM/excess-returns model.",
            "part": "A",
        }
    else:
        if intrinsic_value > 0:
            upside_scenario = intrinsic_value * 1.20
            downside_scenario = intrinsic_value * 0.80
            if current_price < downside_scenario:
                asymmetry_ratio = float("inf")  # All upside, no downside priced in
            elif current_price > upside_scenario:
                asymmetry_ratio = 0.0
            else:
                asymmetry_ratio = (upside_scenario - current_price) / max(current_price - downside_scenario, 1e-9)
            ASYMMETRY_MIN = 3.0
            check_2_passed = asymmetry_ratio > ASYMMETRY_MIN
        else:
            asymmetry_ratio = 0.0
            ASYMMETRY_MIN = 3.0
            check_2_passed = False
        checks["2_asymmetric_payoff"] = {
            "name": "Asymmetric upside-to-downside payoff",
            "metric_name": "Upside/Downside ratio (+-20% bands, placeholder)",
            "value": asymmetry_ratio,
            "threshold_str": "> 3.0x",
            "passed": check_2_passed,
            "proximity": _scoring.proximity(asymmetry_ratio, ASYMMETRY_MIN, "above"),
            "detail": (
                f"Asymmetry ratio = {asymmetry_ratio:.2f} > 3.0"
                if check_2_passed
                else f"Asymmetry ratio = {asymmetry_ratio:.2f} (< 3.0 threshold)"
            ),
            "part": "A",
        }

    # 3. Downside protection — tangible book / market cap
    # v0.3 simplified: use latest total equity as proxy for tangible book.
    # Test: equity / market_cap > 0.30
    latest_equity = hist_total_equity[-1]
    if market_cap > 0:
        tangible_book_ratio = latest_equity / market_cap
    else:
        tangible_book_ratio = 0.0
    TB_RATIO_MIN = 0.30
    check_3_passed = tangible_book_ratio > TB_RATIO_MIN
    checks["3_downside_protection"] = {
        "name": "Downside protection (tangible book)",
        "metric_name": "Equity / Market Cap (proxy for tangible book)",
        "value": tangible_book_ratio,
        "threshold_str": "> 30%",
        "passed": check_3_passed,
        "proximity": _scoring.proximity(tangible_book_ratio, TB_RATIO_MIN, "above"),
        "detail": f"Equity/MCap = {tangible_book_ratio*100:.2f}% ({'>' if check_3_passed else '<='} 30%)",
        "part": "A",
    }

    # 4. Multiple expansion not exhausted
    # v0.3 placeholder: trailing P/E < 25x (sector comp deferred to v0.4)
    trailing_pe = financials.get("trailing_pe")
    PE_MAX = 25.0
    if trailing_pe is not None and trailing_pe > 0:
        check_4_passed = trailing_pe < PE_MAX
        detail_4 = f"Trailing P/E = {trailing_pe:.1f}x ({'< 25x' if check_4_passed else '>= 25x'})"
    else:
        check_4_passed = True  # Default PASS when P/E unavailable
        detail_4 = "Trailing P/E unavailable; check defaulted PASS"
    checks["4_multiple_expansion"] = {
        "name": "Multiple expansion not exhausted",
        "metric_name": "Trailing P/E vs 25x ceiling (v0.3 placeholder)",
        "value": trailing_pe,
        "threshold_str": "< 25x (v0.3 placeholder; sector comp in v0.4)",
        "passed": check_4_passed,
        "proximity": _scoring.proximity(trailing_pe, PE_MAX, "below") if trailing_pe is not None and trailing_pe > 0 else None,
        "detail": detail_4,
        "part": "A",
    }

    # =========================================================================
    # PART B — Cycle Position (Checks 5-7)
    # =========================================================================

    # 5. Sector cycle position (soft, LLM)
    # Test: LLM read in {trough, early_recovery, mid_cycle}. Excluded (N/A) when
    # qualitative is unavailable, the cycle read is unclear, or confidence is low.
    q_status = (qualitative_results or {}).get("status", "unavailable")
    cp = (qualitative_results or {}).get("cycle_position", {}) or {}
    sector_cycle = cp.get("sector_cycle")
    cycle_confidence = cp.get("confidence")
    cycle_quote = (cp.get("evidence_quote") or "")[:300]
    cycle_reasoning = (cp.get("reasoning") or "")[:500]
    cycle_quote_str = f' Evidence: "{cycle_quote}"' if cycle_quote else ""
    cycle_conf_str = f" (confidence: {cycle_confidence})" if cycle_confidence else ""
    cycle_passed, cycle_applicable, cycle_detail = _scoring.resolve_soft(
        q_status, sector_cycle, {"trough", "early_recovery", "mid_cycle"},
        confidence=cycle_confidence,
        pass_detail=f"Signal: {sector_cycle}{cycle_conf_str}.{cycle_quote_str} {cycle_reasoning}",
        fail_detail=f"Signal: {sector_cycle}{cycle_conf_str}.{cycle_quote_str} {cycle_reasoning}",
    )
    checks["5_sector_cycle"] = {
        "name": "Sector cycle position",
        "metric_name": "LLM cycle read",
        "value": sector_cycle,
        "threshold_str": "trough | early_recovery | mid_cycle",
        "passed": cycle_passed,
        "applicable": cycle_applicable,
        "detail": cycle_detail,
        "part": "B",
    }

    # 6. Company earnings vs cyclical peak
    # Test: latest_net_income / max(4y_net_income) > 0.70
    EPS_VS_PEAK_MIN = 0.70
    if hist_net_income and max(hist_net_income) > 0:
        eps_vs_peak = hist_net_income[-1] / max(hist_net_income)
        check_6_passed = eps_vs_peak > EPS_VS_PEAK_MIN
    else:
        eps_vs_peak = 0.0
        check_6_passed = False
    checks["6_company_cycle"] = {
        "name": "Company earnings vs cyclical peak",
        "metric_name": "Latest Net Income / 4y Peak NI",
        "value": eps_vs_peak,
        "threshold_str": "> 70% of peak",
        "passed": check_6_passed,
        "proximity": _scoring.proximity(eps_vs_peak, EPS_VS_PEAK_MIN, "above"),
        "detail": f"Latest NI / Peak NI = {eps_vs_peak*100:.1f}%",
        "part": "B",
    }

    # 7. Sentiment indicator — going against the crowd
    # Test: consensus analyst rating mean 2.5-4.0 (mixed/cautious)
    recommendation_mean = financials.get("recommendation_mean")
    if recommendation_mean is not None:
        check_7_passed = 2.5 <= recommendation_mean <= 4.0
        detail_7 = (
            f"Consensus rating mean: {recommendation_mean:.2f} "
            f"({'PASS' if check_7_passed else 'FAIL'} — Marks prefers 2.5-4.0 mixed/cautious; "
            f"strong buy consensus is a contrarian caution signal)"
        )
    else:
        check_7_passed = True  # Default PASS when unavailable
        detail_7 = "Consensus rating unavailable; defaulted PASS"
    checks["7_sentiment"] = {
        "name": "Sentiment — going against the crowd",
        "metric_name": "Consensus analyst rating",
        "value": recommendation_mean,
        "threshold_str": "Mean rating 2.5-4.0 (mixed/cautious consensus)",
        "passed": check_7_passed,
        "detail": detail_7,
        "part": "B",
    }

    # =========================================================================
    # PART C — Risk Architecture (Checks 8-11)
    # These are pre-conditions. Failure here excludes the position.
    # =========================================================================

    # 8. Capital structure resilience
    # Test: debt/ebitda < 4.0 AND interest_coverage > 4.0
    if latest_ebitda > 0:
        debt_to_ebitda = latest_debt / latest_ebitda
    else:
        debt_to_ebitda = float("inf") if latest_debt > 0 else 0.0
    latest_interest = hist_interest_expense[-1]
    if latest_interest > 0:
        coverage = hist_ebit[-1] / latest_interest
    else:
        coverage = float("inf")
    check_8_passed = debt_to_ebitda < 4.0 and coverage > 4.0
    cov_str = f"{coverage:.2f}" if coverage != float("inf") else "inf"
    checks["8_capital_structure"] = {
        "name": "Capital structure resilience",
        "metric_name": "Debt/EBITDA & Interest Coverage",
        "value": (debt_to_ebitda, coverage),
        "threshold_str": "Debt/EBITDA < 4x AND Coverage > 4x",
        "passed": check_8_passed,
        "detail": f"Debt/EBITDA = {debt_to_ebitda:.2f}x, Coverage = {cov_str}x",
        "part": "C",
    }

    # 9. FCF stability through downturn
    # Test: min(fcf_4y) > 0 (never negative in observed window)
    check_9_passed = all(f > 0 for f in hist_fcf)
    checks["9_fcf_stability"] = {
        "name": "FCF stability through downturn",
        "metric_name": "min(FCF over 4y) > 0",
        "value": min(hist_fcf) if hist_fcf else 0,
        "threshold_str": "All 4 years positive FCF",
        "passed": check_9_passed,
        "detail": f"4y FCF: {[round(f, 2) for f in hist_fcf]}",
        "part": "C",
    }

    # 10. Volatility / beta within Marks's range
    # Test: stock_beta < 1.5
    beta = financials.get("stock_beta", 1.0)
    BETA_MAX = 1.5
    check_10_passed = beta < BETA_MAX
    checks["10_beta"] = {
        "name": "Volatility / beta",
        "metric_name": "Stock beta",
        "value": beta,
        "threshold_str": "< 1.5",
        "passed": check_10_passed,
        "proximity": _scoring.proximity(beta, BETA_MAX, "below"),
        "detail": f"Beta = {beta:.2f} ({'<' if check_10_passed else '>='} 1.5)",
        "part": "C",
    }

    # 11. No single-point failure mode
    # Soft: count concentration/regulatory risks from LLM extraction; <= 1 passes.
    # Excluded (N/A) when qualitative is unavailable — a zero count from missing
    # extraction is not evidence of a clean risk profile.
    if q_status != "available":
        check_11_passed = False
        check_11_applicable = False
        soft_failure_risk_count = None
        detail_11 = "N/A — qualitative unavailable; excluded from denominator"
    else:
        soft_failure_risk_count = 0
        risks = qualitative_results.get("risk_callouts", []) or []
        concentration_keywords = ["concentration", "single customer", "regulatory", "license"]
        for r in risks:
            text = (r.get("risk", "") + " " + r.get("context", "")).lower()
            if any(kw in text for kw in concentration_keywords):
                soft_failure_risk_count += 1
        check_11_passed = soft_failure_risk_count <= 1
        check_11_applicable = True
        detail_11 = f"Concentration/regulatory risks identified: {soft_failure_risk_count}"
    checks["11_no_single_point_failure"] = {
        "name": "No single-point failure mode",
        "metric_name": "Concentration/regulatory risks in LLM extraction",
        "value": soft_failure_risk_count,
        "threshold_str": "<= 1 concentration/regulatory risk flagged",
        "passed": check_11_passed,
        "applicable": check_11_applicable,
        "detail": detail_11,
        "part": "C",
    }

    # =========================================================================
    # PART D — Second-Level Thinking & Contrarianism (Checks 12-14)
    # =========================================================================

    # 12. Variant perception present
    # Test: LLM variant_present=True AND specificity=high. Excluded (N/A) when
    # qualitative is unavailable or the model could not assess (variant_present None).
    vp = (qualitative_results or {}).get("variant_perception", {}) or {}
    variant = vp.get("variant_present")
    spec = vp.get("specificity")
    vp_quote = (vp.get("evidence_quote") or "")[:300]
    vp_confidence = vp.get("confidence")
    if q_status != "available" or variant is None:
        check_12_passed = False
        check_12_applicable = False
        detail_12 = "N/A — variant perception unavailable/unclear; excluded from denominator"
    elif vp_confidence == "low":
        check_12_passed = False
        check_12_applicable = False
        detail_12 = "N/A — low-confidence signal; excluded from denominator"
    else:
        check_12_passed = (variant is True) and (spec == "high")
        check_12_applicable = True
        cons_view = (vp.get("consensus_view") or "")[:200]
        comp_view = (vp.get("company_view") or "")[:200]
        conf_str = f" (confidence: {vp_confidence})" if vp_confidence else ""
        quote_str = f' Evidence: "{vp_quote}"' if vp_quote else ""
        detail_12 = (
            f"Variant: {variant}, Specificity: {spec}{conf_str}.{quote_str} "
            f"Consensus: '{cons_view}' | Company view: '{comp_view}'"
        )
    checks["12_variant_perception"] = {
        "name": "Variant perception",
        "metric_name": "LLM variant perception check",
        "value": check_12_passed,
        "threshold_str": "variant_present=true AND specificity=high",
        "passed": check_12_passed,
        "applicable": check_12_applicable,
        "detail": detail_12,
        "part": "D",
    }

    # 13. Management humility (knowing what you don't know)
    # Test: LLM verdict = "humble". Excluded (N/A) when unavailable, unclear, or low-confidence.
    mh = (qualitative_results or {}).get("management_humility", {}) or {}
    humility_verdict = mh.get("verdict")
    humility_confidence = mh.get("confidence")
    humility_quote = (mh.get("evidence_quote") or "")[:300]
    humility_evidence = (mh.get("evidence") or "")[:500]
    humility_quote_str = f' Evidence: "{humility_quote}"' if humility_quote else ""
    humility_conf_str = f" (confidence: {humility_confidence})" if humility_confidence else ""
    check_13_passed, check_13_applicable, detail_13 = _scoring.resolve_soft(
        q_status, humility_verdict, {"humble"},
        confidence=humility_confidence,
        pass_detail=f"Signal: {humility_verdict}{humility_conf_str}.{humility_quote_str} {humility_evidence}",
        fail_detail=f"Signal: {humility_verdict}{humility_conf_str}.{humility_quote_str} {humility_evidence}",
    )
    checks["13_management_humility"] = {
        "name": "Management humility (knowing what you don't know)",
        "metric_name": "LLM humility check",
        "value": humility_verdict,
        "threshold_str": "verdict = humble",
        "passed": check_13_passed,
        "applicable": check_13_applicable,
        "detail": detail_13,
        "part": "D",
    }

    # 14. Patient opportunism — why now?
    # Hybrid check: Hard path (drawdown >= 20% from 1y high) OR Soft path (LLM dislocation_present)
    DISLOCATION_MIN = 0.20
    price_high = financials.get("price_high_1y")
    current_price = financials.get("current_price", 0)
    hard_available = price_high is not None and current_price > 0
    drawdown = (price_high - current_price) / price_high if hard_available else None
    hard_dislocation = (drawdown is not None and drawdown >= DISLOCATION_MIN)

    wn = (qualitative_results or {}).get("why_now_signal", {}) or {}
    wn_verdict = wn.get("verdict")
    wn_confidence = wn.get("confidence")
    llm_dislocation = (wn_verdict == "dislocation_present")
    qual_available_for_check = (q_status == "available" and wn_verdict is not None and wn_confidence != "low" and wn_verdict not in ["unclear", "unknown", ""])

    applicable = hard_available or qual_available_for_check
    passed = applicable and (hard_dislocation or (qual_available_for_check and llm_dislocation))
    proximity = _scoring.proximity(drawdown, DISLOCATION_MIN, "above") if hard_available else None

    detail_parts = []
    if hard_available:
        detail_parts.append(f"Drawdown {drawdown*100:.1f}% from 1y high.")
    if qual_available_for_check:
        wn_quote = (wn.get("evidence_quote") or "")[:300]
        wn_event = (wn.get("specific_event") or "")[:200]
        wn_notes = (wn.get("notes") or "")[:500]
        wn_quote_str = f' Evidence: "{wn_quote}"' if wn_quote else ""
        wn_conf_str = f" (confidence: {wn_confidence})" if wn_confidence else ""
        detail_parts.append(f"Qual: {wn_verdict}{wn_conf_str}.{wn_quote_str} Event: {wn_event}. {wn_notes}")
        
    detail = " ".join(detail_parts).strip() if applicable else "N/A — no price history and qualitative signal unavailable/unclear; excluded from denominator"

    checks["14_why_now"] = {
        "name": "Patient opportunism (why now)",
        "metric_name": "Drawdown or LLM dislocation",
        "value": f"{drawdown*100:.1f}% / {wn_verdict}" if hard_available and qual_available_for_check else (f"{drawdown*100:.1f}%" if hard_available else wn_verdict),
        "threshold_str": ">= 20% drawdown OR verdict = dislocation_present",
        "passed": passed,
        "applicable": applicable,
        "proximity": proximity,
        "detail": detail,
        "part": "D",
    }

    # =========================================================================
    # Inject framework_reasoning into every check (v0.6)
    # =========================================================================
    for check_id, check_dict in checks.items():
        check_num = int(check_id.split("_")[0])
        reasoning = framework_parser.get_reasoning("marks", check_num)
        if reasoning is None:
            raise ValueError(
                f"framework_reasoning missing for marks check {check_id} "
                f"(check_num={check_num}). Update analysis/framework_parser.py."
            )
        check_dict["framework_reasoning"] = reasoning

    # =========================================================================
    # Scoring & Verdict (per frameworks/marks.md)
    # =========================================================================
    # Exclude-from-denominator: bank valuation N/A (checks 1,2) and any soft check
    # with an unavailable/unclear signal drop out of both score and max_score.
    # Verdict thresholds are ratio-based against ORIG_MAX=14 (original 11/9 cutoffs).
    ORIG_MAX = 14
    score, max_score = _scoring.tally(checks)
    deep_mos_passes = checks["1_deep_mos"]["passed"]
    asymmetric_passes = checks["2_asymmetric_payoff"]["passed"]
    multiple_passes = checks["4_multiple_expansion"]["passed"]
    valuation_applicable = checks["1_deep_mos"].get("applicable", True)

    if valuation_applicable and _scoring.meets(score, max_score, ORIG_MAX, 11) and deep_mos_passes and asymmetric_passes:
        verdict = "BUY"
        reason = "Risk architecture clean, deep MoS, asymmetric payoff, contrarian setup present."
    elif valuation_applicable and _scoring.meets(score, max_score, ORIG_MAX, 9) and (not deep_mos_passes or not multiple_passes):
        verdict = "WAIT"
        if intrinsic_value is not None and intrinsic_value > 0:
            target = intrinsic_value * 0.60  # 40% MoS price = 60% of intrinsic
            reason = (
                f"Risk architecture acceptable but MoS or multiple position inadequate. "
                f"Set re-rating alert at {target:.2f} (60% of intrinsic = 40% MoS)."
            )
        else:
            reason = "Risk architecture acceptable but MoS or multiple position inadequate."
    elif _scoring.meets(score, max_score, ORIG_MAX, 9):
        verdict = "WATCH"
        reason = "Mixed signals across Marks framework; monitor for cycle/sentiment change."
        if not valuation_applicable:
            reason = (
                "Risk architecture acceptable; margin of safety and asymmetric "
                "payoff pending a bank valuation model (DDM) — monitor until then."
            )
    else:
        verdict = "SKIP"
        reason = "Insufficient asymmetric edge under Marks framework."

    logger.info(
        f"Marks lens evaluation completed for {financials['ticker']}. "
        f"Score: {score}/{max_score}, Verdict: {verdict}"
    )
    return {
        "ticker": financials["ticker"],
        "checks": checks,
        "score": score,
        "max_score": max_score,
        "verdict": verdict,
        "reason": reason,
    }
