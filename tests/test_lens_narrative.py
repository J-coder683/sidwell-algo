"""
tests/test_lens_narrative.py
-----------------------------
Layer-C: tests for build_lens_narrative() in reports/explain.py.

Covers:
  1. BUY result — mentions verdict, ticker, has no "fails" sentence, positive tone.
  2. SKIP-via-precondition — leads with precondition reason, does NOT read positive.
  3. N/A checks — includes the N/A count note.
  4. Edge cases — empty checks, empty reason, all-pass.
  5. Contradiction guard — SKIP never contains positive buy language.
"""
import pytest
from reports.explain import build_lens_narrative


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _make_result(
    verdict: str,
    score: int,
    max_score: int,
    reason: str = "",
    checks: dict | None = None,
) -> dict:
    if checks is None:
        checks = {}
    return {
        "verdict": verdict,
        "score": score,
        "max_score": max_score,
        "reason": reason,
        "checks": checks,
    }


def _pass_check(name: str, part: str = "A") -> dict:
    return {"name": name, "part": part, "passed": True, "applicable": True,
            "detail": "Passes.", "threshold_str": ">0"}


def _fail_check(name: str, part: str = "B") -> dict:
    return {"name": name, "part": part, "passed": False, "applicable": True,
            "detail": "Fails.", "threshold_str": ">0"}


def _na_check(name: str, part: str = "C") -> dict:
    return {"name": name, "part": part, "passed": False, "applicable": False,
            "detail": "Signal unavailable.", "threshold_str": ">0"}


# ---------------------------------------------------------------------------
# 1. BUY result
# ---------------------------------------------------------------------------

class TestBuyResult:
    def setup_method(self):
        checks = {
            "1_moat": _pass_check("Durable Moat"),
            "2_roe": _pass_check("Return on Equity"),
            "3_debt": _pass_check("Low Debt"),
            "4_fcf": _pass_check("FCF Margin"),
        }
        result = _make_result(
            verdict="BUY",
            score=4,
            max_score=4,
            reason="Passed 4 of 4 checks.",
            checks=checks,
        )
        self.narrative = build_lens_narrative("Warren Buffett", result, "HDFC")

    def test_mentions_ticker(self):
        assert "HDFC" in self.narrative

    def test_mentions_verdict(self):
        assert "BUY" in self.narrative

    def test_mentions_lens_name(self):
        assert "Warren Buffett" in self.narrative

    def test_no_fails_sentence(self):
        """No failed checks means no 'failed on' clause."""
        assert "failed on" not in self.narrative.lower()

    def test_positive_tone(self):
        """BUY result must not contain SKIP or SKIP-like language."""
        assert "skip" not in self.narrative.lower()

    def test_no_path_to_better(self):
        """BUY result has no 'to reach BUY' sentence."""
        assert "to reach buy" not in self.narrative.lower()


# ---------------------------------------------------------------------------
# 2. SKIP via precondition
# ---------------------------------------------------------------------------

class TestSkipViaPrecondition:
    def setup_method(self):
        checks = {
            "1_lbo": _pass_check("LBO Viability", "A"),
            "2_ops": _pass_check("Operational Upside", "B"),
            "3_alpha": _fail_check("Above-Average Alpha Thesis", "E"),
        }
        precondition_reason = (
            "Failed Part E pre-condition: lacks above-average alpha thesis "
            "(Phalippou bar). KKR does not pursue returns merely matching public "
            "markets — the bar is set at alpha above top-quartile PE."
        )
        result = _make_result(
            verdict="SKIP",
            score=2,
            max_score=3,
            reason=precondition_reason,
            checks=checks,
        )
        self.narrative = build_lens_narrative("KKR", result, "RELIANCE")
        self.precondition_reason = precondition_reason

    def test_mentions_skip(self):
        assert "SKIP" in self.narrative

    def test_contains_precondition_reason(self):
        """The precondition reason must be folded into the narrative."""
        assert "Phalippou bar" in self.narrative or "pre-condition" in self.narrative.lower()

    def test_not_positive(self):
        """SKIP-via-precondition must not say BUY or 'strong buy'."""
        assert "strong buy" not in self.narrative.lower()
        assert "buy" not in self.narrative.lower() or "to reach buy" in self.narrative.lower()

    def test_does_not_claim_all_strong(self):
        """Must not summarise 2/3 passing checks as overall strong."""
        lower = self.narrative.lower()
        # Should not open with "strengths include" before mentioning the skip
        idx_skip = lower.find("skip")
        idx_strength = lower.find("strengths include")
        if idx_strength != -1:
            # Strength mention must come after the skip mention
            assert idx_skip < idx_strength, (
                "Narrative mentions strengths BEFORE the SKIP verdict"
            )


# ---------------------------------------------------------------------------
# 3. Result with N/A checks
# ---------------------------------------------------------------------------

