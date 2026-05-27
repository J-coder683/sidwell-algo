# Antigravity prompt — Sidwell v0.5 build (KKR + Blackstone + Apollo lenses)

---

You are extending **Sidwell** from v0.4.1 (Buffett + Marks dual-lens) to **v0.5 (quintuple-lens: Buffett + Marks + KKR + Blackstone + Apollo)**. The three new lenses are PE / alternative-asset frameworks already specified in `frameworks/`. Your job is Stage 2 implementation: convert those markdown specs into working Python without inventing thresholds, predicting outputs, or reshaping rules to fit a desired verdict on any specific ticker.

## Read these first (in this order — do not skip)
1. `PROJECT.md` — vision, architecture, module sequence
2. `BUILD_NOTES.md` — every prior version's assumptions and conventions (especially statistical conventions and Asian Paints calibration)
3. `frameworks/buffett.md` and `frameworks/marks.md` — to see how existing lenses are structured (so your new code matches the pattern)
4. `lenses/buffett.py` and `lenses/marks.py` — the canonical Python implementation pattern; copy structure exactly
5. `frameworks/kkr.md` — 18 checks across 5 Parts; the most complex of the three new lenses
6. `frameworks/blackstone.md` — 14 checks across 5 Parts
7. `frameworks/apollo.md` — 16 checks across 5 Parts
8. `analysis/prompts/qualitative_extraction.md` — current LLM schema (v0.3); you will extend to v0.4
9. `reports/render.py` — current dual-lens report layout; you will extend to quintuple-lens

---

## v0.5 deliverable (this run only)

Working end-to-end pipeline through **five lenses** on a single command:

```bash
python value.py ASIANPAINT.NS
```

Produces `output/asianpaint_report.md` containing:

1. **Executive Summary** — table of all 5 verdicts side-by-side (Buffett, Marks, KKR, Blackstone, Apollo)
2. **Company Snapshot** — unchanged from v0.4
3. **DCF Valuation & WACC Sourcing** — unchanged from v0.4
4. **Buffett Investor Lens** — unchanged (14 checks)
5. **Qualitative Analysis** — extended with new soft fields (see §4 below)
6. **Marks Investor Lens** — unchanged (14 checks)
7. **KKR Investor Lens** — NEW (18 checks, 5 Parts)
8. **Blackstone Investor Lens** — NEW (14 checks, 5 Parts)
9. **Apollo Investor Lens** — NEW (16 checks, 5 Parts)
10. **Margin-of-Safety Check** — unchanged
11. **Investment Verdicts (Quintuple-Lens Synthesis)** — extended table + paragraph explaining lens divergence

Console summary at end of run must print all 5 scores and 5 verdicts.

---

## Hard constraints (methodology integrity — NON-NEGOTIABLE)

These are the rules that protect Sidwell from becoming a confirmation-bias machine. Violations are not "small bugs" — they invalidate the whole pipeline.

1. **No predicted outputs.** Do NOT write code that targets a specific verdict for Asian Paints (or any ticker). The verdict is whatever the math produces. If the score-to-verdict mapping in the framework produces a different verdict than the framework's example output, **trust the math, log the discrepancy, and surface it in BUILD_NOTES** — do not tune thresholds. The example outputs in the framework `.md` files are illustrative narrative, not specifications.
2. **`raise ValueError`, not `assert`.** Every validation in production code must use `raise ValueError(...)` (or a more specific exception). `assert` is for tests only — Python strips assertions under `-O`.
3. **`np.std(..., ddof=1)` everywhere.** Sample standard deviation. Same convention as Buffett and Marks lenses.
4. **"Historical" = 4 years; "Latest" = most recent FY.** Hard-coded across all checks. Same as Buffett/Marks.
5. **Graceful degrade for soft (LLM) checks.** When `qualitative_results["status"] != "available"`, each soft check must use the explicit default specified in the framework (`PASS`, `FAIL`, or `neutral`). Never crash on missing qualitative data. The default behavior is specified per-check in the framework `.md` — read the **Determinism note** in each check.
6. **Frameworks are immutable during implementation.** If you find a check specification ambiguous, write a `BUILD_NOTES` entry documenting your interpretation, but DO NOT edit `frameworks/kkr.md`, `frameworks/blackstone.md`, or `frameworks/apollo.md`. The framework files are the spec; the code conforms to them.
7. **Snapshot test is hand-edited.** `tests/test_snapshot.py`'s expected output **will change** because three new lens sections are added. You must hand-edit the expected snapshot string to match — do NOT add a "regenerate snapshot" CLI flag, do NOT use `pytest --snapshot-update`. Hand-edit so a human review of the diff is mandatory.
8. **No paid APIs. No live network calls in tests.** Same as v0.1.
9. **One lens per file.** Split the existing `lenses/kkr_blackstone.py` stub into three separate modules: `lenses/kkr.py`, `lenses/blackstone.py`, `lenses/apollo.py`. The combined stub is deleted.

