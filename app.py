"""
app.py — Sidwell v0.6 Streamlit Frontend
-----------------------------------------
Desktop-first (1024px+) investment analysis dashboard.

Tab layout:
  1. DCF Valuation
  2. Buffett Lens (14 checks)
  3. Marks Lens (14 checks)
  4. KKR Lens (18 checks)
  5. Blackstone Lens (14 checks)
  6. Apollo Lens (16 checks)

Exports:
  - Per-lens PDF (weasyprint)
  - DCF Excel workbook (openpyxl)
"""

import os
import sys
import logging
import streamlit as st

# ---- Page config must be first Streamlit call ----
st.set_page_config(
    page_title="Sidwell — Investment Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Must come after set_page_config ----
from reports.render import SIDWELL_VERSION


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("sidwell.app")


# ---------------------------------------------------------------------------
# Inject API keys from Streamlit secrets → os.environ
# ---------------------------------------------------------------------------

def _inject_secrets():
    """Load API keys from st.secrets into os.environ if available."""
    try:
        for key in ("GEMINI_API_KEY", "FRED_API_KEY"):
            if key in st.secrets and not os.environ.get(key):
                os.environ[key] = st.secrets[key]
    except Exception:
        pass  # Secrets not configured; app degrades gracefully


_inject_secrets()


# ---------------------------------------------------------------------------
# Streamlit cache wrappers (sit on top of the existing file-cache layer)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=86_400, show_spinner=False)   # 24h — matches TTL_PRICES
def _fetch_financials(ticker: str):
    from data import public
    return public.fetch_financials(ticker)


@st.cache_data(ttl=86_400, show_spinner=False)   # 24h
def _fetch_rf_rate(ticker: str):
    from data import public
    return public.fetch_risk_free_rate(ticker)


@st.cache_data(ttl=2_592_000, show_spinner=False)  # 30d — matches TTL_MACRO
def _fetch_damodaran(ticker: str):
    from data import public
    return public.fetch_damodaran_data(ticker)


@st.cache_data(ttl=2_592_000, show_spinner=False)  # 30d
def _extract_qualitative(ticker: str, doc_paths: tuple):
    """doc_paths as tuple (hashable for st.cache_data)."""
    from analysis import qualitative
    return qualitative.extract_qualitative(ticker, list(doc_paths))


@st.cache_data(ttl=86_400, show_spinner=False)   # 24h
def _run_pipeline(ticker: str) -> dict:
    """
    Full pipeline: financials → rf_rate → damodaran → DCF → qualitative → all 5 lenses.
    Returns the same dict as value.analyze().
    """
    from data import documents as doc_module
    from valuation import dcf
    from lenses import buffett, marks, kkr, blackstone, apollo
    from reports import render

    financials = _fetch_financials(ticker)
    rf_rate = _fetch_rf_rate(ticker)
    damodaran_data = _fetch_damodaran(ticker)
    dcf_results = dcf.run_dcf_valuation(financials, damodaran_data, rf_rate)

    docs = doc_module.discover_documents(ticker)
    qualitative_results = _extract_qualitative(ticker, tuple(sorted(str(d) for d in docs)))

    buffett_results = buffett.evaluate_buffett_lens(
        financials, dcf_results, qualitative_results=qualitative_results
    )
    marks_results = marks.evaluate_marks_lens(
        financials, dcf_results, qualitative_results=qualitative_results
    )
    kkr_results = kkr.evaluate_kkr_lens(
        financials, dcf_results, qualitative_results=qualitative_results
    )
    blackstone_results = blackstone.evaluate_blackstone_lens(
        financials, dcf_results, qualitative_results=qualitative_results
    )
    apollo_results = apollo.evaluate_apollo_lens(
        financials, dcf_results, qualitative_results=qualitative_results
    )

    # Also write markdown report (side-effect, no cache impact)
    try:
        render.render_markdown_report(
            dcf_results, buffett_results, financials,
            qualitative_results=qualitative_results,
            marks_results=marks_results,
            kkr_results=kkr_results,
            blackstone_results=blackstone_results,
            apollo_results=apollo_results,
        )
    except Exception as e:
        logger.warning(f"Markdown report write failed (non-fatal): {e}")

    return {
        "ticker": ticker,
        "financials": financials,
        "rf_rate": rf_rate,
        "damodaran_data": damodaran_data,
        "dcf_results": dcf_results,
        "qualitative_results": qualitative_results,
        "docs": docs,
        "buffett_results": buffett_results,
        "marks_results": marks_results,
        "kkr_results": kkr_results,
        "blackstone_results": blackstone_results,
        "apollo_results": apollo_results,
    }


# ---------------------------------------------------------------------------
# CSS — max-width constraint + component polish
# ---------------------------------------------------------------------------

st.markdown("""
<style>
/* Desktop-first: cap content width */
.main .block-container {
    max-width: 1100px;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* Verdict pills */
.verdict-pill {
    display: inline-block;
    padding: 3px 14px;
    border-radius: 14px;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 0.04em;
}
.verdict-buy   { background: #2d7a3e; color: #fff; }
.verdict-wait  { background: #c08a1c; color: #fff; }
.verdict-watch { background: #3b6ca8; color: #fff; }
.verdict-skip  { background: #a43030; color: #fff; }

/* Check rows */
.check-pass { color: #2d7a3e; font-weight: bold; }
.check-fail { color: #a43030; font-weight: bold; }
.check-card {
    border-left: 3px solid #e0e0e0;
    padding: 4px 0 4px 12px;
    margin-bottom: 6px;
}
.check-card-fail {
    border-left-color: #e88;
}
.check-card-pass {
    border-left-color: #5a5;
}
.framework-note {
    font-style: italic;
    color: #666;
    font-size: 0.85rem;
    padding: 4px 8px;
    background: #f8f9fa;
    border-left: 2px solid #ccc;
    margin-top: 4px;
}

/* Metric label cleanup */
.stMetric label {
    font-size: 0.80rem;
    color: #555;
}

/* Sidebar width */
section[data-testid="stSidebar"] {
    min-width: 260px;
    max-width: 310px;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LENS_NAMES = {
    "buffett": "Warren Buffett",
    "marks": "Howard Marks",
    "kkr": "KKR",
    "blackstone": "Blackstone",
    "apollo": "Apollo",
}

_LENS_MAX_SCORES = {
    "buffett": 14,
    "marks": 14,
    "kkr": 18,
    "blackstone": 14,
    "apollo": 16,
}


def _verdict_pill_html(verdict: str) -> str:
    css = f"verdict-{verdict.lower()}" if verdict else "verdict-skip"
    return f'<span class="verdict-pill {css}">{verdict or "?"}</span>'


def _render_check(check_id: str, check_dict: dict):
    """Render a single check row with expander for detail."""
    passed = check_dict.get("passed", False)
    name = check_dict.get("name", check_id)
    detail = check_dict.get("detail", "")
    threshold = check_dict.get("threshold_str", "")
    reasoning = check_dict.get("framework_reasoning", "")

    icon = "✅" if passed else "❌"
    card_class = "check-card check-card-pass" if passed else "check-card check-card-fail"

    with st.expander(f"{icon} **{name}**", expanded=False):
        if threshold:
            st.caption(f"Threshold: {threshold}")
        if detail:
            st.write(detail)
        if not passed and reasoning:
            st.markdown(
                f'<div class="framework-note">'
                f'<strong>Framework says:</strong> {reasoning}'
                f'</div>',
                unsafe_allow_html=True,
            )


def _render_lens_tab(lens_results: dict, lens_key: str, financials: dict,
                     dcf_results: dict):
    """Render one lens tab: score summary + part-grouped check expanders + export button."""
    if lens_results is None:
        st.info("Lens results unavailable for this run.")
        return

    score = lens_results.get("score", 0)
    max_score = _LENS_MAX_SCORES[lens_key]
    verdict = lens_results.get("verdict", "SKIP")
    reason = lens_results.get("reason", "")
    checks = lens_results.get("checks", {})
    ticker = financials["ticker"]

    # ---- Score header ----
    col_score, col_verdict, col_reason = st.columns([1, 1, 3])
    with col_score:
        st.metric(label="Score", value=f"{score} / {max_score}")
    with col_verdict:
        st.markdown("**Verdict**")
        st.markdown(_verdict_pill_html(verdict), unsafe_allow_html=True)
    with col_reason:
        st.markdown("**Reason**")
        st.write(reason)

    st.divider()

    # ---- Checks by part ----
    parts: dict[str, list] = {}
    for check_id, check_dict in checks.items():
        part = check_dict.get("part", "?")
        parts.setdefault(part, []).append((check_id, check_dict))

    for part_id in sorted(parts.keys()):
        part_checks = parts[part_id]
        passed_count = sum(1 for _, c in part_checks if c["passed"])
        total_count = len(part_checks)
        st.markdown(f"**Part {part_id}** &nbsp; {passed_count}/{total_count} checks passed")
        for check_id, check_dict in part_checks:
            _render_check(check_id, check_dict)

    # ---- PDF export ----
    st.divider()
    st.markdown("**Export this lens as PDF**")
    try:
        from exports.pdf import export_lens_pdf, _WEASYPRINT_AVAILABLE
        if _WEASYPRINT_AVAILABLE:
            if st.button(f"Generate PDF — {_LENS_NAMES[lens_key]}", key=f"pdf_{lens_key}"):
                with st.spinner("Generating PDF…"):
                    pdf_bytes = export_lens_pdf(lens_results, financials, dcf_results, lens_key)
                st.download_button(
                    label=f"Download {_LENS_NAMES[lens_key]} Lens PDF",
                    data=pdf_bytes,
                    file_name=f"{ticker}_{lens_key}_lens_{SIDWELL_VERSION}.pdf",
                    mime="application/pdf",
                    key=f"dl_pdf_{lens_key}",
                )
        else:
            st.caption(
                "PDF export requires weasyprint system libraries (libgobject, libcairo). "
                "Available on Streamlit Cloud; not available on Windows local runs."
            )
    except Exception as e:
        st.error(f"PDF export error: {e}")


# ---------------------------------------------------------------------------
# DCF tab
# ---------------------------------------------------------------------------

def _render_dcf_tab(dcf_results: dict, financials: dict):
    ticker = financials["ticker"]
    intrinsic = dcf_results["intrinsic_value_per_share"]
    price = dcf_results["current_price"]
    wacc = dcf_results["wacc"]
    assumptions = dcf_results["assumptions"]

    is_india = ticker.endswith(".NS") or ticker.endswith(".BO")
    currency = "₹" if is_india else "$"

    upside = (intrinsic - price) / price if price > 0 else 0

    # ---- Key metrics ----
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Intrinsic Value", f"{currency}{intrinsic:,.2f}")
    with col2:
        st.metric("Current Price", f"{currency}{price:,.2f}")
    with col3:
        st.metric("Implied Upside", f"{upside:+.1%}")
    with col4:
        st.metric("WACC", f"{wacc:.2%}")

    st.divider()

    # ---- Assumptions table ----
    with st.expander("DCF Assumptions", expanded=True):
        import pandas as pd
        rows = [
            ("Risk-Free Rate", f"{assumptions.get('risk_free_rate', 0):.2%}"),
            ("Total ERP", f"{assumptions.get('total_erp', 0):.2%}"),
            ("Levered Beta", f"{assumptions.get('beta_levered', 0):.3f}"),
            ("Cost of Equity", f"{assumptions.get('cost_of_equity', 0):.2%}"),
            ("Cost of Debt", f"{assumptions.get('cost_of_debt', 0):.2%}"),
            ("Equity Weight", f"{assumptions.get('equity_weight', 0):.1%}"),
            ("Debt Weight", f"{assumptions.get('debt_weight', 0):.1%}"),
            ("WACC", f"{assumptions.get('wacc', 0):.2%}"),
            ("Stage 1 Growth (CAGR)", f"{assumptions.get('revenue_growth', assumptions.get('stage_1_growth', 0)):.2%}"),
            ("Terminal Growth Rate", f"{assumptions.get('terminal_growth_rate', 0):.2%}"),
            ("Tax Rate", f"{assumptions.get('tax_rate', 0):.2%}"),
            ("Industry (Beta source)", assumptions.get("target_industry", "—")),
        ]
        df = pd.DataFrame(rows, columns=["Assumption", "Value"])
        st.dataframe(df, hide_index=True, use_container_width=True)

    # ---- Projections table ----
    with st.expander("10-Year Cash Flow Projections", expanded=False):
        import pandas as pd
        projs = dcf_results.get("projections", [])
        if projs:
            rows = []
            for i, p in enumerate(projs[:10], start=1):
                rows.append({
                    "Year": i,
                    "Revenue": f"{currency}{p.get('revenue', 0):,.0f}",
                    "FCF": f"{currency}{p.get('fcf', 0):,.0f}",
                    "PV FCF": f"{currency}{p.get('pv_fcf', 0):,.2f}",
                    "Stage": p.get("stage", "—"),
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        else:
            st.caption("Projection data unavailable.")

    # ---- Excel download ----
    st.divider()
    st.markdown("**Export DCF as Excel workbook**")
    if st.button("Generate DCF Excel", key="btn_excel"):
        with st.spinner("Building workbook…"):
            from exports.excel import export_dcf_excel
            excel_bytes = export_dcf_excel(dcf_results, financials)
        st.download_button(
            label="Download DCF Workbook (.xlsx)",
            data=excel_bytes,
            file_name=f"{ticker}_DCF_{SIDWELL_VERSION}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_excel",
        )


# ---------------------------------------------------------------------------
# Sidebar: ticker input + pipeline trigger
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(f"## Sidwell {SIDWELL_VERSION}")
    st.markdown("Personal investment decision engine")
    st.divider()

    ticker_input = st.text_input(
        "Ticker",
        value="",
        placeholder="e.g. ASIANPAINT.NS or AAPL",
        help="Yahoo Finance ticker. Append .NS for NSE India, .BO for BSE.",
        key="ticker_input",
    )

    analyze_btn = st.button("Analyze", type="primary", use_container_width=True)

    st.divider()
    st.caption(
        "Data sources: Yahoo Finance · Damodaran (Jan 2026) · FRED\n\n"
        "Qualitative analysis: Gemini (when API key configured)\n\n"
        "This app is for personal research only. Not financial advice."
    )


# ---------------------------------------------------------------------------
# Main content area
# ---------------------------------------------------------------------------

st.title("Sidwell — Investment Analysis")

if not ticker_input:
    st.info(
        "Enter a ticker in the sidebar and click **Analyze** to run the full pipeline.\n\n"
        "Example tickers: `ASIANPAINT.NS`, `AAPL`, `RELIANCE.NS`"
    )
    st.stop()

ticker = ticker_input.strip().upper()

if analyze_btn or ("_last_ticker" in st.session_state and st.session_state["_last_ticker"] == ticker):
    st.session_state["_last_ticker"] = ticker

    # ---- Run pipeline ----
    with st.spinner(f"Running Sidwell pipeline for **{ticker}**…"):
        try:
            results = _run_pipeline(ticker)
        except ValueError as e:
            st.error(f"**Data error:** {e}")
            st.stop()
        except Exception as e:
            st.error(f"**Pipeline failed:** {e}")
            logger.exception(f"Pipeline error for {ticker}")
            st.stop()

    financials = results["financials"]
    dcf_results = results["dcf_results"]
    qualitative_results = results["qualitative_results"]
    buffett_results = results["buffett_results"]
    marks_results = results["marks_results"]
    kkr_results = results["kkr_results"]
    blackstone_results = results["blackstone_results"]
    apollo_results = results["apollo_results"]

    # ---- Qualitative status banner ----
    if qualitative_results.get("status") == "available":
        model = qualitative_results.get("model", "unknown")
        n_docs = len(results.get("docs", []))
        st.success(f"Qualitative layer: {n_docs} document(s) analyzed via **{model}**")
    else:
        reason = qualitative_results.get("reason", "unknown")
        st.info(
            f"Qualitative layer unavailable ({reason}). "
            f"Soft checks default to their documented neutral values."
        )

    # ---- Tabs ----
    tabs = st.tabs([
        "DCF Valuation",
        "Buffett",
        "Marks",
        "KKR",
        "Blackstone",
        "Apollo",
    ])

    with tabs[0]:
        _render_dcf_tab(dcf_results, financials)

    with tabs[1]:
        _render_lens_tab(buffett_results, "buffett", financials, dcf_results)

    with tabs[2]:
        _render_lens_tab(marks_results, "marks", financials, dcf_results)

    with tabs[3]:
        _render_lens_tab(kkr_results, "kkr", financials, dcf_results)

    with tabs[4]:
        _render_lens_tab(blackstone_results, "blackstone", financials, dcf_results)

    with tabs[5]:
        _render_lens_tab(apollo_results, "apollo", financials, dcf_results)
