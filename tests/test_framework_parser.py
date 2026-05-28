"""
tests/test_framework_parser.py
------------------------------
Tests for analysis/framework_parser.py

Verifies:
  - Each lens returns the expected number of check reasonings
  - All reasoning strings are non-empty plain text
  - get_reasoning() returns correct type
  - Unknown lens raises ValueError
  - A framework file missing a Logic paragraph raises ValueError at import time
"""

import importlib
import sys
import types
import re
import pytest
from unittest.mock import patch
from pathlib import Path

from analysis import framework_parser


class TestBuffettParser:
    def test_returns_14_reasonings(self):
        reasonings = framework_parser.get_all_reasonings("buffett")
        assert len(reasonings) == 14, (
            f"Expected 14 Buffett checks, got {len(reasonings)}. "
            f"Keys found: {sorted(reasonings.keys())}"
        )

    def test_keys_are_integers_1_to_14(self):
        reasonings = framework_parser.get_all_reasonings("buffett")
        assert set(reasonings.keys()) == set(range(1, 15))

    def test_all_strings_nonempty(self):
        reasonings = framework_parser.get_all_reasonings("buffett")
        for num, text in reasonings.items():
            assert isinstance(text, str), f"Check #{num} is not a string"
            assert len(text.strip()) > 0, f"Check #{num} has empty reasoning"

    def test_no_markdown_bold_in_output(self):
        """Verify **text** markers are stripped."""
        reasonings = framework_parser.get_all_reasonings("buffett")
        for num, text in reasonings.items():
            assert "**" not in text, (
                f"Check #{num} still contains ** markers: {text[:80]}"
            )

    def test_get_reasoning_returns_string(self):
        result = framework_parser.get_reasoning("buffett", 1)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_reasoning_check_14(self):
        result = framework_parser.get_reasoning("buffett", 14)
        assert result is not None
        # The holdability check mentions the 20-year test
        assert "20" in result or "forever" in result.lower() or "Buffett" in result


class TestKKRParser:
    def test_returns_18_reasonings(self):
        reasonings = framework_parser.get_all_reasonings("kkr")
        assert len(reasonings) == 18, (
            f"Expected 18 KKR checks, got {len(reasonings)}. "
            f"Keys found: {sorted(reasonings.keys())}"
        )

    def test_keys_are_integers_1_to_18(self):
        reasonings = framework_parser.get_all_reasonings("kkr")
        assert set(reasonings.keys()) == set(range(1, 19))

    def test_all_strings_nonempty(self):
        reasonings = framework_parser.get_all_reasonings("kkr")
        for num, text in reasonings.items():
            assert len(text.strip()) > 0, f"KKR check #{num} has empty reasoning"


class TestMarksParser:
    def test_returns_14_reasonings(self):
        reasonings = framework_parser.get_all_reasonings("marks")
        assert len(reasonings) == 14, (
            f"Expected 14 Marks checks, got {len(reasonings)}. "
            f"Keys found: {sorted(reasonings.keys())}"
        )

    def test_all_strings_nonempty(self):
        reasonings = framework_parser.get_all_reasonings("marks")
        for num, text in reasonings.items():
            assert len(text.strip()) > 0, f"Marks check #{num} has empty reasoning"


class TestBlackstoneParser:
    def test_returns_14_reasonings(self):
        reasonings = framework_parser.get_all_reasonings("blackstone")
        assert len(reasonings) == 14, (
            f"Expected 14 Blackstone checks, got {len(reasonings)}. "
            f"Keys found: {sorted(reasonings.keys())}"
        )

    def test_all_strings_nonempty(self):
        reasonings = framework_parser.get_all_reasonings("blackstone")
        for num, text in reasonings.items():
            assert len(text.strip()) > 0, f"Blackstone check #{num} has empty reasoning"


class TestApolloParser:
    def test_returns_16_reasonings(self):
        reasonings = framework_parser.get_all_reasonings("apollo")
        assert len(reasonings) == 16, (
            f"Expected 16 Apollo checks, got {len(reasonings)}. "
            f"Keys found: {sorted(reasonings.keys())}"
        )

    def test_all_strings_nonempty(self):
        reasonings = framework_parser.get_all_reasonings("apollo")
        for num, text in reasonings.items():
            assert len(text.strip()) > 0, f"Apollo check #{num} has empty reasoning"


class TestAllLensesReasonings:
    def test_all_lenses_nonempty(self):
        """Broad sweep: every lens, every check, non-empty string."""
        for lens_name in ["buffett", "marks", "kkr", "blackstone", "apollo"]:
            reasonings = framework_parser.get_all_reasonings(lens_name)
            for num, text in reasonings.items():
                assert len(text.strip()) > 0, (
                    f"{lens_name} check #{num} has empty reasoning"
                )

    def test_unknown_lens_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unknown lens"):
            framework_parser.get_reasoning("soros", 1)

    def test_unknown_lens_get_all_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unknown lens"):
            framework_parser.get_all_reasonings("dalio")

    def test_missing_check_returns_none(self):
        """Check number 999 should return None, not raise."""
        result = framework_parser.get_reasoning("buffett", 999)
        assert result is None


class TestParserOnMissingLogic:
    """
    Verify that a framework file with a check section missing its **Logic:**
    paragraph raises ValueError at parse time.

    We test the _parse_framework private function directly to avoid the
    module-level cache complication.
    """

    def test_missing_logic_raises_valueerror(self, tmp_path):
        """A framework file where check 2 has no **Logic:** section."""
        bad_framework = tmp_path / "bad_lens.md"
        bad_framework.write_text(
            "# Bad Lens\n\n"
            "#### 1. First Check\n"
            "**Logic:** This is a valid logic paragraph for check 1.\n"
            "**Source:** Some source.\n\n"
            "#### 2. Second Check\n"
            "**Test:** some_value > 0\n"
            "**Source:** A source, but NO Logic section.\n\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="no \\*\\*Logic:\\*\\* paragraph"):
            framework_parser._parse_framework("bad_lens", bad_framework)

    def test_valid_framework_parses_cleanly(self, tmp_path):
        """Minimal valid framework file parses without error."""
        good_framework = tmp_path / "good_lens.md"
        good_framework.write_text(
            "# Good Lens\n\n"
            "#### 1. Only Check\n"
            "**Logic:** This is a solid logic paragraph.\n"
            "**Source:** Relevant source.\n\n",
            encoding="utf-8",
        )
        result = framework_parser._parse_framework("good_lens", good_framework)
        assert result == {1: "This is a solid logic paragraph."}