---

## Files to create / modify

### CREATE
| Path | Purpose |
|---|---|
| `lenses/kkr.py` | `evaluate_kkr_lens(financials, dcf_results, qualitative_results=None) -> dict` — 18 checks per `frameworks/kkr.md` |
| `lenses/blackstone.py` | `evaluate_blackstone_lens(financials, dcf_results, qualitative_results=None) -> dict` — 14 checks per `frameworks/blackstone.md` |
| `lenses/apollo.py` | `evaluate_apollo_lens(financials, dcf_results, qualitative_results=None) -> dict` — 16 checks per `frameworks/apollo.md` |
| `tests/test_kkr.py` | At least 5 tests (see §6) |
| `tests/test_blackstone.py` | At least 5 tests |
| `tests/test_apollo.py` | At least 5 tests |

### DELETE
| Path | Reason |
|---|---|
| `lenses/kkr_blackstone.py` | Replaced by separated `lenses/kkr.py` and `lenses/blackstone.py` |

### MODIFY
| Path | Change |
|---|---|
| `lenses/__init__.py` | Export `kkr`, `blackstone`, `apollo` modules; remove `kkr_blackstone` |
| `value.py` | Import three new lens modules; call `evaluate_kkr_lens`, `evaluate_blackstone_lens`, `evaluate_apollo_lens` after the Marks call; pass all three results into `render_markdown_report`; extend console summary block to print 5 verdicts |
| `reports/render.py` | Bump `SIDWELL_VERSION` to `"v0.5"`. Extend `render_markdown_report` signature to accept `kkr_results`, `blackstone_results`, `apollo_results`. Add three new sections (after current Marks section). Extend Executive Summary table to 5 verdicts. Replace "Dual-Lens Synthesis" with "Quintuple-Lens Synthesis" — show divergence pattern in plain English. |
| `analysis/prompts/qualitative_extraction.md` | Add new fields listed in §4. Update prompt version comment from v0.3 → v0.4. |
| `analysis/qualitative.py` | Bump `PROMPT_VERSION = "v0.4"` — invalidates all prior qualitative cache entries (this is intentional). |
| `tests/test_snapshot.py` | Hand-edit expected snapshot to include new sections. Do NOT auto-regenerate. |
| `tests/test_buffett.py`, `tests/test_marks.py` | Should NOT need modification. If you change shared fixtures, update both — but try not to touch them. |
| `frameworks/_future_lenses.md` | Remove KKR/Blackstone entries (now implemented). Keep distressed/special-situations as the remaining future lens. |
| `BUILD_NOTES.md` | Append a new top-level section `## v0.5 — Triple-lens addition (KKR, Blackstone, Apollo)` documenting: any threshold ambiguities encountered, sector-mapping choices (see §3), qualitative schema migration, and any Asian Paints actual-vs-framework-example discrepancies. |
| `README.md` | Update version banner, lens count, and the example `python value.py` output snippet. |

### LEAVE AS STUB (do not implement in v0.5)
- `valuation/lbo.py` — KKR Check 15 uses an inline simplified IRR estimator (see `frameworks/kkr.md` Check 15 code block); the full LBO model with explicit debt schedule, sources & uses, fees, and waterfall is a v0.6+ deliverable. Keep the `NotImplementedError` stub.
- `lenses/distressed.py` — distressed lens stays as future work.
- `valuation/comps.py`, `valuation/precedent.py` — unchanged.

