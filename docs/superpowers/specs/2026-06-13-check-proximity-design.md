# Distance-Graded Check Proximity — Design Spec

**Date:** 2026-06-13
**Status:** Approved, pending implementation
**Scope:** All 5 lenses (Buffett, Marks, KKR, Blackstone, Apollo)

## Problem

Lens verdicts are falsely binary. A check that passes at 15.1% against a 15%
threshold renders identically to one passing at 40%. The user cannot see which
checks are knife-edge — which matters for a tool that is also a learning vehicle,
where *how close* a company is to a threshold is often more informative than the
pass/fail bit itself.

## Goal

Annotate every **single-comparison numeric** check with a signed, normalized
distance-to-threshold, and render it on a color gradient in the app and the
markdown report.

## Hard constraints (non-goals)

- **Pure annotation.** Does NOT change `passed`, `score`, `max_score`, or
  `verdict` for any lens. This is a regression-tested promise.
- **No framework-text change.** `frameworks/*.md` are untouched.
- **Only single-comparison numeric checks** get a proximity. Compound checks
  (`A AND B`, `A OR B`), categorical/soft (LLM verdict) checks, and N/A checks
  (value is `None`) get no proximity and render exactly as they do today.
- Offline test suite stays green and < 15s.

## Component 1 — shared helper (`lenses/_scoring.py`)

```python
def proximity(value, threshold, direction, *, eps=1e-9):
    """
    Signed normalized distance from a numeric check's value to its threshold.

    direction="above": check passes when value >= threshold (higher is better)
    direction="below": check passes when value <= threshold (lower is better)

    Returns a signed float:
      > 0  value is on the passing side (magnitude = how comfortably)
      ~ 0  knife-edge
      < 0  value failed (magnitude = how badly)
    Returns None if value or threshold is None (keeps N/A checks clean).

    Normalization: raw_gap / abs(threshold). When abs(threshold) < eps, fall
    back to abs(value). When both are ~0, return the raw absolute gap.
    """
```

Logic:
- `raw_gap = (value - threshold) if direction == "above" else (threshold - value)`
- `denom = abs(threshold) if abs(threshold) > eps else (abs(value) if abs(value) > eps else None)`
- `return raw_gap if denom is None else raw_gap / denom`
- `None` in either `value` or `threshold` → return `None`.

Unclamped; the UI clamps for color.

## Component 2 — wiring (~50 numeric checks across 5 lenses)

Each single-comparison numeric check gains one field:

```python
"proximity": proximity(val, thresh, "above"),
```

computed at the existing check construction site where `val` and `thresh` are
already in scope.

**Threshold-drift mitigation (required pattern):** the numeric threshold
currently appears both in the `passed` comparison and (as text) in
`threshold_str`. Adding `proximity` introduces a third occurrence. To prevent
silent drift, hoist the threshold to a local constant used by *both* the `passed`
comparison and the `proximity` call:

```python
GM_STD_MAX = 0.03
hist_gm_std = ...
checks["1_moat"] = {
    ...,
    "threshold_str": "< 3.0%",
    "passed": hist_gm_std < GM_STD_MAX,
    "proximity": proximity(hist_gm_std, GM_STD_MAX, "below"),
    ...
}
```

Checks that are NOT single-comparison numeric (compound, soft/categorical, N/A)
do not set `proximity`. Display code treats missing/`None` proximity as
"render as today, no badge".

## Component 3 — display

### `app.py::_render_lens_tab`
A bucketed gradient badge next to each check that has a non-`None` proximity,
using the existing CSS color variables (`--pos`, `--warn`, `--neg`):

| proximity range | label | color |
|---|---|---|
| `>= +0.25` | strong pass | green (`--pos`) |
| `+0.10 … +0.25` | pass | green |
| `0 … +0.10` | narrow pass — knife-edge | amber (`--warn`) |
| `-0.10 … 0` | narrow miss | orange |
| `<= -0.10` | clear miss | red (`--neg`) |

Also show the raw distance numerically (e.g. `+0.7%` or `+0.08`).

### `reports/render.py`
Append the same proximity annotation to each numeric check line in the markdown
report so the report and UI stay consistent.

## Component 4 — tests (`tests/test_scoring.py` + lens assertions)

Helper tests:
- sign correctness for both `direction` values (passing → positive, failing → negative)
- normalization (e.g. value 0.30 vs threshold 0.15 "above" → +1.0)
- `threshold ≈ 0` fallback path
- `None` value/threshold → `None`

Lens-level tests:
- assert a couple of representative checks now carry a `proximity` of the
  expected sign
- **regression guard:** assert `score` / `max_score` / `verdict` are identical
  to current behavior for the existing fixtures (the annotation-only promise)

All offline, < 15s.
