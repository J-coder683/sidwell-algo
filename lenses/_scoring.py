"""
lenses/_scoring.py
------------------
Shared scoring utilities implementing the **exclude-from-denominator** soft-check
policy used by all five investor lenses. See BUILD_NOTES_soft_check_policy.md.

The policy in one sentence: a pure-qualitative check whose signal is unavailable
or unclear is marked not-applicable and dropped from BOTH the score and the
max_score, so a verdict reflects only the checks that actually fired — rather than
silently defaulting such checks to PASS (which inflates) or FAIL (which punishes
missing data instead of the company).
"""
import math

# Verdict strings that mean "the model could not form a view" → excluded.
UNCLEAR = {None, "", "unclear", "unknown"}


def resolve_soft(q_status, verdict, positive_set, *,
                 na_detail="", pass_detail="", fail_detail="",
                 confidence=None):
    """
    Three-state resolution of a *pure-qualitative* soft check.

    Returns (passed: bool, applicable: bool, detail: str):
      - signal absent/unclear      -> (False, False)  [excluded from the denominator]
      - confidence == "low"        -> (False, False)  [excluded: signal too weak]
      - verdict in positive_set    -> (True,  True)   [genuine positive]
      - verdict present, adverse   -> (False, True)   [genuine negative — counts against]

    Do NOT use this for hybrid (quantitative-OR-soft) checks: those are always
    applicable because the hard path is computable.
    """
    if q_status != "available" or verdict in UNCLEAR:
        return False, False, (na_detail or
                              "N/A — qualitative signal unavailable/unclear; excluded from denominator")
    if confidence == "low":
        return False, False, (na_detail or
                              "N/A — low-confidence signal; excluded from denominator")
    passed = verdict in positive_set
    if passed:
        return True, True, (pass_detail or f"PASS (signal: {verdict})")
    return False, True, (fail_detail or f"FAIL (signal: {verdict})")


def tally(checks):
    """
    (score, max_score) under exclude-from-denominator: only applicable checks count.
    A check is applicable unless it explicitly sets "applicable": False.
    """
    score = sum(1 for c in checks.values() if c.get("applicable", True) and c["passed"])
    max_score = sum(1 for c in checks.values() if c.get("applicable", True))
    return score, max_score


def meets(score, max_score, orig_max, threshold):
    """
    Ratio threshold via integer cross-multiply, preserving the original calibration.

    True iff score/max_score >= threshold/orig_max. When max_score == orig_max this
    reduces exactly to `score >= threshold`, so full-data behavior is identical to the
    pre-policy absolute cutoffs.
    """
    if max_score <= 0:
        return False
    return score * orig_max >= threshold * max_score


def proportional_gate(levers, base_passed=4, base_total=6):
    """
    Proportional Phalippou edge gate.

    levers: iterable of (passed: bool, applicable: bool).
    Returns (passed_count, n_applicable, threshold, gate_passed).

    threshold = ceil(base_passed/base_total * n_applicable). The gate requires at
    least one applicable lever; if every lever is N/A the gate cannot be cleared.
    """
    applicable = [(p, a) for (p, a) in levers if a]
    n = len(applicable)
    passed = sum(1 for (p, _a) in applicable if p)
    threshold = math.ceil(base_passed / base_total * n) if n > 0 else 0
    gate_passed = n > 0 and passed >= threshold
    return passed, n, threshold, gate_passed


def proximity(value, threshold, direction, *, eps=1e-9):
    """
    Signed normalized distance from a numeric check's value to its threshold.

    direction="above": check passes when value >= threshold (higher is better)
    direction="below": check passes when value <= threshold (lower is better)

    Returns a signed float:
      > 0  value is on the passing side (magnitude = how comfortably)
      ~ 0  knife-edge
      < 0  value failed (magnitude = how badly)
    Returns None if value or threshold is None.

    Normalization: raw_gap / abs(threshold). When abs(threshold) < eps, fall
    back to abs(value). When both are ~0, return the raw absolute gap.
    """
    if value is None or threshold is None:
        return None
    try:
        raw_gap = (float(value) - float(threshold)) if direction == "above" else (float(threshold) - float(value))
        denom = abs(float(threshold)) if abs(float(threshold)) > eps else (abs(float(value)) if abs(float(value)) > eps else None)
        return raw_gap if denom is None else raw_gap / denom
    except (TypeError, ValueError):
        return None
