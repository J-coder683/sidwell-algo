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
        for key in ("GEMINI_API_KEY", "FRED_API_KEY", "DEEPSEEK_API_KEY", "EDGAR_IDENTITY"):
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
def _run_pipeline(ticker: str, research_tuple: tuple = ()) -> dict:
    """
    Full pipeline — delegates to value.analyze() so app.py and value.py
    always call the SAME code path.  Parity is structural, not a convention.

    research_tuple: hashable tuple of (filename, bytes) pairs so @st.cache_data
    can vary its key with uploaded research without needing a dict.
    Empty tuple () => no research => identical to prior behaviour.
    """
    from value import analyze
    research_docs = [{"filename": n, "bytes": b} for n, b in research_tuple] or None
    return analyze(ticker, research_docs=research_docs)


@st.cache_data(ttl=86_400, show_spinner=False)
def _peer_options() -> dict:
    """Map 'Company Name (TICKER)' -> TICKER from the committed universe index."""
    from data.ticker_resolver import get_local_index, get_us_universe
    opts = {}
    for name, info in get_local_index().items():
        nse = info.get("nse_symbol", "")
        bse = info.get("bse_code", "")
        if nse:
            t = f"{nse}.NS"
        elif bse:
            t = f"{bse}.BO"
        else:
            continue
        opts[f"{name} ({t})"] = t
        
    for tkr, name in get_us_universe().items():
        opts[f"{name} ({tkr})"] = tkr
        
    return opts

@st.cache_data(ttl=86_400, show_spinner=False)
def _fetch_price_history(ticker: str):
    from data.stooq import fetch_price_history
    return fetch_price_history(ticker)

@st.cache_data(ttl=86_400, show_spinner=False)
def _build_variables(ticker: str):
    from analysis.metric_lab import build_variables
    return build_variables(ticker)

@st.cache_data(ttl=86400, show_spinner=False)
def _get_fun_fact(ticker: str) -> str:
    import os
    from openai import OpenAI
    try:
        api_key = st.secrets.get("DEEPSEEK_API_KEY")
    except Exception:
        api_key = None
    api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        return f"Did you know {ticker} has an interesting history? (Configure DEEPSEEK_API_KEY for real fun facts!)"
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=15.0)
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f"Give me exactly one very short, witty, and obscure financial fun fact about the company with ticker {ticker}. 1 sentence only. No intro, no quotes."}]
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return f"Did you know {ticker} has an interesting history? (DeepSeek is too busy right now.)"


# ---------------------------------------------------------------------------
# Theme State & CSS Setup
# ---------------------------------------------------------------------------

if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

theme = st.session_state["theme"]

tokens = """
:root {
    /* Succession — boardroom at night: warm charcoal + champagne brass */
    --font-display: 'Fraunces', Georgia, 'Times New Roman', serif;
    --font-ui: 'IBM Plex Sans', -apple-system, sans-serif;
    --font-mono: 'IBM Plex Mono', ui-monospace, monospace;
    --bg: #161513;
    --surface: #1f1d1a;
    --surface-2: #2a2723;
    --border: #38342e;
    --ink: #ece7dd;
    --muted: #b3ac9e;
    --faint: #8a8275;
    --accent: #c2a063;
    --accent-ink: #1a1813;
    --pos: #7fa987;
    --neg: #c47a72;
    --warn: #c2a063;
    --info: #8fa6c0;

    /* Native widget overrides */
    --input-bg: #1a1815;
    --input-border: #38342e;
}
""" if theme == "dark" else """
:root {
    /* Succession — old-money paper: warm bone + ink, restrained brass */
    --font-display: 'Fraunces', Georgia, 'Times New Roman', serif;
    --font-ui: 'IBM Plex Sans', -apple-system, sans-serif;
    --font-mono: 'IBM Plex Mono', ui-monospace, monospace;
    --bg: #f2f1ec;
    --surface: #fcfbf8;
    --surface-2: #eae7df;
    --border: #ddd8cd;
    --ink: #1a1815;
    --muted: #6b665b;
    --faint: #9a958a;
    --accent: #9c7c43;
    --accent-ink: #fcfbf8;
    --pos: #4a6f52;
    --neg: #9a4a44;
    --warn: #9c7c43;
    --info: #46607f;

    /* Native widget overrides */
    --input-bg: #fcfbf8;
    --input-border: #d3cdbf;
}
"""

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

{tokens}
""" + """

/* Base resets & typography */
html, body, [class*="css"] {
    font-family: var(--font-ui) !important;
    color: var(--ink) !important;
}

.stApp {
    background-color: var(--bg) !important;
}

/* Desktop-first: cap content width */
.main .block-container {
    max-width: 1100px;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    min-width: 260px;
    max-width: 310px;
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

/* NATIVE TEXT OVERRIDES — force theme tokens to win over config.toml's fixed textColor
   (this is what was breaking dark mode: native h-tags & labels kept the light textColor) */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
[data-testid="stHeading"],
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong {
    color: var(--ink) !important;
}
/* Editorial section headers in the display serif (carry the hero identity) */
.stApp [data-testid="stMarkdownContainer"] h2,
.stApp [data-testid="stMarkdownContainer"] h3 {
    font-family: var(--font-display) !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em;
}
.stApp [data-testid="stMarkdownContainer"] h3 { font-size: 1.6rem !important; }
[role="radiogroup"] label, [role="radiogroup"] label *,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *,
.stSlider label,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p {
    color: var(--muted) !important;
}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
    color: var(--faint) !important;
}

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background-color: var(--input-bg) !important;
    color: var(--ink) !important;
    border-color: var(--input-border) !important;
}
/* Placeholder ("auto") was invisible on the dark input */
[data-testid="stTextInput"] input::placeholder,
[data-testid="stNumberInput"] input::placeholder {
    color: var(--faint) !important;
    opacity: 1 !important;
}
/* Number input wrapper + the white +/- stepper buttons */
[data-testid="stNumberInput"] > div {
    background-color: var(--input-bg) !important;
    border-color: var(--input-border) !important;
}
[data-testid="stNumberInput"] button,
[data-testid="stNumberInputStepUp"],
[data-testid="stNumberInputStepDown"] {
    background-color: var(--surface-2) !important;
    color: var(--ink) !important;
    border-color: var(--input-border) !important;
}
[data-testid="stNumberInput"] button svg { fill: var(--ink) !important; }
[data-baseweb="select"] > div {
    background-color: var(--input-bg) !important;
    border-color: var(--input-border) !important;
}
[data-baseweb="select"] * {
    color: var(--ink) !important;
}
/* Dropdown popovers (multiselect / selectbox menus) — were rendering on the
   light config theme, so options were invisible (light-on-light) in dark mode. */
