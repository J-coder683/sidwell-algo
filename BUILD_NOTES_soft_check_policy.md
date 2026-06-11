# Soft-Check Policy: Exclude-from-Denominator (implementation plan)

> **STATUS: SHIPPED (2026-06-11).** Implemented across all 5 lenses + shared helper
> `lenses/_scoring.py`. Suite: 426 passing (was 399; +22 helper, +1 Buffett full-data,
> +4 lens N/A regression tests). UI (`app.py`) and markdown report (`reports/render.py`)
> render N/A checks and the reduced denominator. Framework determinism notes updated.
> Snapshot regenerated (KKR 9/18→7/15 SKIP; Apollo 12/16 BUY→11/15 WATCH — the Apollo
> change is the intended de-inflation: its old BUY relied on check 12 defaulting PASS).
> Scope decision: only **LLM-qualitative** checks get N/A treatment; data-feed gaps
> (Buffett #8/#9, Marks #7 analyst consensus) keep their existing default behavior.


**Decision (locked with user, 2026-06-10):**
1. Soft/qualitative checks whose signal is **unavailable or unclear** → mark `applicable: False`, exclude
   from BOTH `score` and `max_score`. (Not default-PASS, not default-FAIL.)
2. Apply uniformly across all 5 lenses, **including** the Phalippou meta-checks.
3. Verdict thresholds become **ratio-based** (absolute cutoffs break when `max_score` shrinks).
   Faithful translation: keep the same fraction via integer cross-multiply
   (`score * ORIG_MAX >= ORIG_THRESHOLD * max_score`) so full-data behavior is byte-identical to today.
4. Phalippou >=4-of-6 edge gate becomes **proportional**: when some levers are N/A, require
   `>= ceil(4/6 * n_applicable_levers)` of the applicable levers.

## Three-state classification for a soft check
- **POSITIVE** verdict (in the check's positive set) → `passed=True, applicable=True`.
- **NEGATIVE** verdict (present, adverse, not in positive set, not unclear) → `passed=False, applicable=True`
  (a real adverse signal still counts against the company — this is the discernment we want).
- **ABSENT/UNCLEAR** (`q_status != "available"`, or verdict in `{None,"","unclear","unknown"}`) →
  `applicable=False` (excluded). `passed` is set False but ignored by the tally.

## Critical nuance — hybrid checks DO NOT get N/A
Checks with a **quantitative OR soft** path (Buffett 10 insider%-or-LLM; Apollo 6 fulcrum, 8 complexity;
KKR 7 wc, 9 mgmt) are **always applicable** — the hard path is always computable. A missing soft signal
just contributes False to the OR. Leave these unchanged. Only **pure-qualitative** checks get the 3-state
treatment.

### Pure-qualitative checks per lens (the ones that change)
- **Buffett:** 11 (coherence), 14 (holdability). [10 hybrid — unchanged]
- **Marks:** 5 (cycle), 11 (single-point, reads risk_callouts), 12 (variant), 13 (humility), 14 (why_now).
  [7 sentiment = analyst-data feed; treat missing-data as N/A too for consistency]
- **KKR:** 8 (M&A), 10 (workforce), 12 (willing seller), 14 (cycle), 17 (why_now). [7,9 hybrid — unchanged]
- **Apollo:** 5 (chaos), 7 (ABF), 12 (hold), 15 (covenant). [6,8 hybrid — unchanged]
- **Blackstone:** 6 (cycle), 7 (tailwind), 12 (core viability), 13 (multi-product).

### Phalippou edge levers (proportional gate)
- **Apollo #16:** levers 5,6,7,8,9,12 — pure-soft: 5,7,12; hybrid(always-applic): 6,8; quant: 9.
- **Blackstone #14:** levers 2,3,5,7,12,13 — quant: 2,3,5; pure-soft: 7,12,13.
- **KKR #18:** levers 5,7,8,9,10,16 — quant: 5,16; hybrid: 7,9; pure-soft: 8,10.
Gate input = the lever check's `(passed, applicable)`. `gate_passed = n_applicable>0 and passed>=ceil(4/6*n_applicable)`.

## Preconditions referencing soft checks (principled default)
Preconditions are gates, not scored checks. **Do not SKIP purely on missing data.**
- Apollo `precond_2 = pass_5 or pass_6 or pass_7`: pass if any *applicable* lever passes, OR if all three N/A.
- Blackstone `precond_1 = >=2 of (8,9,10)`: all quant → unchanged.
- KKR `precond_1 = all(1..4)`: all quant → unchanged.
- Phalippou preconds (Apollo precond_1, Blackstone precond_2, KKR precond_2) use the proportional gate.

## Shared helper — `lenses/_scoring.py`
- `UNCLEAR = {None, "", "unclear", "unknown"}`
- `resolve_soft(q_status, verdict, positive_set, *, na_detail, pass_detail, fail_detail) -> (passed, applicable, detail)`
- `tally(checks) -> (score, max_score)`  (guards `applicable and passed`)
- `cross_verdict(score, max_score, orig_max, threshold) -> bool`  (integer cross-multiply)
- `proportional_gate(levers) -> (passed, n_applicable, threshold, gate_passed)`

## Blast radius / files
1. `lenses/_scoring.py` (new) + `tests/test_scoring.py` (new, TDD first).
2. `lenses/{buffett,marks,kkr,blackstone,apollo}.py` — apply policy.
3. `app.py::_render_lens_tab` (line ~774) — part totals use `applicable`; `_render_check` shows ⏸️ N/A;
   add "scored on N of M checks" note. (`render.py` markdown path already N/A-aware; align legacy line ~778.)
4. `tests/test_{buffett,marks,kkr,blackstone,apollo}.py` — replace brittle absolute-count asserts with
   verdict + `applicable` + ratio asserts; add N/A-exclusion tests.
5. `frameworks/*.md` determinism notes — change "defaults PASS when unavailable" wording to
   "excluded from denominator (N/A)". Keep `**Logic:**` paragraphs intact (parser contract).

## Invariant
`.venv\Scripts\python.exe -m pytest tests/ -q -p no:cacheprovider` stays green & <15s.
