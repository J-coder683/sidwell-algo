import logging
import numpy as np

# Use the new engine imports
from sidwell.engine.core import run_engine
from sidwell.ajp.schema import AJP
from sidwell.ajp.loader import AJPLoader

logger = logging.getLogger("sidwell.valuation.dcf")

def run_dcf_valuation(financials: dict, macro_data: dict, risk_free_rate: float, qualitative_results: dict = None) -> dict:
    """
    Adapter that calls the new deterministic sidwell.engine, applying legacy constraints
    (bank short-circuit, cyclicality checks) and mapping outputs back to the legacy schema
    expected by the lenses and app.py.
    """
    ticker = financials["ticker"]
    current_price = financials["current_price"]
    market_cap = financials["market_cap"]
    
    # 1. Bank short-circuit (preserve v0.7.7 behavior)
    if financials.get("is_bank", False):
        logger.info(
            f"DCF skipped for {ticker}: bank detected. FCF-DCF not applicable; "
            f"awaiting DDM/excess-returns model."
        )
        return {
            "ticker": ticker,
            "current_price": current_price,
            "market_cap": market_cap,
            "intrinsic_value_per_share": None,
            "wacc": None,
            "enterprise_value": None,
            "equity_value": None,
            "pv_fcf": None,
            "pv_terminal_value": None,
            "terminal_value": None,
            "projections": [],
            "assumptions": {
                "dcf_methodology": "N/A — bank (DCF not applicable)",
                "target_industry": "Bank (Money Center)",
                "tax_rate": 0.25,
                "revenue_growth": 0.08,
            },
            "not_applicable": True,
            "not_applicable_reason": (
                "DCF not applicable to banks — FCF-based DCF doesn't capture bank "
                "economics (net interest margin, regulatory capital). A DDM / "
                "excess-returns model is coming soon."
            ),
        }
        
    # 2. Reconstruct AJP from qualitative results or build fallback
    ajp = None
    if qualitative_results and qualitative_results.get("ajp"):
        ajp_dict = qualitative_results.get("ajp")
        try:
            ajp = AJP.from_dict(ajp_dict)
        except Exception as e:
            logger.error(f"Failed to load AJP from qualitative results for {ticker}: {e}")
            
    if not ajp:
        # Fallback AJP construction (rare, handles no-doc cases)
        from sidwell.ajp.schema import AJPMeta, AJPAssumption
        meta = AJPMeta(
            ticker=ticker,
            as_of="2026-05-29",
            currency="INR_MM",
            sources_ingested=[],
            fiscal_year_end_month=3,
            last_actual_fy="FY2024",
            is_holdco=False,
            scenario_active="BASE"
        )
        assumptions = []
        ajp = AJP(meta=meta, assumptions=assumptions)
        
    # 3. Call the deterministic engine!
    engine_results = run_engine(financials, ajp)
    
    intrinsic_value_per_share = engine_results["intrinsic_value_per_share"]
    
    # 4. Check cyclical / cash-burning constraint if valuation is negative
    if intrinsic_value_per_share <= 0:
        fcf_4y = [(v if v is not None else 0.0) for v in (financials.get("fcf", []) or [])]
        if not fcf_4y:
            fcf_4y = [0.0, 0.0, 0.0, 0.0]
        fcf_abs_mean = abs(np.mean(fcf_4y)) if abs(np.mean(fcf_4y)) > 1e6 else 1e6  # avoid div-by-zero
        fcf_cv = np.std(fcf_4y, ddof=1) / fcf_abs_mean
        fcf_sign_flips = sum(1 for i in range(1, len(fcf_4y)) if fcf_4y[i] * fcf_4y[i-1] < 0)
        min_fcf = min(fcf_4y)
        
        is_likely_cyclical = (
            fcf_cv > 1.5
            or fcf_sign_flips >= 1
            or (min_fcf < 0 and max(fcf_4y) > 0)
        )
        
        is_structurally_cash_burning = (
            max(fcf_4y) < 0
            and fcf_sign_flips == 0
        )

        fcf_display = [f"${v/1e9:.2f}B" for v in fcf_4y]

        if is_structurally_cash_burning:
            raise ValueError(
                f"DCF cannot value {ticker}: this company is structurally cash-burning.\n"
                f"4-year FCF window: {fcf_display} \u2014 all four years negative, no sign changes.\n"
                f"\n"
                f"The DCF model values future cash flows; companies in pre-revenue or "
                f"clinical/R&D phases (early-stage biotech, growth-stage SaaS pre-profitability, "
                f"some EV startups) cannot be valued this way. They require option-pricing "
                f"or pipeline-NPV models which Sidwell does not yet implement.\n"
                f"\n"
                f"This is a KNOWN MODEL LIMITATION, not a data error. Lens checks will not run "
                f"for this ticker. Affected sectors: clinical-stage biotech (NVAX, MRNA pre-2020), "
                f"pre-profit growth SaaS, capital-burn EV/AV plays."
            )
        elif is_likely_cyclical:
            raise ValueError(
                f"DCF cannot value {ticker}: this company appears to be cyclical.\n"
                f"4-year FCF window: {fcf_display} \u2014 straddles or includes a trough.\n"
                f"FCF coefficient of variation: {fcf_cv:.2f} (>1.5 indicates high volatility).\n"
                f"Sign changes in 4y window: {fcf_sign_flips}.\n"
                f"\n"
                f"The DCF model uses 4y FCF as the normalized base, which doesn't work for cyclicals "
                f"where the historical window catches a peak or trough.\n"
                f"\n"
                f"This is a KNOWN MODEL LIMITATION, not a data error. Lens checks will not run for "
                f"this ticker until v0.7+ adds cyclical normalization (mid-cycle EBITDA margins, "
                f"7-10 year window, or peak-trough averaging).\n"
                f"\n"
                f"Affected sectors include: Semiconductors (MU, AMAT, WDC), Memory/DRAM, Steel, "
                f"Mining, Oil & Gas E&P, Shipping, Commodity chemicals."
            )
        else:
            raise ValueError(
                f"DCF produced non-positive intrinsic value ({intrinsic_value_per_share:.2f}) for {ticker}. "
                f"Likely causes: terminal_growth >= WACC; corrupted CRP/beta inputs; "
                f"projected FCF negative across forecast horizon."
            )
            
    margin_of_safety = (intrinsic_value_per_share - current_price) / current_price if current_price > 0 else 0.0

    # Map projections to legacy schema format expected by lenses/markdown report
    proj_mapped = []
    for i in range(len(engine_results["proj"]["years"])):
        proj_mapped.append({
            "stage": "high" if i < 5 else "fade",
            "year": engine_results["proj"]["years"][i],
            "year_growth": engine_results["proj"]["revenue"][i] / (engine_results["proj"]["revenue"][i-1] if i > 0 else engine_results["hist"]["is"]["sales"][-1]),
            "revenue": engine_results["proj"]["revenue"][i] * 1e6,
            "ebit": engine_results["proj"]["ebit"][i] * 1e6,
            "tax": engine_results["proj"]["taxes"][i] * 1e6,
            "nopat": engine_results["proj"]["nopat"][i] * 1e6,
            "depreciation": engine_results["proj"]["da"][i] * 1e6,
            "da": engine_results["proj"]["da"][i] * 1e6,
            "capex": engine_results["proj"]["capex"][i] * 1e6,
            "working_capital_change": engine_results["proj"]["nwc_change"][i] * 1e6,
            "nwc_change": engine_results["proj"]["nwc_change"][i] * 1e6,
            "fcf": engine_results["proj"]["ufcf"][i] * 1e6,
            "discount_factor": engine_results["fcf"]["discount_factor_list"][i],
            "pv_fcf": engine_results["fcf"]["pv_ufcf_list"][i] * 1e6
        })

    # Return mapped legacy dict superset
    return {
        "ticker": ticker,
        "current_price": current_price,
        "shares_outstanding": engine_results["shares"]["diluted_shares"],
        "intrinsic_value_per_share": intrinsic_value_per_share,
        "margin_of_safety": margin_of_safety,
        "wacc": engine_results["wacc"]["avg_wacc"],
        "enterprise_value": engine_results["fcf"]["enterprise_value"] * 1e6,
        "equity_value": engine_results["bridge"]["equity_value"] * 1e6,
        "pv_fcf": engine_results["fcf"]["cum_pv_ufcf"] * 1e6,
        "pv_terminal_value": engine_results["fcf"]["pv_tv"] * 1e6,
        "terminal_value": engine_results["terminal"]["avg_tv"] * 1e6,
        "projections": proj_mapped,
        "engine_results": engine_results,  # attach full payload for workbook
        "assumptions": {
            "dcf_methodology": "3-Statement AJP Engine v0.7",
            "target_industry": "AJP Detected",
            "tax_rate": 0.25, # Required by buffett lens
            "revenue_growth": 0.08, # Required by lenses
            "ebit_margin": 0.15,
            "cost_of_equity": engine_results["wacc"]["current_ke"],
            "cost_of_debt": engine_results["wacc"]["after_tax_kd"],
            "terminal_growth_rate": engine_results["terminal"]["terminal_growth"],
            "beta_levered": engine_results["wacc"]["current_levered_beta"],
            "beta_unlevered": engine_results["wacc"]["median_asset_beta"],
            "risk_free_rate": engine_results["wacc"]["rf"],
            "total_erp": engine_results["wacc"]["total_erp"],
            "mature_market_erp": engine_results["wacc"]["total_erp"],
            "country_risk_premium": 0.0,
            "equity_weight": 0.5,
            "debt_weight": 0.5,
            "stage_1_years": 5,
            "stage_2_years": 5,
            "stage_1_growth": engine_results["proj"]["revenue"][0] / engine_results["hist"]["is"]["sales"][-1] - 1 if engine_results["hist"]["is"]["sales"][-1] > 0 else 0.0,
            "sector_terminal_source": "AJP Engine Fallback",
            "debt_source": "AJP Engine Fallback",
            "wacc": engine_results["wacc"]["avg_wacc"],
            "latest_cash": (engine_results["hist"]["bs"]["cash_equivalents"][-1] if engine_results["hist"]["bs"]["cash_equivalents"] else 0.0) * 1e6,
            "latest_debt": ((engine_results["hist"]["bs"]["borrowings"][-1] if engine_results["hist"]["bs"]["borrowings"] else 0.0) + (engine_results["hist"]["bs"]["lease_liabilities"][-1] if engine_results["hist"]["bs"].get("lease_liabilities") else 0.0)) * 1e6,
            "shares_outstanding": engine_results["shares"]["diluted_shares"]
        }
    }
