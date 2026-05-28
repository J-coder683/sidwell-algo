"""
tests/test_framework_reasoning_integration.py
----------------------------------------------
Integration tests verifying that framework_reasoning is present and non-empty
in every check dict returned by each of the 5 lens evaluators.

These tests confirm that the Step 2 injection (framework_reasoning field added
to each check in all 5 lens files) is working end-to-end.
"""

import pytest
from tests.fixture_company import (
    FIXTURE_INPUTS,
    FIXTURE_RISK_FREE_RATE,
    FIXTURE_MACRO,
    _make_unavailable_qualitative,
)
from valuation import dcf
from lenses import buffett, marks, kkr, blackstone, apollo


# ---------------------------------------------------------------------------
# Shared fixture — cheap to build, reused across all 5 tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def dcf_results():
    return dcf.run_dcf_valuation(FIXTURE_INPUTS, FIXTURE_MACRO, FIXTURE_RISK_FREE_RATE)


@pytest.fixture(scope="module")
def qual():
    return _make_unavailable_qualitative()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_all_checks_have_reasoning(lens_name: str, lens_results: dict):
    checks = lens_results["checks"]
    assert len(checks) > 0, f"{lens_name}: no checks returned"
    for check_id, check_dict in checks.items():
        assert "framework_reasoning" in check_dict, (
            f"{lens_name} check '{check_id}' is missing 'framework_reasoning' key"
        )
        reasoning = check_dict["framework_reasoning"]
        assert isinstance(reasoning, str), (
            f"{lens_name} check '{check_id}': framework_reasoning is not a str "
            f"(got {type(reasoning).__name__})"
        )
        assert len(reasoning.strip()) > 0, (
            f"{lens_name} check '{check_id}': framework_reasoning is empty string"
        )
        # Confirm markdown stripping happened
        assert "**" not in reasoning, (
            f"{lens_name} check '{check_id}': framework_reasoning still contains ** markers"
        )


# ---------------------------------------------------------------------------
# Per-lens tests
# ---------------------------------------------------------------------------

class TestBuffettFrameworkReasoning:
    def test_all_14_checks_have_reasoning(self, dcf_results, qual):
        results = buffett.evaluate_buffett_lens(
            FIXTURE_INPUTS, dcf_results, qualitative_results=qual
        )
        assert results["score"] >= 0
        _assert_all_checks_have_reasoning("buffett", results)

    def test_exactly_14_checks(self, dcf_results, qual):
        results = buffett.evaluate_buffett_lens(
            FIXTURE_INPUTS, dcf_results, qualitative_results=qual
        )
        assert len(results["checks"]) == 14


class TestMarksFrameworkReasoning:
    def test_all_14_checks_have_reasoning(self, dcf_results, qual):
        results = marks.evaluate_marks_lens(
            FIXTURE_INPUTS, dcf_results, qualitative_results=qual
        )
        _assert_all_checks_have_reasoning("marks", results)

    def test_exactly_14_checks(self, dcf_results, qual):
        results = marks.evaluate_marks_lens(
            FIXTURE_INPUTS, dcf_results, qualitative_results=qual
        )
        assert len(results["checks"]) == 14


class TestKKRFrameworkReasoning:
    def test_all_18_checks_have_reasoning(self, dcf_results, qual):
        results = kkr.evaluate_kkr_lens(
            FIXTURE_INPUTS, dcf_results, qualitative_results=qual
        )
        _assert_all_checks_have_reasoning("kkr", results)

    def test_exactly_18_checks(self, dcf_results, qual):
        results = kkr.evaluate_kkr_lens(
            FIXTURE_INPUTS, dcf_results, qualitative_results=qual
        )
        assert len(results["checks"]) == 18


class TestBlackstoneFrameworkReasoning:
    def test_all_14_checks_have_reasoning(self, dcf_results, qual):
        results = blackstone.evaluate_blackstone_lens(
            FIXTURE_INPUTS, dcf_results, qualitative_results=qual
        )
        _assert_all_checks_have_reasoning("blackstone", results)

    def test_exactly_14_checks(self, dcf_results, qual):
        results = blackstone.evaluate_blackstone_lens(
            FIXTURE_INPUTS, dcf_results, qualitative_results=qual
        )
        assert len(results["checks"]) == 14


class TestApolloFrameworkReasoning:
    def test_all_16_checks_have_reasoning(self, dcf_results, qual):
        results = apollo.evaluate_apollo_lens(
            FIXTURE_INPUTS, dcf_results, qualitative_results=qual
        )
        _assert_all_checks_have_reasoning("apollo", results)

    def test_exactly_16_checks(self, dcf_results, qual):
        results = apollo.evaluate_apollo_lens(
            FIXTURE_INPUTS, dcf_results, qualitative_results=qual
        )
        assert len(results["checks"]) == 16
