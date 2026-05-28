"""
exports/pdf.py
--------------
Per-lens PDF export for Sidwell v0.6.

Public API
----------
export_lens_pdf(
    lens_results: dict,
    financials: dict,
    dcf_results: dict,
    lens_name: str,
) -> bytes

The returned bytes can be passed directly to Streamlit's st.download_button.
Requires: weasyprint>=62.0, libpango, libcairo (listed in packages.txt).
"""

import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("sidwell.exports.pdf")

# ---- weasyprint import with graceful failure message ----
try:
    import weasyprint
    _WEASYPRINT_AVAILABLE = True
except Exception as e:
    _WEASYPRINT_AVAILABLE = False
    _WEASYPRINT_ERROR = str(e)

_CSS_PATH = Path(__file__).parent / "pdf_style.css"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LENS_DISPLAY_NAMES = {
    "buffett": "Warren Buffett — Quality & Intrinsic Value",
    "marks": "Howard Marks — Risk-First Framework",
    "kkr": "KKR — Operator-Buyer Framework",
    "blackstone": "Blackstone — Thematic Value Creation",
    "apollo": "Apollo — Credit & Complexity Arbitrage",
}

_PART_DISPLAY_NAMES = {
    "A": "Part A",
    "B": "Part B",
    "C": "Part C",
    "D": "Part D",
    "E": "Part E",
}

# KKR Part display names for richer context
_KKR_PART_NAMES = {
    "A": "Part A — LBO Viability",
    "B": "Part B — Operational Upside",
    "C": "Part C — Workforce & Playbook Fit",
    "D": "Part D — Cycle & Seller Dynamics",
    "E": "Part E — Alpha Thesis (Phalippou Check)",
}

_BUFFETT_PART_NAMES = {
    "A": "Part A — Business Quality",
    "B": "Part B — Financial Health",
    "C": "Part C — Management & Capital Allocation",
    "D": "Part D — Margin of Safety & Holdability",
}

_MARKS_PART_NAMES = {
    "A": "Part A — Margin of Safety & Asymmetric Payoff",
    "B": "Part B — Cycle Position",
    "C": "Part C — Risk Architecture (pre-conditions)",
    "D": "Part D — Second-Level Thinking & Contrarianism",
}

_BLACKSTONE_PART_NAMES = {
    "A": "Part A — Asset Quality",
    "B": "Part B — Macro & Thematic Positioning",
    "C": "Part C — Risk Architecture",
    "D": "Part D — Value Creation Thesis",
}

_APOLLO_PART_NAMES = {
    "A": "Part A — Credit Foundation",
    "B": "Part B — Complexity & Catalyst",
    "C": "Part C — ABF Structural Fit",
    "D": "Part D — Credit Quality Controls",
}

_PART_NAMES_BY_LENS = {
    "buffett": _BUFFETT_PART_NAMES,
    "marks": _MARKS_PART_NAMES,
    "kkr": _KKR_PART_NAMES,
    "blackstone": _BLACKSTONE_PART_NAMES,
    "apollo": _APOLLO_PART_NAMES,
}


# ---------------------------------------------------------------------------
# HTML building helpers
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    """Basic HTML escaping."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _verdict_pill(verdict: str) -> str:
    css_class = f"verdict-{verdict.lower()}" if verdict else "verdict-skip"
    v = _esc(verdict or "UNKNOWN")
    return f'<span class="verdict-pill {css_class}">{v}</span>'


def _status_icon(passed: bool) -> str:
    if passed:
        return '<span class="check-status-pass">&#10003;</span>'
    return '<span class="check-status-fail">&#10007;</span>'


def _format_value(value) -> str:
    """Format a check value for display."""
    if value is None:
        return "—"
    if isinstance(value, float):
        if abs(value) < 10:
            return f"{value:.2f}"
        return f"{value:,.1f}"
    if isinstance(value, tuple):
        return " / ".join(_format_value(v) for v in value)
    return _esc(str(value))


# ---------------------------------------------------------------------------
# Cover page
# ---------------------------------------------------------------------------

def _build_cover_html(lens_results: dict, financials: dict, dcf_results: dict,
                      lens_name: str) -> str:
    ticker = financials["ticker"]
    verdict = lens_results.get("verdict", "SKIP")
    score = lens_results.get("score", 0)
    reason = lens_results.get("reason", "")

    # Determine total checks
    total_checks = len(lens_results.get("checks", {}))
    lens_display = _LENS_DISPLAY_NAMES.get(lens_name, lens_name.upper())
    date_str = datetime.now().strftime("%B %d, %Y")

    intrinsic = dcf_results.get("intrinsic_value_per_share", 0)
    price = dcf_results.get("current_price", 0)
    upside = (intrinsic - price) / price * 100 if price > 0 else 0
    upside_sign = "+" if upside >= 0 else ""

    is_india = ticker.endswith(".NS") or ticker.endswith(".BO")
    currency = "₹" if is_india else "$"

    return f"""
