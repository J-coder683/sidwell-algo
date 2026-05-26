import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("sidwell.reports.render")

SIDWELL_VERSION = "v0.3"

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

def render_markdown_report(
    dcf_results: dict,
    buffett_results: dict,
    financials: dict,
    qualitative_results: dict = None,
    marks_results: dict = None,
    generated_at: datetime = None,
    output_dir: Path = None
) -> Path:
    """
    Generates a professional Markdown investment report with dual-lens output.

    Sections:
      1. Company Snapshot
      2. DCF Valuation & WACC
      3. Buffett Investor Lens (14 checks, 4 Parts)
      3.5 Qualitative Analysis
      3.6 Marks Lens (14 checks, 4 Parts)  [if marks_results provided]
      4. Margin-of-Safety Check
      5. Investment Verdict
      6. Dual-Lens Synthesis              [if marks_results provided]
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

    md = []

    # -------------------------------------------------------------------------
    # Header
    # -------------------------------------------------------------------------
    md.append(f"# Investment Analysis Report: {ticker}")
    md.append(f"**Generated on**: {generated_at.strftime('%B %d, %Y')}")
    md.append(f"**Valuation Engine**: Discounted Cash Flow (DCF)")
    md.append(f"**Investor Lenses**: Warren Buffett + Howard Marks ({SIDWELL_VERSION})")
    md.append("")

    # DCF Coverage Gap Warning
    if intrinsic_val < 0.30 * current_price or intrinsic_val > 3.00 * current_price:
        md.append("> [!WARNING]")
        md.append("> **DCF COVERAGE GAP WARNING**: The computed DCF intrinsic value deviates significantly from the current market price.")
        md.append("> This indicates a potential DCF coverage gap. A simple 1-stage DCF model with a terminal growth ceiling may severely undervalue premium consumer staples ")
        md.append("> because historical CAGR may capture a depressed window, capacity expansion CapEx is elevated relative to normalized levels, ")
        md.append("> and the terminal growth ceiling is too conservative for high-quality consumer businesses. Treat this intrinsic value as a conservative floor, not a fair value.")
        md.append("")

    # -------------------------------------------------------------------------
    # Executive Summary
    # -------------------------------------------------------------------------
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

    # Buffett verdict row
    buffett_emoji = _verdict_emoji(buffett_results["verdict"])
    md.append(f"| **Buffett Score** | **{buffett_results['score']}/14** | Buffett Lens (14 checks) |")
    md.append(f"| **Buffett Verdict** | **{buffett_results['verdict']}** {buffett_emoji} | Buffett Lens Rules |")

    # Marks verdict row (if available)
    if marks_results is not None:
        marks_emoji = _verdict_emoji(marks_results["verdict"])
        md.append(f"| **Marks Score** | **{marks_results['score']}/14** | Marks Lens (14 checks) |")
        md.append(f"| **Marks Verdict** | **{marks_results['verdict']}** {marks_emoji} | Marks Lens Rules |")

    md.append("")

    # Verdict summaries
    md.append("### Verdict Summary")
    md.append(f"> **Buffett**: **{buffett_results['verdict']}** — {buffett_results['reason']}")
    if marks_results is not None:
        md.append(f">")
        md.append(f"> **Marks**: **{marks_results['verdict']}** — {marks_results['reason']}")
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

    equity_row = ["Stockholders Equity"] + [format_currency(eq, is_india) for eq in financials["total_equity"]]
    md.append("| " + " | ".join(equity_row) + " |")
    md.append("")

    # -------------------------------------------------------------------------
    # 2. DCF Valuation & WACC Sourcing
    # -------------------------------------------------------------------------
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

    rev_p = ["Revenue"] + [format_currency(p["revenue"], is_india) for p in dcf_results["projections"]] + ["-"]
    md.append("| " + " | ".join(rev_p) + " |")
    ebit_p = ["EBIT"] + [format_currency(p["ebit"], is_india) for p in dcf_results["projections"]] + ["-"]
    md.append("| " + " | ".join(ebit_p) + " |")
    tax_p = ["Taxes"] + [format_currency(p["tax"], is_india) for p in dcf_results["projections"]] + ["-"]
    md.append("| " + " | ".join(tax_p) + " |")
    dep_p = ["D&A"] + [format_currency(p["depreciation"], is_india) for p in dcf_results["projections"]] + ["-"]
    md.append("| " + " | ".join(dep_p) + " |")
    cap_p = ["CapEx"] + [format_currency(p["capex"], is_india) for p in dcf_results["projections"]] + ["-"]
    md.append("| " + " | ".join(cap_p) + " |")
    nwc_p = ["NWC Change (CF)"] + [format_currency(p["working_capital_change"], is_india) for p in dcf_results["projections"]] + ["-"]
    md.append("| " + " | ".join(nwc_p) + " |")
    fcf_p = ["Free Cash Flow"] + [format_currency(p["fcf"], is_india) for p in dcf_results["projections"]] + [format_currency(dcf_results["terminal_value"], is_india)]
    md.append("| " + " | ".join(fcf_p) + " |")
    df_p = ["Discount Factor"] + [f"{p['discount_factor']:.4f}" for p in dcf_results["projections"]] + [f"{(1.0 + dcf_results['wacc'])**5:.4f}"]
    md.append("| " + " | ".join(df_p) + " |")
    pv_p = ["PV of Cash Flow"] + [format_currency(p["pv_fcf"], is_india) for p in dcf_results["projections"]] + [format_currency(dcf_results["pv_terminal_value"], is_india)]
    md.append("| " + " | ".join(pv_p) + " |")
    md.append("")

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

    # -------------------------------------------------------------------------
    # 3. Buffett Investor Lens (14 checks)
    # -------------------------------------------------------------------------
    md.append("## 3. Buffett Investor Lens")
    md.append(f"All 14 checks per Warren Buffett's framework across 4 Parts (frameworks/buffett.md):")
    md.append("")

    _render_lens_table(md, buffett_results, current_price, intrinsic_val, "Buffett")

    md.append(f"**Total Buffett Score**: **{buffett_results['score']}/14**")
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
    # 3.6 Marks Investor Lens (14 checks)
    # -------------------------------------------------------------------------
    if marks_results is not None:
        md.append("## 3.6 Marks Investor Lens")
        md.append(f"All 14 checks per Howard Marks's risk-first framework across 4 Parts (frameworks/marks.md):")
        md.append("")
        _render_lens_table(md, marks_results, current_price, intrinsic_val, "Marks")
        md.append(f"**Total Marks Score**: **{marks_results['score']}/14**")
        md.append("")

    # -------------------------------------------------------------------------
    # 4. Margin-of-Safety Check
    # -------------------------------------------------------------------------
    md.append("## 4. Margin-of-Safety Check")
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

    # -------------------------------------------------------------------------
    # 6. Dual-Lens Synthesis (if both lenses ran)
    # -------------------------------------------------------------------------
    if marks_results is not None:
        md.append("## 6. Dual-Lens Synthesis")
        md.append("Sidwell preserves both lens verdicts without collapsing them to a single recommendation.")
        md.append("The disagreement between lenses IS the insight. See `frameworks/marks.md` section 'How This Lens Differs from Buffett' for design rationale.")
        md.append("")
        md.append("| | Buffett | Marks |")
        md.append("| :--- | :---: | :---: |")
        md.append(f"| **Score** | {buffett_results['score']}/14 | {marks_results['score']}/14 |")
        md.append(f"| **Verdict** | **{buffett_results['verdict']}** {_verdict_emoji(buffett_results['verdict'])} | **{marks_results['verdict']}** {_verdict_emoji(marks_results['verdict'])} |")
        md.append("")

        # Pattern interpretation
        bv = buffett_results["verdict"]
        mv = marks_results["verdict"]
        if bv == "BUY" and mv == "BUY":
            md.append("**Pattern: Both BUY** — Rare, high-conviction signal. Quality compounder available at deep distress.")
        elif bv in ("BUY", "WAIT", "WATCH") and mv == "SKIP":
            md.append("**Pattern: Buffett favors / Marks SKIP** — Quality business at fair price but no cyclical edge or asymmetric payoff. Suitable for permanent-capital, long-horizon holders.")
        elif bv == "SKIP" and mv in ("BUY", "WAIT", "WATCH"):
            md.append("**Pattern: Marks favors / Buffett SKIP** — Cyclical opportunity at deep discount but business quality fails Buffett's quality bars. Tradeable trough opportunity; not a forever-hold.")
        else:
            md.append(f"**Pattern: Both {bv}/{mv}** — Monitor for change in conditions.")
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
    Renders a lens check table grouped by Part (A/B/C/D).
    Each Part gets its own sub-header before its checks.
    """
    part_labels = {
        "A": "Part A — Business Quality" if lens_name == "Buffett" else "Part A — Margin of Safety & Asymmetric Payoff",
        "B": "Part B — Financial Health" if lens_name == "Buffett" else "Part B — Cycle Position",
        "C": "Part C — Management & Capital Allocation" if lens_name == "Buffett" else "Part C — Risk Architecture",
        "D": "Part D — Margin of Safety & Holdability" if lens_name == "Buffett" else "Part D — Second-Level Thinking & Contrarianism",
    }

    checks = lens_results["checks"]
    keys = sorted(checks.keys())

    current_part = None
    table_open = False

    for key in keys:
        c = checks[key]
        part = c.get("part", "A")

        # Emit part header + table header when part changes
        if part != current_part:
            if table_open:
                md.append("")
                # Show part subtotal
                part_keys = [k for k in keys if checks[k].get("part") == current_part]
                part_pass = sum(1 for k in part_keys if checks[k]["passed"])
                md.append(f"_{part_labels.get(current_part, current_part)}: **{part_pass}/{len(part_keys)} passed**_")
                md.append("")
            current_part = part
            md.append(f"### {part_labels.get(part, part)}")
            md.append("")
            md.append("| Check | Status | Value | Threshold | Detail |")
            md.append("| :--- | :---: | :--- | :--- | :--- |")
            table_open = True

        status = "✅" if c["passed"] else "❌"
        v = c["value"]

        # Format value
        if key == "12_margin_of_safety" and lens_name == "Buffett":
            if intrinsic_val <= 0:
                v_str = "Model failed"
            elif intrinsic_val < current_price:
                v_str = f"Trading at {current_price/intrinsic_val:.1f}x intrinsic"
            else:
                v_str = f"{(intrinsic_val - current_price)/intrinsic_val*100:.2f}%"
        elif key == "1_deep_mos" and lens_name == "Marks":
            if intrinsic_val <= 0:
                v_str = "Model failed"
            elif intrinsic_val < current_price:
                v_str = f"Trading at {current_price/intrinsic_val:.1f}x intrinsic"
            else:
                v_str = f"{v*100:+.2f}%"
        elif isinstance(v, float):
            v_str = f"{v*100:.2f}%" if "%" in c.get("threshold_str", "") else f"{v:.3f}"
        elif isinstance(v, tuple) and len(v) == 2:
            v0, v1 = v
            if isinstance(v0, float) and isinstance(v1, float):
                v_str = f"{v0:.2f} / {v1:.2f}"
            else:
                v_str = f"{v0} / {v1}"
        elif isinstance(v, list):
            v_str = f"[{len(v)} values]"
        elif v is None:
            v_str = "N/A"
        else:
            v_str = str(v)

        # Truncate long detail at 300 chars to keep table readable
        detail_str = str(c.get("detail", ""))[:300]

        md.append(f"| {c['name']} | {status} | {v_str} | {c['threshold_str']} | {detail_str} |")

    # Close last part
    if table_open and current_part:
        md.append("")
        part_keys = [k for k in keys if checks[k].get("part") == current_part]
        part_pass = sum(1 for k in part_keys if checks[k]["passed"])
        md.append(f"_{part_labels.get(current_part, current_part)}: **{part_pass}/{len(part_keys)} passed**_")
        md.append("")