---

## §1 — Implementation order (build in this sequence to avoid breaking the pipeline mid-implementation)

Do these in order. After each step, the existing `python value.py ASIANPAINT.NS` should still produce a valid (if intermediate) report.

1. **Extend qualitative prompt + bump PROMPT_VERSION** (§4). Run `python value.py ASIANPAINT.NS` to confirm Buffett+Marks still pass; the cache gets invalidated, a fresh Gemini call runs (or graceful-degrade if no GEMINI_API_KEY). New fields appear in qualitative_results as `None`-defaulted.
2. **Delete `lenses/kkr_blackstone.py`** and update `lenses/__init__.py` so imports don't break.
3. **Implement `lenses/kkr.py`** with all 18 checks. Wire into `value.py` and `render.py`. Confirm Asian Paints produces a verdict — record the actual score in BUILD_NOTES; expected per framework example output is SKIP (10/18) due to Phalippou failure.
4. **Implement `lenses/blackstone.py`** with all 14 checks. Wire in. Asian Paints expected per framework example is BUY (11/14) but check what the math actually produces.
5. **Implement `lenses/apollo.py`** with all 16 checks. Wire in. Asian Paints expected per framework example is SKIP (8/16) due to both pre-conditions failing.
6. **Extend `render.py`** to quintuple-lens layout (Executive Summary + 3 new sections + Quintuple-Lens Synthesis).
7. **Write all three test files** with at least 5 tests each (§6).
8. **Hand-edit `tests/test_snapshot.py`** to include the new sections.
9. **Update `_future_lenses.md`**, `README.md`, append `BUILD_NOTES.md` section.
10. **Verification** (§7).

---

## §2 — Per-lens implementation notes

### `lenses/kkr.py` (18 checks)

Follow `frameworks/kkr.md` exactly. Key implementation details:

- **Function signature:** `evaluate_kkr_lens(financials, dcf_results, qualitative_results=None) -> dict` — same shape as Buffett/Marks.
- **Returned dict shape:** `{"ticker", "checks", "score", "verdict", "reason"}` — same as Buffett/Marks. The `checks` dict uses keys `"1_ebitda_scale"`, `"2_fcf_conversion"`, etc., each value being a check dict with keys `name`, `metric_name`, `value`, `threshold_str`, `passed`, `detail`, `part`.
- **Two pre-conditions:** All 4 of Part A must pass (LBO viability), AND Check 18 (Phalippou) must pass. If either pre-condition fails, verdict is `"SKIP"` regardless of total score.
- **Check 15 (7-year IRR feasibility)** uses the simplified inline estimator in the framework — do NOT call `valuation.lbo` (which remains a stub). Implement the math directly in the check.
- **Check 6 (capex optimization)** has three pass paths and one fail path — implement the three-branch logic exactly. This is the most intricate single check.
- **Sector mapping (Check 11):** Define `KKR_PLAYBOOK_SECTORS = {...}` at module top from the framework's Python block. Use the existing `financials["target_industry"]` field (populated via `data/public.py:TICKER_INDUSTRY_MAP`).
- **Regulatory blocker (Check 13):** Define `INDIA_PE_RESTRICTED = {"Bank (Money Center)"}` at module top. Check both ticker suffix and industry.
- **Soft checks default behavior** (per framework Determinism notes):
  - Check 7 (WC optimization) soft signal → if unavailable, use ONLY the hard signal
  - Check 8 (M&A platform) → defaults PASS
  - Check 9 (mgmt/board upgrade) soft → quantitative path always available; soft is supplementary
  - Check 10 (workforce Stavros fit) → defaults to `mixed` (PASS)
  - Check 12 (willing-seller) → defaults to `unclear` (neutral; do NOT count toward score either way) — this is a special case; document the handling in BUILD_NOTES
  - Check 14 (cycle position) → reuses `qualitative_results["cycle_position"]["sector_cycle"]` (already in schema)
  - Check 17 (why-now catalyst) → reuses `qualitative_results["why_now_signal"]["verdict"]` (already in schema); the Marks lens uses `dislocation_present`, the KKR lens accepts `catalyst_present` (broader). You will need to add `catalyst_present` as a third allowed verdict in the qualitative schema — see §4.