<div class="cover-page">
  <div class="cover-wordmark">Sidwell</div>
  <div class="cover-tagline">Personal Investment Decision Engine · v0.6</div>
  <div class="cover-ticker">{_esc(ticker)}</div>
  <div class="cover-lens">{_esc(lens_display)}</div>
  <div style="margin: 1.5em 0;">
    {_verdict_pill(verdict)}
  </div>
  <div class="score-block" style="display:inline-block; text-align:center; min-width:200px;">
    <span class="score-number">{score} / {total_checks}</span>
    <span style="font-size:10pt; color:#555;"> checks passed</span>
  </div>
  <div class="reason-block" style="max-width:380px; margin: 1em auto; text-align:left;">
    {_esc(reason)}
  </div>
  <div class="cover-meta">
    <div>Intrinsic Value: {currency}{intrinsic:,.2f} &nbsp;|&nbsp;
         Market Price: {currency}{price:,.2f} &nbsp;|&nbsp;
         Implied: {upside_sign}{upside:.1f}%</div>
    <div style="margin-top:0.4em;">{date_str}</div>
    <div style="margin-top:0.2em; font-size:8pt; color:#aaa;">
      This report is for personal investment research only.
      Not financial advice.
    </div>
  </div>
</div>
"""


# ---------------------------------------------------------------------------
# Executive summary
# ---------------------------------------------------------------------------

def _build_exec_summary_html(lens_results: dict, lens_name: str) -> str:
    checks = lens_results.get("checks", {})
    score = lens_results.get("score", 0)
    total_checks = len(checks)

    # Part summary
    parts: dict[str, list] = {}
    for check_id, check_dict in checks.items():
        part = check_dict.get("part", "?")
        parts.setdefault(part, []).append(check_dict)

    part_names = _PART_NAMES_BY_LENS.get(lens_name, _PART_DISPLAY_NAMES)

    summary_rows = []
    for part_id in sorted(parts.keys()):
        part_checks = parts[part_id]
        passed_count = sum(1 for c in part_checks if c["passed"])
        part_label = part_names.get(part_id, f"Part {part_id}")
        status_icon = "&#10003;" if passed_count == len(part_checks) else (
            "&#8212;" if passed_count > 0 else "&#10007;"
        )
        css = "check-status-pass" if passed_count == len(part_checks) else (
            "" if passed_count > 0 else "check-status-fail"
        )
        summary_rows.append(
            f'<tr><td><span class="{css}">{status_icon}</span></td>'
            f'<td>{_esc(part_label)}</td>'
            f'<td style="text-align:right;">{passed_count} / {len(part_checks)}</td></tr>'
        )

    rows_html = "\n".join(summary_rows)

    return f"""
<h2>Executive Summary</h2>
<div class="score-block">
  <span class="score-number">{score}</span>
  <span style="font-size:10pt;"> / {total_checks} checks passed</span>
</div>

<table class="summary-table">
  <thead>
    <tr>
      <th style="width:30px;">&nbsp;</th>
      <th>Part</th>
      <th style="text-align:right; width:80px;">Score</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>
"""


# ---------------------------------------------------------------------------
# Check-by-check detail
# ---------------------------------------------------------------------------

def _build_checks_html(lens_results: dict, lens_name: str) -> str:
    checks = lens_results.get("checks", {})

    # Group by part
    parts: dict[str, list] = {}
    for check_id, check_dict in checks.items():
        part = check_dict.get("part", "?")
        parts.setdefault(part, []).append((check_id, check_dict))

    part_names = _PART_NAMES_BY_LENS.get(lens_name, _PART_DISPLAY_NAMES)

    html_parts = []
    for part_idx, part_id in enumerate(sorted(parts.keys())):
        part_check_pairs = parts[part_id]
        part_label = part_names.get(part_id, f"Part {part_id}")
        passed_in_part = sum(1 for _, c in part_check_pairs if c["passed"])
        total_in_part = len(part_check_pairs)

        # Part header
        page_break_class = "part-section" if part_idx > 0 else ""
        checks_html_list = []

        for check_id, check_dict in part_check_pairs:
            passed = check_dict.get("passed", False)
            name = check_dict.get("name", check_id)
            detail = check_dict.get("detail", "")
            threshold = check_dict.get("threshold_str", "")
            reasoning = check_dict.get("framework_reasoning", "")

            icon = _status_icon(passed)
            name_html = _esc(name)
            detail_html = _esc(str(detail))
            threshold_html = _esc(str(threshold))

            # Framework reasoning only shown for FAILED checks
            reasoning_html = ""
            if not passed and reasoning:
                reasoning_html = f'<div class="framework-reasoning">{_esc(reasoning)}</div>'

            checks_html_list.append(f"""
