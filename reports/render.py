import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("sidwell.reports.render")

SIDWELL_VERSION = "v0.1"

def format_currency(val: float, is_india: bool) -> str:
    """
    Formats numeric values as currency.
    If is_india is True, formats as INR (e.g., ₹12,34,567.89 or ₹12.35M).
    Otherwise formats as USD.
    """
    symbol = "₹" if is_india else "$"
    if abs(val) >= 1e9:
        return f"{symbol}{val / 1e9:,.2f}B"
    elif abs(val) >= 1e6:
        return f"{symbol}{val / 1e6:,.2f}M"
    else:
        return f"{symbol}{val:,.2f}"

def render_markdown_report(
    dcf_results: dict,
    buffett_results: dict,
    financials: dict,
    generated_at: datetime = None,
    output_dir: Path = None
) -> Path:
    """
    Generates a professional Markdown investment report.
    """
    if generated_at is None:
        generated_at = datetime.now()
    if output_dir is None:
        output_dir = Path("output")
    else:
        output_dir = Path(output_dir)

    ticker = financials["ticker"]
    is_india = ticker.endswith(".NS") or ticker.endswith(".BO")
    
    current_price = dcf_results["current_price"]
    market_cap = dcf_results["market_cap"]
    intrinsic_val = dcf_results["intrinsic_value_per_share"]
    
    assumptions = dcf_results["assumptions"]
    
    # Header
    md = []
    md.append(f"# Investment Analysis Report: {ticker}")
    md.append(f"**Generated on**: {generated_at.strftime('%B %d, %Y')}")
    md.append(f"**Valuation Engine**: Discounted Cash Flow (DCF)")
    md.append(f"**Investor Lens**: Warren Buffett ({SIDWELL_VERSION})")
    md.append("")
    
    # DCF Coverage Gap Warning block
    if intrinsic_val < 0.30 * current_price or intrinsic_val > 3.00 * current_price:
        md.append("> [!WARNING]")
        md.append("> **DCF COVERAGE GAP WARNING**: The computed DCF intrinsic value deviates significantly from the current market price.")
        md.append("> This indicates a potential DCF coverage gap. A simple 1-stage DCF model with a terminal growth ceiling may severely undervalue premium consumer staples ")
        md.append("> because historical CAGR may capture a depressed window, capacity expansion CapEx is elevated relative to normalized levels, ")
        md.append("> and the terminal growth ceiling is too conservative for high-quality consumer businesses. Treat this intrinsic value as a conservative floor, not a fair value.")
        md.append("")
        
    # Summary Table
    md.append("## Executive Summary")
    md.append("| Metric | Value | Source / Detail |")
    md.append("| :--- | :--- | :--- |")
    md.append(f"| **Current Price** | {format_currency(current_price, is_india)} | Yahoo Finance |")
    md.append(f"| **Intrinsic Value (DCF)** | {format_currency(intrinsic_val, is_india)} | Sidwell DCF Engine |")
    
    if intrinsic_val <= 0:
        mos_display = "DCF produced non-positive intrinsic value — model failed"
    elif intrinsic_val < current_price:
        mos_display = f"Trading at {current_price/intrinsic_val:.1f}x intrinsic value (target ≤ 0.75x)"
    else:
        mos_display = f"{(intrinsic_val - current_price)/intrinsic_val*100:.2f}% margin of safety"
        
    md.append(f"| **Margin of Safety** | {mos_display} | Current Discount to Intrinsic |")
    md.append(f"| **Buffett Score** | **{buffett_results['score']}/8** | Spec criteria checks passed |")
    
    verdict_emoji = "✅" if buffett_results["verdict"] == "BUY" else "⏳" if buffett_results["verdict"] == "WAIT" else "👀" if buffett_results["verdict"] == "WATCH" else "❌"
    md.append(f"| **Final Verdict** | **{buffett_results['verdict']}** {verdict_emoji} | Buffett Lens Rules |")
    md.append("")
    
    # Verdict Detail
    md.append("### Verdict Summary")
    md.append(f"> **{buffett_results['verdict']}** — {buffett_results['reason']}")
    md.append("")
    
    # 1. Company Snapshot
    md.append("## 1. Company Snapshot")
    md.append("Historical financial statements over the last 4 years:")
    md.append("")
    
    # Header row for years
    snapshot_headers = ["Metric"] + [y.split("-")[0] for y in financials["years"]]
    md.append("| " + " | ".join(snapshot_headers) + " |")
    md.append("| " + " | ".join([":---"] * len(snapshot_headers)) + " |")
    
    # Revenue row
    rev_row = ["Revenue"] + [format_currency(r, is_india) for r in financials["revenue"]]
    md.append("| " + " | ".join(rev_row) + " |")
    
    # Gross Margin row
    gm_list = []
    for gp, r in zip(financials["gross_profit"], financials["revenue"]):
        gm_list.append(f"{gp/r*100:.2f}%" if r > 0 else "0.00%")
    gm_row = ["Gross Margin (%)"] + gm_list
    md.append("| " + " | ".join(gm_row) + " |")
    
    # EBIT row
    ebit_row = ["EBIT"] + [format_currency(eb, is_india) for eb in financials["ebit"]]
    md.append("| " + " | ".join(ebit_row) + " |")
    
    # FCF row
    fcf_row = ["Free Cash Flow"] + [format_currency(f, is_india) for f in financials["fcf"]]
    md.append("| " + " | ".join(fcf_row) + " |")
    
    # Total Debt row
    debt_row = ["Total Debt"] + [format_currency(d, is_india) for d in financials["debt"]]
    md.append("| " + " | ".join(debt_row) + " |")
    
    # Stockholders Equity row
    equity_row = ["Stockholders Equity"] + [format_currency(eq, is_india) for eq in financials["total_equity"]]
    md.append("| " + " | ".join(equity_row) + " |")
    md.append("")
    
    # 2. DCF Valuation & WACC Sourcing
    md.append("## 2. DCF Valuation & WACC Sourcing")
    md.append("Every component of the Weighted Average Cost of Capital (WACC) is explicitly sourced and modeled below:")
    md.append("")
    md.append("### WACC Components & Assumptions")
    md.append("| Component | Value | Source / Reference |")
    md.append("| :--- | :--- | :--- |")
    md.append(f"| **Risk-Free Rate ($R_f$)** | {assumptions['risk_free_rate']*100:.2f}% | FRED Series: `{'INDIRLTLT01STM` (India 10Y G-Sec)' if is_india else 'DGS10` (US 10Y Treasury)'} |")
    md.append(f"| **Mature Market ERP** | {assumptions['mature_market_erp']*100:.2f}% | Damodaran NYU Stern (Mature Equity Risk Premium) |")
    md.append(f"| **Country Risk Premium** | {assumptions['country_risk_premium']*100:.2f}% | Damodaran NYU Stern (Country default spread adjusted) |")
    md.append(f"| **Total Equity Risk Premium** | {assumptions['total_erp']*100:.2f}% | Damodaran mature ERP + country premium = {assumptions['total_erp']*100:.2f}% |")
    source_tag = "ticker-mapped" if assumptions.get('industry_source') == 'mapped' else 'default fallback'
    md.append(f"| **Industry Unlevered Beta** | {assumptions['beta_unlevered']:.2f} | Damodaran '{assumptions.get('target_industry', 'Chemical (Specialty)')}' ({source_tag}) |")
    md.append(f"| **Target Levered Beta ($\\beta$)** | {assumptions['beta_levered']:.2f} | Re-levered using actual D/E = {assumptions['beta_levered']:.2f} |")
    md.append(f"| **Cost of Equity ($K_e$)** | {assumptions['cost_of_equity']*100:.2f}% | CAPM: $R_f + \\beta \\times ERP$ = {assumptions['cost_of_equity']*100:.2f}% |")
    md.append(f"| **Cost of Debt ($K_d$)** | {assumptions['cost_of_debt']*100:.2f}% | {assumptions['debt_source']} |")
    md.append(f"| **Effective Tax Rate ($t$)** | {assumptions['tax_rate']*100:.2f}% | 4-year historical average from filings |")
    md.append(f"| **Equity Weight ($W_e$)** | {assumptions['equity_weight']*100:.2f}% | Market Cap / (Market Cap + Total Debt) |")
    md.append(f"| **Debt Weight ($W_d$)** | {assumptions['debt_weight']*100:.2f}% | Total Debt / (Market Cap + Total Debt) |")
    md.append(f"| **Computed WACC** | **{assumptions['wacc']*100:.2f}%** | Weighted cost of capital = **{assumptions['wacc']*100:.2f}%** |")
    md.append("")
    
    md.append("### 5-Year Explicit Forecast Projections")
    md.append("Projections are based on historical averages relative to Revenue. Revenue growth is projected at **{:.2f}%** (historical 4y CAGR capped between 5% and 20%).".format(assumptions["revenue_growth"]*100))
    md.append("")
    
    proj_headers = ["Metric"] + [p["year"] for p in dcf_results["projections"]] + ["Terminal Value"]
    md.append("| " + " | ".join(proj_headers) + " |")
    md.append("| " + " | ".join([":---"] * len(proj_headers)) + " |")
    
    # Revenue row
    rev_p = ["Revenue"] + [format_currency(p["revenue"], is_india) for p in dcf_results["projections"]] + ["-"]
    md.append("| " + " | ".join(rev_p) + " |")
    
    # EBIT row
    ebit_p = ["EBIT"] + [format_currency(p["ebit"], is_india) for p in dcf_results["projections"]] + ["-"]
    md.append("| " + " | ".join(ebit_p) + " |")
    
    # Tax row
    tax_p = ["Taxes"] + [format_currency(p["tax"], is_india) for p in dcf_results["projections"]] + ["-"]
    md.append("| " + " | ".join(tax_p) + " |")
    
    # D&A row
    dep_p = ["D&A"] + [format_currency(p["depreciation"], is_india) for p in dcf_results["projections"]] + ["-"]
    md.append("| " + " | ".join(dep_p) + " |")
    
    # CapEx row
    cap_p = ["CapEx"] + [format_currency(p["capex"], is_india) for p in dcf_results["projections"]] + ["-"]
    md.append("| " + " | ".join(cap_p) + " |")
    
    # NWC change row
    nwc_p = ["NWC Change (CF)"] + [format_currency(p["working_capital_change"], is_india) for p in dcf_results["projections"]] + ["-"]
    md.append("| " + " | ".join(nwc_p) + " |")
    
    # FCF row
    fcf_p = ["Free Cash Flow"] + [format_currency(p["fcf"], is_india) for p in dcf_results["projections"]] + [format_currency(dcf_results["terminal_value"], is_india)]
    md.append("| " + " | ".join(fcf_p) + " |")
    
    # Discount Factor row
    df_p = ["Discount Factor"] + [f"{p['discount_factor']:.4f}" for p in dcf_results["projections"]] + [f"{(1.0 + dcf_results['wacc'])**5:.4f}"]
    md.append("| " + " | ".join(df_p) + " |")
    
    # Present Value row
    pv_p = ["PV of Cash Flow"] + [format_currency(p["pv_fcf"], is_india) for p in dcf_results["projections"]] + [format_currency(dcf_results["pv_terminal_value"], is_india)]
    md.append("| " + " | ".join(pv_p) + " |")
    md.append("")
    
    # Discounting breakdown
    md.append("### Valuation Bridge")
    md.append(f"- **PV of Explicit FCFs**: {format_currency(dcf_results['pv_fcf'], is_india)}")
    md.append(f"- **PV of Terminal Value (g = {assumptions['terminal_growth_rate']*100:.2f}%)**: {format_currency(dcf_results['pv_terminal_value'], is_india)}")
    md.append(f"- **Enterprise Value**: {format_currency(dcf_results['enterprise_value'], is_india)}")
    md.append(f"- **Add: Cash & Equivalents**: {format_currency(assumptions['latest_cash'], is_india)}")
    md.append(f"- **Less: Total Debt**: {format_currency(assumptions['latest_debt'], is_india)}")
    md.append(f"- **Equity Value**: {format_currency(dcf_results['equity_value'], is_india)}")
    md.append(f"- **Shares Outstanding**: {assumptions['shares_outstanding']:,.0f}")
    md.append(f"- **Intrinsic Value per Share**: **{format_currency(intrinsic_val, is_india)}**")
    md.append("")
    
    # 3. Buffett Lens Checks
    md.append("## 3. Buffett Investor Lens")
    md.append("All 8 checks per Warren Buffett's framework (distilled from annual letters):")
    md.append("")
    md.append("| Check | Status | Value | Target Threshold | Description |")
    md.append("| :--- | :---: | :--- | :--- | :--- |")
    
    keys = sorted(buffett_results["checks"].keys())
    for key in keys:
        c = buffett_results["checks"][key]
        status = "✅" if c["passed"] else "❌"
        v = c["value"]
        
        if key == "7_margin_of_safety":
            if intrinsic_val <= 0:
                v_str = "DCF produced non-positive intrinsic value — model failed"
            elif intrinsic_val < current_price:
                v_str = f"Trading at {current_price/intrinsic_val:.1f}x intrinsic value (target ≤ 0.75x)"
            else:
                v_str = f"{(intrinsic_val - current_price)/intrinsic_val*100:.2f}%"
        elif isinstance(v, float):
            v_str = f"{v*100:.2f}%" if "%" in c["threshold_str"] else f"{v:.2f}"
        elif isinstance(v, tuple):
            if len(v) == 2:
                v1, v2 = v
                v1_str = f"{v1*100:.2f}%" if "%" in c["threshold_str"] else f"{v1:.2f}"
                v2_str = f"{v2*100:.2f}%" if "%" in c["threshold_str"] or "growth" in c["metric_name"].lower() else f"{v2:.2f}"
                v_str = f"{v1_str} / {v2_str}"
            else:
                v_str = str(v)
        else:
            v_str = str(v)
            
        md.append(f"| {c['name']} | {status} | {v_str} | {c['threshold_str']} | {c['detail']} |")
        
    md.append("")
    md.append(f"**Total Buffett Score**: **{buffett_results['score']}/8**")
    md.append("")
    
    # 4. Margin of Safety
    md.append("## 4. Margin-of-Safety Check")
    checks = buffett_results["checks"]
    mos = checks["7_margin_of_safety"]["value"]
    mos_passed = checks["7_margin_of_safety"]["passed"]
    
    md.append(f"Current Stock Price: **{format_currency(current_price, is_india)}**")
    md.append(f"DCF Intrinsic Value: **{format_currency(intrinsic_val, is_india)}**")
    md.append(f"Required Margin of Safety: **25.00%** ( Graham & Dodd standard)")
    
    if intrinsic_val <= 0:
        mos_computed_str = "DCF produced non-positive intrinsic value — model failed"
    elif intrinsic_val < current_price:
        mos_computed_str = f"Trading at {current_price/intrinsic_val:.1f}x intrinsic value (target ≤ 0.75x)"
    else:
        mos_computed_str = f"{(intrinsic_val - current_price)/intrinsic_val*100:.2f}% margin of safety"
        
    md.append(f"Computed Margin of Safety: {mos_computed_str}")
    
    if mos_passed:
        md.append("### Status: [PASS] ✅")
        md.append("The current stock price trades at a discount of more than 25% to its intrinsic value, offering an attractive entry point.")
    else:
        md.append("### Status: [FAIL] ❌")
        if intrinsic_val > 0 and current_price > intrinsic_val:
            ratio = current_price / intrinsic_val
            md.append(f"The stock trades above the safety threshold. Trading at {ratio:.1f}x intrinsic value is insufficient for investment under the Buffett framework.")
        else:
            md.append(f"The stock trades above the safety threshold (price > 0.75 × intrinsic value). A discount of {mos*100:.2f}% is insufficient for investment under the Buffett framework.")
    md.append("")
    
    # 5. Verdict
    md.append("## 5. Investment Verdict")
    md.append(f"**RECOMMENDATION: {buffett_results['verdict']}**")
    md.append("")
    md.append(buffett_results["reason"])
    md.append("")
    
    if buffett_results["verdict"] == "WAIT":
        buy_alert_price = intrinsic_val * 0.75
        md.append(f"**Action Item**: Set alert at buy-trigger price: **{format_currency(buy_alert_price, is_india)}** (75% of intrinsic value).")
        
    report_content = "\n".join(md)
    
    # Write to output folder
    os.makedirs(output_dir, exist_ok=True)
    report_filename = output_dir / f"{ticker.split('.')[0].lower()}_report.md"
    try:
        with open(report_filename, "w", encoding="utf-8", newline='') as f:
            f.write(report_content)
        logger.info(f"Report successfully saved to {report_filename}")
    except Exception as e:
        logger.error(f"Failed to write report to file {report_filename}: {e}")
        
    return report_filename