- **Verdict thresholds:** BUY≥15, WAIT≥13 (with specific sub-conditions), WATCH≥13, SKIP otherwise. Math is in the framework's Scoring block.

### `lenses/blackstone.py` (14 checks)

Follow `frameworks/blackstone.md` exactly. Key implementation details:

- **Two pre-conditions:** Part C (checks 8, 9, 10) must have ≥2/3 passing, AND Check 14 (Phalippou) must pass.
- **Sector mapping (Check 5):** `BLACKSTONE_FAVORED_THEMES` from the framework. Note the framework also has a `BLACKSTONE_AVOIDED_THEMES` set — failing into this set is a hard FAIL, not just "not in favored". Implement both.
- **Check 1 (large growing market):** `revenue_4y_max > revenue_4y_min` is trivially true unless revenue is monotonically declining; combined with the 5% CAGR test. The CAGR uses the same calculation as Buffett's Check 4 — `(revenue[-1] / revenue[0]) ** (1/3) - 1` for a 4-year window (3 growth periods).
- **Check 6 (cycle position):** reuses `qualitative_results["cycle_position"]["sector_cycle"]` (already in schema).
- **Check 7 (structural tailwind):** NEW soft field — see §4.
- **Check 12 (20y Core viability):** reuses `qualitative_results["holdability_assessment"]["verdict"]` (already in schema — same semantic as Buffett Check 14).
- **Check 13 (multi-product engagement):** NEW soft field — see §4. Defaults to `unclear` (NEUTRAL — neither PASS nor FAIL, which means the check is treated as PASS for scoring but should be flagged in the detail as "neutral default"). Document this neutrality convention in BUILD_NOTES.
- **Verdict thresholds:** BUY≥11, WAIT≥9 (with sub-conditions), WATCH≥9, SKIP otherwise.

### `lenses/apollo.py` (16 checks)

Follow `frameworks/apollo.md` exactly. Key implementation details:

- **Two pre-conditions:** Check 16 (Phalippou) must pass, AND at least one of Check 5 (chaos), Check 6 (fulcrum), or Check 7 (ABF fit) must pass.
- **Check 1 (entry valuation discount):** Needs `sector_median_ev_ebitda`. **Apollo's Check 1 requires sector EV/EBITDA medians not currently in `financials`.** For v0.5, use a hard-coded sector median lookup table at module top, populated from Damodaran's January 2026 multiples dataset for the relevant sectors. Document the lookup table source in BUILD_NOTES. For sectors not in the lookup, fall back to FAIL (conservative — Apollo's price discipline cuts both ways). Document this fallback choice.
- **Check 1 alternative (book value):** Needs `latest_book_value_per_share`. Derive as `financials["total_equity"][-1] / financials["shares_outstanding"]`. Available from existing `financials` dict.
- **Check 14 (tangible asset ratio):** Needs `total_intangibles` and `goodwill`. **These fields may not currently be in `financials`.** Add them to `data/public.py:fetch_financials` output. If yfinance does not surface them for a ticker, treat as 0 (conservative — over-reports tangibility, but failure mode is over-investing, which the surrounding checks will catch).
- **Check 15 (covenant control):** NEW soft field — see §4. Check whether the company has public bonds — proxy via yfinance balance sheet bond items if available, otherwise rely on the LLM soft signal only.
- **Sector mapping (Check 9):** `APOLLO_DOMAIN_SECTORS` from the framework.
- **Verdict thresholds:** BUY≥12, WAIT≥10 (with sub-conditions), WATCH≥10, SKIP otherwise.

---

## §3 — Sector mapping additions

Audit `data/public.py:TICKER_INDUSTRY_MAP` and `DEFAULT_INDUSTRY`. The three new lenses reference industry strings that must EXACTLY match the keys in:
- `KKR_PLAYBOOK_SECTORS` (in `lenses/kkr.py`)
- `BLACKSTONE_FAVORED_THEMES` / `BLACKSTONE_AVOIDED_THEMES` (in `lenses/blackstone.py`)
- `APOLLO_DOMAIN_SECTORS` (in `lenses/apollo.py`)

For each set, use the EXACT industry strings from the framework Python blocks. If a ticker maps to an industry not in any of the new sets, that's fine — the sector-compatibility checks for that lens will FAIL for that ticker, which is correct (the lens shouldn't apply).

