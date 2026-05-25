import logging

logger = logging.getLogger("sidwell.valuation.dcf")

def run_dcf_valuation(financials: dict, macro_data: dict, risk_free_rate: float) -> dict:
    """
    Computes WACC and performs a 5-year DCF valuation.
    
    financials: dict of historical financials (from public.fetch_financials)
    macro_data: dict of Damodaran ERP & Betas (from public.fetch_damodaran_data)
    risk_free_rate: float (risk-free rate in decimal, e.g. 0.0712)
    
    Returns a dict with DCF results.
    """
    # 1. Inputs and averages
    ticker = financials["ticker"]
    current_price = financials["current_price"]
    shares_outstanding = financials["shares_outstanding"]
    market_cap = financials["market_cap"]
    
    hist_years = financials["years"]
    hist_years_count = len(hist_years)
    
    if hist_years_count != 4:
        raise ValueError(f"Expected exactly 4 years of historical data, got {hist_years_count}")
        
    hist_revenue = financials["revenue"]
    hist_gross_profit = financials["gross_profit"]
    hist_ebit = financials["ebit"]
    hist_interest_expense = financials["interest_expense"]
    hist_tax_provision = financials["tax_provision"]
    hist_pretax_income = financials["pretax_income"]
    hist_net_income = financials["net_income"]
    
    latest_cash = financials["cash"][-1]
    latest_debt = financials["debt"][-1]
    latest_assets = financials["total_assets"][-1]
    
    # Calculate historical ratios
    if hist_years_count >= 2 and hist_revenue[0] > 0 and hist_revenue[-1] > 0:
        hist_revenue_cagr = (hist_revenue[-1] / hist_revenue[0]) ** (1.0 / (hist_years_count - 1)) - 1.0
    else:
        hist_revenue_cagr = 0.08  # Default 8% growth if data is missing or negative
        
    # Cap growth rate between 5% and 20% for conservative projections
    proj_revenue_growth = max(0.05, min(0.20, hist_revenue_cagr))
    
    # EBIT Margin
    hist_ebit_margins = []
    for i in range(hist_years_count):
        if hist_revenue[i] > 0:
            hist_ebit_margins.append(hist_ebit[i] / hist_revenue[i])
        else:
            hist_ebit_margins.append(0.0)
    hist_ebit_margin_avg = sum(hist_ebit_margins) / hist_years_count if hist_ebit_margins else 0.15
    
    # Tax Rate
    hist_tax_rates = []
    for i in range(hist_years_count):
        if hist_pretax_income[i] > 0 and hist_tax_provision[i] >= 0:
            hist_tax_rates.append(hist_tax_provision[i] / hist_pretax_income[i])
        elif hist_ebit[i] > 0 and hist_tax_provision[i] >= 0:
            hist_tax_rates.append(hist_tax_provision[i] / hist_ebit[i])
            
    hist_tax_rate_avg = sum(hist_tax_rates) / len(hist_tax_rates) if hist_tax_rates else 0.2517
    if hist_tax_rate_avg < 0 or hist_tax_rate_avg > 0.45:
        hist_tax_rate_avg = 0.2517
        
    # D&A Ratio
    hist_deprec_ratios = []
    for i in range(hist_years_count):
        if hist_revenue[i] > 0:
            hist_deprec_ratios.append(financials["depreciation"][i] / hist_revenue[i])
    hist_deprec_ratio_avg = sum(hist_deprec_ratios) / hist_years_count if hist_deprec_ratios else 0.02
    
    # CapEx Ratio
    hist_capex_ratios = []
    for i in range(hist_years_count):
        if hist_revenue[i] > 0:
            hist_capex_ratios.append(financials["capex"][i] / hist_revenue[i])
    hist_capex_ratio_avg = sum(hist_capex_ratios) / hist_years_count if hist_capex_ratios else 0.03
    
    # NWC Change Ratio (relative to revenue)
    hist_nwc_ratios = []
    for i in range(hist_years_count):
        if hist_revenue[i] > 0:
            hist_nwc_ratios.append(financials["working_capital_change"][i] / hist_revenue[i])
    hist_nwc_ratio_avg = sum(hist_nwc_ratios) / hist_years_count if hist_nwc_ratios else 0.0
    
    # 2. Cost of Equity (CAPM)
    beta_unlevered = macro_data["industry_unlevered_beta"]
    total_erp = macro_data["total_erp"]
    
    latest_d_e_ratio = latest_debt / market_cap if market_cap > 0 else 0.0
    latest_beta_levered = beta_unlevered * (1.0 + (1.0 - hist_tax_rate_avg) * latest_d_e_ratio)
    
    # If market cap is zero or ratio is invalid, fall back to industry levered beta
    if latest_beta_levered <= 0.0 or latest_beta_levered > 3.0:
        latest_beta_levered = macro_data["industry_levered_beta"]
        
    latest_cost_of_equity = risk_free_rate + latest_beta_levered * total_erp
    
    # 3. Cost of Debt
    Kd_floor = risk_free_rate + 0.01
    Kd_ceiling = risk_free_rate + 0.05
    
    if latest_debt < 0.05 * latest_assets:
        latest_cost_of_debt = risk_free_rate + 0.02
        debt_source = "Default: Rf + 2% (debt < 5% of total assets)"
    else:
        calc_kd = hist_interest_expense[-1] / latest_debt if latest_debt > 0 else 0.0
        if calc_kd < Kd_floor:
            latest_cost_of_debt = Kd_floor
            debt_source = f"Calculated and floored to Rf + 1% (raw: {calc_kd:.2%})"
        elif calc_kd > Kd_ceiling:
            latest_cost_of_debt = Kd_ceiling
            debt_source = f"Calculated and capped at Rf + 5% (raw: {calc_kd:.2%})"
        else:
            latest_cost_of_debt = calc_kd
            debt_source = f"Calculated: int_expense/debt = {calc_kd:.2%}"
        
    # 4. WACC Calculation
    total_capital = market_cap + latest_debt
    if total_capital > 0:
        weight_equity = market_cap / total_capital
        weight_debt = latest_debt / total_capital
    else:
        weight_equity = 1.0
        weight_debt = 0.0
        
    wacc = (weight_equity * latest_cost_of_equity) + (weight_debt * latest_cost_of_debt * (1.0 - hist_tax_rate_avg))
    
    # WACC sanity check (raise ValueError for production invariants)
    if not (0.05 < wacc < 0.30):
        raise ValueError(f"WACC of {wacc:.2%} is implausible — check inputs")
        
    # 5. Explicit 5-Year Forecast
    proj_projections = []
    prev_rev = hist_revenue[-1]
    
    for proj_year_idx in range(1, 6):
        proj_rev = prev_rev * (1.0 + proj_revenue_growth)
        proj_ebit = proj_rev * hist_ebit_margin_avg
        proj_tax = proj_ebit * hist_tax_rate_avg
        proj_dep = proj_rev * hist_deprec_ratio_avg
        proj_cap = proj_rev * hist_capex_ratio_avg
        proj_nwc = proj_rev * hist_nwc_ratio_avg
        
        proj_fcf = proj_ebit * (1.0 - hist_tax_rate_avg) + proj_dep - proj_cap + proj_nwc
        
        proj_projections.append({
            "year": f"Year {proj_year_idx}",
            "revenue": proj_rev,
            "ebit": proj_ebit,
            "tax": proj_tax,
            "depreciation": proj_dep,
            "capex": proj_cap,
            "working_capital_change": proj_nwc,
            "fcf": proj_fcf
        })
        prev_rev = proj_rev
        
    # 6. Terminal Value (Gordon Growth)
    g_terminal = min(0.04, risk_free_rate - 0.01)
    if g_terminal >= wacc:
        g_terminal = wacc - 0.02
    if g_terminal < 0.0:
        g_terminal = 0.02
        
    fcf_5 = proj_projections[-1]["fcf"]
    terminal_value = (fcf_5 * (1.0 + g_terminal)) / (wacc - g_terminal)
    
    # 7. Discounting Cash Flows
    pv_fcf = 0.0
    for idx, proj in enumerate(proj_projections):
        discount_factor = (1.0 + wacc) ** (idx + 1)
        proj["discount_factor"] = discount_factor
        proj["pv_fcf"] = proj["fcf"] / discount_factor
        pv_fcf += proj["pv_fcf"]
        
    pv_terminal_value = terminal_value / ((1.0 + wacc) ** 5)
    enterprise_value = pv_fcf + pv_terminal_value
    
    # Intrinsic Equity Value
    equity_value = enterprise_value + latest_cash - latest_debt
    intrinsic_value_per_share = equity_value / shares_outstanding if shares_outstanding > 0 else 0.0
    
    # Compile output data
    assumptions = {
        "revenue_growth": proj_revenue_growth,
        "ebit_margin": hist_ebit_margin_avg,
        "tax_rate": hist_tax_rate_avg,
        "deprec_ratio": hist_deprec_ratio_avg,
        "capex_ratio": hist_capex_ratio_avg,
        "nwc_ratio": hist_nwc_ratio_avg,
        "terminal_growth_rate": g_terminal,
        "risk_free_rate": risk_free_rate,
        "mature_market_erp": macro_data["mature_market_erp"],
        "country_risk_premium": macro_data["country_risk_premium"],
        "total_erp": total_erp,
        "beta_unlevered": beta_unlevered,
        "beta_levered": latest_beta_levered,
        "cost_of_equity": latest_cost_of_equity,
        "cost_of_debt": latest_cost_of_debt,
        "debt_source": debt_source,
        "equity_weight": weight_equity,
        "debt_weight": weight_debt,
        "wacc": wacc,
        "shares_outstanding": shares_outstanding,
        "latest_cash": latest_cash,
        "latest_debt": latest_debt,
        "target_industry": macro_data.get("target_industry", "Chemical (Specialty)"),
        "industry_source": macro_data.get("industry_source", "default")
    }
    
    res = {
        "ticker": ticker,
        "current_price": current_price,
        "market_cap": market_cap,
        "intrinsic_value_per_share": intrinsic_value_per_share,
        "wacc": wacc,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "pv_fcf": pv_fcf,
        "pv_terminal_value": pv_terminal_value,
        "terminal_value": terminal_value,
        "projections": proj_projections,
        "assumptions": assumptions
    }
    
    logger.info(f"DCF valuation completed for {ticker}. Intrinsic value: {intrinsic_value_per_share:.2f}")
    return res
