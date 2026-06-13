import numpy as np
import logging
from analysis import framework_parser
from lenses import _scoring

logger = logging.getLogger("sidwell.lenses.buffett")

def evaluate_buffett_lens(
    financials: dict,
    dcf_results: dict,
    qualitative_results: dict = None,
    ddm_results: dict = None,
) -> dict:
    """
    Evaluates a company against Warren Buffett's 14-check framework.

    Checks are grouped into 4 Parts per frameworks/buffett.md:
      Part A (1-4):  Business Quality
      Part B (5-7):  Financial Health
      Part C (8-11): Management & Capital Allocation
      Part D (12-14): Margin of Safety & Holdability

    financials: dict from public.fetch_financials (v0.3+)
    dcf_results: dict from dcf.run_dcf_valuation
    qualitative_results: optional dict from analysis.qualitative (v0.2+)
    ddm_results: optional dict from a bank valuation model (DDM/excess-returns,
        not yet built). When it supplies an intrinsic value it takes precedence
        over the DCF, which lets the margin-of-safety check (#12) auto-activate
        for banks once that model lands.

    Returns a dict with check details, part summaries, total score, and verdict.
    """
    hist_revenue = financials["revenue"]
    if len(hist_revenue) != 4:
        raise ValueError(f"Expected exactly 4 years of historical data, got {len(hist_revenue)}")

    hist_gross_profit = financials["gross_profit"]
    hist_ebit = financials["ebit"]
    hist_interest_expense = financials["interest_expense"]
    hist_tax_provision = financials["tax_provision"]
    hist_pretax_income = financials["pretax_income"]
    hist_net_income = financials["net_income"]
    hist_total_assets = financials["total_assets"]
    hist_total_equity = financials["total_equity"]
    hist_cash = financials["cash"]
    hist_debt = financials["debt"]
    hist_capex = financials["capex"]
    hist_depreciation = financials["depreciation"]
    hist_fcf = financials["fcf"]

    current_price = dcf_results["current_price"]
    # Prefer a bank valuation (DDM/excess-returns) intrinsic value if present;
    # fall back to the DCF. For banks today both are None → margin-of-safety
    # check is marked N/A and excluded from the denominator (see check 12).
    intrinsic_value = (ddm_results or {}).get("intrinsic_value_per_share")
    if intrinsic_value is None:
        intrinsic_value = dcf_results.get("intrinsic_value_per_share")
    tax_rate = dcf_results["assumptions"]["tax_rate"]

    checks = {}

    # =========================================================================
    # PART A — Business Quality (Checks 1-4)
    # =========================================================================

    # 1. Durable competitive advantage (moat)
    # Test: stdev(gross_margin, ddof=1) < 0.03
    hist_gross_margins = [gp / rev if gp is not None and rev is not None and rev > 0 else 0.0 for gp, rev in zip(hist_gross_profit, hist_revenue)]
    hist_gm_std = np.std(hist_gross_margins, ddof=1) if len(hist_gross_margins) > 1 else 0.0
    GM_STD_MAX = 0.03
    checks["1_moat"] = {
        "name": "Durable competitive advantage (moat)",
        "metric_name": "Gross Margin Std Dev",
        "value": hist_gm_std,
        "threshold_str": "< 3.0%",
        "passed": hist_gm_std < GM_STD_MAX,
        "proximity": _scoring.proximity(hist_gm_std, GM_STD_MAX, "below"),
        "detail": (
            f"stdev = {hist_gm_std*100:.2f}% < 3%" if hist_gm_std < GM_STD_MAX
            else f"stdev = {hist_gm_std*100:.2f}% >= 3%"
        ),
        "part": "A",
    }

    # 2. High return on invested capital
    # Test: mean(roic_4y) > 0.15; ROIC = EBIT*(1-t) / (Debt+Equity-Cash)
    hist_roic_list = []
    for i in range(len(hist_revenue)):
        eq = hist_total_equity[i] or 0.0
        dbt = hist_debt[i] or 0.0
        csh = hist_cash[i] or 0.0
        ic = eq + dbt - csh
        eb = hist_ebit[i] or 0.0
        if ic > 0.0:
            roic_val = eb * (1.0 - tax_rate) / ic
        else:
            roic_val = 0.35 if eb > 0.0 else 0.0
        hist_roic_list.append(roic_val)

    hist_roic_avg = np.mean(hist_roic_list) if hist_roic_list else 0.0
    ROIC_MIN = 0.15
    checks["2_roic"] = {
        "name": "High return on invested capital",
        "metric_name": "Average ROIC",
        "value": hist_roic_avg,
        "threshold_str": "> 15.0%",
        "passed": hist_roic_avg > ROIC_MIN,
        "proximity": _scoring.proximity(hist_roic_avg, ROIC_MIN, "above"),
        "detail": (
            f"4y avg = {hist_roic_avg*100:.2f}% > 15%" if hist_roic_avg > ROIC_MIN
            else f"4y avg = {hist_roic_avg*100:.2f}% <= 15%"
        ),
        "part": "A",
    }

    # 3. Strong free-cash-flow generation
    # Test: mean(fcf_margin_4y) > 0.10 AND fcf_growth_4y > 0
    hist_fcf_margins = [f / r if f is not None and r is not None and r > 0 else 0.0 for f, r in zip(hist_fcf, hist_revenue)]
    hist_fcf_margin_avg = np.mean(hist_fcf_margins) if hist_fcf_margins else 0.0
    if len(hist_fcf) >= 2 and hist_fcf[0] != 0:
        hist_fcf_growth = (hist_fcf[-1] - hist_fcf[0]) / abs(hist_fcf[0])
    elif len(hist_fcf) >= 2:
        hist_fcf_growth = 1.0 if hist_fcf[-1] > 0 else 0.0
    else:
        hist_fcf_growth = 0.0
    hist_fcf_passed = hist_fcf_margin_avg > 0.10 and hist_fcf_growth > 0.0
    checks["3_fcf"] = {
        "name": "Strong free-cash-flow generation",
        "metric_name": "Average FCF Margin & Growth",
        "value": (hist_fcf_margin_avg, hist_fcf_growth),
        "threshold_str": "Margin > 10% & Growth > 0%",
        "passed": hist_fcf_passed,
        "detail": f"avg margin = {hist_fcf_margin_avg*100:.2f}%, FCF growth = {hist_fcf_growth*100:.2f}%",
        "part": "A",
    }

    # 4. Earnings predictability
    # Test: 0.05 < revenue_cagr_4y < 0.30 AND stdev(yoy_growth, ddof=1) < 0.10
    hist_revenue_cagr = dcf_results["assumptions"]["revenue_growth"]
    hist_growth_rates = [
        (hist_revenue[i] / hist_revenue[i - 1] - 1.0)
        for i in range(1, len(hist_revenue))
        if hist_revenue[i - 1]   # skip years where prior revenue is 0 or None
    ]
    hist_growth_std = np.std(hist_growth_rates, ddof=1) if len(hist_growth_rates) > 1 else 0.0
    check_4_passed = (0.05 < hist_revenue_cagr < 0.30) and (hist_growth_std < 0.10)
    checks["4_predictability"] = {
        "name": "Earnings predictability",
        "metric_name": "Revenue CAGR & YoY Growth StDev",
        "value": (hist_revenue_cagr, hist_growth_std),
        "threshold_str": "5% < CAGR < 30% & YoY Growth StDev < 10.0%",
        "passed": check_4_passed,
        "detail": f"Revenue CAGR = {hist_revenue_cagr*100:.2f}%, YoY Growth StDev = {hist_growth_std*100:.2f}%",
        "part": "A",
    }

    # =========================================================================
    # PART B — Financial Health (Checks 5-7)
    # =========================================================================

    # 5. Conservative balance sheet
    # Test: debt/ebitda < 3.0 AND interest_coverage > 5.0
    latest_ebitda = hist_ebit[-1] + hist_depreciation[-1]
    latest_debt = hist_debt[-1]
    if latest_ebitda > 0:
        latest_debt_to_ebitda = latest_debt / latest_ebitda
    else:
        latest_debt_to_ebitda = 0.0 if latest_debt == 0.0 else float("inf")
    latest_interest = hist_interest_expense[-1]
    if latest_interest > 0:
        latest_interest_coverage = hist_ebit[-1] / latest_interest
    else:
        latest_interest_coverage = float("inf")
    checks["5_balance_sheet"] = {
        "name": "Conservative balance sheet",
        "metric_name": "Debt/EBITDA & Interest Coverage",
        "value": (latest_debt_to_ebitda, latest_interest_coverage),
        "threshold_str": "Debt/EBITDA < 3x & Coverage > 5x",
        "passed": latest_debt_to_ebitda < 3.0 and latest_interest_coverage > 5.0,
        "detail": (
            f"Debt/EBITDA = {latest_debt_to_ebitda:.2f}x, Int. Coverage = {latest_interest_coverage:.2f}x"
            if latest_interest_coverage != float("inf")
            else f"Debt/EBITDA = {latest_debt_to_ebitda:.2f}x, Int. Coverage = N/A (no interest)"
        ),
        "part": "B",
    }

    # 6. ROE without excess leverage
    # Test: mean(roe_4y) > 0.15 AND latest_equity/assets > 0.4
    hist_roe_list = [ni / eq if ni is not None and eq is not None and eq > 0 else 0.0 for ni, eq in zip(hist_net_income, hist_total_equity)]
    hist_roe_avg = np.mean(hist_roe_list) if hist_roe_list else 0.0
    latest_equity_to_assets = hist_total_equity[-1] / hist_total_assets[-1] if hist_total_assets[-1] > 0 else 0.0
    checks["6_roe_leverage"] = {
        "name": "ROE without excess leverage",
        "metric_name": "Avg ROE & Equity/Assets",
        "value": (hist_roe_avg, latest_equity_to_assets),
        "threshold_str": "ROE > 15% & Equity/Assets > 40%",
        "passed": hist_roe_avg > 0.15 and latest_equity_to_assets > 0.4,
        "detail": f"4y avg ROE = {hist_roe_avg*100:.2f}%, Equity/Assets = {latest_equity_to_assets*100:.2f}%",
        "part": "B",
    }

    # 7. Liquidity cushion (Gibraltar test)
    # Test: cash/debt > 0.5 OR debt == 0
    latest_cash_eq = hist_cash[-1]
    if latest_debt == 0.0:
        check_7_passed = True
        detail_7 = "Debt-free; Gibraltar test passes trivially"
        cash_to_debt = float("inf")
    else:
        cash_to_debt = latest_cash_eq / latest_debt
        check_7_passed = cash_to_debt > 0.5
        detail_7 = f"Cash / Debt = {cash_to_debt:.2f}x ({'>' if check_7_passed else '<='} 0.5)"
    checks["7_liquidity_cushion"] = {
        "name": "Liquidity cushion (Gibraltar test)",
        "metric_name": "Cash / Total Debt",
        "value": (latest_cash_eq, latest_debt),
        "threshold_str": "Cash / Debt > 0.5x OR debt-free",
        "passed": check_7_passed,
        "detail": detail_7,
        "part": "B",
    }

    # =========================================================================
    # PART C — Management & Capital Allocation (Checks 8-11)
    # =========================================================================

    # 8. Anti-dilution discipline
    # Test: shares_latest / shares_4y_ago <= 1.02
    historical_shares = financials.get("historical_shares", [])
    SHARE_GROWTH_MAX = 1.02
    if len(historical_shares) >= 4 and historical_shares[0] > 0 and historical_shares[-1] > 0:
        share_growth = historical_shares[-1] / historical_shares[0]
        check_8_passed = share_growth <= SHARE_GROWTH_MAX
        detail_8 = f"Share count growth (4y): {(share_growth - 1) * 100:+.2f}% (threshold: <= +2%)"
    else:
        check_8_passed = True  # Default PASS if data unavailable
        detail_8 = "Share count data unavailable; check defaulted PASS"
        share_growth = None
    checks["8_anti_dilution"] = {
        "name": "Anti-dilution discipline",
        "metric_name": "Share count growth (4y)",
        "value": share_growth,
        "threshold_str": "<= 2% growth over 4y",
        "passed": check_8_passed,
        # Proximity on the growth-delta scale (0% vs +2% allowed), not the raw
        # ratio (1.00 vs 1.02) — normalizing by a ~1.0 threshold would compress a
        # comfortable 0%-dilution pass to a misleading "+0.02 knife-edge".
        "proximity": _scoring.proximity(share_growth - 1.0, SHARE_GROWTH_MAX - 1.0, "below") if share_growth is not None else None,
        "detail": detail_8,
        "part": "C",
    }

    # 9. Capital allocation track record
    # Test: ROIC not declining > 3pp (latter-2y vs earlier-2y) AND capital returned
    if len(hist_roic_list) >= 4:
        roic_first_half = np.mean(hist_roic_list[:2])
        roic_second_half = np.mean(hist_roic_list[2:])
        roic_trend = roic_second_half - roic_first_half
        capital_returned = (
            (share_growth is not None and share_growth <= 1.0)  # net buybacks
            or (financials.get("dividend_yield", 0) > 0)
        )
        check_9_passed = roic_trend > -0.03 and capital_returned
        detail_9 = (
            f"ROIC trend (latter-2y vs earlier-2y): {roic_trend*100:+.2f}pp; "
            f"capital returned to shareholders: {'yes' if capital_returned else 'no'}"
        )
    else:
        check_9_passed = True
        detail_9 = "Insufficient ROIC history; check defaulted PASS"
        roic_trend = None
        capital_returned = False
    checks["9_capital_allocation"] = {
        "name": "Capital allocation track record",
        "metric_name": "ROIC trend + capital return",
        "value": (roic_trend, capital_returned),
        "threshold_str": "ROIC not declining > 3pp AND capital returned",
        "passed": check_9_passed,
        "detail": detail_9,
        "part": "C",
    }

    # 10. Owner orientation
    # Test: insider_ownership > 0.05 OR (soft) LLM = owner_oriented
    # Hybrid: hard path is always computable. Soft branch only fires when
    # confidence != 'low' (low-confidence soft signal cannot rescue a hard FAIL).
    insider_pct = financials.get("insider_ownership", 0.0)
    hard_owner_pass = insider_pct > 0.05
    soft_owner_verdict = None
    soft_owner_confidence = None
    soft_owner_quote = ""
    soft_owner_pass = False  # default: soft branch does not fire
    if qualitative_results and qualitative_results.get("status") == "available":
        oo = qualitative_results.get("owner_orientation_signal", {}) or {}
        soft_owner_verdict = oo.get("verdict")
        soft_owner_confidence = oo.get("confidence")
        soft_owner_quote = (oo.get("evidence_quote") or "")[:300]
        # Only let the soft branch fire when signal is usable (not low confidence)
        if soft_owner_verdict == "owner_oriented" and soft_owner_confidence != "low":
            soft_owner_pass = True
    check_10_passed = hard_owner_pass or soft_owner_pass
    quote_str = f' Evidence: "{soft_owner_quote}"' if soft_owner_quote else ""
    conf_str = f" (confidence: {soft_owner_confidence})" if soft_owner_confidence else ""
    detail_10 = (
        f"Insider ownership: {insider_pct*100:.2f}% "
        f"({'PASS' if hard_owner_pass else 'FAIL'} at >5%). "
        f"Signal: {soft_owner_verdict or 'unavailable'}{conf_str}.{quote_str}"
    )
    checks["10_owner_orientation"] = {
        "name": "Owner orientation",
        "metric_name": "Insider ownership OR LLM owner-orientation",
        "value": (insider_pct, soft_owner_verdict),
        "threshold_str": "Insiders > 5% OR LLM = owner_oriented",
        "passed": check_10_passed,
        "detail": detail_10,
        "part": "C",
    }

    # 11. Management coherence
    # Test (soft): LLM coherence verdict = "coherent". Excluded from denominator
    # (N/A) when qualitative is unavailable, the verdict is unclear, or confidence is low.
    q_status = (qualitative_results or {}).get("status", "unavailable")
    coh = (qualitative_results or {}).get("coherence_assessment", {}) or {}
    coh_verdict = coh.get("verdict")
    coh_confidence = coh.get("confidence")
    coh_quote = (coh.get("evidence_quote") or "")[:300]
    coh_reasoning = (coh.get("reasoning") or "")[:500]
    coh_quote_str = f' Evidence: "{coh_quote}"' if coh_quote else ""
    coh_conf_str = f" (confidence: {coh_confidence})" if coh_confidence else ""
    coh_passed, coh_applicable, coh_detail = _scoring.resolve_soft(
        q_status, coh_verdict, {"coherent"},
        confidence=coh_confidence,
        pass_detail=f"Signal: coherent{coh_conf_str}.{coh_quote_str} {coh_reasoning}",
        fail_detail=f"Signal: {coh_verdict}{coh_conf_str}.{coh_quote_str} {coh_reasoning}",
    )
    checks["11_mgmt_coherence"] = {
        "name": "Management coherence",
        "metric_name": "LLM coherence verdict",
        "value": coh_verdict,
        "threshold_str": "LLM coherence = coherent",
        "passed": coh_passed,
        "applicable": coh_applicable,
        "detail": coh_detail,
        "part": "C",
    }

    # =========================================================================
    # PART D — Margin of Safety & Holdability (Checks 12-14)
    # =========================================================================

    # 12. Margin of safety
    # Test: (intrinsic - price) / intrinsic > 0.25
    # When no valuation model applies (banks have no DCF and no DDM yet),
    # intrinsic_value is None: mark the check N/A (applicable=False) so it is
    # excluded from the denominator. It auto-activates once ddm_results supplies
    # an intrinsic value.
    MOS_MIN = 0.25
    if intrinsic_value is None:
        checks["12_margin_of_safety"] = {
            "name": "Margin of safety",
            "metric_name": "Discount to Intrinsic Value",
            "value": None,
            "threshold_str": "> 25.0%",
            "passed": False,
            "applicable": False,
            "detail": "N/A — DCF not applicable to banks; awaiting DDM/excess-returns model.",
            "part": "D",
        }
    else:
        if intrinsic_value > 0:
            mos = (intrinsic_value - current_price) / intrinsic_value
        else:
            mos = -1.0
        if intrinsic_value <= 0:
            mos_detail = "DCF produced non-positive intrinsic value — model failed"
        elif intrinsic_value < current_price:
            mos_detail = (
                f"Trading at {current_price/intrinsic_value:.1f}x intrinsic value "
                f"(target ≤ 0.75x) (Price: {current_price:.2f}, Intrinsic: {intrinsic_value:.2f})"
            )
        else:
            mos_detail = f"mos = {mos*100:.2f}% (Price: {current_price:.2f}, Intrinsic: {intrinsic_value:.2f})"
        checks["12_margin_of_safety"] = {
            "name": "Margin of safety",
            "metric_name": "Discount to Intrinsic Value",
            "value": mos,
            "threshold_str": "> 25.0%",
            "passed": mos > MOS_MIN,
            "proximity": _scoring.proximity(mos, MOS_MIN, "above"),
            "detail": mos_detail,
            "part": "D",
        }

    # 13. Hard understandability blacklist
    # Test: ticker not in avoided sectors (crypto, etc.)
    avoided_prefixes = ["BTC", "ETH", "COIN"]
    hard_pass = not any(financials["ticker"].startswith(p) for p in avoided_prefixes)
    checks["13_hard_blacklist"] = {
        "name": "Understandable business (hard blacklist)",
        "metric_name": "Ticker not in avoided sectors",
        "value": hard_pass,
        "threshold_str": "Ticker not BTC/ETH/COIN",
        "passed": hard_pass,
        "detail": (
            "Hard check: PASS (ticker not in avoided-sector blacklist)" if hard_pass
            else "Hard check: FAIL (ticker in avoided-sector blacklist)"
        ),
        "part": "D",
    }

    # 14. Holdability — 20-year test (soft, LLM-based)
    # Test: LLM verdict = "holdable_20y". Excluded from denominator (N/A) when
    # qualitative is unavailable, the verdict is unclear, or confidence is low.
    ha = (qualitative_results or {}).get("holdability_assessment", {}) or {}
    hold_verdict = ha.get("verdict")
    hold_confidence = ha.get("confidence")
    hold_quote = (ha.get("evidence_quote") or "")[:300]
    hold_reasoning = (ha.get("reasoning") or "")[:500]
    hold_quote_str = f' Evidence: "{hold_quote}"' if hold_quote else ""
    hold_conf_str = f" (confidence: {hold_confidence})" if hold_confidence else ""
    hold_passed, hold_applicable, hold_detail = _scoring.resolve_soft(
        q_status, hold_verdict, {"holdable_20y"},
        confidence=hold_confidence,
        pass_detail=f"Signal: {hold_verdict}{hold_conf_str}.{hold_quote_str} {hold_reasoning}",
        fail_detail=f"Signal: {hold_verdict}{hold_conf_str}.{hold_quote_str} {hold_reasoning}",
    )
    checks["14_holdability"] = {
        "name": "Holdability (20-year test)",
        "metric_name": "LLM holdability assessment",
        "value": hold_verdict,
        "threshold_str": "LLM verdict = holdable_20y",
        "passed": hold_passed,
        "applicable": hold_applicable,
        "detail": hold_detail,
        "part": "D",
    }

    # =========================================================================
    # Inject framework_reasoning into every check (v0.6)
    # =========================================================================
    for check_id, check_dict in checks.items():
        check_num = int(check_id.split("_")[0])
        reasoning = framework_parser.get_reasoning("buffett", check_num)
        if reasoning is None:
            raise ValueError(
                f"framework_reasoning missing for buffett check {check_id} "
                f"(check_num={check_num}). Update analysis/framework_parser.py."
            )
        check_dict["framework_reasoning"] = reasoning

    # =========================================================================
    # Scoring & Verdict (per frameworks/buffett.md)
    # =========================================================================
    # Exclude-from-denominator: soft checks marked not-applicable (qualitative
    # unavailable/unclear) and the bank margin-of-safety N/A drop out of both
    # score and max_score. Verdict thresholds are ratio-based against ORIG_MAX=14
    # so full-data behavior is identical to the original absolute 12/10 cutoffs.
    ORIG_MAX = 14
    score, max_score = _scoring.tally(checks)
    check_12 = checks["12_margin_of_safety"]
    check_12_passes = check_12["passed"]
    mos_applicable = check_12.get("applicable", True)

    if mos_applicable and _scoring.meets(score, max_score, ORIG_MAX, 12) and check_12_passes:
        verdict = "BUY"
        reason = "Excellent business meeting Buffett quality, management, and price criteria."
    elif mos_applicable and _scoring.meets(score, max_score, ORIG_MAX, 10) and not check_12_passes:
        verdict = "WAIT"
        reason = (
            f"High-quality business that satisfies most Buffett criteria but lacks "
            f"margin of safety. Set alert at buy-trigger price: "
            f"₹{intrinsic_value * 0.75:.2f} (75% of intrinsic value)."
        )
    elif _scoring.meets(score, max_score, ORIG_MAX, 10):
        verdict = "WATCH"
        reason = "Most quality criteria pass; monitor for resolution of failed checks."
        if not mos_applicable:
            reason = (
                "Most quality criteria pass; margin of safety pending a bank "
                "valuation model (DDM) — monitor until then."
            )
    else:
        verdict = "SKIP"
        reason = "Does not meet enough Buffett criteria across business quality, management, and price."

    logger.info(
        f"Buffett lens evaluation completed for {financials['ticker']}. "
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