**Do not add new tickers to `TICKER_INDUSTRY_MAP` as part of v0.5 unless needed for tests.** The map will grow organically as users analyze more tickers in v0.6+.

---

## §4 — Qualitative extraction schema extension (v0.3 → v0.4)

Add the following fields to `analysis/prompts/qualitative_extraction.md`. Update the schema, the rules section, and the version comment. Bump `PROMPT_VERSION` in `analysis/qualitative.py` from `"v0.3"` to `"v0.4"` (this invalidates the prior cache — intentional).

### New fields (add to the JSON schema in the prompt)

```jsonc
{
  // ... existing v0.3 fields unchanged ...

  // For KKR lens
  "willing_seller_signal": {
    "verdict": "willing_seller | strategic_holdout | unclear",
    "evidence": "one paragraph — family/founder succession, conglomerate divestiture signals, insider ownership + activism pressure, low public sponsorship, promoter pledge / stake-sale signals (India context)"
  },
  "ma_platform_potential": {
    "verdict": "platform_potential | bolt_on_only | not_applicable",
    "reasoning": "one paragraph — is the company in a fragmented industry with consolidation upside? Does it already have M&A infrastructure?"
  },
  "workforce_stavros_fit": {
    "verdict": "frontline_heavy | mixed | knowledge_worker_heavy | unclear",
    "evidence": "one paragraph — large frontline hourly workforce indicators from transcripts/MD&A"
  },
  "mgmt_upgrade_potential": {
    "verdict": "upgrade_available | management_best_in_class | unclear",
    "reasoning": "one paragraph — operational complacency, strategic drift, governance concerns vs top-quartile execution"
  },
  "wc_optimization_signal": {
    "verdict": "wc_optimization_available | already_optimized | unclear",
    "evidence": "one paragraph — DSO/DPO/inventory turn issues, channel stuffing recovery, supplier-term renegotiation opportunities"
  },

  // For Blackstone lens
  "structural_tailwind_signal": {
    "verdict": "tailwind | neutral | headwind",
    "reasoning": "one paragraph — multi-decade structural tailwind (AI compute, India consumption, healthcare aging, energy transition, urbanization) vs. headwind (commodity disruption, technology obsolescence, regulatory tightening)"
  },
  "multi_product_engagement_signal": {
    "verdict": "multi_product_potential | single_product_only | unclear",
    "reasoning": "one paragraph — does the company invite engagement across senior debt, mezzanine, preferred, control equity, real estate, structured?"
  },

  // For Apollo lens
  "chaos_dislocation_catalyst": {
    "verdict": "chaos_present | dislocation_present | moderate_stress | normal | unclear",
    "specific_event": "one sentence naming the event, or 'no specific dislocation'",
    "reasoning": "one paragraph"
  },
  "fulcrum_security_signal": {
    "verdict": "fulcrum_identified | multi_tranche_complex | clean_structure | unclear",
    "reasoning": "one paragraph — multi-tranche complexity, debt stress, equity destruction signals"
  },
  "abf_credit_fit": {
    "verdict": "abf_primary_opportunity | direct_lending_opportunity | not_credit_compatible",
    "reasoning": "one paragraph — does the company generate diversified-collateral self-liquidating amortizing assets (ABF) or have identifiable mid-market cash flows (direct lending)?"
  },
  "complexity_moat_signal": {
    "verdict": "complexity_premium_available | moderate_complexity | straightforward | unclear",
    "reasoning": "one paragraph — regulatory, structural, cross-border, or financial-structure complexity that creates pricing edge for sophisticated investors"
  },
  "permanent_hold_viable": {
    "verdict": "permanent_hold_viable | requires_near_term_exit | unclear",
    "reasoning": "one paragraph — can this be held indefinitely on Athene's balance sheet without requiring IPO / strategic sale / secondary?"
  },
  "covenant_control_potential": {
    "verdict": "covenant_rich_opportunity | mixed | covenant_lite_existing | investment_grade_public | unclear",
    "reasoning": "one paragraph — could Apollo negotiate meaningful covenants on a private credit facility?"
  }
}
```

