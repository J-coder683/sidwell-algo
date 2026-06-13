import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("sidwell.reports.render")

SIDWELL_VERSION = "v0.6"

_PART_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}

def _sorted_checks(checks: dict) -> list:
    """
    Sort checks by (Part order A→D, numeric check index 1→14).
    Falls back gracefully if a check is missing a 'part' field
    (treats it as Part Z, sorts last).
    """
    def sort_key(item):
        key, check = item
        part = check.get("part", "Z")
        part_idx = _PART_ORDER.get(part, 99)
        # Extract leading numeric prefix from key (e.g. "12_variant" → 12)
        try:
            num = int(key.split("_")[0])
        except (ValueError, IndexError):
            num = 999
        return (part_idx, num)
    return sorted(checks.items(), key=sort_key)

def format_currency(val: float, is_india: bool) -> str:
    """
    Formats numeric values as currency.
    If is_india is True, formats as INR (e.g., ₹12.35B).
    Otherwise formats as USD.
    """
    symbol = "₹" if is_india else "$"
    if abs(val) >= 1e9:
        return f"{symbol}{val / 1e9:,.2f}B"
    elif abs(val) >= 1e6:
        return f"{symbol}{val / 1e6:,.2f}M"
    else:
        return f"{symbol}{val:,.2f}"

def _verdict_emoji(verdict: str) -> str:
    return "✅" if verdict == "BUY" else "⏳" if verdict == "WAIT" else "👀" if verdict == "WATCH" else "❌"