[data-baseweb="popover"] div,
[data-baseweb="menu"],
[data-baseweb="menu"] ul,
[role="listbox"] {
    background-color: var(--surface) !important;
    border-color: var(--border) !important;
}
[data-baseweb="popover"] li,
[data-baseweb="menu"] li,
[role="option"], [role="option"] * {
    color: var(--ink) !important;
    background-color: var(--surface) !important;
}
[role="option"]:hover,
[data-baseweb="menu"] li:hover,
[aria-selected="true"][role="option"] {
    background-color: var(--surface-2) !important;
}
/* Multiselect selected-value tags */
[data-baseweb="tag"] {
    background-color: var(--accent) !important;
    color: var(--accent-ink) !important;
}
[data-baseweb="tag"] span { color: var(--accent-ink) !important; }
[data-testid="stFileUploaderDropzone"] {
    background-color: var(--surface-2) !important;
    border-color: var(--border) !important;
}
[data-testid="stFileUploaderDropzone"] * {
    color: var(--ink) !important;
}
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stBaseButton-secondary"] {
    background-color: var(--surface) !important;
    color: var(--ink) !important;
    border: 1px solid var(--border) !important;
}

/* Top toolbar / header bar (was rendering white on the light base) */
[data-testid="stHeader"] {
    background-color: var(--bg) !important;
}
[data-testid="stToolbar"], [data-testid="stDecoration"] {
    background: transparent !important;
}
[data-testid="stHeader"] button, [data-testid="stHeader"] a, [data-testid="stHeader"] span {
    color: var(--ink) !important;
}
[data-testid="stExpander"] summary {
    background-color: var(--surface) !important;
    color: var(--ink) !important;
    border-color: var(--border) !important;
}
[data-testid="stExpander"] {
    border-color: var(--border) !important;
    background-color: var(--surface) !important;
}

/* Buttons */
.stButton button {
    background-color: var(--surface-2) !important;
    color: var(--ink) !important;
    border-color: var(--border) !important;
    transition: transform 160ms ease-out, background 160ms ease-out, border 160ms ease-out;
}
.stButton button:hover {
    border-color: var(--accent) !important;
}
.stButton button:active {
    transform: scale(0.98);
}
.stButton button[kind="primary"] {
    background-color: var(--accent) !important;
    color: var(--accent-ink) !important;
    border-color: var(--accent) !important;
}
@media (prefers-reduced-motion: reduce) {
    .stButton button {
        transition: none;
    }
    .stButton button:active {
        transform: none;
    }
}

/* Tabs Segmented Control */
[data-testid="stTabs"] button {
    font-family: var(--font-ui) !important;
    color: var(--muted) !important;
    border-bottom-color: var(--border) !important;
    background-color: transparent !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
}
[data-testid="stTabs"] button:hover {
    color: var(--ink) !important;
}

/* DataFrames */
.stDataFrame {
    font-variant-numeric: tabular-nums;
    font-family: var(--font-mono) !important;
}
[data-testid="stDataFrame"] * {
    color: var(--ink) !important;
    background-color: var(--surface) !important;
    border-color: var(--border) !important;
}

/* Custom HTML Tables */
.custom-table {
    width: 100%;
    border-collapse: collapse;
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    font-size: 0.9rem;
    margin-bottom: 1rem;
    text-align: right;
}
.custom-table th, .custom-table td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
    color: var(--ink);
}
.custom-table th:first-child, .custom-table td:first-child {
    text-align: left;
    font-family: var(--font-ui);
}
.custom-table th {
    font-weight: 600;
    color: var(--muted);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 2px solid var(--border);
}

/* CUSTOM COMPONENTS */

/* Hero Band */
.hero-band {
    padding: 1.5rem 0 2.25rem 0;
    margin-bottom: 2.25rem;
    border-bottom: 1px solid var(--border);
}
.hero-eyebrow {
    font-family: var(--font-ui);
    font-size: 0.72rem;
    color: var(--faint) !important;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    margin-bottom: 0.9rem;
}
.hero-title {
    font-family: var(--font-display) !important;
    font-size: 4.2rem;
    font-weight: 600;
    margin: 0;
    line-height: 1.0;
    letter-spacing: -0.028em;
    color: var(--ink) !important;
}
.hero-metrics {
    display: flex;
    gap: 32px;
    margin-top: 1.5rem;
}
.hero-metric {
    display: flex;
    flex-direction: column;
}
.hero-metric-label {
    font-size: 0.8rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.hero-metric-val {
    font-size: 1.5rem;
    font-weight: 500;
    color: var(--ink) !important;
    font-family: var(--font-mono);
}

/* Verdict Scorecard */
.scorecard-strip {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 16px;
    margin-bottom: 2rem;
}
.sc-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 18px 18px 16px;
}
.sc-title {
    font-family: var(--font-ui);
    font-size: 0.7rem;
    color: var(--faint) !important;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 12px;
}
.sc-body {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 12px;
}
.sc-score {
    font-family: var(--font-mono);
    font-weight: 500;
    font-size: 1.25rem;
    color: var(--ink) !important;
}
.sc-bar-bg {
    height: 3px;
    background: var(--surface-2);
    border-radius: 0;
    overflow: hidden;
}
.sc-bar-fill {
    height: 100%;
    border-radius: 0;
    background: var(--accent);
}

/* DCF Cards */
.dcf-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 2rem;
}
.dcf-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 22px 22px 20px;
}
.dcf-label {
    font-family: var(--font-ui);
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--faint) !important;
    margin-bottom: 12px;
    font-weight: 600;
}
.dcf-val {
    font-family: var(--font-mono);
    font-size: 2.1rem;
    font-weight: 500;
    color: var(--ink) !important;
    letter-spacing: -0.01em;
}
/* Hero moment: intrinsic value is the one number that drives the call */
.dcf-card-hero {
    border-top: 2px solid var(--accent);
}
.dcf-card-hero .dcf-label { color: var(--muted) !important; }
.dcf-card-hero .dcf-val {
    font-size: 2.7rem;
    font-weight: 600;
    color: var(--accent) !important;
}
.dcf-sub {
    font-size: 0.9rem;
    margin-top: 4px;
}

/* Verdict pills */
.verdict-pill {
    display: inline-block;
    padding: 3px 11px;
    border-radius: 2px;
    font-family: var(--font-ui);
    font-weight: 600;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    background: var(--surface-2);
    color: var(--ink);
}
.verdict-buy   { background: var(--pos); color: var(--accent-ink); }
.verdict-wait  { background: var(--warn); color: var(--accent-ink); }
.verdict-watch { background: var(--info); color: var(--accent-ink); }
.verdict-skip  { background: var(--neg); color: var(--accent-ink); }

/* Check rows */
.check-row-container {
    display: flex;
    align-items: baseline;
    gap: 12px;
    padding: 8px 0;
}
.check-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}
.check-dot-pass { background-color: var(--pos); }
.check-dot-fail { background-color: var(--neg); }
.check-dot-na { background-color: transparent; border: 1.5px solid var(--faint); opacity: 0.5; }