### Also extend the existing `why_now_signal` verdict enum

Add `catalyst_present` as a third allowed verdict (between `dislocation_present` and `normal_cycle`):
```
"verdict": "dislocation_present | catalyst_present | normal_cycle | unclear"
```
Marks's check 14 continues to require `dislocation_present` (strict). KKR's check 17 accepts `dislocation_present | catalyst_present` (broader). The schema change is backward-compatible for Marks.

### Update `_unavailable()` in `analysis/qualitative.py`

Add the new fields to the empty-schema dict so downstream code doesn't `KeyError`. Each new field gets `{"verdict": None, ...}` shape.

---

## §5 — Report rendering changes (`reports/render.py`)

### Signature change
```python
def render_markdown_report(
    dcf_results: dict,
    buffett_results: dict,
    financials: dict,
    qualitative_results: dict = None,
    marks_results: dict = None,
    kkr_results: dict = None,            # NEW
    blackstone_results: dict = None,     # NEW
    apollo_results: dict = None,         # NEW
    generated_at: datetime = None,
    output_dir: Path = None,
) -> Path:
```

All three new results are keyword-optional so v0.4 callers don't break (defensive).

### Executive Summary table
Add three new rows:
```
| **KKR Score** | **{kkr_results['score']}/18** | KKR Lens (18 checks) |
| **KKR Verdict** | **{kkr_results['verdict']}** {emoji} | KKR Lens Rules |
| **Blackstone Score** | **{blackstone_results['score']}/14** | Blackstone Lens (14 checks) |
| **Blackstone Verdict** | **{blackstone_results['verdict']}** {emoji} | Blackstone Lens Rules |
| **Apollo Score** | **{apollo_results['score']}/16** | Apollo Lens (16 checks) |
| **Apollo Verdict** | **{apollo_results['verdict']}** {emoji} | Apollo Lens Rules |
```

### Verdict Summary block
Add three new `> **KKR**: ... | > **Blackstone**: ... | > **Apollo**: ...` lines.

### New sections (in this order, after current §3.6 Marks)
- `## 3.7 KKR Investor Lens` — uses existing `_render_lens_table` helper; score shown as `{score}/18`
- `## 3.8 Blackstone Investor Lens` — score shown as `{score}/14`
- `## 3.9 Apollo Investor Lens` — score shown as `{score}/16`

### Quintuple-Lens Synthesis (replaces "Dual-Lens Synthesis")
A short narrative section showing the divergence pattern in plain English. Template:

```markdown
## 7. Quintuple-Lens Synthesis

| Lens | Score | Verdict | First-order driver |
|---|---|---|---|
| Buffett | X/14 | ... | Quality + price |
| Marks | X/14 | ... | Risk-first + asymmetry |
| KKR | X/18 | ... | Operating lever stack |
| Blackstone | X/14 | ... | Theme + scale + 20y hold |
| Apollo | X/16 | ... | Chaos / complexity / Athene fit |

**Pattern read:** {one paragraph generated deterministically from the 5 verdicts}
```

The "Pattern read" paragraph is generated by a deterministic rule-based function — NOT LLM. Implement these patterns (extend as you find others):
- All five BUY → "Convergent high-conviction signal — extraordinarily rare. Treat as a flag for deeper diligence."
- All five SKIP → "Convergent rejection — no lens sees an edge. Move on."
- Buffett BUY + Apollo SKIP + KKR SKIP → "Quality compounder without operational or distressed angle. Classic Buffett-only setup."
- KKR BUY + Buffett SKIP → "Operationally improvable target without compounding quality. PE-edge, not public-quality."
- Apollo BUY + others SKIP → "Chaos/distress entry — only Apollo's complexity-arbitrage lens engages."
- Blackstone BUY + KKR SKIP → "Theme-aligned scale company already well-run — Blackstone's hold thesis applies; KKR cannot add operational alpha."
- Marks BUY + Blackstone SKIP → "Cyclically mispriced name without scale or theme alignment. Marks would trade; Blackstone has no use."
- Generic fallback: "Mixed signals across lenses — see per-lens reasoning above. Lens disagreement is informative, not contradictory."

