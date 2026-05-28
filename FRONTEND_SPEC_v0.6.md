# Sidwell v0.6 — Frontend Specification (Stage 1)

This document specifies the v0.6 frontend layer of Sidwell. It is the product brief — what the application looks like, how the user interacts with it, what the deliverables are. It is NOT the implementation plan (that's Stage 2, written separately as `ANTIGRAVITY_PROMPT_v0.6.md` based on this spec). Stage 1 codifies decisions; Stage 2 converts them to code.

---

## 1. Vision

Sidwell v0.6 transforms the existing CLI tool into a **deployable web application** that any reviewer — interviewer, hiring manager, fellow analyst — can open in a browser and use to value a public company through 1–5 investor lenses.

The v0.6 frontend is the user's **interview portfolio piece**. Design quality, clarity of analytical reasoning, and shareability are first-class concerns alongside functional correctness. A reviewer who has never seen Sidwell before should be able to:

1. Open a public URL
2. Type a ticker
3. Pick lenses
4. See a complete valuation + lens analysis within ~30–60 seconds
5. Download a PDF of any lens or an Excel of the DCF
6. Understand exactly why each lens reached its verdict — not just the score, but which specific checks failed and what the framework says about why those checks matter

What v0.6 is NOT:
- A real-time market dashboard
- A portfolio management system
- A multi-ticker scanner / screener
- A multi-user product with authentication
- A chatbot or conversational interface
- A mobile-optimized app

What v0.6 IS:
- A single-page desktop web app
- A polished, reviewer-grade analytical artifact
- A demonstrable showcase of valuation + investor-framework thinking
- A locally runnable Python tool (`streamlit run app.py`)
- A free-hosted public URL on Streamlit Community Cloud

---

## 2. Target users

**Primary (interview reviewers):** PE / IB hiring managers, banking analysts, finance recruiters. These users will spend 2–10 minutes exploring the tool. They care about:
- Visual polish and professionalism (signals attention to detail)
- Analytical depth (signals real understanding of valuation + lens frameworks)
- Traceability (every number sources its inputs; every verdict shows its math)
- Speed (they have many candidates to review)

**Secondary (the user himself):** for actual analytical use on real tickers across personal study, exam prep, real-world stock interest, and ongoing learning. The same UX serves both audiences — there is no "interview mode" toggle.

**Out of scope:** Anyone wanting to commercialize the tool, sell signals, manage portfolios, or perform real trading. Sidwell remains a personal-decision and learning vehicle.

---

## 3. Deployment surfaces

### 3.1 Streamlit Community Cloud (primary, production)
- Free tier (sufficient for personal portfolio use)
- Public URL of the form `https://<app-name>.streamlit.app`
- Auto-redeploys from the GitHub `main` branch on push
- Secrets (`GEMINI_API_KEY`, `FRED_API_KEY`) configured via the Streamlit Cloud dashboard, NOT committed to git
- Goes to sleep after inactivity; wakes on first request (~10–30 second cold start) — acceptable for an interview-portfolio piece

### 3.2 Local development (`streamlit run app.py`)
- Runs identically to the cloud deployment
- Reads secrets from `.streamlit/secrets.toml` (gitignored) OR from `.env` (existing v0.5 mechanism)
- All existing CLI behavior preserved — `python value.py ASIANPAINT.NS` continues to work unchanged

### 3.3 Implications for v0.6 architecture
- **No filesystem assumptions beyond the project root.** Cache directory must work on Linux (Streamlit Cloud) and Windows (user's local).
- **No background processes / scheduled tasks.** Streamlit Cloud doesn't support them.
- **No persistent server-side state.** Each analysis runs from the inputs; results are computed on demand. The existing `~/.sidwell/cache/` file cache remains for yfinance/FRED/Damodaran, but its contents are best-effort — a cold cache is acceptable.
- **No database.** File-cache only, same as v0.5.
- **All secrets via `st.secrets` with `.env` fallback** so local and cloud both work without code changes.

---

## 4. Information architecture

The application is a **single-page layout with tab navigation**. There is no multi-page routing. State (the analysis result) persists across tab switches within a single browser session.

### 4.1 Page header (persistent, always visible at top)
- **Wordmark:** "Sidwell" in a serif display face
- **Tagline:** "Personal investment-decision engine"
- **Version + GitHub link** on the right side, small text

### 4.2 Input panel (persistent, below header, collapses after first run)
- Ticker input (text field)
- Lens selector (5 checkboxes — see §7)
- "Analyze" primary button
- "Re-run" secondary button (visible only after first analysis)

### 4.3 Result tabs (appear only after first analysis completes)
1. **Summary** — at-a-glance verdicts, all selected lenses side-by-side
2. **DCF** — full valuation breakdown + Excel export
3. **Lens Detail** — per-lens deep dive + PDF export
4. **Qualitative** — Gemini-extracted soft signals + source documents
5. **About / Methodology** — what Sidwell is, links to framework specs in repo, version notes

Tabs are ordered for the reviewer's natural read: **headline → math → reasoning → context → meta**.

---

## 5. User flow

```
Reviewer arrives at public URL
       ↓
Sees Sidwell wordmark + tagline + ticker input
       ↓
Types ticker (default suggestion: ASIANPAINT.NS) and selects lenses
       ↓
Clicks "Analyze"
       ↓
Loading state: pipeline-step progress (Fetch → DCF → Qualitative → Lenses → Render)
       ↓ (15–60 seconds total depending on cache state)
       ↓
Result lands on Summary tab — sees verdicts + score bars + one-line reasons
       ↓
Optionally clicks DCF tab — sees full valuation with download Excel button
       ↓
Optionally clicks Lens Detail — picks any lens from dropdown, sees every check with pass/fail + framework reasoning, download lens PDF button
       ↓
Optionally clicks Qualitative — sees soft signals with source citations
       ↓
Optionally re-runs with different ticker / lens selection — Input panel re-expands
```

There is no save, no bookmark, no history. Each session is self-contained.

---

## 6. Detailed component spec

### 6.1 Tab 1 — Summary

The headline tab. Reviewer should grasp the analysis in 30 seconds.

**Layout (top to bottom):**

**Company headline block:**
- Company name (large)
- Ticker, sector, region flag (small)
- Current price | Intrinsic value (DCF) | Implied upside/downside %

**N-lens verdict cards:** one card per selected lens, displayed in a row (single row on desktop; wraps to grid on narrower screens). Card order is canonical: Buffett, Marks, KKR, Blackstone, Apollo.

Each card contains:
- Lens name (top)
- Verdict pill: BUY (green) / WAIT (amber) / WATCH (blue) / SKIP (red) — colors are status, not decoration
- Score with denominator (e.g., "9/14")
- Mini horizontal stacked-bar showing per-Part pass counts (e.g., Part A: ▰▰▰▱, Part B: ▰▰▰, ...)
- One-sentence reason (truncated; click "more" expands within the card)
- "View detail →" link that takes the user to Tab 3 with this lens preselected

**N-lens Synthesis panel** (only when N ≥ 2):
- Title: "Dual-Lens Synthesis" (N=2), "Triple" (N=3), "Quadruple" (N=4), "Quintuple" (N=5)
- The deterministic pattern-read paragraph (same logic as v0.5 render.py — adapted to handle N<5)
- Table view of the N lenses with: Lens | Score | Verdict | First-order driver

### 6.2 Tab 2 — DCF

This tab is where the reviewer judges "does this person actually know valuation."

**Layout (top to bottom):**

**Section 2.1 — WACC sourcing block**
- A 2-column table: Input | Value | Source
- Every input traced: risk-free rate (FRED series ID + date), ERP (Damodaran sheet + date), beta (industry mapping + unlevered/levered), cost of debt (with bound logic), tax rate (4-year effective), terminal growth (sector mapping)
- A "Why this WACC" paragraph below — 2–3 sentences explaining the company-specific reasoning (e.g., "Asian Paints' low D/E led to re-levering the industry beta to 0.96; terminal growth capped at 4.0% per India inflation floor.")

**Section 2.2 — 2-stage forecast tables**
- Stage 1 (years 1–5): high-growth projection
- Stage 2 (years 6–10): fade
- Side-by-side or stacked tables with revenue, growth rate, EBIT, NOPAT, D&A, capex, NWC change, FCF
- Years as columns, line items as rows (Excel-like)

**Section 2.3 — Terminal value calculation**
- Gordon-growth formula shown explicitly
- Inputs: year-10 FCF, terminal growth, WACC
- Result: terminal value, PV of terminal value, % of total EV

**Section 2.4 — Valuation bridge**
- A small visual bridge: PV of explicit FCFs + PV of fade FCFs + PV of terminal = EV
- EV → equity value (less net debt) → per-share intrinsic
- Final number: per-share intrinsic, with current price comparison

**Section 2.5 — Export**
- **"Download DCF as Excel" button**
- Excel structure (see §8.2)

### 6.3 Tab 3 — Lens Detail

The reviewer's deep-dive tab. They came from the Summary card and now want to see what every check evaluated to.

**Layout:**

**Lens picker** (top): dropdown with selected lenses; first one preselected (or whichever the user clicked from Summary)

**Headline block** (mirrors the Summary card but expanded):
- Lens name + verdict pill + score + one-paragraph reason
- The Phalippou meta-check status called out separately (e.g., "✅ Phalippou: 4 of 6 alpha levers passed" or "❌ Phalippou: only 3 of 6 — generic PE thesis")

**Pre-condition status block** (where applicable):
- Each lens that has pre-conditions shows them explicitly with PASS/FAIL
- E.g., for KKR: "Pre-condition 1 (Part A all 4 pass): ✅ — LBO viability confirmed"; "Pre-condition 2 (Check 18 Phalippou): ❌ — only 3 of 6 alpha levers"
- Failure of any pre-condition is the dominant reason; surface it clearly

**Check-by-check accordion** (organized by Part):
- Each Part shows: "Part A — Business Quality (3/4 passed)" as header
- Click to expand
- Each check inside the Part:
  - ✅ / ❌ status icon
  - Check name (bold)
  - "Threshold" line: what the test was
  - "Value" line: what the actual computed value was
  - "Detail" line: human-readable explanation
  - For FAILED checks, also show: the **framework's reasoning paragraph** (the "why this matters" prose from `frameworks/<lens>.md`)
- The reasoning paragraphs are loaded from the framework `.md` files at build time and embedded into the lens evaluator output dict (new field: `"framework_reasoning"`)

**Export block** (bottom):
- **"Download <Lens> as PDF" button**
- PDF structure (see §8.1)

### 6.4 Tab 4 — Qualitative

The transparency tab. Reviewer sees what the LLM extracted and where it came from.

**Layout:**

- Status banner at top: "Qualitative analysis available — N documents analyzed via gemini-3.5-flash" OR "Qualitative unavailable — <reason>; soft checks defaulted per framework rules"
- Documents-used list with filenames
- Each extracted field shown as a card: field name + verdict + reasoning + source citations
- Fields are grouped by which lens they primarily feed (e.g., "Buffett-relevant" / "Marks-relevant" / "KKR-relevant" / etc.) — the same field can appear under multiple groups if it feeds multiple lenses

If qualitative is unavailable, the entire tab still renders but with a clear notice and a list of which checks fell back to soft defaults (PASS, FAIL, or NEUTRAL per the framework's Determinism notes).

### 6.5 Tab 5 — About / Methodology

The "show your work" tab. Reviewer wants to confirm this isn't vapor.

- One-paragraph "What is Sidwell" intro (from PROJECT.md)
- Version badge: v0.6
- The 5 lens names with one-sentence summaries
- Links to the framework .md files in the GitHub repo (e.g., `frameworks/buffett.md`) — opens in new tab
- Architecture diagram (text or simple ascii — data flow from input → DCF + LLM → lenses → report)
- "Methodology integrity" callout: the rules (no predicted outputs, raise ValueError not assert, ddof=1, etc.) listed so the reviewer sees the rigor
- Link to BUILD_NOTES.md for version history
- GitHub link (the public repo)

---

## 7. Lens selection UX

The user can choose 1, 2, 3, 4, or 5 lenses per analysis.

**UI:**
- 5 checkboxes labeled with lens names, displayed horizontally in the input panel
- Each checkbox has a tiny tooltip on hover summarizing the lens (e.g., "Buffett — Quality compounder, durable moat, margin of safety")
- A "Select all / Clear all" toggle next to the checkboxes

**Default state on first visit:** all 5 selected. Reviewers see the full picture by default.

**Persistence:** the last selected set persists in `st.session_state` across re-runs within the same browser session. It does NOT persist across sessions (no localStorage / cookies — keep it simple).

**Validation:**
- At least 1 lens must be selected before "Analyze" is enabled
- If 0 selected, the Analyze button is disabled with a tooltip explaining

**Architectural impact:**
- `value.py` (and any equivalent backend function the Streamlit app calls) accepts a `lenses_to_run` parameter — a set/list of lens names
- The pipeline calls only the requested `evaluate_X_lens()` functions
- `reports/render.py` already supports optional kwargs (built that way in v0.5) — no further change needed
- The qualitative Gemini call still happens once regardless of how many lenses are selected (extracting fewer fields would save trivial tokens at the cost of complexity — not worth it)
- The N-lens Synthesis section adapts:
  - N=1: no synthesis section shown
  - N=2: "Dual-Lens Synthesis" header
  - N=3: "Triple-Lens Synthesis"
  - N=4: "Quadruple-Lens Synthesis"
  - N=5: "Quintuple-Lens Synthesis"
  - The pattern-read rules from v0.5 must handle partial sets gracefully (fall back to "Mixed signals" if no specific pattern matches the selected subset)

---

## 8. Export specifications

Two export types. Both are pure-local operations using Python libraries — **zero API tokens, zero external calls.**

### 8.1 PDF export (per-lens)

**Trigger:** "Download <Lens> as PDF" button on the Lens Detail tab.

**File name:** `{ticker}_{lens}_v0.6.pdf` (e.g., `ASIANPAINT.NS_KKR_v0.6.pdf`)

**Contents (single-PDF, multi-page):**
- Page 1 — Cover: Sidwell wordmark, ticker, company name, lens name, generation date, verdict pill (rendered as a stylized text block), score
- Page 2 — Executive summary: one-paragraph reason, pre-condition status, the deterministic pattern-read line for this lens vs. others (if N≥2 lenses were run)
- Pages 3+ — Check-by-check detail: every check organized by Part, with ✅/❌, threshold, value, detail line, and (for failed checks) the framework's reasoning paragraph
- Last page — Sources & methodology: the lens's source citations from the framework .md file, plus a note that the verdict was produced deterministically from the framework's scoring rules

**Implementation:**
- Source: extract the lens-specific section from the existing markdown report → standalone styled markdown → PDF
- Library: `weasyprint` (HTML/CSS to PDF, high-quality output, pure-Python, works on Windows + Linux)
- A minimal CSS stylesheet `pdf_style.css` defines the visual identity (typography, headers, page breaks, status colors)
- The CSS is shared across all 5 lens PDFs so they look like a coherent product family

**Quality bar:** the PDF must be print-quality — clean typography, no jagged edges, no broken layouts, no Streamlit chrome. Imagine a reviewer printing it out for a panel discussion.

### 8.2 Excel export (DCF)

**Trigger:** "Download DCF as Excel" button on the DCF tab.

**File name:** `{ticker}_DCF_v0.6.xlsx` (e.g., `ASIANPAINT.NS_DCF_v0.6.xlsx`)

**Contents (multi-sheet workbook):**

| Sheet | Purpose |
|---|---|
| `1_Cover` | Ticker, company, region, generation date, Sidwell version, link to GitHub repo |
| `2_Assumptions` | WACC components table (every input with source); revenue growth + terminal growth + tax rate + capex/sales + NWC/sales assumptions |
| `3_Stage1_Explicit` | Years 1–5 high-growth projection — revenue, growth %, EBIT, NOPAT, D&A, capex, NWC change, FCF — formulas live where possible (e.g., NOPAT = EBIT × (1 - t)) so the reviewer can audit |
| `4_Stage2_Fade` | Years 6–10 fade projection — same line items, with the growth rate fading linearly |
| `5_Terminal` | Year-10 FCF, terminal growth, WACC, terminal value formula, PV of terminal value |
| `6_Valuation_Bridge` | Sum of PV(stage 1 FCFs) + Sum of PV(stage 2 FCFs) + PV(terminal) = EV → less net debt → equity value → ÷ shares → intrinsic per share; current price comparison; implied upside/downside |
| `7_Sensitivity` | A 2D sensitivity table: rows = WACC bps moves (-100, -50, 0, +50, +100); columns = terminal growth moves (-100, -50, 0, +50, +100); cells = intrinsic per share — formulas live so the reviewer can drag the inputs |

**Implementation:**
- Library: `openpyxl` (formulas, formatting, multi-sheet, active maintenance)
- Cell formatting: currency cells use ₹ for India tickers (`.NS`/`.BO`), $ for US — same logic as the existing `format_currency` helper in render.py
- Formulas as much as possible (so the spreadsheet is editable, not a flat dump) — every number on Stage1/Stage2/Terminal/Bridge tabs is either a hardcoded assumption OR a formula referencing assumptions; nothing is a baked-in static number except actual fetched historicals
- Header rows are bold, frozen panes where appropriate
- Number formats: 2 decimal places for prices, 1 decimal for percentages, integer for years

**Quality bar:** a reviewer should be able to open the Excel, change the terminal growth from 4% to 5%, and see the intrinsic value recompute. This proves the model is a real model, not a screenshot dump.

### 8.3 What's NOT exported
- The full report markdown (the user can still grab it from the existing `output/` directory if they want)
- The qualitative LLM JSON (visible in Tab 4 but not separately downloadable in v0.6)
- The other 4 lens results when downloading 1 lens PDF (each PDF is single-lens; if user wants all 5, they download 5 PDFs)
- Anything as CSV / JSON / HTML (the two formats above cover the use case)

---

## 9. Design principles

The frontend must look like an analyst-grade artifact, not a hobbyist Streamlit demo.

### 9.1 Typography
- **Wordmark / display:** a serif face — IBM Plex Serif or similar (free Google Font, available via Streamlit theming)
- **Body:** a clean sans — Inter, IBM Plex Sans, or system default
- **Tabular numbers:** use a monospaced or tabular-number figure style for all numeric tables (so digits align across rows)
- **Heading hierarchy:** H1 (tab title) → H2 (section) → H3 (subsection); restrained sizing, plenty of vertical rhythm

### 9.2 Color palette
- **Background:** off-white (`#fafafa` or `#ffffff`)
- **Text primary:** deep charcoal (`#1a1a1a` or `#222`)
- **Text secondary:** mid-grey (`#666`)
- **Accent (one):** a navy or deep blue (`#1e3a5f` or similar) for links, buttons, the wordmark — used sparingly
- **Status colors (used only for verdicts and ✅/❌ icons):**
  - BUY / pass: forest green (`#2d7a3e`)
  - WAIT: amber (`#c08a1c`)
  - WATCH: blue (`#3b6ca8`)
  - SKIP / fail: red (`#a43030`)
- **NO decorative emoji.** Status icons (✅/❌) are OK because they convey information. Emoji as flair (🚀 📊 💰) is forbidden — looks juvenile.

### 9.3 Spacing & hierarchy
- Generous whitespace; the page should breathe
- Section dividers using thin horizontal rules, not heavy borders
- Tables use subtle alternating row tint or none; no heavy gridlines
- Cards use a 1px border or 0px border with shadow — pick one convention and stick to it

### 9.4 Iconography
- ✅ for pass, ❌ for fail (matches existing render.py convention)
- Tab icons can be small, monoline (NOT colored emoji)
- A flag emoji for the region indicator (🇮🇳 / 🇺🇸) is the ONE allowed emoji as it functions as a label, not decoration

### 9.5 Streamlit-specific theming
- Use `.streamlit/config.toml` to override default theme (set primary color, background, font)
- Custom CSS via `st.markdown(..., unsafe_allow_html=True)` ONLY for things the theme can't control (verdict pills, status icons inline in tables)
- Avoid Streamlit's default ballooning whitespace — set `max_width: 1100px` on the main container
- No sidebars (use header + tabs instead; sidebars feel app-y, the analytical artifact is centered)

---

## 10. Loading & error states

### 10.1 Loading state
The pipeline takes 15–60 seconds depending on cache state. A blank screen for that duration is unacceptable.

**Progress indicator:** a labeled progress bar with sub-steps:
1. "Fetching financials..." (~5–15s cold, instant cached)
2. "Computing DCF..." (~1s)
3. "Extracting qualitative signals..." (~3–10s; skipped if `GEMINI_API_KEY` not set, shown as "Qualitative skipped — soft signals will default")
4. "Evaluating lens(es)..." (~1s)
5. "Rendering report..." (~1s)

Each sub-step shows its own spinner; the overall progress bar advances proportionally. If a sub-step takes longer than 30 seconds, surface a "this is taking a while, possibly first-time cache build" message.

### 10.2 Error states
Failures should be **loud and informative**, not silent or generic.

| Failure | UI response |
|---|---|
| Invalid ticker (not found in yfinance) | Inline error below ticker field: "Ticker not found. Check spelling; Indian tickers end in `.NS` or `.BO`." |
| FRED API key missing | Block analysis with clear modal: "FRED_API_KEY is required for risk-free rate. Configure in `.streamlit/secrets.toml` (local) or Streamlit Cloud secrets dashboard." |
| FRED API error | Show error toast; offer "Retry" button; do NOT silently use a stale cache without warning |
| Damodaran data fetch error | Similar — toast + retry; if it fails twice, suggest using cached defaults and show which industry it fell back to |
| Gemini key missing | NOT an error — graceful degrade as today; show "Qualitative skipped" status in Tab 4 |
| Gemini rate-limit / error | Graceful degrade with a banner explaining what was missed; analysis continues with soft defaults |
| Internal exception | Show traceback to the user (with a "this is a bug, please report" framing) — do NOT swallow errors; this is a personal tool, debuggability beats prettiness |

### 10.3 What NOT to do
- **No fake / synthetic data ever shown to the user.** If data is missing, say so — don't paper over it.
- **No "approximate" or "estimated" labels on numbers that are computed exactly.** Every number is either real or absent.
- **No hidden retry loops that mask transient failures.** One automatic retry max; second failure surfaces to user.

---

## 11. Methodology integrity (preserved from v0.5)

The frontend introduces ZERO new ways to compromise analytical integrity. All of these v0.5 rules carry forward unchanged:

1. **No predicted outputs.** The frontend does not display a "predicted" or "expected" verdict next to the actual computed one. There is one verdict per lens per analysis, and it's whatever the math produces.
2. **No manual override of lens verdicts.** The user cannot click "I think this should be BUY" — verdicts are deterministic outputs of the framework.
3. **No "tune the thresholds" UI.** The framework specs in `frameworks/*.md` remain the source of truth. The Streamlit app does not expose check thresholds as user-configurable sliders. (A reviewer could fork the repo and change them, but that's a code change, not a UI feature.)
4. **`raise ValueError`, not `assert`.** All v0.5 backend code stays as-is. New frontend code follows the same convention.
5. **Statistical conventions (`ddof=1`, 4-year window, etc.)** unchanged.
6. **Snapshot test (`tests/test_snapshot.py`)** stays hand-edited. The frontend does not regenerate it.
7. **Frameworks immutable during implementation.** v0.6 does not edit `frameworks/*.md` files. If a check needs to expose its framework reasoning paragraph to the UI (per §6.3), that text is read from the framework file at runtime — not duplicated into the lens code.
8. **No new LLM calls in the deterministic pipeline.** The qualitative layer remains the only LLM touchpoint. No "summarize this lens for the UI" Gemini call. The one-sentence verdict reasons are already deterministically generated by `evaluate_X_lens()`.
9. **The 8 v0.5 BUILD_NOTES integrity rules in section 19** all carry forward.

---

## 12. What stays out of v0.6 (explicit non-goals)

These will tempt scope creep during the build. Reject them.

- ❌ User accounts / authentication
- ❌ Saving / loading past analyses
- ❌ Multi-ticker comparison view
- ❌ Watchlist / portfolio tracking
- ❌ Real-time price updates (one fetch per analysis is enough)
- ❌ News feed / sentiment scrolling
- ❌ Chatbot / Q&A interface ("Ask Sidwell about this stock")
- ❌ Mobile-optimized layout (desktop only)
- ❌ Multi-language support
- ❌ Dark mode
- ❌ Custom CSS animations / transitions (clean static layout is the look)
- ❌ Email / Slack / Telegram notifications
- ❌ n8n integration (deferred to v0.8 if pursued at all)
- ❌ Docker MCP catalog integration
- ❌ Private company path / CIM upload (deferred to v1.0)
- ❌ Distressed lens (deferred to v0.9)
- ❌ Full LBO model (deferred to v0.9)
- ❌ Custom lens authoring UI
- ❌ A/B testing different verdict thresholds
- ❌ Charting beyond what the DCF/Lens tables need (no candlestick charts, no price history graphs)
- ❌ Anything that requires server-side persistent state

If a feature is not explicitly listed in §6–§10, it's out of scope.

---

## 13. Open decisions for Stage 2

These are deliberately deferred to Stage 2 (`ANTIGRAVITY_PROMPT_v0.6.md`) where they become implementation details:

1. **Streamlit version pin.** Stage 2 should pin to a specific Streamlit version (likely 1.40+ for the latest tabs API) and document why.
2. **Where the Streamlit app lives.** Likely `app.py` at root, importing from existing `data/`, `valuation/`, `lenses/`, `reports/` modules. Alternative: a `frontend/` subdirectory. Stage 2 picks one.
3. **PDF library choice.** Spec recommends `weasyprint` but Stage 2 should verify it installs cleanly on Streamlit Cloud's Linux base image. Fallback: `pandoc` via subprocess, or `reportlab`.
4. **Excel formula vs. value.** Spec says "formulas where possible" — Stage 2 enumerates which cells are formulas vs. hardcoded values per sheet.
5. **Streamlit theming mechanism.** `.streamlit/config.toml` for global theme; inline `st.markdown` for verdict pills. Stage 2 decides whether to use a third-party theming library (e.g., `streamlit-extras`) or pure native + custom CSS.
6. **Caching strategy.** Streamlit's `@st.cache_data` for the pipeline functions, with TTL matching the existing file-cache TTLs. Stage 2 spells out the cache decorators.
7. **`requirements.txt` extension.** New deps: `streamlit`, `weasyprint` (or alternative), `openpyxl` (already used by pandas/yfinance internally — may not need explicit add). Stage 2 finalizes.
8. **Streamlit Community Cloud deployment configuration.** Stage 2 documents the `secrets.toml` template, the deployment YAML / settings, and the GitHub branch policy.
9. **PDF stylesheet (`pdf_style.css`).** Stage 2 writes it; this spec only says it must produce print-quality output.
10. **Excel sheet column widths, freeze panes, exact cell formatting.** Stage 2 picks the polish details.

---

## 14. Acceptance criteria (Stage 1 → Stage 2 handoff)

This spec is "approved for Stage 2" when:

- All 5 information-architecture tabs are scoped (§6.1–§6.5)
- Lens selection UX is defined (§7)
- Both export formats are specified (§8)
- Design principles are concrete enough to write CSS against (§9)
- Loading and error states are enumerated (§10)
- Non-goals are explicit (§12)
- Open Stage-2 decisions are listed so the implementation prompt knows what's still flexible (§13)

When Stage 2 is written (`ANTIGRAVITY_PROMPT_v0.6.md`), it will translate this spec into:
- File-by-file create/modify list
- Build sequence
- Per-component code-shape notes
- Test requirements (Streamlit apps have limited test affordances; we'll specify what we can test)
- Verification gates (manual: deploy works; download buttons produce valid files; loading state shows; etc.)
- Hard constraints carried forward from v0.5 methodology integrity

---

## 15. Success criteria for v0.6 ship

The v0.6 build is successful when ALL of these are true:

1. **Public URL works.** Anyone with the link can open the Sidwell app on Streamlit Community Cloud, type `ASIANPAINT.NS`, and see all 5 lens verdicts within 60 seconds (cold cache).
2. **Local run works.** `streamlit run app.py` starts the same app on `localhost:8501` for the user.
3. **Lens selection works.** Picking 1, 2, 3, 4, or 5 lenses produces correct N-lens output. The synthesis section adapts. No errors at any N.
4. **PDF download works.** From the Lens Detail tab, clicking "Download <Lens> as PDF" produces a valid, print-quality PDF that contains every check with its threshold, value, and (for failures) the framework reasoning.
5. **Excel download works.** From the DCF tab, clicking "Download DCF as Excel" produces a valid `.xlsx` with all 7 sheets, formulas intact, that a reviewer can edit (e.g., change terminal growth) and see the intrinsic value recompute.
6. **Methodology integrity intact.** All v0.5 tests still pass (`pytest tests/` — 107+ green). No new way to manually override a verdict was introduced.
7. **Design quality.** A non-technical reviewer (or your dad, or a friend in a non-finance field) can open the app, type a ticker, and produce something they can understand and admire visually. If the look is "Streamlit demo," v0.6 has failed the polish bar — iterate on CSS until it doesn't.
8. **GitHub repo updated.** README.md reflects v0.6 with a screenshot and the public URL. BUILD_NOTES.md has section 20 covering the v0.6 changes.
9. **Interview-ready.** You can confidently send the public URL to a hiring manager and say "Here's a personal project that takes a ticker and applies 5 investor frameworks to value it. Source on GitHub." Without caveats. Without "it's a work in progress." Without apologies for rough edges.

---

## 16. Sources & inspiration (for Stage 2 reference)

- `PROJECT.md` — original vision (Module 2: investor lenses; v0.6 is the productization of Modules 1–2)
- `BUILD_NOTES.md` §19 — v0.5 architecture decisions that carry forward
- `reports/render.py` — existing markdown rendering logic that the Streamlit UI mirrors structurally
- `ANTIGRAVITY_PROMPT_v0.5.md` — Stage 2 prompt template; Stage 2 for v0.6 will follow the same structural pattern
- `frameworks/*.md` — investor lens specs; framework reasoning paragraphs are loaded from these files at runtime
- Streamlit docs: https://docs.streamlit.io (tabs API, theming, secrets management, Community Cloud deployment)
- weasyprint docs: https://weasyprint.org (HTML/CSS to PDF, used for per-lens PDF export)
- openpyxl docs: https://openpyxl.readthedocs.io (Excel workbook construction with formulas)

---