.framework-note {
    font-size: 0.85rem;
    color: var(--muted);
    padding: 8px 12px;
    background: var(--surface-2);
    border-radius: 8px;
    margin-top: 6px;
    max-width: 70ch;
}

/* Dividers */
hr {
    border-bottom-color: var(--border) !important;
}

/* Running spinners (st.status + st.spinner) — default icon is invisible on the
   dark background; brass reads in both themes. */
[data-testid="stExpanderIconSpinner"],
[data-testid="stExpanderIconSpinner"] svg,
[data-testid="stSpinnerIcon"],
[data-testid="stSpinner"] svg,
[data-testid="stSpinner"] i {
    color: var(--accent) !important;
    fill: var(--accent) !important;
    border-top-color: var(--accent) !important;
}
/* Streamlit Spinner Visibility Fix */
.stSpinner > div > div {
    border-top-color: var(--accent) !important;
    border-right-color: var(--surface-2) !important;
    border-bottom-color: var(--surface-2) !important;
    border-left-color: var(--surface-2) !important;
}
[data-testid="stStatusWidget"] [data-testid="stSpinner"] > div > div {
    border-top-color: var(--accent) !important;
    border-right-color: var(--surface-2) !important;
    border-bottom-color: var(--surface-2) !important;
    border-left-color: var(--surface-2) !important;
}