Document the full pattern list in BUILD_NOTES so future versions can extend it.

### Version banner
Bump `SIDWELL_VERSION = "v0.5"` at top of `reports/render.py`.

---

## §6 — Test requirements

Each new test file (`tests/test_kkr.py`, `tests/test_blackstone.py`, `tests/test_apollo.py`) must have at least 5 tests:

1. **`test_perfect_X_pass`** — a fixture company that passes all checks; verdict is BUY.
2. **`test_phalippou_failure_skips`** — a fixture that passes most checks except the Phalippou meta-check; verdict must be SKIP (pre-condition failure).
3. **`test_X_specific_precondition_failure`** — lens-specific pre-condition test:
   - KKR: Part A failure (e.g., EBITDA too small) → SKIP regardless of other scores
   - Blackstone: Part C < 2/3 (e.g., negative FCF in one year) → SKIP
   - Apollo: none of checks 5/6/7 pass → SKIP
4. **`test_asianpaints_actual`** — load the canonical Asian Paints fixture used in `tests/test_buffett.py` and `tests/test_marks.py`, run the lens, assert the score and verdict equal what the framework example output predicts. **If the math produces a different verdict, the test should FAIL and you should debug — do NOT change the test to match wrong code.** If the framework example output and the math genuinely disagree (after debugging), document the discrepancy in BUILD_NOTES and adjust the test assertion with a clear explanatory comment.
5. **`test_unavailable_qualitative_graceful_degrade`** — pass `qualitative_results = _make_unavailable_qualitative()` (same helper as in `tests/test_buffett.py`); the lens must not crash and must produce a verdict (typically more conservative because soft FAIL defaults apply).

For Apollo specifically, add a **6th test**:
- **`test_chaos_or_fulcrum_or_abf_required`** — fixture with all 16 checks passing EXCEPT checks 5, 6, and 7 all FAIL; verdict must be SKIP even though score is 13/16.

### Shared fixtures
Move the Asian Paints fixture from `tests/test_buffett.py` to `tests/fixture_company.py` (which already exists). Refactor `test_buffett.py` and `test_marks.py` to import from it. The new test files also import from it. This is a small refactor — keep the data values unchanged.

### Snapshot test (`tests/test_snapshot.py`)
Hand-edit the expected snapshot string to include three new sections. The diff should be reviewable by a human in one sitting (< 200 lines added). If the snapshot is too unwieldy, consider parameterizing the snapshot test to check section-by-section rather than as one giant string — but only as a refactor, not to avoid the hand-edit.

---

## §7 — Verification (you are done when ALL of these pass)

1. `pip install -r requirements.txt` works on a clean venv (no new dependencies should be needed — same library set as v0.4.1).
2. `pytest tests/` — all tests green, including the 15+ new tests across the 3 new lens files, the hand-edited snapshot test, and the (unchanged) existing Buffett/Marks/DCF/data tests.
3. `python value.py ASIANPAINT.NS` runs to completion (with or without GEMINI_API_KEY), writes `output/asianpaint_report.md`, and the report contains all 5 lens sections.
4. Console summary at end of run prints all 5 scores and 5 verdicts (Buffett, Marks, KKR, Blackstone, Apollo).
5. Re-running with no internet (after first run cached) still produces the report.
6. The qualitative cache file generated by v0.4.1 is NOT used (because PROMPT_VERSION bumped). A fresh Gemini call is made (or graceful-degrade fires if no API key) — this is the correct behavior.
7. `python value.py AAPL` runs end-to-end (cross-region sanity check; AAPL is already in `TICKER_INDUSTRY_MAP`).
8. The Asian Paints verdicts produced match the framework example outputs as closely as the math allows. **If they diverge, document why in BUILD_NOTES — do NOT reshape the framework or the code to force agreement.**

### Expected Asian Paints verdicts (per framework example outputs)
| Lens | Expected verdict per framework | Score per framework |
|---|---|---|
| Buffett | WAIT (per v0.4 baseline) | ~10/14 |
| Marks | per existing v0.4 output | per existing v0.4 |
| KKR | SKIP | 10/18 (fails Phalippou) |
| Blackstone | BUY | 11/14 |
| Apollo | SKIP | 8/16 (fails both pre-conditions) |