def _render_dcf_valuation_body(md, dcf_results, financials, assumptions, intrinsic_val, is_india):
    """Renders the full DCF section 2 body (WACC sourcing, projections, terminal
    value, valuation bridge). Only called for non-bank tickers — banks have no
    DCF and get a 'not applicable' note instead (see render_markdown_report)."""
    md.append("Every component of the Weighted Average Cost of Capital (WACC) is explicitly sourced and modeled below:")
    md.append("")
    md.append("### WACC Components & Assumptions")
    md.append("| Component | Value | Source / Reference |")
    md.append("| :--- | :--- | :--- |")
    md.append(f"| **Risk-Free Rate ($R_f$)** | {assumptions['risk_free_rate']*100:.2f}% | FRED Series: `{'INDIRLTLT01STM` (India 10Y G-Sec)' if is_india else 'DGS10` (US 10Y Treasury)'} |")
    md.append(f"| **Mature Market ERP** | {assumptions['mature_market_erp']*100:.2f}% | Damodaran NYU Stern (Mature Equity Risk Premium) |")
    md.append(f"| **Country Risk Premium** | {assumptions['country_risk_premium']*100:.2f}% | Damodaran NYU Stern (Country default spread adjusted) |")
    md.append(f"| **Total Equity Risk Premium** | {assumptions['total_erp']*100:.2f}% | Damodaran mature ERP + country premium = {assumptions['total_erp']*100:.2f}% |")
    source_tag = "from Damodaran sheet" if assumptions.get('industry_source') == 'mapped' else 'hardcoded fallback (Damodaran lookup failed)'
    md.append(f"| **Industry Unlevered Beta** | {assumptions['beta_unlevered']:.2f} | Damodaran '{assumptions.get('target_industry', 'Chemical (Specialty)')}' ({source_tag}) |")
    if financials.get("stock_beta") == 1.0 and financials.get("source", "").lower() == "screener.in":
        beta_str = f"Damodaran industry $\\beta$ for {assumptions.get('target_industry')}; company-specific $\\beta$ unavailable on screener.in"
    else:
        src = financials.get('source', 'stockanalysis.com')
        beta_str = f"Direct $\\beta$ from {src}"
    md.append(f"| **Beta ($\\beta$)** | {assumptions['beta_levered']:.2f} | {beta_str} |")
    md.append(f"| **Cost of Equity ($K_e$)** | {assumptions['cost_of_equity']*100:.2f}% | CAPM: $R_f + \\beta \\times ERP$ = {assumptions['cost_of_equity']*100:.2f}% |")
    md.append(f"| **Cost of Debt ($K_d$)** | {assumptions['cost_of_debt']*100:.2f}% | {assumptions['debt_source']} |")
    md.append(f"| **Effective Tax Rate ($t$)** | {assumptions['tax_rate']*100:.2f}% | 4-year historical average from filings |")
    md.append(f"| **Equity Weight ($W_e$)** | {assumptions['equity_weight']*100:.2f}% | Market Cap / (Market Cap + Total Debt) |")
    md.append(f"| **Debt Weight ($W_d$)** | {assumptions['debt_weight']*100:.2f}% | Total Debt / (Market Cap + Total Debt) |")
    md.append(f"| **Computed WACC** | **{assumptions['wacc']*100:.2f}%** | Weighted cost of capital = **{assumptions['wacc']*100:.2f}%** |")
    md.append("")

    md.append("### 5-Year High-Growth Forecast (Stage 1)")
    md.append("Projections are based on historical averages relative to Revenue. Revenue growth is projected at **{:.2f}%** (historical 4y CAGR capped between 5% and 20%).".format(assumptions["revenue_growth"]*100))
    md.append("")

    stage1_projs = [p for p in dcf_results["projections"] if p.get("stage", "high") == "high"]
    proj_headers = ["Metric"] + [p["year"] for p in stage1_projs]
    md.append("| " + " | ".join(proj_headers) + " |")
    md.append("| " + " | ".join([":---"] * len(proj_headers)) + " |")

    rev_p = ["Revenue"] + [format_currency(p["revenue"], is_india) for p in stage1_projs]
    md.append("| " + " | ".join(rev_p) + " |")
    ebit_p = ["EBIT"] + [format_currency(p["ebit"], is_india) for p in stage1_projs]
    md.append("| " + " | ".join(ebit_p) + " |")
    tax_p = ["Taxes"] + [format_currency(p["tax"], is_india) for p in stage1_projs]
    md.append("| " + " | ".join(tax_p) + " |")
    dep_p = ["D&A"] + [format_currency(p["depreciation"], is_india) for p in stage1_projs]
    md.append("| " + " | ".join(dep_p) + " |")
    cap_p = ["CapEx"] + [format_currency(p["capex"], is_india) for p in stage1_projs]
    md.append("| " + " | ".join(cap_p) + " |")
    nwc_p = ["NWC Change (CF)"] + [format_currency(p["working_capital_change"], is_india) for p in stage1_projs]
    md.append("| " + " | ".join(nwc_p) + " |")
    fcf_p = ["Free Cash Flow"] + [format_currency(p["fcf"], is_india) for p in stage1_projs]
    md.append("| " + " | ".join(fcf_p) + " |")
    df_p = ["Discount Factor"] + [f"{p['discount_factor']:.4f}" for p in stage1_projs]
    md.append("| " + " | ".join(df_p) + " |")
    pv_p = ["PV of Cash Flow"] + [format_currency(p["pv_fcf"], is_india) for p in stage1_projs]
    md.append("| " + " | ".join(pv_p) + " |")
    md.append("")

    stage2_projs = [p for p in dcf_results["projections"] if p.get("stage") == "fade"]
    if stage2_projs:
        md.append(f"### 5-Year Fade Forecast (Stage 2) — growth fading from {assumptions['stage_1_growth']*100:.2f}% to {assumptions['terminal_growth_rate']*100:.2f}%")
        md.append("")

        proj_headers2 = ["Metric"] + [p["year"] for p in stage2_projs]
        md.append("| " + " | ".join(proj_headers2) + " |")
        md.append("| " + " | ".join([":---"] * len(proj_headers2)) + " |")

        rev_p2 = ["Revenue"] + [format_currency(p["revenue"], is_india) for p in stage2_projs]
        md.append("| " + " | ".join(rev_p2) + " |")
        ebit_p2 = ["EBIT"] + [format_currency(p["ebit"], is_india) for p in stage2_projs]
        md.append("| " + " | ".join(ebit_p2) + " |")
        tax_p2 = ["Taxes"] + [format_currency(p["tax"], is_india) for p in stage2_projs]
        md.append("| " + " | ".join(tax_p2) + " |")
        dep_p2 = ["D&A"] + [format_currency(p["depreciation"], is_india) for p in stage2_projs]
        md.append("| " + " | ".join(dep_p2) + " |")
        cap_p2 = ["CapEx"] + [format_currency(p["capex"], is_india) for p in stage2_projs]
        md.append("| " + " | ".join(cap_p2) + " |")
        nwc_p2 = ["NWC Change (CF)"] + [format_currency(p["working_capital_change"], is_india) for p in stage2_projs]
        md.append("| " + " | ".join(nwc_p2) + " |")
        fcf_p2 = ["Free Cash Flow"] + [format_currency(p["fcf"], is_india) for p in stage2_projs]
        md.append("| " + " | ".join(fcf_p2) + " |")
        df_p2 = ["Discount Factor"] + [f"{p['discount_factor']:.4f}" for p in stage2_projs]
        md.append("| " + " | ".join(df_p2) + " |")
        pv_p2 = ["PV of Cash Flow"] + [format_currency(p["pv_fcf"], is_india) for p in stage2_projs]
        md.append("| " + " | ".join(pv_p2) + " |")
        md.append("")

    md.append("### Terminal Value")
    last_year_num = len(dcf_results["projections"])
    fcf_final = dcf_results["projections"][-1]["fcf"] if dcf_results["projections"] else 0.0
    g_term = assumptions.get('terminal_growth_rate', 0.0)
    md.append(f"- Final fade year (Year {last_year_num}) FCF: {format_currency(fcf_final, is_india)}")
    md.append(f"- Terminal growth (Gordon): {g_term*100:.2f}%")
    md.append(f"- Sector mapping: {assumptions.get('sector_terminal_source', 'Unknown')}")
    md.append(f"- Terminal Value: {format_currency(dcf_results['terminal_value'], is_india)}")
    md.append(f"- PV of Terminal Value (discounted from Year {last_year_num}): {format_currency(dcf_results['pv_terminal_value'], is_india)}")
    md.append("")

    md.append("### Valuation Bridge")
    md.append(f"- **PV of Explicit FCFs**: {format_currency(dcf_results['pv_fcf'], is_india)}")
    md.append(f"- **PV of Terminal Value (g = {g_term*100:.2f}%)**: {format_currency(dcf_results['pv_terminal_value'], is_india)}")
    md.append(f"- **Enterprise Value**: {format_currency(dcf_results['enterprise_value'], is_india)}")
    md.append(f"- **Add: Cash & Equivalents**: {format_currency(assumptions['latest_cash'], is_india)}")
    md.append(f"- **Less: Total Debt**: {format_currency(assumptions['latest_debt'], is_india)}")
    md.append(f"- **Equity Value**: {format_currency(dcf_results['equity_value'], is_india)}")
    md.append(f"- **Shares Outstanding**: {assumptions['shares_outstanding']:,.0f}")
    md.append(f"- **Intrinsic Value per Share**: **{format_currency(intrinsic_val, is_india)}**")
    md.append("")