<div class="check-row">
  <div class="check-row-header">
    {icon}
    <span class="check-name">{name_html}</span>
  </div>
  <div class="check-threshold">Threshold: {threshold_html}</div>
  <div class="check-detail">{detail_html}</div>
  {reasoning_html}
</div>""")

        checks_block = "\n".join(checks_html_list)
        html_parts.append(f"""
<div class="{page_break_class}">
  <div class="part-header">{_esc(part_label)} &nbsp;·&nbsp; {passed_in_part}/{total_in_part}</div>
  {checks_block}
</div>""")

    return "\n".join(html_parts)


# ---------------------------------------------------------------------------
# Sources page (extracted from framework .md files)
# ---------------------------------------------------------------------------

def _extract_sources_section(lens_name: str) -> str:
    """
    Read the framework .md and extract the Sources / References section.
    Returns plain text or an empty string if not found.
    """
    try:
        frameworks_dir = Path(__file__).parent.parent / "frameworks"
        md_path = frameworks_dir / f"{lens_name}.md"
        if not md_path.exists():
            return ""
        text = md_path.read_text(encoding="utf-8")
        # Find the last "## Sources" or "## References" section
        match = re.search(
            r"##\s+(?:Sources|References|Source material)\s*\n(.*?)(?=\n##|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
        return ""
    except Exception:
        return ""


def _build_sources_html(lens_name: str) -> str:
    sources_text = _extract_sources_section(lens_name)
    if not sources_text:
        return ""

    # Convert markdown bullet list to HTML
    lines = sources_text.splitlines()
    items = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            items.append(f"<li>{_esc(stripped[2:])}</li>")
        elif stripped:
            items.append(f"<li>{_esc(stripped)}</li>")

    if not items:
        return ""

    items_html = "\n".join(items)
    return f"""
<div class="sources-page">
  <h2>Sources & References</h2>
  <ul class="sources-list">
    {items_html}
  </ul>
</div>
"""


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def export_lens_pdf(
    lens_results: dict,
    financials: dict,
    dcf_results: dict,
    lens_name: str,
) -> bytes:
    """
    Build a per-lens PDF and return as bytes.

    Parameters
    ----------
    lens_results : dict
        Output from evaluate_<lens>_lens() — contains "checks", "score", "verdict", "reason".
    financials : dict
        From fetch_financials() — used for ticker, market data.
    dcf_results : dict
        From run_dcf_valuation() — used for intrinsic value, current price.
    lens_name : str
        One of "buffett", "marks", "kkr", "blackstone", "apollo".

    Returns
    -------
    bytes
        PDF bytes starting with b'%PDF-'.

    Raises
    ------
    RuntimeError
        If weasyprint is not installed or the system libraries are unavailable.
    """
    if not _WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            f"weasyprint is not available. Install it and its system dependencies "
            f"(see packages.txt). Error: {_WEASYPRINT_ERROR}"
        )

    ticker = financials.get("ticker", "UNKNOWN")

    # Build full HTML document
    cover = _build_cover_html(lens_results, financials, dcf_results, lens_name)
    exec_summary = _build_exec_summary_html(lens_results, lens_name)
    checks_detail = _build_checks_html(lens_results, lens_name)
    sources = _build_sources_html(lens_name)

    # Read CSS
    css_string = ""
    if _CSS_PATH.exists():
        css_string = _CSS_PATH.read_text(encoding="utf-8")
    else:
        logger.warning(f"PDF stylesheet not found at {_CSS_PATH}; using inline defaults.")

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sidwell — {_esc(ticker)} — {_esc(lens_name.capitalize())} Lens</title>
</head>
<body data-ticker="{_esc(ticker)}">
  {cover}
  {exec_summary}
  {checks_detail}
  {sources}
</body>
</html>"""

    # Generate PDF
    logger.info(f"Generating PDF for {ticker} / {lens_name} lens")
    try:
        css = weasyprint.CSS(string=css_string)
        pdf_bytes = weasyprint.HTML(
            string=html_doc,
            base_url=str(Path(__file__).parent),
        ).write_pdf(stylesheets=[css])
    except Exception as e:
        logger.error(f"weasyprint PDF generation failed: {e}")
        raise RuntimeError(f"PDF generation failed: {e}") from e

    logger.info(f"PDF generated: {len(pdf_bytes):,} bytes")
    return pdf_bytes
