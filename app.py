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
def _fetch_damodaran(
    ticker: str,
    scraped_industry: str | None,
    scraped_broad_industry: str | None,
    scraped_sector: str | None,
):
    """v0.6.4.2 changed fetch_damodaran_data signature to (ticker, financials).
    Pass scraped fields as separate strings (hashable for @st.cache_data)
    and reconstruct minimal financials dict inside."""
    from data import public
    financials_subset = {
        "scraped_industry": scraped_industry,
        "scraped_broad_industry": scraped_broad_industry,
        "scraped_sector": scraped_sector,
    }
    return public.fetch_damodaran_data(ticker, financials_subset)


@st.cache_data(ttl=2_592_000, show_spinner=False)  # 30d
def _extract_qualitative(ticker: str, doc_tuples: tuple):
    """v0.7: documents are now dicts with url/type/label/date.
    We pass them in as a tuple-of-tuples (hashable for @st.cache_data),
    then reconstruct to list-of-dicts inside before calling the real extractor."""
    from analysis import qualitative
    documents = [
        {"url": url, "type": dtype, "label": label, "date": date}
        for (url, dtype, label, date) in doc_tuples
    ]
    return qualitative.extract_qualitative(ticker, documents)


@st.cache_data(ttl=86_400, show_spinner=False)   # 24h
def _run_pipeline(ticker: str) -> dict:
    """
    Full pipeline — delegates to value.analyze() so app.py and value.py
    always call the SAME code path.  Parity is structural, not a convention.
    """
    from value import analyze
    return analyze(ticker)


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


def _ajp_val(ajp, driver_id, default):
    """Return the scenario-active float value for driver_id from the AJP, or default.
    Mirrors sidwell/engine/statements.py get_val so slider defaults match engine inputs.
    """
    try:
        active = getattr(getattr(ajp, "meta", None), "scenario_active", "BASE") or "BASE"
        for a in ajp.assumptions:
            if a.driver_id == driver_id:
                sc = getattr(a, "scenario", None)
                if sc is not None:
                    if active == "BEAR" and sc.BEAR is not None: return float(sc.BEAR)
                    if active == "BULL" and sc.BULL is not None: return float(sc.BULL)
                    if sc.BASE is not None: return float(sc.BASE)
                if a.value is not None:
                    return float(a.value)
    except Exception:
        pass
    return default


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