def render_markdown_report(
    dcf_results: dict,
    buffett_results: dict,
    financials: dict,
    qualitative_results: dict = None,
    marks_results: dict = None,
    kkr_results: dict = None,
    blackstone_results: dict = None,
    apollo_results: dict = None,
    generated_at: datetime = None,
    output_dir: Path = None
) -> Path:
    """
    Generates a professional Markdown investment report with quintuple-lens output.

    Sections:
      1. Company Snapshot
      2. DCF Valuation & WACC
      3. Buffett Investor Lens
      3.1 Marks Lens
      3.2 KKR Lens
      3.3 Blackstone Lens
      3.4 Apollo Lens
      3.5 Qualitative Analysis
      4. Margin-of-Safety Check
      5. Investment Verdict
      6. Quintuple-Lens Synthesis
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
    intrinsic_val = dcf_results["intrinsic_value_per_share"]
    assumptions = dcf_results["assumptions"]
    # Banks: DCF is not applicable. intrinsic_val / wacc / enterprise_value are
    # None, so the valuation displays are replaced with a "coming soon" message.
    dcf_na = bool(dcf_results.get("not_applicable"))
    dcf_na_reason = dcf_results.get("not_applicable_reason", "DCF not applicable.")

    md = []

    # -------------------------------------------------------------------------
    # Header
    # -------------------------------------------------------------------------
    md.append(f"# Investment Analysis Report: {ticker}")
    md.append(f"**Generated on**: {generated_at.strftime('%B %d, %Y')}")
    md.append(f"**Valuation Engine**: Discounted Cash Flow (DCF)")
    md.append(f"**Investor Lenses**: Warren Buffett + Howard Marks + KKR + Blackstone + Apollo ({SIDWELL_VERSION})")
    md.append("")

    # DCF Coverage Gap Warning (skipped for banks — no DCF intrinsic value)
    intrinsic_to_price_pct = (intrinsic_val / current_price) * 100 if (not dcf_na and current_price > 0) else 0
    if not dcf_na and (intrinsic_to_price_pct < 30.0 or intrinsic_to_price_pct > 300.0):
        md.append("> [!WARNING]")
        md.append("> **DCF COVERAGE GAP WARNING**: The computed DCF intrinsic value")
        md.append("> deviates significantly from the current market price (intrinsic")
        md.append(f"> at {intrinsic_to_price_pct:.0f}% of price).")
        md.append(">")
        md.append("> Even this v0.4 2-stage DCF (Stage 1 high-growth + Stage 2 fade +")
        md.append("> sector-aware terminal) may understate premium businesses because:")
        md.append("> - Historical CapEx ratios may include expansionary capex that won't")
        md.append(">   recur indefinitely (a future v0.5+ refinement could fade capex")
        md.append(">   toward maintenance level in Stage 2)")
        md.append("> - DCF cannot capture brand premium, distribution moat, optionality")
        md.append(">   on adjacent categories, or India consumption-story re-rating")
        md.append("> - Market is willing to pay for sustained 15-20% earnings growth that")
        md.append(">   exceeds Damodaran's published sector terminal rates")
        md.append(">")
        md.append("> Treat this intrinsic value as a conservative floor anchor, not a")
        md.append("> fair-value estimate.")
        md.append("")

    # -------------------------------------------------------------------------
    # Executive Summary
    # -------------------------------------------------------------------------
    md.append("## Executive Summary")
    md.append("| Metric | Value | Source / Detail |")
    md.append("| :--- | :--- | :--- |")
    md.append(f"| **Current Price** | {format_currency(current_price, is_india)} | Yahoo Finance |")

    if dcf_na:
        md.append("| **Intrinsic Value** | N/A — DCF not applicable to banks | Bank valuation (DDM) coming soon |")
        md.append("| **Margin of Safety** | N/A — awaiting bank valuation model | Pending DDM/excess-returns |")
    else:
        md.append(f"| **Intrinsic Value (DCF)** | {format_currency(intrinsic_val, is_india)} | Sidwell DCF Engine |")
        if intrinsic_val <= 0:
            mos_display = "DCF produced non-positive intrinsic value — model failed"
        elif intrinsic_val < current_price:
            mos_display = f"Trading at {current_price/intrinsic_val:.1f}x intrinsic value (target ≤ 0.75x)"
        else:
            mos_display = f"{(intrinsic_val - current_price)/intrinsic_val*100:.2f}% margin of safety"
        md.append(f"| **Margin of Safety** | {mos_display} | Current Discount to Intrinsic |")

    # Buffett verdict row
    buffett_emoji = _verdict_emoji(buffett_results["verdict"])
    buffett_max = buffett_results.get("max_score", 14)
    md.append(f"| **Buffett Score** | **{buffett_results['score']}/{buffett_max}** | Buffett Lens ({buffett_max} checks) |")
    md.append(f"| **Buffett Verdict** | **{buffett_results['verdict']}** {buffett_emoji} | Buffett Lens Rules |")

    # Marks verdict row (if available)
    if marks_results is not None:
        marks_max = marks_results.get("max_score", 14)
        marks_emoji = _verdict_emoji(marks_results["verdict"])
        md.append(f"| **Marks Score** | **{marks_results['score']}/{marks_max}** | Marks Lens ({marks_max} checks) |")
        md.append(f"| **Marks Verdict** | **{marks_results['verdict']}** {marks_emoji} | Marks Lens Rules |")

    # KKR verdict row
    if kkr_results is not None:
        kkr_max = kkr_results.get("max_score", 18)
        kkr_emoji = _verdict_emoji(kkr_results["verdict"])
        md.append(f"| **KKR Score** | **{kkr_results['score']}/{kkr_max}** | KKR Lens ({kkr_max} checks) |")
        md.append(f"| **KKR Verdict** | **{kkr_results['verdict']}** {kkr_emoji} | KKR Lens Rules |")

    # Blackstone verdict row
    if blackstone_results is not None:
        bx_max = blackstone_results.get("max_score", 14)
        bx_emoji = _verdict_emoji(blackstone_results["verdict"])
        md.append(f"| **Blackstone Score** | **{blackstone_results['score']}/{bx_max}** | Blackstone Lens ({bx_max} checks) |")
        md.append(f"| **Blackstone Verdict** | **{blackstone_results['verdict']}** {bx_emoji} | Blackstone Lens Rules |")

    # Apollo verdict row
    if apollo_results is not None:
        ap_max = apollo_results.get("max_score", 16)
        ap_emoji = _verdict_emoji(apollo_results["verdict"])
        md.append(f"| **Apollo Score** | **{apollo_results['score']}/{ap_max}** | Apollo Lens ({ap_max} checks) |")
        md.append(f"| **Apollo Verdict** | **{apollo_results['verdict']}** {ap_emoji} | Apollo Lens Rules |")

    md.append("")

    # Verdict summaries
    md.append("### Verdict Summary")
    md.append(f"> **Buffett**: **{buffett_results['verdict']}** — {buffett_results['reason']}")
    if marks_results is not None:
        md.append(f"> **Marks**: **{marks_results['verdict']}** — {marks_results['reason']}")
    if kkr_results is not None:
        md.append(f"> **KKR**: **{kkr_results['verdict']}** — {kkr_results['reason']}")
    if blackstone_results is not None:
        md.append(f"> **Blackstone**: **{blackstone_results['verdict']}** — {blackstone_results['reason']}")
    if apollo_results is not None:
        md.append(f"> **Apollo**: **{apollo_results['verdict']}** — {apollo_results['reason']}")
    md.append("")

    # -------------------------------------------------------------------------
    # 1. Company Snapshot
    # -------------------------------------------------------------------------
    md.append("## 1. Company Snapshot")
    md.append("Historical financial statements over the last 4 years:")
    md.append("")

    snapshot_headers = ["Metric"] + [y.split("-")[0] for y in financials["years"]]
    md.append("| " + " | ".join(snapshot_headers) + " |")
    md.append("| " + " | ".join([":---"] * len(snapshot_headers)) + " |")

    rev_row = ["Revenue"] + [format_currency(r, is_india) for r in financials["revenue"]]
    md.append("| " + " | ".join(rev_row) + " |")

    gm_list = []
    for gp, r in zip(financials["gross_profit"], financials["revenue"]):
        gm_list.append(f"{gp/r*100:.2f}%" if r > 0 else "0.00%")
    gm_row = ["Gross Margin (%)"] + gm_list
    md.append("| " + " | ".join(gm_row) + " |")

    ebit_row = ["EBIT"] + [format_currency(eb, is_india) for eb in financials["ebit"]]
    md.append("| " + " | ".join(ebit_row) + " |")

    fcf_row = ["Free Cash Flow"] + [format_currency(f, is_india) for f in financials["fcf"]]
    md.append("| " + " | ".join(fcf_row) + " |")

    debt_row = ["Total Debt"] + [format_currency(d, is_india) for d in financials["debt"]]
    md.append("| " + " | ".join(debt_row) + " |")

    ie_row = ["Interest Expense"] + [format_currency(ie, is_india) for ie in financials["interest_expense"]]
    md.append("| " + " | ".join(ie_row) + " |")

    equity_row = ["Stockholders Equity"] + [format_currency(eq, is_india) for eq in financials["total_equity"]]
    md.append("| " + " | ".join(equity_row) + " |")
    md.append("")
    
    if financials.get("interest_source") == "proxy":
        note = f"**Data Note:** Interest Expense values shown (all 4 years) are estimated via debt \u00d7 0.05 proxy \u2014 stockanalysis.com does not expose this field for {ticker}. v0.7+ may add SEC EDGAR for direct 10-K extraction."
        if ticker == "AAPL":
            note += " Real Apple interest expense per 10-K is approximately $3.5B/year."
        md.append(note)
        md.append("")

    # -------------------------------------------------------------------------
    # 2. DCF Valuation & WACC Sourcing
    # -------------------------------------------------------------------------
    md.append("## 2. DCF Valuation & WACC Sourcing")
    if dcf_na:
        md.append("")
        md.append("> [!NOTE]")
        md.append(f"> **{dcf_na_reason}**")
        md.append(">")
        md.append("> Banks are analysed through all five investor lenses on real financials;")
        md.append("> only the FCF-based DCF valuation is skipped here. A dividend-discount /")
        md.append("> excess-returns model for banks is planned.")
        md.append("")
    else:
        _render_dcf_valuation_body(md, dcf_results, financials, assumptions, intrinsic_val, is_india)

    # -------------------------------------------------------------------------
    # 3. Buffett Investor Lens (14 checks)
    # -------------------------------------------------------------------------
    md.append("## 3. Buffett Investor Lens")
    buffett_max = buffett_results.get("max_score", 14)
    md.append(f"All {buffett_max} checks per Warren Buffett's framework across 4 Parts (frameworks/buffett.md):")
    md.append("")

    from reports.explain import build_lens_narrative
    md.append("> **Summary:** " + build_lens_narrative("Warren Buffett", buffett_results, ticker))
    md.append("")

    _render_lens_table(md, buffett_results, current_price, intrinsic_val, "Buffett")

    md.append(f"**Total Buffett Score**: **{buffett_results['score']}/{buffett_max}**")
    md.append("")

    # -------------------------------------------------------------------------
    # 3.1 Marks Investor Lens
    # -------------------------------------------------------------------------
    if marks_results is not None:
        md.append("## 3.1 Marks Investor Lens")
        marks_max = marks_results.get("max_score", 14)
        md.append(f"All {marks_max} checks per Howard Marks's risk-first framework (frameworks/marks.md):")
        md.append("")
        md.append("> **Summary:** " + build_lens_narrative("Howard Marks", marks_results, ticker))
        md.append("")
        _render_lens_table(md, marks_results, current_price, intrinsic_val, "Marks")
        md.append(f"**Total Marks Score**: **{marks_results['score']}/{marks_max}**")
        md.append("")
        
    # -------------------------------------------------------------------------
    # 3.2 KKR Investor Lens
    # -------------------------------------------------------------------------
    if kkr_results is not None:
        md.append("## 3.2 KKR Investor Lens")
        kkr_max = kkr_results.get("max_score", 18)
        md.append(f"All {kkr_max} checks per KKR's operating playbook framework (frameworks/kkr.md):")
        md.append("")
        md.append("> **Summary:** " + build_lens_narrative("KKR", kkr_results, ticker))
        md.append("")
        _render_lens_table(md, kkr_results, current_price, intrinsic_val, "KKR")
        md.append(f"**Total KKR Score**: **{kkr_results['score']}/{kkr_max}**")
        md.append("")

    # -------------------------------------------------------------------------
    # 3.3 Blackstone Investor Lens
    # -------------------------------------------------------------------------
    if blackstone_results is not None:
        md.append("## 3.3 Blackstone Investor Lens")
        bx_max = blackstone_results.get("max_score", 14)
        md.append(f"All {bx_max} checks per Blackstone's thematic framework (frameworks/blackstone.md):")
        md.append("")
        md.append("> **Summary:** " + build_lens_narrative("Blackstone", blackstone_results, ticker))
        md.append("")
        _render_lens_table(md, blackstone_results, current_price, intrinsic_val, "Blackstone")
        md.append(f"**Total Blackstone Score**: **{blackstone_results['score']}/{bx_max}**")
        md.append("")

    # -------------------------------------------------------------------------
    # 3.4 Apollo Investor Lens
    # -------------------------------------------------------------------------
    if apollo_results is not None:
        md.append("## 3.4 Apollo Investor Lens")
        ap_max = apollo_results.get("max_score", 16)
        md.append(f"All {ap_max} checks per Apollo's credit & complexity framework (frameworks/apollo.md):")
        md.append("")
        md.append("> **Summary:** " + build_lens_narrative("Apollo", apollo_results, ticker))
        md.append("")
        _render_lens_table(md, apollo_results, current_price, intrinsic_val, "Apollo")
        md.append(f"**Total Apollo Score**: **{apollo_results['score']}/{ap_max}**")
        md.append("")

    # -------------------------------------------------------------------------
    # 3.5 Qualitative Analysis
    # -------------------------------------------------------------------------
    md.append("## 3.5 Qualitative Analysis")
    if qualitative_results is None or qualitative_results.get("status") != "available":
        reason = (qualitative_results or {}).get("reason", "Not run")
        md.append(f"_Qualitative analysis unavailable: {reason}_")
        md.append("")
    else:
        docs = qualitative_results.get("documents_used", [])
        md.append(
            f"Based on {len(docs)} document(s): "
            f"{', '.join(docs)}. Model: `{qualitative_results.get('model')}`."
        )
        md.append("")

        # Forward guidance
        md.append("### Forward Guidance")
        guidance = qualitative_results.get("forward_guidance", [])
        if guidance:
            for g in guidance:
                md.append(
                    f"- **{g.get('period', '?')}** ({g.get('metric', '?')}): "
                    f"{g.get('statement', '')} _[{g.get('source_doc', '?')}]_"
                )
        else:
            md.append("_No forward guidance extracted._")
        md.append("")

        # Risk callouts
        md.append("### Risk Callouts")
        risks = qualitative_results.get("risk_callouts", [])
        if risks:
            for r in risks:
                md.append(
                    f"- **{r.get('risk', '?')}**: {r.get('context', '')} "
                    f"_[{r.get('source_doc', '?')}]_"
                )
        else:
            md.append("_No risks extracted._")
        md.append("")

        # Strategic themes
        md.append("### Strategic Themes")
        themes = qualitative_results.get("strategic_themes", [])
        if themes:
            for t in themes:
                md.append(
                    f"- **{t.get('theme', '?')}**: {t.get('evidence', '')} "
                    f"_[{t.get('source_doc', '?')}]_"
                )
        else:
            md.append("_No strategic themes extracted._")
        md.append("")

        # Tone & coherence
        tone = qualitative_results.get("tone_assessment", {}) or {}
        coh = qualitative_results.get("coherence_assessment", {}) or {}
        md.append("### Tone & Coherence")
        md.append(f"- **Tone (current)**: {tone.get('current', '?')}")
        md.append(f"- **Tone (trajectory)**: {tone.get('trajectory', '?')}")
        md.append(f"- **Coherence verdict**: {coh.get('verdict', '?')}")
        md.append("")
        if tone.get("notes"):
            md.append(f"_{tone['notes']}_")
            md.append("")
        if coh.get("reasoning"):
            md.append(f"_{coh['reasoning']}_")
            md.append("")

        # New v0.3 sections
        oo = qualitative_results.get("owner_orientation_signal", {}) or {}
        ha = qualitative_results.get("holdability_assessment", {}) or {}
        cp = qualitative_results.get("cycle_position", {}) or {}
        vp = qualitative_results.get("variant_perception", {}) or {}
        mh = qualitative_results.get("management_humility", {}) or {}
        wn = qualitative_results.get("why_now_signal", {}) or {}

        if any([oo.get("verdict"), ha.get("verdict"), cp.get("sector_cycle"),
                vp.get("variant_present") is not None, mh.get("verdict"), wn.get("verdict")]):
            md.append("### Marks-Relevant Signals")
            if oo.get("verdict"):
                md.append(f"- **Owner orientation**: {oo.get('verdict')} — {(oo.get('evidence') or '')[:300]}")
            if ha.get("verdict"):
                md.append(f"- **Holdability (20y)**: {ha.get('verdict')} — {(ha.get('reasoning') or '')[:300]}")
            if cp.get("sector_cycle"):
                md.append(f"- **Sector cycle**: {cp.get('sector_cycle')} / Company cycle: {cp.get('company_cycle')} — {(cp.get('reasoning') or '')[:300]}")
            if vp.get("variant_present") is not None:
                md.append(
                    f"- **Variant perception**: present={vp.get('variant_present')}, "
                    f"specificity={vp.get('specificity')}. "
                    f"Consensus: '{(vp.get('consensus_view') or '')[:150]}'"
                )
            if mh.get("verdict"):
                md.append(f"- **Management humility**: {mh.get('verdict')} — {(mh.get('evidence') or '')[:300]}")
            if wn.get("verdict"):
                md.append(f"- **Why now**: {wn.get('verdict')} — {(wn.get('specific_event') or '')[:200]}")
            md.append("")



    # -------------------------------------------------------------------------
    # 4. Margin-of-Safety Check
    # -------------------------------------------------------------------------
    md.append("## 4. Margin-of-Safety Check")
    if dcf_na:
        md.append(f"Current Stock Price: **{format_currency(current_price, is_india)}**")
        md.append("Intrinsic Value: **N/A — DCF not applicable to banks**")
        md.append("")
        md.append("### Status: [N/A] ⏸️")
        md.append(
            "Margin of safety cannot be computed without a valuation. A bank "
            "valuation model (DDM / excess-returns) is coming soon; until then "
            "this check is excluded from the Buffett and Marks scores."
        )
        md.append("")
    else:
        buffett_checks = buffett_results["checks"]
        mos_check = buffett_checks.get("12_margin_of_safety", {})
        mos = mos_check.get("value", -1.0)
        mos_passed = mos_check.get("passed", False)

        md.append(f"Current Stock Price: **{format_currency(current_price, is_india)}**")
        md.append(f"DCF Intrinsic Value: **{format_currency(intrinsic_val, is_india)}**")
        md.append(f"Required Margin of Safety: **25.00%** (Graham & Dodd standard — Buffett lens)")

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
                md.append(f"The stock trades above the safety threshold. A discount of {mos*100:.2f}% is insufficient for investment under the Buffett framework.")
        md.append("")

    # -------------------------------------------------------------------------
    # 5. Investment Verdict
    # -------------------------------------------------------------------------
    md.append("## 5. Investment Verdict")
    md.append(f"**BUFFETT RECOMMENDATION: {buffett_results['verdict']}**")
    md.append("")
    md.append(buffett_results["reason"])
    md.append("")
    if buffett_results["verdict"] == "WAIT":
        buy_alert_price = intrinsic_val * 0.75
        md.append(f"**Action Item**: Set alert at buy-trigger price: **{format_currency(buy_alert_price, is_india)}** (75% of intrinsic value).")
        md.append("")

    if marks_results is not None:
        md.append(f"**MARKS RECOMMENDATION: {marks_results['verdict']}**")
        md.append("")
        md.append(marks_results["reason"])
        md.append("")
        if marks_results["verdict"] == "WAIT" and intrinsic_val > 0:
            marks_alert_price = intrinsic_val * 0.60
            md.append(f"**Marks Action Item**: Set re-rating alert at **{format_currency(marks_alert_price, is_india)}** (60% of intrinsic = 40% MoS).")
            md.append("")

    if kkr_results is not None:
        md.append(f"**KKR RECOMMENDATION: {kkr_results['verdict']}**")
        md.append("")
        md.append(kkr_results["reason"])
        md.append("")
        
    if blackstone_results is not None:
        md.append(f"**BLACKSTONE RECOMMENDATION: {blackstone_results['verdict']}**")
        md.append("")
        md.append(blackstone_results["reason"])
        md.append("")
        
    if apollo_results is not None:
        md.append(f"**APOLLO RECOMMENDATION: {apollo_results['verdict']}**")
        md.append("")
        md.append(apollo_results["reason"])
        md.append("")

    # -------------------------------------------------------------------------
    # 6. Dual-Lens Synthesis (if both lenses ran)
    # -------------------------------------------------------------------------
    if marks_results is not None:
        md.append("## 6. Quintuple-Lens Synthesis")
        md.append("Sidwell preserves all lens verdicts without collapsing them to a single recommendation.")
        md.append("The disagreement between lenses IS the insight.")
        md.append("")
        
        headers = ["Score", "Verdict"]
        
        md.append("| Lens | Score | Verdict |")
        md.append("| :--- | :---: | :---: |")
        buffett_max = buffett_results.get("max_score", 14)
        md.append(f"| **Buffett** | {buffett_results['score']}/{buffett_max} | **{buffett_results['verdict']}** {_verdict_emoji(buffett_results['verdict'])} |")
        
        marks_max = marks_results.get("max_score", 14)
        md.append(f"| **Marks** | {marks_results['score']}/{marks_max} | **{marks_results['verdict']}** {_verdict_emoji(marks_results['verdict'])} |")
        
        if kkr_results:
            kkr_max = kkr_results.get("max_score", 18)
            md.append(f"| **KKR** | {kkr_results['score']}/{kkr_max} | **{kkr_results['verdict']}** {_verdict_emoji(kkr_results['verdict'])} |")
        
        if blackstone_results:
            bx_max = blackstone_results.get("max_score", 14)
            md.append(f"| **Blackstone** | {blackstone_results['score']}/{bx_max} | **{blackstone_results['verdict']}** {_verdict_emoji(blackstone_results['verdict'])} |")
            
        if apollo_results:
            ap_max = apollo_results.get("max_score", 16)
            md.append(f"| **Apollo** | {apollo_results['score']}/{ap_max} | **{apollo_results['verdict']}** {_verdict_emoji(apollo_results['verdict'])} |")
            
        md.append("")

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


def _render_lens_table(md: list, lens_results: dict, current_price: float, intrinsic_val: float, lens_name: str):
    """
    Renders a lens check list grouped by Part (A/B/C/D), using the 3-part explanation format.
    Each Part gets its own sub-header before its checks.
    """
    from reports.explain import build_check_explanation
    
    part_labels = {}
    if lens_name == "Buffett":
        part_labels = {
            "A": "Part A \u2014 Business Quality",
            "B": "Part B \u2014 Financial Health",
            "C": "Part C \u2014 Management & Capital Allocation",
            "D": "Part D \u2014 Margin of Safety & Holdability",
        }
    elif lens_name == "Marks":
        part_labels = {
            "A": "Part A \u2014 Margin of Safety & Asymmetric Payoff",
            "B": "Part B \u2014 Cycle Position",
            "C": "Part C \u2014 Risk Architecture",
            "D": "Part D \u2014 Second-Level Thinking & Contrarianism",
        }
    elif lens_name == "KKR":
        part_labels = {
            "A": "Part A \u2014 LBO Viability",
            "B": "Part B \u2014 Operational Upside",
            "C": "Part C \u2014 Strategic Fit",
            "D": "Part D \u2014 Cycle Timing & Returns",
            "E": "Part E \u2014 Defensibility vs Phalippou Bar",
        }
    elif lens_name == "Blackstone":
        part_labels = {
            "A": "Part A \u2014 Good Business Filter",
            "B": "Part B \u2014 Good Neighborhood (Thematic)",
            "C": "Part C \u2014 Downside Protection",
            "D": "Part D \u2014 Scale Fit & Hold Economics",
            "E": "Part E \u2014 Defensibility vs Phalippou Bar",
        }
    elif lens_name == "Apollo":
        part_labels = {
            "A": "Part A \u2014 Purchase Price & Capital Structure Entry",
            "B": "Part B \u2014 Chaos, Complexity, Credit Edge",
            "C": "Part C \u2014 Athene Permanent Capital Fit",
            "D": "Part D \u2014 Credit Downside Quality",
            "E": "Part E \u2014 Defensibility vs Phalippou Bar",
        }

    checks = lens_results["checks"]
    sorted_items = _sorted_checks(checks)

    current_part = None
    table_open = False

    for key, c in sorted_items:
        part = c.get("part", "A")

        # Emit part header when part changes
        if part != current_part:
            if table_open:
                md.append("")
                # Show part subtotal
                part_items = [item for item in sorted_items if item[1].get("part") == current_part]
                part_pass = sum(1 for k, chk in part_items if chk.get("passed", False))
                part_total = sum(1 for k, chk in part_items if chk.get("applicable", True))
                md.append(f"_{part_labels.get(current_part, current_part)}: **{part_pass}/{part_total} passed**_")
                md.append("")
            current_part = part
            md.append(f"### {part_labels.get(part, part)}")
            md.append("")
            table_open = True

        expl = build_check_explanation(key, c)
        
        icon = "⏸️" if expl["status"] == "na" else ("✅" if expl["status"] == "pass" else "❌")
        
        proximity = c.get("proximity")
        badge = ""
        if proximity is not None:
            if proximity >= 0.10:
                label = "Strong Pass" if proximity >= 0.25 else "Pass"
            elif proximity >= 0:
                label = "Narrow Pass"
            elif proximity >= -0.10:
                label = "Narrow Miss"
            else:
                label = "Clear Miss"
            prox_str = ("+∞" if proximity == float("inf")
                        else "-∞" if proximity == float("-inf")
                        else f"{proximity:+.2f}")
            badge = f" `[{label}: {prox_str}]`"
        
        md.append(f"#### {icon} {expl['title']}{badge}")
        if expl['what_why']:
            md.append(f"- **What this measures**: {expl['what_why']}")
        if expl['finding']:
            md.append(f"- **This company**: {expl['finding']}")
        md.append(f"- **Verdict**: {expl['judgment']}")
        md.append("")

    # Close last part
    if table_open and current_part:
        md.append("")
        part_items = [item for item in sorted_items if item[1].get("part") == current_part]
        part_pass = sum(1 for k, chk in part_items if chk.get("applicable", True) and chk.get("passed", False))
        part_total = sum(1 for k, chk in part_items if chk.get("applicable", True))
        md.append(f"_{part_labels.get(current_part, current_part)}: **{part_pass}/{part_total} passed**_")
        md.append("")