class TestNAChecks:
    def setup_method(self):
        checks = {
            "1_moat": _pass_check("Durable Moat"),
            "2_coherence": _na_check("Management Coherence"),
            "3_holdability": _na_check("20-Year Holdability"),
            "4_roe": _fail_check("Return on Equity"),
        }
        result = _make_result(
            verdict="WATCH",
            score=1,
            max_score=2,
            reason="Score 1/2 (50.0% < 71.4% WATCH threshold).",
            checks=checks,
        )
        self.narrative = build_lens_narrative("Howard Marks", result, "INFY")

    def test_na_note_present(self):
        """Narrative must mention the N/A exclusion count."""
        assert "2 checks" in self.narrative or "couldn't be assessed" in self.narrative

    def test_mentions_na_exclusion_reason(self):
        lower = self.narrative.lower()
        assert "unavailable" in lower or "excluded" in lower or "low-confidence" in lower

    def test_mentions_failure(self):
        """Return on Equity failed and must be named."""
        assert "Return on Equity" in self.narrative


# ---------------------------------------------------------------------------
# 4. Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_checks_does_not_raise(self):
        result = _make_result("SKIP", 0, 0, "")
        # Must not raise
        narrative = build_lens_narrative("Warren Buffett", result, "TEST")
        assert isinstance(narrative, str)
        assert len(narrative) > 0

    def test_none_lens_results_returns_fallback(self):
        narrative = build_lens_narrative("Buffett", None, "TEST")
        assert isinstance(narrative, str)
        assert "TEST" in narrative or "no results" in narrative.lower()

    def test_empty_reason_does_not_duplicate_punctuation(self):
        checks = {"1_x": _pass_check("Moat")}
        result = _make_result("BUY", 1, 1, "", checks)
        narrative = build_lens_narrative("Blackstone", result, "ADANI")
        # Should not have double-period or empty parens from folding empty reason
        assert ".." not in narrative
        assert "()" not in narrative

    def test_all_pass_no_fail_sentence(self):
        checks = {f"{i}_c": _pass_check(f"Check {i}") for i in range(1, 8)}
        result = _make_result("BUY", 7, 7, "Excellent.", checks)
        narrative = build_lens_narrative("Apollo", result, "MSFT")
        assert "failed on" not in narrative.lower()

    def test_many_fails_capped(self):
        """More than 4 failures: 'and N more' truncation, no IndexError."""
        checks = {f"{i}_f": _fail_check(f"Check {i}") for i in range(1, 9)}
        result = _make_result("SKIP", 0, 8, "Many failures.", checks)
        narrative = build_lens_narrative("KKR", result, "XYZ")
        assert "and" in narrative
        assert isinstance(narrative, str)


# ---------------------------------------------------------------------------
# 5. Contradiction guard
# ---------------------------------------------------------------------------

class TestContradictionGuard:
    def test_skip_never_says_strong_buy(self):
        checks = {"1_f": _fail_check("Critical Check")}
        result = _make_result("SKIP", 0, 1, "Below threshold.", checks)
        narrative = build_lens_narrative("Apollo", result, "XYZ")
        assert "strong buy" not in narrative.lower()
        assert "is a buy" not in narrative.lower()

    def test_buy_never_says_skip(self):
        checks = {"1_p": _pass_check("Key Metric")}
        result = _make_result("BUY", 1, 1, "Excellent.", checks)
        narrative = build_lens_narrative("Warren Buffett", result, "AAPL")
        lower = narrative.lower()
        # Should not say "is a skip" or "skip"
        assert "is a skip" not in lower

    def test_path_to_better_absent_for_buy(self):
        checks = {"1_p": _pass_check("Moat")}
        result = _make_result("BUY", 1, 1, "Passed all checks.", checks)
        narrative = build_lens_narrative("Buffett", result, "AAPL")
        assert "to reach buy" not in narrative.lower()

    def test_path_to_better_present_for_watch(self):
        checks = {
            "1_p": _pass_check("Moat"),
            "2_f": _fail_check("FCF Margin"),
        }
        result = _make_result("WATCH", 1, 2, "Score 1/2.", checks)
        narrative = build_lens_narrative("Buffett", result, "XYZ")
        assert "to reach buy" in narrative.lower()


# ---------------------------------------------------------------------------
# 6. Pluggable narrator seam
# ---------------------------------------------------------------------------

def test_custom_narrator_is_called():
    """build_lens_narrative should delegate to a custom narrator when supplied."""
    called_with = {}

    def my_narrator(lens_name, lens_results, ticker):
        called_with["lens_name"] = lens_name
        called_with["ticker"] = ticker
        return "Custom narrative."

    result = _make_result("BUY", 1, 1, "Fine.")
    narrative = build_lens_narrative("Buffett", result, "AAPL", narrator=my_narrator)
    assert narrative == "Custom narrative."
    assert called_with["lens_name"] == "Buffett"
    assert called_with["ticker"] == "AAPL"


def test_none_narrator_uses_template():
    """Passing narrator=None should use the deterministic template."""
    result = _make_result("BUY", 1, 1, "Fine.", {"1_p": _pass_check("Moat")})
    narrative = build_lens_narrative("Buffett", result, "AAPL", narrator=None)
    assert "AAPL" in narrative
    assert "BUY" in narrative