def _render_dcf_tab(results: dict):
    financials = results["financials"]
    dcf_results = results["dcf_results"]
    ticker = financials["ticker"]
    price = dcf_results["current_price"]
    assumptions = dcf_results["assumptions"]

    is_india = ticker.endswith(".NS") or ticker.endswith(".BO")
    currency = "₹" if is_india else "$"

    # Banks: DCF is not applicable. Show the "coming soon" note instead of the
    # intrinsic/WACC metrics and Excel export (both rely on None fields).
    if dcf_results.get("not_applicable"):
        st.info(
            dcf_results.get("not_applicable_reason", "DCF not applicable.")
            + "\n\nBanks are still analysed through all five investor lenses on real "
            "financials — see the lens tabs."
        )
        st.metric("Current Price", f"{currency}{price:,.2f}")
        return

    intrinsic = dcf_results["intrinsic_value_per_share"]
    wacc = dcf_results["wacc"]

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
        st.dataframe(df, hide_index=True, width="stretch")

    # ---- Projections table ----
    with st.expander("10-Year Cash Flow Projections", expanded=False):
        import pandas as pd
        projs = dcf_results.get("projections", [])
        if projs:
            rows = []
            for i, p in enumerate(projs[:10], start=1):
                rows.append({
                    "Year": p.get("year", i),
                    "Revenue": f"{currency}{p.get('revenue', 0):,.0f}",
                    "FCF": f"{currency}{p.get('fcf', 0):,.0f}",
                    "PV FCF": f"{currency}{p.get('pv_fcf', 0):,.2f}",
                    "Stage": p.get("stage", "—"),
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        else:
            st.caption("Projection data unavailable.")

    # ---- Live sensitivity sliders (offline re-run via overrides hook) ----
    from valuation import dcf as _dcf

    base_ajp = dcf_results.get("ajp")
    base_wacc = float(dcf_results.get("wacc") or 0.10)
    base_intrinsic = dcf_results["intrinsic_value_per_share"]
    macro_data = results["damodaran_data"]
    rf = results["rf_rate"]
    qual = results["qualitative_results"]

    def _snap(v, lo, step):
        """Snap v to the nearest grid point lo + n*step."""
        return round(lo + round((v - lo) / step) * step, 6)

    # Scenario-aware, grid-snapped base defaults (match what the engine used)
    d = {
        "g1":    _snap(_ajp_val(base_ajp, "stage1_revenue_growth",    0.10), 0.0,  0.01),
        "ebit":  _snap(_ajp_val(base_ajp, "ebit_margin_target",        0.15), 0.02, 0.01),
        "capex": _snap(_ajp_val(base_ajp, "capex_pct_sales_target",    0.05), 0.0,  0.01),
        "tax":   _snap(_ajp_val(base_ajp, "tax_rate",                  0.25), 0.10, 0.01),
        "wacc":  _snap(base_wacc,                                              0.06, 0.0025),
        "wc":    int(_ajp_val(base_ajp, "working_capital_days",         0)),
        "exit":  _snap(_ajp_val(base_ajp, "exit_ev_ebitda_multiple",   10.0), 4.0,  0.5),
    }
    _tg_max0 = max(0.0, round(d["wacc"] - 0.005, 4))
    d["tg"] = min(_snap(_ajp_val(base_ajp, "terminal_growth", 0.02), 0.0, 0.0025), _tg_max0)

    # Ticker-scoped keys so switching companies resets slider state automatically
    sk = {name: f"sl_{name}_{ticker}" for name in d}
    for name, val in d.items():
        st.session_state.setdefault(sk[name], val)

    st.divider()
    with st.expander(
        "\U0001f39b\ufe0f Live Sensitivity (what-if) \u2014 adjust assumptions, value updates live",
        expanded=False,
    ):
        if st.button("Reset to base case", key=f"sens_reset_{ticker}"):
            for name, val in d.items():
                st.session_state[sk[name]] = val
            st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            g1    = st.slider("Stage-1 revenue growth",   0.00, 0.40, step=0.01,   key=sk["g1"])
            ebit  = st.slider("EBIT margin target",        0.02, 0.50, step=0.01,   key=sk["ebit"])
            capex = st.slider("CapEx % sales (target)",    0.00, 0.40, step=0.01,   key=sk["capex"])
            tax   = st.slider("Tax rate",                  0.10, 0.40, step=0.01,   key=sk["tax"])
        with c2:
            wacc_eff = st.slider("WACC",                   0.06, 0.20, step=0.0025, key=sk["wacc"])
            tg_max = max(0.0, round(wacc_eff - 0.005, 4))
            # Clamp stored terminal-g if WACC was lowered below it
            if st.session_state[sk["tg"]] > tg_max:
                st.session_state[sk["tg"]] = tg_max
            tg    = st.slider("Terminal growth (< WACC)",  0.00, tg_max, step=0.0025, key=sk["tg"])
            wc    = st.slider("Working-capital days",       -60,  180,   step=1,      key=sk["wc"])
            exitm = st.slider("Exit EV/EBITDA",             4.0,  30.0,  step=0.5,    key=sk["exit"])

        # Only pass drivers that actually differ from the grid-snapped base
        overrides: dict = {}
        if abs(g1    - d["g1"])    > 1e-9: overrides["stage1_revenue_growth"]  = g1
        if abs(tg    - d["tg"])    > 1e-9: overrides["terminal_growth"]        = tg
        if abs(ebit  - d["ebit"])  > 1e-9: overrides["ebit_margin_target"]     = ebit
        if abs(capex - d["capex"]) > 1e-9: overrides["capex_pct_sales_target"] = capex
        if abs(tax   - d["tax"])   > 1e-9: overrides["tax_rate"]               = tax
        if wc != d["wc"]:                  overrides["working_capital_days"]   = wc
        if abs(exitm - d["exit"])  > 1e-9: overrides["exit_ev_ebitda_multiple"] = exitm
        if abs(wacc_eff - d["wacc"]) > 1e-9: overrides["wacc_override"]        = wacc_eff

        try:
            adj = _dcf.run_dcf_valuation(
                financials, macro_data, rf, qual, overrides=overrides
            )
            adj_intrinsic = adj["intrinsic_value_per_share"]
        except Exception as e:
            st.warning(f"Could not recompute with these inputs: {e}")
            adj_intrinsic = None

        if adj_intrinsic is not None:
            m1, m2, m3 = st.columns(3)
            m1.metric("Base intrinsic", f"{currency}{base_intrinsic:,.2f}")
            if adj_intrinsic <= 0:
                m2.metric("Adjusted intrinsic", "\u2264 0")
                m3.metric("\u0394 vs base", "n/m")
            else:
                delta = (
                    (adj_intrinsic - base_intrinsic) / base_intrinsic
                    if base_intrinsic else 0.0
                )
                adj_upside = (adj_intrinsic - price) / price if price > 0 else 0.0
                m2.metric(
                    "Adjusted intrinsic",
                    f"{currency}{adj_intrinsic:,.2f}",
                    f"{delta:+.1%} vs base",
                )
                m3.metric("Adjusted upside vs price", f"{adj_upside:+.1%}")
            st.caption(
                "Live what-if only \u2014 does not change the committed base case or the Excel workbook."
            )

    # ---- Charts (history vs forecast + valuation curve) ----
    import altair as alt
    import pandas as pd

    _eng = dcf_results.get("engine_results")
    if _eng:
        st.divider()
        st.markdown("### \U0001f4c8 Charts")

        h   = _eng.get("hist", {})
        pj  = _eng.get("proj", {})
        his = h.get("is", {})
        hy  = h.get("years_annual", [])
        hrev  = his.get("sales") or his.get("revenue") or []
        hebit = his.get("operating_profit") or []
        hnp   = his.get("net_profit") or []
        py   = pj.get("years", [])
        prev  = pj.get("revenue", [])
        pebit = pj.get("ebit", [])
        pnp   = pj.get("net_income", [])

        def _mk_chart(title, hyrs, hvals, pyrs, pvals):
            nh  = min(len(hyrs), len(hvals))
            npj = min(len(pyrs), len(pvals))
            if nh + npj == 0:
                return None
            years  = [str(y) for y in hyrs[:nh]]  + [str(y) for y in pyrs[:npj]]
            vals   = list(hvals[:nh])              + list(pvals[:npj])
            phase  = ["Actual"] * nh               + ["Forecast"] * npj
            df = pd.DataFrame({"Year": years, "Value": vals, "Phase": phase})
            return (
                alt.Chart(df).mark_bar().encode(
                    x=alt.X("Year:N", sort=years, title=None),
                    y=alt.Y("Value:Q", title="Rs mm"),
                    color=alt.Color("Phase:N", scale=alt.Scale(
                        domain=["Actual", "Forecast"],
                        range=["#3b6ca8", "#c08a1c"])),
                    tooltip=["Year", "Phase",
                             alt.Tooltip("Value:Q", format=",.0f")],
                ).properties(height=220, title=title)
            )

        with st.expander(
            "History vs forecast \u2014 Revenue, EBIT, Net profit", expanded=True
        ):
            for ttl, hv, pvv in [
                ("Revenue",     hrev,  prev),
                ("EBIT",        hebit, pebit),
                ("Net profit",  hnp,   pnp),
            ]:
                ch = _mk_chart(ttl, hy, hv, py, pvv)
                if ch is not None:
                    st.altair_chart(ch, width="stretch")
            st.caption("Blue = actuals, gold = Sidwell\u2019s forecast. Rs mm.")

        with st.expander("Valuation vs a single driver", expanded=False):
            sweep_opts = {
                "Stage-1 revenue growth": (
                    "stage1_revenue_growth", 0.0,
                    0.40,
                ),
                "Terminal growth": (
                    "terminal_growth", 0.0,
                    max(0.005, round(base_wacc - 0.01, 4)),
                ),
                "EBIT margin target": (
                    "ebit_margin_target", 0.05, 0.40,
                ),
                "WACC": (
                    "wacc_override",
                    max(0.06, round(base_wacc - 0.05, 4)),
                    round(base_wacc + 0.05, 4),
                ),
                "Exit EV/EBITDA": (
                    "exit_ev_ebitda_multiple", 5.0, 25.0,
                ),
            }
            sel = st.selectbox(
                "Driver to sweep", list(sweep_opts.keys()),
                key=f"sweep_sel_{ticker}",
            )
            if st.button("Plot valuation curve", key=f"sweep_btn_{ticker}"):
                drv, lo, hi = sweep_opts[sel]
                xs = [round(lo + (hi - lo) * k / 12.0, 6) for k in range(13)]
                ys, errs = [], []
                for xv in xs:
                    try:
                        r = _dcf.run_dcf_valuation(financials, macro_data, rf, qual, overrides={drv: xv})
                        ys.append(r.get("intrinsic_value_per_share"))
                    except Exception as e:
                        ys.append(None)
                        errs.append(f"{drv}={xv}: {e}")
                st.session_state[f"sweep_data_{ticker}"] = {"label": sel, "xs": xs, "ys": ys, "errs": errs}

            data = st.session_state.get(f"sweep_data_{ticker}")
            if data:
                # safe column name ("Driver") to avoid Vega field-name issues with spaced labels
                dfc = pd.DataFrame({"Driver": data["xs"], "Intrinsic": data["ys"]}).dropna()
                if dfc.empty:
                    st.warning("Couldn't compute the valuation curve — every point returned no value "
                               "(the engine may reject this driver's range for this company).")
                    if data.get("errs"):
                        st.caption("First error: " + data["errs"][0])
                else:
                    if data.get("errs"):
                        st.caption(f"{len(data['errs'])} of {len(data['xs'])} points failed and were dropped.")
                    line = (alt.Chart(dfc).mark_line(point=True).encode(
                                x=alt.X("Driver:Q", title=data["label"]),
                                y=alt.Y("Intrinsic:Q", title=f"Intrinsic ({currency})"),
                                tooltip=[alt.Tooltip("Driver:Q", format=".4f"),
                                         alt.Tooltip("Intrinsic:Q", format=",.2f")]))
                    rule = (alt.Chart(pd.DataFrame({"price": [price]}))
                            .mark_rule(color="red", strokeDash=[4, 4]).encode(x="price:Q"))
                    st.altair_chart((line + rule), width="stretch")
                    st.caption("Red dashed line = current price. Each point re-runs the engine (offline).")

    st.divider()
    st.markdown("### \U0001f3df\ufe0f Comps & Football Field")
    with st.expander("Comparable companies (you choose the peers)", expanded=False):
        st.caption("Enter 2\u20135 peers (tickers or names), comma-separated, e.g. "
                   "BRITANNIA.NS, NESTLEIND.NS. You pick the peers; multiples are computed from screener.")
        peers_raw = st.text_input("Peers", key=f"comps_peers_{ticker}",
                                  placeholder="BRITANNIA.NS, NESTLEIND.NS")
        if st.button("Run comps", key=f"comps_btn_{ticker}"):
            from data.ticker_resolver import resolve_ticker_from_input
            from valuation.comps import run_comps_valuation
            raw = [x.strip() for x in (peers_raw or "").split(",") if x.strip()]
            resolved = []
            for r in raw:
                try:
                    t, _ = resolve_ticker_from_input(r)
                except Exception:
                    t = r.upper()
                resolved.append(t)
            if len(resolved) < 2:
                st.warning("Enter at least 2 peers.")
            else:
                with st.spinner("Fetching peers and computing multiples\u2026"):
                    try:
                        st.session_state[f"comps_data_{ticker}"] = run_comps_valuation(financials, resolved[:5])
                    except Exception as e:
                        st.session_state[f"comps_data_{ticker}"] = {"error": f"Comps failed: {e}"}

        comps = st.session_state.get(f"comps_data_{ticker}")
        if comps:
            if comps.get("error"):
                st.warning(comps["error"])
            else:
                pm = comps.get("peer_multiples", [])
                if pm:
                    st.dataframe(pd.DataFrame([{
                        "Peer": r.get("ticker"),
                        "EV/EBITDA": r.get("ev_ebitda"),
                        "EV/Sales": r.get("ev_sales"),
                        "P/E": r.get("pe"),
                    } for r in pm]), hide_index=True, width="stretch")

                med = comps.get("medians", {})
                def _fm(m): return (f"{m['med']:.1f}\u00d7 (min {m['min']:.1f} / max {m['max']:.1f})"
                                    if m else "\u2014")
                st.markdown(f"**Median multiples** \u2014 EV/EBITDA: {_fm(med.get('ev_ebitda'))} \u00b7 "
                            f"EV/Sales: {_fm(med.get('ev_sales'))} \u00b7 P/E: {_fm(med.get('pe'))}")

                imp = comps.get("implied_per_share", {})
                c_a, c_b, c_c = st.columns(3)
                c_a.metric("Implied (EV/EBITDA)", f"{currency}{imp['ev_ebitda']:,.0f}" if imp.get("ev_ebitda") else "\u2014")
                c_b.metric("Implied (EV/Sales)",  f"{currency}{imp['ev_sales']:,.0f}"  if imp.get("ev_sales")  else "\u2014")
                c_c.metric("Implied (P/E)",       f"{currency}{imp['pe']:,.0f}"        if imp.get("pe")        else "\u2014")

                if comps.get("caveat"):
                    st.caption("\u26a0\ufe0f " + comps["caveat"])
                if comps.get("excluded"):
                    with st.expander("Excluded legs"):
                        for t, reason in comps["excluded"]:
                            st.caption(f"{t}: {reason}")

                # ---- Football field ----
                st.markdown("**Football field**")
                intrinsic = dcf_results["intrinsic_value_per_share"]
                rows = [{"Method": "DCF (base)", "low": intrinsic, "high": intrinsic, "mid": intrinsic}]
                for lbl, key in [("Comps EV/EBITDA", "ev_ebitda"),
                                 ("Comps EV/Sales", "ev_sales"), ("Comps P/E", "pe")]:
                    v = imp.get(key)
                    if v:
                        rows.append({"Method": lbl, "low": v, "high": v, "mid": v})
                cr = comps.get("comps_range")
                if cr and cr.get("low") is not None:
                    rows.append({"Method": "Comps blended", "low": cr["low"], "high": cr["high"],
                                 "mid": (cr["low"] + cr["high"]) / 2.0})
                dff = pd.DataFrame(rows)
                order = list(dff["Method"])
                bars = alt.Chart(dff).mark_bar(height=14, color="#9ec5e8").encode(
                    x=alt.X("low:Q", title=f"Value per share ({currency})"), x2="high:Q",
                    y=alt.Y("Method:N", sort=order, title=None))
                pts = alt.Chart(dff).mark_point(size=90, filled=True, color="#1f3a5f").encode(
                    x="mid:Q", y=alt.Y("Method:N", sort=order),
                    tooltip=["Method", alt.Tooltip("mid:Q", format=",.0f")])
                rule = alt.Chart(pd.DataFrame({"price": [price]})).mark_rule(
                    color="red", strokeDash=[4, 4]).encode(x="price:Q")
                st.altair_chart((bars + pts + rule).properties(height=28 * len(rows) + 40),
                                width="stretch")
                st.caption("Dots = point estimates, bars = ranges, red dashed line = current price.")

    # ---- Excel download (new 13-sheet, 3-statement AJP engine workbook) ----
    st.divider()
    st.markdown("**Export DCF as Excel workbook** (13-sheet, 3-statement model)")
    eng = dcf_results.get("engine_results")
    if not eng:
        st.caption("Workbook unavailable for this ticker (DCF not applicable).")
    elif st.button("Generate DCF Excel", key="btn_excel"):
        with st.spinner("Building workbook\u2026"):
            import tempfile, os
            from sidwell.render.workbook import create_workbook
            tmp = os.path.join(tempfile.gettempdir(), f"{ticker}_DCF_v0.7.xlsx")
            create_workbook(eng, dcf_results.get("ajp"), tmp)
            with open(tmp, "rb") as fh:
                excel_bytes = fh.read()
        st.download_button(
            label="Download DCF Workbook (.xlsx)",
            data=excel_bytes,
            file_name=f"{ticker}_DCF_v0.7.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_excel",
        )


# ---------------------------------------------------------------------------
# Sidebar: ticker input + pipeline trigger
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## Sidwell")
    st.markdown("Personal investment decision engine")
    st.divider()

    # streamlit-searchbox needs a rerun on every keystroke to populate its live
    # dropdown — that CANNOT happen inside st.form (forms suppress reruns until the
    # submit button). So the searchbox lives OUTSIDE any form, with a plain Analyze
    # button. The text_input fallback stays inside a form so pressing Enter submits.
    has_searchbox = False
    try:
        from streamlit_searchbox import st_searchbox
        from data.ticker_resolver import search_companies
        has_searchbox = True
    except ImportError:
        pass

    if has_searchbox:
        @st.cache_data(ttl=3600, show_spinner=False)
        def _cached_search(query: str):
            return search_companies(query)

        ticker_input = st_searchbox(
            _cached_search,
            key="ticker_input",
            placeholder="Search company or ticker...",
            label="Company Name or Ticker",
        )
        analyze_btn = st.button("Analyze", type="primary", width="stretch")
    else:
        with st.form(key="ticker_form", clear_on_submit=False, border=False):
            ticker_input = st.text_input(
                "Ticker",
                value="",
                placeholder="e.g. ASIANPAINT.NS",
                help="Press Enter or click Analyze. Append .NS for NSE India, .BO for BSE.",
                key="ticker_input",
            )
            analyze_btn = st.form_submit_button(
                "Analyze", type="primary", width="stretch"
            )

    st.divider()

    with st.expander("Advanced (optional): your own assumptions", expanded=False):
        st.caption("Leave any field blank to let Sidwell/DeepSeek decide. Filled fields override ours.")
        _uo: dict = {}

        def _opt(label, lo, hi, step, key, drv):
            v = st.number_input(label, min_value=lo, max_value=hi, value=None,
                                step=step, key=key, placeholder="auto")
            if v is not None:
                _uo[drv] = v

        _opt("Stage-1 revenue growth", 0.0,  0.40, 0.01,   "pre_g1",   "stage1_revenue_growth")
        _opt("Terminal growth",        0.0,  0.10, 0.0025, "pre_tg",   "terminal_growth")
        _opt("EBIT margin target",     0.02, 0.50, 0.01,   "pre_ebit", "ebit_margin_target")
        _opt("CapEx % sales target",   0.0,  0.40, 0.01,   "pre_capex","capex_pct_sales_target")
        _opt("Tax rate",               0.10, 0.40, 0.01,   "pre_tax",  "tax_rate")
        _opt("Working-capital days",   -60,  180,  1,      "pre_wc",   "working_capital_days")
        _opt("Exit EV/EBITDA",         4.0,  30.0, 0.5,    "pre_exit", "exit_ev_ebitda_multiple")
        _opt("WACC (override)",        0.06, 0.20, 0.0025, "pre_wacc", "wacc_override")
        st.session_state["user_overrides"] = _uo

    st.divider()
    st.caption(
        "Data sources: Yahoo Finance \u00b7 Damodaran (Jan 2026) \u00b7 FRED\n\n"
        "Qualitative analysis: Gemini (when API key configured)\n\n"
        "This app is for personal research only. Not financial advice."
    )


# ---------------------------------------------------------------------------
# Main content area
# ---------------------------------------------------------------------------

st.title("Sidwell — Investment Analysis")

if not ticker_input:
    st.info(
        "Enter a **ticker or company name** in the sidebar and press **Enter** (or click **Analyze**) to run the full pipeline.\n\n"
        "Examples — names: `Reliance`, `Nestle India`. Tickers: `ASIANPAINT.NS`, `RELIANCE.NS`."
    )
    st.stop()

# v0.7.5: resolve company name → ticker if user typed a name rather than a ticker
from data.ticker_resolver import resolve_ticker_from_input
ticker, _resolve_source = resolve_ticker_from_input(ticker_input)
if _resolve_source != "ticker" and _resolve_source != "unresolved":
    st.caption(f"Resolved **'{ticker_input.strip()}'** → `{ticker}`")
elif _resolve_source == "unresolved":
    st.warning(f"Could not auto-resolve '{ticker_input.strip()}' to a ticker. Trying anyway as `{ticker}` — analysis may fail.")

if analyze_btn or ("_last_ticker" in st.session_state and st.session_state["_last_ticker"] == ticker):
    st.session_state["_last_ticker"] = ticker

    # ---- Run pipeline ----
    with st.spinner(f"Running Sidwell pipeline for **{ticker}**…"):
        try:
            results = _run_pipeline(ticker)
        except ValueError as e:
            err_msg = str(e)
            if "appears to be cyclical" in err_msg:
                st.info(f"**Model Limitation:**\n\n{err_msg}")
            elif "non-positive intrinsic value" in err_msg:
                st.error(f"DCF model failed for {ticker} — non-positive intrinsic. See logs.")
            else:
                st.error(f"**Data error:** {err_msg}")
            st.stop()
        except Exception as e:
            st.error(f"**Pipeline failed:** {e}")
            logger.exception(f"Pipeline error for {ticker}")
            st.stop()

    financials = results["financials"]
    dcf_results = results["dcf_results"]

    # ---- Apply pre-run user overrides (offline; no re-scrape) ----
    user_overrides = st.session_state.get("user_overrides", {})
    if user_overrides:
        from valuation import dcf as _dcf
        try:
            dcf_results = _dcf.run_dcf_valuation(
                results["financials"], results["damodaran_data"], results["rf_rate"],
                results["qualitative_results"], overrides=user_overrides,
            )
            results["dcf_results"] = dcf_results
            st.info("Using your assumptions for: " + ", ".join(user_overrides.keys()))
        except Exception as e:
            st.warning(f"Could not apply your assumptions ({e}); showing Sidwell's base case.")
    qualitative_results = results["qualitative_results"]
    buffett_results = results["buffett_results"]
    marks_results = results["marks_results"]
    kkr_results = results["kkr_results"]
    blackstone_results = results["blackstone_results"]
    apollo_results = results["apollo_results"]

    # ---- Qualitative status banner ----
    if qualitative_results.get("status") == "available":
        model = qualitative_results.get("model", "unknown")
        docs_used = qualitative_results.get("documents_used", results.get("docs", []))
        st.success(f"Qualitative layer: {len(docs_used)} document(s) analyzed via **{model}**")
    else:
        reason = qualitative_results.get("reason", "unknown")
        if "no documents" in reason.lower() or "fewer than" in reason.lower() or "0" in reason:
            st.info(
                "**Numbers-only valuation** — no curated high-value filings available; qualitative drivers unavailable. "
                "Soft checks default to neutral values."
            )
        else:
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
        _render_dcf_tab(results)

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
