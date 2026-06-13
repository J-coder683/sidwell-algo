"""Tests for lenses/_scoring.py — the exclude-from-denominator policy helpers."""
import math
import pytest
from lenses import _scoring


# --- resolve_soft: three-state classification -------------------------------

@pytest.mark.parametrize("q_status,verdict", [
    ("unavailable", "owner_oriented"),  # status not available → N/A regardless of verdict
    ("available", None),
    ("available", ""),
    ("available", "unclear"),
    ("available", "unknown"),
])
def test_resolve_soft_na(q_status, verdict):
    passed, applicable, detail = _scoring.resolve_soft(q_status, verdict, {"owner_oriented"})
    assert applicable is False
    assert passed is False
    assert "excluded" in detail.lower() or "n/a" in detail.lower()


def test_resolve_soft_positive():
    passed, applicable, _ = _scoring.resolve_soft("available", "coherent", {"coherent"})
    assert (passed, applicable) == (True, True)


def test_resolve_soft_negative_counts_against():
    """A real adverse verdict is applicable AND failing — this is the discernment we want."""
    passed, applicable, _ = _scoring.resolve_soft("available", "incoherent", {"coherent"})
    assert (passed, applicable) == (False, True)


# --- tally: only applicable checks count ------------------------------------

def test_tally_excludes_na():
    checks = {
        "1": {"passed": True, "applicable": True},
        "2": {"passed": False, "applicable": True},
        "3": {"passed": False, "applicable": False},   # N/A — excluded both sides
        "4": {"passed": True},                          # missing flag defaults applicable
    }
    score, max_score = _scoring.tally(checks)
    assert score == 2          # checks 1 and 4
    assert max_score == 3      # checks 1, 2, 4 (not 3)


def test_tally_na_passed_is_ignored():
    """An N/A check that happens to have passed=True must not leak into score."""
    checks = {"x": {"passed": True, "applicable": False}}
    assert _scoring.tally(checks) == (0, 0)


# --- meets: ratio threshold preserves calibration ---------------------------

def test_meets_full_data_is_identical_to_absolute():
    """With max_score == orig_max, meets() == (score >= threshold)."""
    for score in range(0, 15):
        assert _scoring.meets(score, 14, 14, 12) == (score >= 12)


def test_meets_shrunk_denominator_is_proportional():
    # Buffett BUY = 12/14 ≈ 0.857. With max_score 12, need score/12 >= 12/14.
    # 11/12 = 0.917 >= 0.857 → True ; 10/12 = 0.833 < 0.857 → False
    assert _scoring.meets(11, 12, 14, 12) is True
    assert _scoring.meets(10, 12, 14, 12) is False


def test_meets_zero_denominator_is_false():
    assert _scoring.meets(0, 0, 14, 12) is False


# --- proportional_gate ------------------------------------------------------

@pytest.mark.parametrize("n,expected_threshold", [
    (6, 4), (5, 4), (4, 3), (3, 2), (2, 2), (1, 1), (0, 0),
])
def test_proportional_gate_threshold(n, expected_threshold):
    levers = [(True, True)] * n
    passed, n_app, threshold, gate = _scoring.proportional_gate(levers)
    assert n_app == n
    assert threshold == expected_threshold


def test_proportional_gate_full_data_matches_4_of_6():
    levers = [(True, True), (True, True), (True, True), (True, True), (False, True), (False, True)]
    _, _, _, gate = _scoring.proportional_gate(levers)
    assert gate is True   # 4 of 6 passed


def test_proportional_gate_excludes_na_levers():
    # 3 applicable (2 pass), 3 N/A → threshold ceil(4/6*3)=2 → 2>=2 → pass
    levers = [(True, True), (True, True), (False, True), (False, False), (False, False), (False, False)]
    passed, n_app, threshold, gate = _scoring.proportional_gate(levers)
    assert (passed, n_app, threshold) == (2, 3, 2)
    assert gate is True


def test_proportional_gate_all_na_cannot_clear():
    levers = [(False, False)] * 6
    _, _, _, gate = _scoring.proportional_gate(levers)
    assert gate is False


# --- resolve_soft: low-confidence exclusion (v0.12) --------------------------

def test_resolve_soft_low_confidence_excluded():
    """A low-confidence signal — even with the correct verdict — must be excluded (N/A)."""
    passed, applicable, detail = _scoring.resolve_soft(
        "available", "owner_oriented", {"owner_oriented"}, confidence="low"
    )
    assert applicable is False
    assert passed is False
    assert "low-confidence" in detail.lower() or "excluded" in detail.lower()


def test_resolve_soft_medium_confidence_counts():
    """Medium confidence should NOT trigger exclusion — it is a valid signal."""
    passed, applicable, _ = _scoring.resolve_soft(
        "available", "owner_oriented", {"owner_oriented"}, confidence="medium"
    )
    assert (passed, applicable) == (True, True)


