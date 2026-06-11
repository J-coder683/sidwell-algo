"""
reports/explain.py
------------------
Layer-A: per-check human-readable explanation cards.
Layer-C: per-lens plain-English narrative summary (build_lens_narrative).
"""


def build_check_explanation(check_id: str, check: dict, *, points: int = 1) -> dict:
    """
    Builds a human-readable 3-part explanation for a single lens check.
    Returns a dict with status, title, what_why, finding, and judgment.
    """
    applicable = check.get("applicable", True)
    passed = check.get("passed", False)
    threshold_str = check.get("threshold_str", "")
    detail = check.get("detail", "")
    reasoning = check.get("framework_reasoning", "")
    name = check.get("name", check_id)

    # Derive status
    if not applicable:
        status = "na"
        status_label = "NOT ASSESSED"
        judgment = f"Not assessed \u2014 {detail}; excluded from the score, so it neither helps nor hurts the verdict."
    elif passed:
        status = "pass"
        status_label = "PASSED"
        judgment = f"Passed \u2014 the result clears the bar ({threshold_str})."
    else:
        status = "fail"
        status_label = "REJECTED"
        judgment = f"Rejected \u2014 the result misses the bar ({threshold_str})."

    # Derive title
    num_prefix = ""
    try:
        parts = check_id.split("_")
        if parts and parts[0].isdigit():
            # If the name already starts with the number, don't duplicate
            if not name.startswith(f"{parts[0]}."):
                num_prefix = f"{parts[0]}. "
    except Exception:
        pass

    # If name already has number from the dict, use it, else prepend
    title = f"{num_prefix}{name}"

    return {
        "status": status,
        "status_label": status_label,
        "title": title,
        "what_why": reasoning,
        "finding": detail,
        "judgment": judgment,
    }


# ---------------------------------------------------------------------------
# Layer-C: per-lens narrative summary
# ---------------------------------------------------------------------------

def _template_narrator(
    lens_name: str,
    lens_results: dict,
    ticker: str,
) -> str:
    """
    Deterministic template-based narrator (Layer-C default).

    Composes a 2-4 sentence plain-English summary from the already-computed
    check results.  No I/O, no API calls.
    """
    verdict = lens_results.get("verdict", "SKIP")
    reason = (lens_results.get("reason") or "").strip()
    score = lens_results.get("score", 0)
    max_score = lens_results.get("max_score", 0)
    checks = lens_results.get("checks") or {}

    # Classify checks
    passed_checks = [
        c for c in checks.values()
        if c.get("applicable", True) and c.get("passed", False)
    ]
    failed_checks = [
        c for c in checks.values()
        if c.get("applicable", True) and not c.get("passed", False)
    ]
    na_checks = [
        c for c in checks.values()
        if not c.get("applicable", True)
    ]

    sentences = []

    # --- Sentence 1: the call ---
    verdict_phrase = {
        "BUY": "a strong BUY",
        "WAIT": "a WAIT (attractive but not yet at the right price)",
        "WATCH": "a WATCH (merits monitoring but doesn't yet clear the bar)",
        "SKIP": "a SKIP (does not meet the framework's requirements)",
    }.get(verdict, f"a {verdict}")

    if reason:
        s1 = (
            f"Through {lens_name}'s lens, {ticker} is {verdict_phrase} "
            f"({score}/{max_score} checks passed). {reason}"
        )
    else:
        s1 = (
            f"Through {lens_name}'s lens, {ticker} is {verdict_phrase} "
            f"with {score} of {max_score} applicable checks cleared."
        )
    sentences.append(s1)

    # --- Sentence 2: strengths (skip for SKIP-via-precondition to avoid
    #     sounding positive when the reason field already explains the SKIP) ---
    _is_precondition_skip = (
        verdict == "SKIP"
        and reason
        and ("pre-condition" in reason.lower() or "failed part" in reason.lower())
    )

    if passed_checks and not _is_precondition_skip:
        # Name up to 3 standout passing checks
        sample_names = [c.get("name", "check") for c in passed_checks[:3]]
        if len(passed_checks) > 3:
            extras = len(passed_checks) - 3
            names_str = ", ".join(sample_names) + f", and {extras} more"
        else:
            names_str = _join_names(sample_names)
        sentences.append(f"Strengths include {names_str}.")

    # --- Sentence 3: weaknesses ---
    if failed_checks:
        fail_names = [c.get("name", "check") for c in failed_checks[:4]]
        if len(failed_checks) > 4:
            extras = len(failed_checks) - 4
            names_str = _join_names(fail_names) + f" and {extras} more"
        else:
            names_str = _join_names(fail_names)
        sentences.append(f"It failed on {names_str}.")

    # --- N/A note ---
    n_na = len(na_checks)
    if n_na > 0:
        check_word = "check" if n_na == 1 else "checks"
        sentences.append(
            f"{n_na} {check_word} couldn\u2019t be assessed "
            f"(qualitative signal unavailable or low-confidence) "
            f"and {'was' if n_na == 1 else 'were'} excluded from the score."
        )

    # --- Path-to-better (non-BUY only) ---
    if verdict != "BUY" and failed_checks:
        gate_names = [c.get("name", "check") for c in failed_checks[:2]]
        names_str = _join_names(gate_names)
        sentences.append(
            f"To reach BUY it would need {names_str} to clear."
        )

    return "  ".join(sentences)


# ---------------------------------------------------------------------------
# Future seam for an AI narrator
# ---------------------------------------------------------------------------
# When an AI narrator is ready, define it here as:
#
#   def _ai_narrator(lens_name: str, lens_results: dict, ticker: str) -> str:
#       """Call LLM API here.  Must return a ≤4-sentence string."""
#       raise NotImplementedError("AI narrator not yet implemented")
#
# Then pass it as narrator=_ai_narrator at call sites.  The public function
# build_lens_narrative() does NOT need to change.
# ---------------------------------------------------------------------------


def build_lens_narrative(
    lens_name: str,
    lens_results: dict,
    ticker: str,
    *,
    narrator=None,
) -> str:
    """
    Return a concise 2-4 sentence plain-English narrative for a lens result.

    Parameters
    ----------
    lens_name : str
        Human-readable lens name, e.g. "Warren Buffett".
    lens_results : dict
        Dict returned by evaluate_*_lens() — must contain at minimum
        "verdict", "reason", "score", "max_score", "checks".
    ticker : str
        Company ticker symbol.
    narrator : callable | None
        Optional override.  Signature: (lens_name, lens_results, ticker) -> str.
        When None (the default), the deterministic template narrator is used.
        Pass a future _ai_narrator here without changing any call site.

    Returns
    -------
    str
        Plain-English narrative. Never raises (returns a safe fallback on error).
    """
    if not lens_results:
        # Edge case: missing results
        return f"No results available for {ticker} under the {lens_name} lens."

    _narrator = narrator if narrator is not None else _template_narrator

    try:
        return _narrator(lens_name, lens_results, ticker)
    except Exception:
        # Defensive: never let a narrative failure break the UI/PDF/report
        verdict = (lens_results.get("verdict") or "SKIP")
        return (
            f"Through {lens_name}'s lens, {ticker} received a verdict of {verdict}. "
            f"(Narrative generation encountered an error.)"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _join_names(names: list) -> str:
    """Oxford-comma join for up to N names."""
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"
