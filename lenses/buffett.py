import numpy as np
import logging

logger = logging.getLogger("sidwell.lenses.buffett")

def evaluate_buffett_lens(financials: dict, dcf_results: dict) -> dict:
    """
    Evaluates a company's financials and DCF results against Warren Buffett's 8 checks.
    
    financials: dict of historical financials (from public.fetch_financials)
    dcf_results: dict of DCF calculations (from dcf.run_dcf_valuation)
    
    Returns a dict with check details, total score, and verdict.
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
    intrinsic_value = dcf_results["intrinsic_value_per_share"]
    
    checks = {}
    
    # 1. Durable competitive advantage (moat)
    # Proxy: Gross margin stability over 4 years.
    # Test: gross_margin_std_4y < 0.03
    hist_gross_margins = [gp / rev if rev > 0 else 0.0 for gp, rev in zip(hist_gross_profit, hist_revenue)]
    hist_gm_std = np.std(hist_gross_margins, ddof=1) if len(hist_gross_margins) > 1 else 0.0
    checks["1_moat"] = {
        "name": "Durable competitive advantage (moat)",
        "metric_name": "Gross Margin Std Dev",
        "value": hist_gm_std,
        "threshold_str": "< 3.0%",
        "passed": hist_gm_std < 0.03,
        "detail": f"stdev = {hist_gm_std*100:.2f}% < 3%" if hist_gm_std < 0.03 else f"stdev = {hist_gm_std*100:.2f}% >= 3%"
    }
    
    # 2. High return on invested capital
    # Test: roic_4y_avg > 0.15
    # ROIC = EBIT * (1-t) / (Debt + Equity - Cash)
    tax_rate = dcf_results["assumptions"]["tax_rate"]
    hist_roic_list = []
    for i in range(len(hist_revenue)):
        eq = hist_total_equity[i]
        dbt = hist_debt[i]
        csh = hist_cash[i]
        ic = eq + dbt - csh
        eb = hist_ebit[i]
        
        if ic > 0.0:
            roic_val = eb * (1.0 - tax_rate) / ic
        else:
            roic_val = 0.35 if eb > 0.0 else 0.0 # High default ROIC if equity/debt are zero but ebit positive
        hist_roic_list.append(roic_val)
        
    hist_roic_avg = np.mean(hist_roic_list) if hist_roic_list else 0.0
    checks["2_roic"] = {
        "name": "High return on invested capital",
        "metric_name": "Average ROIC",
        "value": hist_roic_avg,
        "threshold_str": "> 15.0%",
        "passed": hist_roic_avg > 0.15,
        "detail": f"4y avg = {hist_roic_avg*100:.2f}% > 15%" if hist_roic_avg > 0.15 else f"4y avg = {hist_roic_avg*100:.2f}% <= 15%"
    }
    
    # 3. Strong free-cash-flow generation
    # Test: fcf_margin_4y_avg > 0.10 AND fcf_growth_4y > 0
    hist_fcf_margins = [f / r if r > 0 else 0.0 for f, r in zip(hist_fcf, hist_revenue)]
    hist_fcf_margin_avg = np.mean(hist_fcf_margins) if hist_fcf_margins else 0.0
    
    # FCF Growth
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
        "detail": f"avg margin = {hist_fcf_margin_avg*100:.2f}%, FCF growth = {hist_fcf_growth*100:.2f}%"
    }
    
    # 4. Conservative balance sheet
    # Test: debt_to_ebitda < 3.0 AND interest_coverage > 5.0
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
        latest_interest_coverage = float("inf") # No interest expense -> perfect coverage
        
    checks["4_balance_sheet"] = {
        "name": "Conservative balance sheet",
        "metric_name": "Debt/EBITDA & Interest Coverage",
        "value": (latest_debt_to_ebitda, latest_interest_coverage),
        "threshold_str": "Debt/EBITDA < 3x & Coverage > 5x",
        "passed": latest_debt_to_ebitda < 3.0 and latest_interest_coverage > 5.0,
        "detail": f"Debt/EBITDA = {latest_debt_to_ebitda:.2f}x, Int. Coverage = {latest_interest_coverage:.2f}x" if latest_interest_coverage != float("inf") else f"Debt/EBITDA = {latest_debt_to_ebitda:.2f}x, Int. Coverage = N/A (no interest)"
    }
    
    # 5. Return on equity without excess leverage
    # Test: roe_4y_avg > 0.15 AND equity_to_assets > 0.4
    hist_roe_list = [ni / eq if eq > 0 else 0.0 for ni, eq in zip(hist_net_income, hist_total_equity)]
    hist_roe_avg = np.mean(hist_roe_list) if hist_roe_list else 0.0
    
    latest_equity_to_assets = hist_total_equity[-1] / hist_total_assets[-1] if hist_total_assets[-1] > 0 else 0.0
    checks["5_roe_leverage"] = {
        "name": "ROE without excess leverage",
        "metric_name": "Avg ROE & Equity/Assets",
        "value": (hist_roe_avg, latest_equity_to_assets),
        "threshold_str": "ROE > 15% & Equity/Assets > 40%",
        "passed": hist_roe_avg > 0.15 and latest_equity_to_assets > 0.4,
        "detail": f"4y avg ROE = {hist_roe_avg*100:.2f}%, Equity/Assets = {latest_equity_to_assets*100:.2f}%"
    }
    
    # 6. Earnings predictability
    # Test: 0.05 < revenue_cagr_4y < 0.30 AND stdev of YoY growth rates < 0.10
    hist_revenue_cagr = dcf_results["assumptions"]["revenue_growth"]
    
    hist_growth_rates = [(hist_revenue[i] / hist_revenue[i-1] - 1.0) for i in range(1, len(hist_revenue))]
    hist_growth_std = np.std(hist_growth_rates, ddof=1) if len(hist_growth_rates) > 1 else 0.0
        
    check_6_passed = (0.05 < hist_revenue_cagr < 0.30) and (hist_growth_std < 0.10)
    
    checks["6_predictability"] = {
        "name": "Earnings predictability",
        "metric_name": "Revenue CAGR & YoY Growth StDev",
        "value": (hist_revenue_cagr, hist_growth_std),
        "threshold_str": "5% < CAGR < 30% & YoY Growth StDev < 10.0%",
        "passed": check_6_passed,
        "detail": f"Revenue CAGR = {hist_revenue_cagr*100:.2f}%, YoY Growth StDev = {hist_growth_std*100:.2f}%"
    }
    
    # 7. Margin of safety
    # Test: (dcf_intrinsic_value - current_price) / dcf_intrinsic_value > 0.25
    if intrinsic_value > 0:
        mos = (intrinsic_value - current_price) / intrinsic_value
    else:
        mos = -1.0
        
    if intrinsic_value <= 0:
        mos_detail = "DCF produced non-positive intrinsic value — model failed"
    elif intrinsic_value < current_price:
        mos_detail = f"Trading at {current_price/intrinsic_value:.1f}x intrinsic value (target ≤ 0.75x) (Price: {current_price:.2f}, Intrinsic: {intrinsic_value:.2f})"
    else:
        mos_detail = f"mos = {mos*100:.2f}% (Price: {current_price:.2f}, Intrinsic: {intrinsic_value:.2f})"
        
    checks["7_margin_of_safety"] = {
        "name": "Margin of safety",
        "metric_name": "Discount to Intrinsic Value",
        "value": mos,
        "threshold_str": "> 25.0%",
        "passed": mos > 0.25,
        "detail": mos_detail
    }
    
    # 8. Understandable business
    # Test: Default True unless specific sector/industry checks fail (manual list)
    # We can inspect the ticker to flag complex companies
    avoided_prefixes = ["BTC", "ETH", "COIN"]
    avoided = False
    for pref in avoided_prefixes:
        if financials["ticker"].startswith(pref):
            avoided = True
            break
            
    checks["8_understandable"] = {
        "name": "Understandable business",
        "metric_name": "Circle of Competence Flag",
        "value": not avoided,
        "threshold_str": "True",
        "passed": not avoided,
        "detail": "Business is within standard circle of competence" if not avoided else "Business is outside circle of competence"
    }
    
    # Scoring
    score = sum(1 for c in checks.values() if c["passed"])
    
    # Verdict logic
    check_7_passes = checks["7_margin_of_safety"]["passed"]
    
    if score >= 7 and check_7_passes:
        verdict = "BUY"
        reason = "Excellent business with a strong competitive moat, conservative capital structure, and a deep margin of safety at the current price."
    elif score >= 6 and not check_7_passes:
        verdict = "WAIT"
        reason = f"High-quality business that satisfies key quality criteria, but currently lacks a sufficient margin of safety (current price {current_price:.2f} is higher than the target buy price of {intrinsic_value * 0.75:.2f}). Wait for a pullback."
    elif score >= 6:
        verdict = "WATCH"
        reason = "A solid business that meets most criteria, but has some minor leverage or growth predictability concerns. Put on watchlist."
    else:
        verdict = "SKIP"
        reason = "Does not meet the quality or financial health standards of the Buffett framework. Skip."
        
    res = {
        "ticker": financials["ticker"],
        "checks": checks,
        "score": score,
        "verdict": verdict,
        "reason": reason
    }
    
    logger.info(f"Buffett lens evaluation completed for {financials['ticker']}. Score: {score}/8, Verdict: {verdict}")
    return res