def test_resolve_soft_high_confidence_counts():
    """High confidence: standard positive path."""
    passed, applicable, _ = _scoring.resolve_soft(
        "available", "coherent", {"coherent"}, confidence="high"
    )
    assert (passed, applicable) == (True, True)


def test_resolve_soft_none_confidence_is_neutral():
    """confidence=None (old call sites, missing field) must not trigger exclusion."""
    passed, applicable, _ = _scoring.resolve_soft(
        "available", "humble", {"humble"}, confidence=None
    )
    assert (passed, applicable) == (True, True)


def test_resolve_soft_low_confidence_adverse_excluded():
    """Even an adverse verdict with low confidence is N/A (not a counted fail)."""
    passed, applicable, _ = _scoring.resolve_soft(
        "available", "incoherent", {"coherent"}, confidence="low"
    )
    assert applicable is False


# --- evidence_quote threading through lens detail strings --------------------

def test_buffett_check11_evidence_quote_in_detail():
    """Buffett check 11 (management coherence) detail must include the evidence_quote when provided."""
    from lenses.buffett import evaluate_buffett_lens
    from tests.test_buffett import get_perfect_financials, get_perfect_dcf

    fin, dcf = get_perfect_financials(), get_perfect_dcf(100.0)
    qual = {
        "status": "available",
        "coherence_assessment": {
            "verdict": "coherent",
            "reasoning": "Consistent.",
            "evidence_quote": "Figures tie to AR [test.pdf]",
            "confidence": "high",
        },
        "owner_orientation_signal": {"verdict": "owner_oriented", "confidence": "high"},
        "holdability_assessment": {"verdict": "holdable_20y", "confidence": "high"},
        "why_now_signal": {"verdict": "dislocation_present", "confidence": "high"},
    }
    result = evaluate_buffett_lens(fin, dcf, qualitative_results=qual)
    detail_11 = result["checks"]["11_mgmt_coherence"]["detail"]
    assert "Figures tie to AR" in detail_11


def test_marks_check13_low_confidence_excluded():
    """Marks check 13 (management humility) must be N/A when confidence='low'."""
    from lenses.marks import evaluate_marks_lens
    from tests.test_marks import get_base_financials as marks_fin, get_base_dcf as marks_dcf

    fin, dcf = marks_fin(), marks_dcf()
    qual = {
        "status": "available",
        "cycle_position": {"sector_cycle": "mid_cycle", "confidence": "high"},
        "variant_perception": {"variant_present": True, "specificity": "high", "confidence": "high"},
        "management_humility": {
            "verdict": "humble",
            "evidence": "Modest.",
            "evidence_quote": "We were wrong about Q3 [test.pdf]",
            "confidence": "low",  # <-- should be excluded
        },
        "why_now_signal": {"verdict": "dislocation_present", "confidence": "high"},
    }
    result = evaluate_marks_lens(fin, dcf, qualitative_results=qual)
    check_13 = result["checks"]["13_management_humility"]
    assert "low-confidence" in check_13["detail"].lower() or "excluded" in check_13["detail"].lower()

# --- proximity --------------------------------------------------------------

def test_proximity_valid_above():
    # threshold 10, value 12, direction "above"
    # distance = (12 - 10) / 10 = 0.2
    assert math.isclose(_scoring.proximity(12.0, 10.0, "above"), 0.2)
    # threshold 10, value 8, direction "above"
    # distance = (8 - 10) / 10 = -0.2
    assert math.isclose(_scoring.proximity(8.0, 10.0, "above"), -0.2)

def test_proximity_valid_below():
    # threshold 20, value 15, direction "below"
    # distance = (20 - 15) / 20 = 0.25
    assert math.isclose(_scoring.proximity(15.0, 20.0, "below"), 0.25)
    # threshold 20, value 25, direction "below"
    # distance = (20 - 25) / 20 = -0.25
    assert math.isclose(_scoring.proximity(25.0, 20.0, "below"), -0.25)

def test_proximity_zero_threshold():
    # threshold 0. We should normalize by max(abs(0), abs(value))
    # value 5, direction "above"
    # distance = 5 - 0 = 5. denom = 5 -> 1.0
    assert math.isclose(_scoring.proximity(5.0, 0.0, "above"), 1.0)
    assert math.isclose(_scoring.proximity(-5.0, 0.0, "above"), -1.0)
    assert math.isclose(_scoring.proximity(5.0, 0.0, "below"), -1.0)

def test_proximity_both_zero():
    # value 0, threshold 0 -> denom is 0, should fallback to denom=1.0 or return 0.0
    assert _scoring.proximity(0.0, 0.0, "above") == 0.0

def test_proximity_invalid_inputs():
    assert _scoring.proximity(None, 10.0, "above") is None
    assert _scoring.proximity(10.0, None, "above") is None
    assert _scoring.proximity("string", 10.0, "above") is None