These are the framework's example outputs, not test specifications. The actual code may produce slightly different scores because real yfinance data drifts from the framework's narrative example. Document any divergence > 1 check.

---

## §8 — Leave as Artifacts

- The generated `output/asianpaint_report.md` for v0.5
- Full `pytest` output (all tests passing)
- `BUILD_NOTES.md` with a new `## v0.5 — Triple-lens addition` section that documents:
  - The actual score and verdict for Asian Paints under each of the 3 new lenses
  - Any divergence > 1 check from the framework example outputs (with a one-paragraph explanation)
  - Threshold ambiguities encountered and how you resolved them
  - The sector-median EV/EBITDA lookup table source (for Apollo Check 1)
  - The qualitative schema migration v0.3 → v0.4 (list of fields added)
  - The neutral-default handling convention for soft checks (e.g., KKR Check 12, Blackstone Check 13)
  - Any places you deviated from the framework spec and why
- An updated `README.md` reflecting v0.5

---

## §9 — What NOT to do

- **Do NOT implement `valuation/lbo.py`.** The full LBO model with explicit debt schedule, S&U, and waterfall is v0.6+. KKR Check 15 uses the inline simplified estimator in the framework.
- **Do NOT implement `lenses/distressed.py`.** Still a future lens.
- **Do NOT auto-regenerate `tests/test_snapshot.py`.** Hand-edit only.
- **Do NOT tune any threshold to make Asian Paints (or any ticker) produce a desired verdict.** The math is the math.
- **Do NOT edit the framework `.md` files.** They are the spec; conformance flows code → framework, never the reverse. If you find a genuine bug in a framework (e.g., a Python code block that doesn't parse, an internal inconsistency), STOP and write a BUILD_NOTES entry flagging it for the human's review — do not silently fix it.
- **Do NOT add a new LLM call in the deterministic pipeline.** The qualitative layer is the only LLM touchpoint; everything else stays deterministic.
- **Do NOT use `assert` in production code.** `raise ValueError(...)` always.
- **Do NOT add new dependencies.** Same library set as v0.4.1 (numpy, pandas, yfinance, nsepython, requests, pyyaml, fredapi, pytest, google-genai).
- **Do NOT create a web UI, dashboard, or HTML output.** Markdown only.
- **Do NOT mock data in production code to paper over fetch failures.** Fail loudly with a clear error. (Tests are allowed to mock; production is not.)
- **Do NOT commit `.env` or any cached qualitative responses containing sensitive data.** Check `.gitignore` is still correct.
- **Do NOT chain a v0.6 work item into v0.5.** Ship v0.5 cleanly; stop and wait for review before extending. The composite verdict displayed in the Synthesis section is rule-based and deterministic — no scoring weights, no "meta-verdict," no probability blends. Those are explicitly v0.6+ decisions to be made after seeing real lens-divergence patterns on a portfolio of tickers.

---

## §10 — After v0.5 ships

Stop and wait for instructions. The architecture must be reviewed against real multi-lens output across at least 5 tickers (suggested: ASIANPAINT.NS, HDFCBANK.NS, RELIANCE.NS, AAPL, MSFT) before any of the following v0.6+ extensions are scoped:
- Distressed / special-situations lens (Howard Marks's distressed framework, fundamentally different from his public-equity framework)
- Full LBO model (`valuation/lbo.py`) replacing the inline IRR estimator in KKR Check 15
- Composite verdict — weighted blend or majority-vote logic
- Private-company path (YAML input + CIM-extraction helper, per `PROJECT.md` module 5)
- Term-sheet recommendation module (board seats, prefs, anti-dilution, drag/tag — per `PROJECT.md` module 6)
- Sector-median EV/EBITDA lookup from a live Damodaran fetch (rather than hard-coded table)
- Expanded `TICKER_INDUSTRY_MAP` from a CSV / database

The v0.5 ship is: **five lenses, deterministic + LLM-soft hybrid, single-ticker public-equity analysis, with the divergence between lenses as the primary diagnostic signal.**

---