/* Custom Alert Theme (Calm & Semantic) */
/* Approach: Single uniform calm style targeting standard attributes */
/* Leaves the existing SVG icon to carry the semantic meaning (info/warn/error) */
[data-testid="stAlert"], [data-testid="stAlertContainer"] {
    background-color: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--ink) !important;
}
[data-testid="stAlert"] p, [data-testid="stAlert"] span, [data-testid="stAlert"] div {
    color: var(--ink) !important;
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


def _render_check(check_id: str, check_dict: dict, ticker: str = None):
    """Render a single check row using the 3-part explanation card."""
    from reports.explain import build_check_explanation
    expl = build_check_explanation(check_id, check_dict)

    if expl["status"] == "na":
        dot_class = "check-dot-na"
        tag_pts = "not scored"
        title_opacity = "0.6"
    elif expl["status"] == "pass":
        dot_class = "check-dot-pass"
        tag_pts = "1 pt"
        title_opacity = "1"
    else:
        dot_class = "check-dot-fail"
        tag_pts = "0 pts"
        title_opacity = "1"

    proximity = check_dict.get("proximity")
    badge_html = ""
    if proximity is not None:
        if proximity >= 0.25:
            prox_color = "var(--pos)"
        elif proximity >= 0.10:
            prox_color = "var(--pos)"
        elif proximity >= 0:
            prox_color = "var(--warn)"
        elif proximity >= -0.10:
            prox_color = "orange"
        else:
            prox_color = "var(--neg)"
            
        prox_str = ("+∞" if proximity == float("inf")
                    else "-∞" if proximity == float("-inf")
                    else f"{proximity:+.2f}")
        badge_html = (
            f'<span style="margin-left: 8px; font-size: 0.75rem; padding: 2px 6px; '
            f'border-radius: 4px; background: {prox_color}; color: white; '
            f'font-weight: 600; opacity: 0.9;">'
            f'{prox_str}</span>'
        )

    prob_badge_html = ""
    if ticker and check_id in ("12_margin_of_safety", "1_deep_mos"):
        mc = st.session_state.get(f"mc_{ticker}")
        if mc and mc.get("applicable"):
            prob = mc.get("prob_intrinsic_gt_price")
            if prob is not None:
                prob_badge_html = (
                    f'<span style="margin-left: 8px; font-size: 0.75rem; padding: 2px 6px; '
                    f'border-radius: 4px; background: var(--surface-2); color: var(--ink); '
                    f'border: 1px solid var(--border); '
                    f'font-weight: 500;">'
                    f'P(intrinsic &gt; price) = {prob:.0%}</span>'
                )

    st.markdown(
        f'<div class="check-row-container">'
        f'<div class="check-dot {dot_class}"></div>'
        f'<div style="font-weight: 500; font-family: var(--font-ui); color: var(--ink); opacity: {title_opacity};">'
        f'{expl["title"]} {badge_html}{prob_badge_html}<span style="opacity:0.6; font-style:italic; font-weight:400; margin-left:6px;">— {tag_pts}</span></div>'
        f'</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div style="margin-left: 22px; margin-bottom: 16px;">', unsafe_allow_html=True)
    if expl["what_why"]:
        with st.expander("What this measures & why it matters", expanded=False):
            st.markdown(f'<div class="framework-note">{expl["what_why"]}</div>', unsafe_allow_html=True)
            
    if expl["finding"]:
        st.markdown(f"<div style='font-size:0.9rem; color:var(--ink); margin-bottom:4px;'><strong>This company:</strong> {expl['finding']}</div>", unsafe_allow_html=True)

    st.markdown(f"<div style='font-size:0.9rem; color:var(--ink);'><strong>Verdict:</strong> {expl['judgment']}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


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
    # Use the lens's actual max_score (exclude-from-denominator may have dropped
    # N/A checks); fall back to the static full count only if absent.
    full_max = _LENS_MAX_SCORES[lens_key]
    max_score = lens_results.get("max_score", full_max)
    excluded = full_max - max_score
    verdict = lens_results.get("verdict", "SKIP")
    reason = lens_results.get("reason", "")
    checks = lens_results.get("checks", {})
    ticker = financials["ticker"]

    # ---- Score header (custom brand card) ----
    _excl_note = (
        f"<div style='font-size:0.8rem; color:var(--faint); margin-top:6px;'>"
        f"{excluded} check{'s' if excluded != 1 else ''} N/A (excluded from {full_max})"
        f"</div>"
        if excluded > 0 else ""
    )
    st.markdown(
        f"<div style='"
        f"background:var(--surface); border:1px solid var(--border); border-radius:4px;"
        f"padding:18px 20px; margin-bottom:12px;'>"
        f"<div style='display:flex; align-items:center; gap:16px; flex-wrap:wrap;'>"
        f"<span style='font-family:var(--font-mono); font-size:1.6rem; color:var(--ink);'>{score}&thinsp;/&thinsp;{max_score}</span>"
        f"{_verdict_pill_html(verdict)}"
        f"</div>"
        f"<div style='font-size:0.9rem; color:var(--muted); margin-top:8px;'>{reason}</div>"
        f"<div style='font-size:0.82rem; color:var(--faint); margin-top:4px;'>Passed {score} of {max_score} applicable checks</div>"
        f"{_excl_note}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ---- Layer-C narrative (plain-English summary) ----
    from reports.explain import build_lens_narrative
    narrative = build_lens_narrative(
        _LENS_NAMES[lens_key], lens_results, ticker
    )
    st.markdown(
        f"<div style='"
        f"background:var(--surface-2); "
        f"border:1px solid var(--border); "
        f"border-radius:8px; "
        f"padding:14px 18px; "
        f"margin-top:4px; "
        f"font-size:0.92rem; "
        f"line-height:1.6; "
        f"color:var(--ink);"
        f"'>"
        f"<strong style='font-size:0.76rem; letter-spacing:0.08em; "
        f"color:var(--faint); text-transform:uppercase;'>In plain English</strong>"
        f"<br><br>{narrative}"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    # ---- Checks by part ----
    parts: dict[str, list] = {}
    for check_id, check_dict in checks.items():
        part = check_dict.get("part", "?")
        parts.setdefault(part, []).append((check_id, check_dict))

    for part_id in sorted(parts.keys()):
        part_checks = parts[part_id]
        # Part totals exclude N/A checks so passed/total reflects the denominator.
        passed_count = sum(1 for _, c in part_checks if c.get("applicable", True) and c["passed"])
        total_count = sum(1 for _, c in part_checks if c.get("applicable", True))
        na_count = len(part_checks) - total_count
        na_suffix = f" &nbsp;·&nbsp; {na_count} N/A" if na_count else ""
        st.markdown(f"**Part {part_id}** &nbsp; {passed_count}/{total_count} checks passed{na_suffix}")
        for check_id, check_dict in part_checks:
            _render_check(check_id, check_dict, ticker)

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
# ---------------------------------------------------------------------------
# Metric Lab Tab
# ---------------------------------------------------------------------------

def _render_metric_lab_tab(peer_opts: dict):
    import altair as alt
    import pandas as pd
    from analysis.metric_lab import evaluate_formula, list_variables
    
    st.header("🧪 Metric Lab")
    
    st.subheader("Part A: Price History")
    selected_price_labels = st.multiselect("Select Companies for Price Chart", options=list(peer_opts.keys()), key="ml_price_select")
    
    if selected_price_labels:
        dfs = []
        for label in selected_price_labels:
            tkr = peer_opts[label]
            df = _fetch_price_history(tkr)
            if not df.empty:
                df = df.copy()
                df["Ticker"] = tkr
                dfs.append(df)
        
        if dfs:
            merged_df = pd.concat(dfs, ignore_index=True)
            brush = alt.selection_interval(bind='scales', encodings=['x'])
            chart = alt.Chart(merged_df).mark_line().encode(
                x='Date:T',
                y='Close:Q',
                color='Ticker:N',
                tooltip=['Date', 'Close', 'Ticker']
            ).add_params(brush).properties(height=400)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.warning("No price history found for selected companies.")
            
    st.divider()
    
    st.subheader("Part B: Metric Builder")
    if "ml_graphs" not in st.session_state:
        st.session_state.ml_graphs = [{"id": 0, "formula": "", "tickers": []}]
        
    def add_graph():
        next_id = max([g["id"] for g in st.session_state.ml_graphs] + [-1]) + 1
        st.session_state.ml_graphs.append({"id": next_id, "formula": "", "tickers": []})
        
    def remove_graph(g_id):
        st.session_state.ml_graphs = [g for g in st.session_state.ml_graphs if g["id"] != g_id]
        if not st.session_state.ml_graphs:
            add_graph()

    for idx, graph_config in enumerate(st.session_state.ml_graphs):
        gid = graph_config["id"]
        with st.container(border=True):
            cols = st.columns([11, 1])
            with cols[0]:
                formula = st.text_input(f"Formula", value=graph_config["formula"], key=f"ml_form_{gid}")
                with st.expander("Help / Available Variables"):
                    st.write("**Examples:** `ccc`, `inventory/cogs`, `cogs[t-2]/sales`, `ccc*beta^2 + (inventory/cogs)^2`, `pe`, `(operating_profit+depreciation)/sales`, `debt/equity*100`")
                    if graph_config["tickers"]:
                        # Show tokens for the first selected ticker
                        tkr = peer_opts[graph_config["tickers"][0]]
                        grouped_tokens = list_variables(tkr)
                        st.write(f"Tokens available for {tkr}:")
                        for group_name, tokens in grouped_tokens.items():
                            st.markdown(f"**{group_name}**")
                            st.write(", ".join([f"`{t}`" for t in tokens]))
                    else:
                        st.write("Select a company below to see available tokens.")
                        
                tickers = st.multiselect(f"Companies", options=list(peer_opts.keys()), default=graph_config["tickers"], key=f"ml_tkrs_{gid}")
            with cols[1]:
                st.write("")
                st.write("")
                if st.button("✕", key=f"ml_rm_{gid}"):
                    remove_graph(gid)
                    st.rerun()
            
            # Save state
            graph_config["formula"] = formula
            graph_config["tickers"] = tickers
            
            if formula and tickers:
                series_data = []
                has_error = False
                for label in tickers:
                    tkr = peer_opts[label]
                    vars_dict = _build_variables(tkr)
                    if not vars_dict:
                        continue
                    try:
                        res_series = evaluate_formula(formula, vars_dict)
                        if not res_series.empty:
                            df = res_series.reset_index()
                            df.columns = ["Year", "Value"]
                            df["Ticker"] = tkr
                            series_data.append(df)
                    except ValueError as e:
                        has_error = True
                        st.warning(f"{tkr}: {str(e)}")
                
                if series_data and not has_error:
                    merged_df = pd.concat(series_data, ignore_index=True)
                    # Convert Year to integer so altair plots it nicely without commas
                    merged_df["Year"] = merged_df["Year"].astype(int)
                    chart = alt.Chart(merged_df).mark_line(point=True).encode(
                        x=alt.X('Year:O', axis=alt.Axis(format="d")),
                        y=alt.Y('Value:Q'),
                        color='Ticker:N',
                        tooltip=['Year', 'Value', 'Ticker']
                    ).properties(height=300)
                    st.altair_chart(chart, use_container_width=True)

    st.button("➕ Add another graph", on_click=add_graph)

# ---------------------------------------------------------------------------
# DCF tab
# ---------------------------------------------------------------------------

def _fmt_amount(v, currency: str, is_india: bool) -> str:
    """Banker-compact money: crore for India, B/M for everything else. Display only."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    if is_india:
        return f"{currency}{v / 1e7:,.0f} cr"   # 1 crore = 10,000,000
    a = abs(v)
    if a >= 1e9:
        return f"{currency}{v / 1e9:,.2f}B"
    if a >= 1e6:
        return f"{currency}{v / 1e6:,.1f}M"
    return f"{currency}{v:,.0f}"


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
    up_col = "var(--pos)" if upside > 0 else "var(--neg)"
    up_sgn = "+" if upside > 0 else ""
    st.markdown(
        f'<div class="dcf-grid">'
        f'<div class="dcf-card dcf-card-hero"><div class="dcf-label">Intrinsic Value</div><div class="dcf-val">{currency}{intrinsic:,.2f}</div></div>'
        f'<div class="dcf-card"><div class="dcf-label">Current Price</div><div class="dcf-val">{currency}{price:,.2f}</div></div>'
        f'<div class="dcf-card"><div class="dcf-label">Implied Upside</div><div class="dcf-val" style="color: {up_col};">{up_sgn}{upside:.1%}</div></div>'
        f'<div class="dcf-card"><div class="dcf-label">WACC</div><div class="dcf-val">{wacc:.2%}</div></div>'
        f'</div>',
        unsafe_allow_html=True
    )

    st.divider()

    # ---- Monte Carlo section ----
    st.markdown("### Monte Carlo Simulation")
    st.caption("A probabilistic band generated by perturbing key growth, margin, and risk assumptions over multiple deterministic engine runs.")
    
    # We use session state to remember if the user has triggered it, or just use a button
    if st.button("Run Monte Carlo (offline)", key=f"mc_btn_{ticker}"):
        with st.spinner("Simulating..."):
            from valuation.monte_carlo import run_monte_carlo
            macro = results.get("damodaran_data", {})
            rf = results.get("rf_rate", 0.04)
            qual = results.get("qualitative_results")
            
            mc = run_monte_carlo(
                dcf_results=dcf_results,
                financials=financials,
                macro_data=macro,
                risk_free_rate=rf,
                qualitative_results=qual,
                n=500  # fast offline default
            )
            
            st.session_state[f"mc_{ticker}"] = mc
            
            if not mc.get("applicable"):
                st.info(f"N/A — {mc.get('reason')}")
            else:
                p50 = mc["percentiles"]["p50"]
                prob = mc["prob_intrinsic_gt_price"]
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("P50 Intrinsic Value", f"{currency}{p50:,.2f}")
                col2.metric("P10 – P90 Band", f"{currency}{mc['percentiles']['p10']:,.2f} – {currency}{mc['percentiles']['p90']:,.2f}")
                
                prob_color = "normal" if prob >= 0.5 else "inverse"
                col3.metric("Prob(Intrinsic > Price)", f"{prob:.1%}", delta_color=prob_color)
                
                # Altair Chart
                import altair as alt
                import pandas as pd
                
                samples_df = pd.DataFrame({"Intrinsic Value": mc["samples"]})
                
                # Clip extreme outliers for plotting
                lower_bound = mc["percentiles"]["p10"] * 0.5
                upper_bound = mc["percentiles"]["p90"] * 1.5
                plot_df = samples_df[(samples_df["Intrinsic Value"] >= lower_bound) & (samples_df["Intrinsic Value"] <= upper_bound)]
                
                hist = alt.Chart(plot_df).mark_bar(opacity=0.7, color="#3b82f6").encode(
                    alt.X("Intrinsic Value:Q", bin=alt.Bin(maxbins=50), title=f"Intrinsic Value ({currency})"),
                    y='count()'
                )
                
                rule = alt.Chart(pd.DataFrame({'Price': [price]})).mark_rule(
                    color='red', strokeDash=[5, 5], size=2
                ).encode(x='Price:Q')
                
                text = alt.Chart(pd.DataFrame({'Price': [price]})).mark_text(
                    align='left', dx=5, dy=-120, color='red', text='Current Price'
                ).encode(x='Price:Q')
                
                st.altair_chart((hist + rule + text).properties(height=300), use_container_width=True)

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
        st.markdown(df.to_html(index=False, classes="custom-table", border=0), unsafe_allow_html=True)

    # ---- Projections table ----
    with st.expander("10-Year Cash Flow Projections", expanded=False):
        import pandas as pd
        projs = dcf_results.get("projections", [])
        if projs:
            rows = []
            for i, p in enumerate(projs[:10], start=1):
                rows.append({
                    "Year": p.get("year", i),
                    "Revenue": _fmt_amount(p.get('revenue', 0), currency, is_india),
                    "FCF": _fmt_amount(p.get('fcf', 0), currency, is_india),
                    "PV FCF": _fmt_amount(p.get('pv_fcf', 0), currency, is_india),
                    "Stage": p.get("stage", "—"),
                })
            df = pd.DataFrame(rows)
            st.markdown(df.to_html(index=False, classes="custom-table", border=0), unsafe_allow_html=True)
        else:
            st.caption("Projection data unavailable.")

    # ---- Quarterly Trend Chart ----
    q_data = financials.get("quarterly")
    if q_data and len(q_data.get("periods", [])) >= 4:
        st.markdown("### Quarterly Trend")
        import altair as alt
        import pandas as pd
        
        q_df = pd.DataFrame({
            "Quarter": q_data["periods"],
            "Revenue": q_data["revenue"],
            "OPM %": [opm if opm is not None else 0.0 for opm in q_data.get("opm", [])]
        })
        
        base_bar = alt.Chart(q_df).mark_bar(opacity=0.7, color="#8fa6c0").encode(
            x=alt.X("Quarter:N", sort=None, title="Quarter"),
            y=alt.Y("Revenue:Q", title=f"Revenue ({currency})")
        )

        line_overlay = alt.Chart(q_df).mark_line(color="#7fa987", point=True).encode(
            x=alt.X("Quarter:N", sort=None),
            y=alt.Y("OPM %:Q", title="OPM %", axis=alt.Axis(format='%'))
        )
        
        st.altair_chart(alt.layer(base_bar, line_overlay).resolve_scale(y='independent').properties(height=300), use_container_width=True)
        st.divider()

    # ---- Live sensitivity sliders (offline re-run via overrides hook) ----
    from valuation import dcf as _dcf

    base_ajp = dcf_results.get("ajp")
    base_wacc = float(dcf_results.get("wacc") or 0.10)
    base_intrinsic = dcf_results["intrinsic_value_per_share"]
    macro_data = results["damodaran_data"]
    rf = results["rf_rate"]
    qual = results["qualitative_results"]

    def _snap(v, lo, step, hi):
        """Snap v to the nearest grid point lo + n*step, clamped to [lo, hi]."""
        s = round(lo + round((v - lo) / step) * step, 6)
        return min(hi, max(lo, s))

    # Scenario-aware, grid-snapped base defaults (match what the engine used).
    # The 4th arg (hi) MUST equal each slider's max so a default can never fall
    # outside the slider range (e.g. ebit_margin_target < 0.02 -> StreamlitValueBelowMinError).
    d = {
        "g1":    _snap(_ajp_val(base_ajp, "stage1_revenue_growth",    0.10), 0.0,  0.01,   0.40),
        "ebit":  _snap(_ajp_val(base_ajp, "ebit_margin_target",        0.15), 0.02, 0.01,   0.50),
        "capex": _snap(_ajp_val(base_ajp, "capex_pct_sales_target",    0.05), 0.0,  0.01,   0.40),
        "tax":   _snap(_ajp_val(base_ajp, "tax_rate",                  0.25), 0.10, 0.01,   0.40),
        "wacc":  _snap(base_wacc,                                              0.06, 0.0025, 0.20),
        "wc":    max(-60, min(180, int(_ajp_val(base_ajp, "working_capital_days", 0)))),
        "exit":  _snap(_ajp_val(base_ajp, "exit_ev_ebitda_multiple",   10.0), 4.0,  0.5,    30.0),
    }
    _tg_max0 = max(0.0, round(d["wacc"] - 0.005, 4))
    d["tg"] = _snap(_ajp_val(base_ajp, "terminal_growth", 0.02), 0.0, 0.0025, _tg_max0)

    # Ticker-scoped keys so switching companies resets slider state automatically.
    # Init each key, and REPAIR any stale session value that's out of range (prevents
    # a previously-cached bad value from re-crashing the slider).
    _ranges = {"g1": (0.0, 0.40), "ebit": (0.02, 0.50), "capex": (0.0, 0.40),
               "tax": (0.10, 0.40), "wacc": (0.06, 0.20), "wc": (-60, 180),
               "exit": (4.0, 30.0), "tg": (0.0, _tg_max0)}
    sk = {name: f"sl_{name}_{ticker}" for name in d}
    for name, val in d.items():
        _lo, _hi = _ranges[name]
        cur = st.session_state.get(sk[name])
        if cur is None or not (_lo <= cur <= _hi):
            st.session_state[sk[name]] = val

    st.divider()
    st.markdown("### Sensitivity")
    with st.expander(
        "Live Sensitivity (what-if) \u2014 adjust assumptions, value updates live",
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
        st.markdown("### Charts")

        # Theme-aware colors for Altair
        c_bg   = "#161513" if theme == "dark" else "transparent"
        c_text = "#b3ac9e" if theme == "dark" else "#6b665b"
        c_grid = "#38342e" if theme == "dark" else "#ddd8cd"
        c_act  = "#b3ac9e" if theme == "dark" else "#6b665b"
        c_fcst = "#c2a063" if theme == "dark" else "#9c7c43"
        c_neg  = "#c47a72" if theme == "dark" else "#9a4a44"

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
            ax_spec = alt.Axis(labelColor=c_text, titleColor=c_text, gridColor=c_grid, domainColor=c_grid, tickColor=c_grid)
            return (
                alt.Chart(df).mark_bar().encode(
                    x=alt.X("Year:N", sort=years, title=None, axis=ax_spec),
                    y=alt.Y("Value:Q", title=f"{currency} mm", axis=ax_spec),
                    color=alt.Color("Phase:N", scale=alt.Scale(
                        domain=["Actual", "Forecast"],
                        range=[c_act, c_fcst]), legend=alt.Legend(labelColor=c_text, titleColor=c_text)),
                    tooltip=["Year", "Phase",
                             alt.Tooltip("Value:Q", format=",.0f")],
                ).properties(height=220, title=alt.TitleParams(text=title, color=c_text), background=c_bg)
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
            st.caption(f"History vs Sidwell\u2019s forecast (highlighted). {currency} mm.")

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
                    ax_spec = alt.Axis(labelColor=c_text, titleColor=c_text, gridColor=c_grid, domainColor=c_grid, tickColor=c_grid)
                    line = (alt.Chart(dfc).mark_line(color=c_fcst, point=True).encode(
                                x=alt.X("Driver:Q", title=data["label"], scale=alt.Scale(zero=False), axis=ax_spec),
                                y=alt.Y("Intrinsic:Q", title=f"Intrinsic ({currency})", axis=ax_spec),
                                tooltip=[alt.Tooltip("Driver:Q", format=".4f"),
                                         alt.Tooltip("Intrinsic:Q", format=",.2f")]))
                    rule = (alt.Chart(pd.DataFrame({"price": [price]}))
                            .mark_rule(color=c_neg, strokeDash=[4, 4]).encode(y="price:Q"))
                    st.altair_chart((line + rule).properties(background=c_bg), width="stretch")
                    st.caption("Red dashed line = current price. Each point re-runs the engine (offline).")

    st.divider()
    st.markdown("### Comps & Football Field")
    with st.expander("Comparable companies (you choose the peers)", expanded=False):
        st.caption("Pick 2\u20135 peer companies \u2014 type a name and choose from the dropdown.")
        _opts = _peer_options()
        selected = st.multiselect(
            "Peers",
            options=list(_opts.keys()),
            max_selections=5,
            key=f"comps_ms_{ticker}",
            placeholder="Type a company name and pick from the list\u2026",
        )
        from valuation.comps import run_comps_valuation
        if st.button("Run comps", key=f"comps_btn_{ticker}"):
            tickers = [_opts[s] for s in selected]
            if len(tickers) < 2:
                st.warning("Pick at least 2 peers.")
            else:
                with st.spinner("Fetching peers and computing multiples\u2026"):
                    try:
                        st.session_state[f"comps_data_{ticker}"] = run_comps_valuation(financials, tickers[:5])
                    except Exception as e:
                        st.session_state[f"comps_data_{ticker}"] = {"error": f"Comps failed: {e}"}

        comps = st.session_state.get(f"comps_data_{ticker}")
        if comps:
            if comps.get("error"):
                st.warning(comps["error"])
            else:
                pm = comps.get("peer_multiples", [])
                if pm:
                    df = pd.DataFrame([{
                        "Peer": r.get("ticker"),
                        "EV/EBITDA": r.get("ev_ebitda"),
                        "EV/Sales": r.get("ev_sales"),
                        "P/E": r.get("pe"),
                    } for r in pm])
                    st.markdown(df.to_html(index=False, classes="custom-table", border=0), unsafe_allow_html=True)

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
                rows = []

                # DCF bear/bull via WACC ±1pp (offline re-run of the engine)
                dcf_lo = dcf_hi = intrinsic
                try:
                    _hi = _dcf.run_dcf_valuation(financials, macro_data, rf, qual,
                            overrides={"wacc_override": max(0.03, round(base_wacc - 0.01, 4))})["intrinsic_value_per_share"]
                    _lo = _dcf.run_dcf_valuation(financials, macro_data, rf, qual,
                            overrides={"wacc_override": round(base_wacc + 0.01, 4)})["intrinsic_value_per_share"]
                    dcf_lo, dcf_hi = min(_lo, _hi), max(_lo, _hi)
                except Exception:
                    pass
                rows.append({"Method": "DCF (WACC ±1%)", "low": dcf_lo, "high": dcf_hi, "mid": intrinsic})

                ir  = comps.get("implied_ranges", {}) or {}
                imp = comps.get("implied_per_share", {}) or {}
                for lbl, key in [("Comps EV/EBITDA", "ev_ebitda"), ("Comps EV/Sales", "ev_sales"), ("Comps P/E", "pe")]:
                    rng = ir.get(key)
                    if rng and rng.get("med") is not None:
                        lo = rng["low"]  if rng.get("low")  is not None else rng["med"]
                        hi = rng["high"] if rng.get("high") is not None else rng["med"]
                        rows.append({"Method": lbl, "low": min(lo, hi), "high": max(lo, hi), "mid": rng["med"]})
                    elif imp.get(key) is not None:          # fallback: cached result w/o ranges -> point
                        v = imp[key]
                        rows.append({"Method": lbl, "low": v, "high": v, "mid": v})

                # Incoherence flag: if the comps method medians span > 2x, peers likely aren't comparable
                _cmeds = [r["mid"] for r in rows if r["Method"].startswith("Comps") and r["mid"]]
                if len(_cmeds) >= 2 and min(_cmeds) > 0 and (max(_cmeds) / min(_cmeds)) > 2.0:
                    st.caption(f"⚠️ Comps span {max(_cmeds)/min(_cmeds):.1f}× — peers likely aren't comparable for "
                               f"this company (common for high-growth names); weight the DCF more than comps.")

                dff = pd.DataFrame(rows)
                order = list(dff["Method"])
                bars = alt.Chart(dff).mark_bar(height=14, color=c_act).encode(
                    x=alt.X("low:Q", title=f"Value per share ({currency})", axis=alt.Axis(labelColor=c_text, titleColor=c_text, gridColor=c_grid, domainColor=c_grid, tickColor=c_grid)), x2="high:Q",
                    y=alt.Y("Method:N", sort=order, title=None, axis=alt.Axis(labelColor=c_text, titleColor=c_text, gridColor=c_grid, domainColor=c_grid, tickColor=c_grid)))
                pts = alt.Chart(dff).mark_point(size=90, filled=True, color=c_fcst).encode(
                    x="mid:Q", y=alt.Y("Method:N", sort=order),
                    tooltip=["Method", alt.Tooltip("mid:Q", format=",.0f")])
                rule = alt.Chart(pd.DataFrame({"price": [price]})).mark_rule(
                    color=c_neg, strokeDash=[4, 4]).encode(x="price:Q")
                st.altair_chart((bars + pts + rule).properties(height=28 * len(rows) + 40, background=c_bg),
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
    
    col_t, col_r = st.columns(2)
    with col_t:
        st.radio("Theme", ["light", "dark"], horizontal=True, key="theme", label_visibility="collapsed")
    with col_r:
        if st.button("Refresh data", help="Clear cache and re-run pipeline (ignores 24h cache)", use_container_width=True):
            st.cache_data.clear()
            st.session_state.pop("_pl_key", None)
            st.session_state.pop("_pl_result", None)
            st.rerun()
            
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

        # Theme the searchbox iframe (CSS can't reach it) via style_overrides.
        _d = theme == "dark"
        _c = {
            "bg":     "#1a1815" if _d else "#fcfbf8",
            "surf":   "#1f1d1a" if _d else "#fcfbf8",
            "border": "#38342e" if _d else "#d3cdbf",
            "ink":    "#ece7dd" if _d else "#1a1815",
            "muted":  "#b3ac9e" if _d else "#6b665b",
            "hover":  "#2a2723" if _d else "#eae7df",
        }
        _sb_styles = {
            # wrapper bg kills the white label band (iframe used config's light theme)
            "wrapper":  {"backgroundColor": _c["surf"]},
            "clear":    {"fill": _c["muted"]},
            "dropdown": {"fill": _c["muted"]},
            "searchbox": {
                "control":     {"backgroundColor": _c["bg"], "borderColor": _c["border"], "color": _c["ink"]},
                "input":       {"color": _c["ink"]},
                "placeholder": {"color": _c["muted"]},
                "singleValue": {"color": _c["ink"]},
                "menu":        {"backgroundColor": _c["surf"], "borderColor": _c["border"]},
                "menuList":    {"backgroundColor": _c["surf"]},
                "option":      {"color": _c["ink"], "backgroundColor": _c["surf"]},
            },
        }
        # Render the label ourselves (the in-iframe label renders dark-on-dark
        # because the component pulls its text color from config.toml's light theme).
        st.markdown(
            '<div style="font-size:0.8rem;color:var(--muted);margin-bottom:0.3rem;'
            'font-weight:500;">Company Name or Ticker</div>',
            unsafe_allow_html=True,
        )
        ticker_input = st_searchbox(
            _cached_search,
            key="ticker_input",
            placeholder="Search company or ticker...",
            label="",
            style_overrides=_sb_styles,
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

    # ---- Lens Selection ----
    _lens_options = {"buffett": "Buffett", "marks": "Howard Marks", "kkr": "KKR", "blackstone": "Blackstone", "apollo": "Apollo"}
    _all_lenses = list(_lens_options.keys())
    
    st.multiselect(
        "Lenses to run",
        options=_all_lenses,
        default=st.session_state.get("selected_lenses", _all_lenses),
        format_func=lambda x: _lens_options.get(x, x),
        key="_lens_ui"
    )
    selected_lenses = st.session_state.get("_lens_ui", _all_lenses)
    if not selected_lenses:
        selected_lenses = _all_lenses
    st.session_state["selected_lenses"] = selected_lenses

    research_files = st.file_uploader(
        "Equity research report (optional, max 2 PDFs)",
        type=["pdf"],
        accept_multiple_files=True,
        key="research_upload",
        help=(
            "Sell-side research. If provided, Sidwell uses ONLY the latest concall + "
            "your report(s) for the qualitative read; otherwise it uses all discovered filings."
        ),
    )
    if research_files and len(research_files) > 2:
        st.warning("Max 2 research reports — using the first 2.")
        research_files = research_files[:2]
    research_tuple = tuple((f.name, f.getvalue()) for f in (research_files or []))
    if research_tuple:
        st.caption(
            f"{len(research_tuple)} research report(s) loaded "
            "\u2014 will use latest concall + your report(s)."
        )

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

if not ticker_input:
    st.markdown(
        '<div class="hero-band">'
        '<div class="hero-eyebrow">Sidwell \u2014 Personal investment decision engine</div>'
        '<h2 class="hero-title">Investment Analysis</h2>'
        '</div>',
        unsafe_allow_html=True
    )
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

    if not research_tuple:
        from data.research_provider import get_research_for_ticker
        _lib = get_research_for_ticker(ticker)
        if _lib:
            research_tuple = tuple((r["filename"], r["bytes"]) for r in _lib)
            st.caption(f"📚 Auto-loaded {len(research_tuple)} research report(s) from your local library "
                       f"for {ticker}.")

    # ---- Run pipeline ----
    import value
    from value import analyze

    fun_fact = _get_fun_fact(ticker)

    status_ui = st.status(f"Step 1/5 — starting analysis for **{ticker}**…", expanded=True)
    status_ui.markdown(f"**Meanwhile, read this:**\n\n{fun_fact}")

    def _on_progress(step, total, label):
        status_ui.update(label=f"Step {step}/{total} — {label}")

    def _on_stream(chars):
        # Animates the Step 2 label as DeepSeek streams; the websocket traffic this
        # generates keeps the connection alive through the multi-minute call.
        status_ui.update(
            label=f"Step 2/5 — Reading filings & qualitative signals… "
                  f"{chars/1000:.1f}k chars analyzed"
        )

    # Run analyze() directly (NOT through the @st.cache_data wrapper) so the stage
    # callbacks flush to the UI live. The cached wrapper both skipped emits on a
    # cache hit and buffered UI updates on a miss, so stages never animated. A
    # session-state cache keeps repeat runs of the same ticker instant; the backend's
    # own file caches (prices 24h, qualitative 30d) still prevent re-scrape / re-LLM.
    _pl_key = (ticker, research_tuple, tuple(sorted(selected_lenses)))
    if st.session_state.get("_pl_key") == _pl_key and st.session_state.get("_pl_result") is not None:
        results = st.session_state["_pl_result"]
        status_ui.update(label=f"Analysis complete — {ticker}", state="complete", expanded=False)
    else:
        value.set_progress_callback(_on_progress)
        value.set_stream_callback(_on_stream)
        try:
            research_docs = [{"filename": n, "bytes": b} for n, b in research_tuple] or None
            results = analyze(ticker, lenses_to_run=selected_lenses, research_docs=research_docs)
            st.session_state["_pl_key"] = _pl_key
            st.session_state["_pl_result"] = results
            status_ui.update(label=f"Analysis complete — {ticker}", state="complete", expanded=False)
        except ValueError as e:
            status_ui.update(label="Analysis failed", state="error", expanded=True)
            err_msg = str(e)
            if "appears to be cyclical" in err_msg:
                st.info(f"**Model Limitation:**\n\n{err_msg}")
            elif "non-positive intrinsic value" in err_msg:
                st.error(f"DCF model failed for {ticker} — non-positive intrinsic. See logs.")
            else:
                st.error(f"**Data error:** {err_msg}")
            st.stop()
        except Exception as e:
            status_ui.update(label="Pipeline failed", state="error", expanded=True)
            st.error(f"**Pipeline failed:** {e}")
            logger.exception(f"Pipeline error for {ticker}")
            st.stop()
        finally:
            value.set_progress_callback(None)
            value.set_stream_callback(None)

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
    buffett_results = results.get("buffett_results")
    marks_results = results.get("marks_results")
    kkr_results = results.get("kkr_results")
    blackstone_results = results.get("blackstone_results")
    apollo_results = results.get("apollo_results")

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

    # ---- Custom Header & Scorecard ----
    is_india_hero = ticker.endswith(".NS") or ticker.endswith(".BO")
    cur_str = "₹" if is_india_hero else "$"
    price_val = dcf_results["current_price"]
    mcap_val = financials.get("market_cap", 0) / 1e9

    st.markdown(
        f'<div class="hero-band">'
        f'<div class="hero-eyebrow">Sidwell \u2014 Personal investment decision engine</div>'
        f'<h2 class="hero-title">{financials.get("ticker")}</h2>'
        f'<div class="hero-metrics">'
        f'<div class="hero-metric"><span class="hero-metric-label">Current Price</span><span class="hero-metric-val">{cur_str}{price_val:,.2f}</span></div>'
        f'<div class="hero-metric"><span class="hero-metric-label">Market Cap</span><span class="hero-metric-val">{cur_str}{mcap_val:,.1f}B</span></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    intrinsic_val = dcf_results.get("intrinsic_value_per_share", 0)
    upside_val = (intrinsic_val / price_val - 1) * 100 if price_val > 0 else 0
    dcf_verdict = "BUY" if upside_val > 15 else "WAIT" if upside_val > -15 else "SKIP"
    up_css = "var(--pos)" if upside_val > 0 else "var(--neg)"
    up_sign = "+" if upside_val > 0 else ""

    # Scorecard = the five investor lenses only. DCF is a valuation input, not a
    # standalone recommendation, so it is shown in its own tab, not as a verdict card.
    sc_html = '<div class="scorecard-strip">'

    for name, res, key in [
        ("Buffett", buffett_results, "buffett"),
        ("Marks", marks_results, "marks"),
        ("KKR", kkr_results, "kkr"),
        ("Blackstone", blackstone_results, "blackstone"),
        ("Apollo", apollo_results, "apollo")
    ]:
        if res:
            sc = res.get("score", 0)
            mx = _LENS_MAX_SCORES[key]
            vd = res.get("verdict", "SKIP")
            pct = (sc / mx) * 100
            bar_color = "var(--pos)" if vd == "BUY" else "var(--info)" if vd == "WATCH" else "var(--warn)" if vd == "WAIT" else "var(--neg)"
            sc_html += (
                f'<div class="sc-card">'
                f'<div class="sc-title">{name}</div>'
                f'<div class="sc-body">'
                f'<span class="sc-score">{sc}/{mx}</span>'
                f'{_verdict_pill_html(vd)}'
                f'</div>'
                f'<div class="sc-bar-bg"><div class="sc-bar-fill" style="width: {pct}%; background: {bar_color};"></div></div>'
                f'</div>'
            )
        else:
            sc_html += (
                f'<div class="sc-card">'
                f'<div class="sc-title">{name}</div>'
                f'<div class="sc-body"><span class="sc-score">-/-</span>{_verdict_pill_html("SKIP")}</div>'
                f'<div class="sc-bar-bg"></div>'
                f'</div>'
            )
    sc_html += '</div>'
    st.markdown(sc_html, unsafe_allow_html=True)

    # ---- Tabs ----
    tab_labels = ["DCF Valuation"]
    lens_names = {"buffett": "Buffett", "marks": "Marks", "kkr": "KKR", "blackstone": "Blackstone", "apollo": "Apollo"}
    
    active_lenses = [k for k in ["buffett", "marks", "kkr", "blackstone", "apollo"] if k in selected_lenses]
    
    for l_key in active_lenses:
        tab_labels.append(lens_names[l_key])
        
    tab_labels.append("🧪 Metric Lab")
    
    tabs = st.tabs(tab_labels)
    
    with tabs[0]:
        _render_dcf_tab(results)

    tab_idx = 1
    if "buffett" in active_lenses:
        with tabs[tab_idx]:
            _render_lens_tab(buffett_results, "buffett", financials, dcf_results)
        tab_idx += 1

    if "marks" in active_lenses:
        with tabs[tab_idx]:
            _render_lens_tab(marks_results, "marks", financials, dcf_results)
        tab_idx += 1

    if "kkr" in active_lenses:
        with tabs[tab_idx]:
            _render_lens_tab(kkr_results, "kkr", financials, dcf_results)
        tab_idx += 1

    if "blackstone" in active_lenses:
        with tabs[tab_idx]:
            _render_lens_tab(blackstone_results, "blackstone", financials, dcf_results)
        tab_idx += 1

    if "apollo" in active_lenses:
        with tabs[tab_idx]:
            _render_lens_tab(apollo_results, "apollo", financials, dcf_results)
        tab_idx += 1

    with tabs[tab_idx]:
        _render_metric_lab_tab(_peer_options())
