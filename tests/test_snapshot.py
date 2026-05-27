import os
import pytest
from datetime import datetime
from pathlib import Path
from valuation.dcf import run_dcf_valuation
from lenses.buffett import evaluate_buffett_lens
from lenses.marks import evaluate_marks_lens
from lenses.kkr import evaluate_kkr_lens
from lenses.blackstone import evaluate_blackstone_lens
from lenses.apollo import evaluate_apollo_lens
from reports.render import render_markdown_report
from tests.fixture_company import FIXTURE_INPUTS, FIXTURE_MACRO, FIXTURE_RISK_FREE_RATE


def test_regression_snapshot(mock_qualitative):
    financials = FIXTURE_INPUTS.copy()
    macro = FIXTURE_MACRO.copy()
    rf = FIXTURE_RISK_FREE_RATE

    # Run pipeline
    dcf_res = run_dcf_valuation(financials, macro, rf)
    buffett_res = evaluate_buffett_lens(financials, dcf_res, qualitative_results=mock_qualitative)
    marks_res = evaluate_marks_lens(financials, dcf_res, qualitative_results=mock_qualitative)
    kkr_res = evaluate_kkr_lens(financials, dcf_res, qualitative_results=mock_qualitative)
    bx_res = evaluate_blackstone_lens(financials, dcf_res, qualitative_results=mock_qualitative)
    apollo_res = evaluate_apollo_lens(financials, dcf_res, qualitative_results=mock_qualitative)

    # Freeze the generated_at date to 2026-01-01 00:00:00
    frozen_date = datetime(2026, 1, 1, 0, 0, 0)

    expected_path = os.path.join(os.path.dirname(__file__), "expected_report.md")
    calculations_path = os.path.join(os.path.dirname(__file__), "expected_calculations.md")

    from unittest.mock import patch, mock_open
    with patch("builtins.open", mock_open()) as mock_file:
        report_path = render_markdown_report(
            dcf_res, buffett_res, financials,
            qualitative_results=mock_qualitative,
            marks_results=marks_res,
            kkr_results=kkr_res,
            blackstone_results=bx_res,
            apollo_results=apollo_res,
            generated_at=frozen_date,
            output_dir=Path("output")
        )

        # Combine written chunks
        write_calls = mock_file().write.call_args_list
        report_content = "".join(call[0][0] for call in write_calls)

    with open(expected_path, "r", encoding="utf-8") as f:
        expected_content = f.read()

    # Standardize line endings to avoid OS conflicts
    expected_standardized = expected_content.replace("\r\n", "\n").strip()
    report_standardized = report_content.replace("\r\n", "\n").strip()

    if report_standardized != expected_standardized:
        # Load and print expected calculations on failure so formulas are visible
        with open(calculations_path, "r", encoding="utf-8") as f:
            calculations_content = f.read()
        print("\n=== EXPECTED CALCULATIONS & DERIVATIONS ===")
        print(calculations_content.encode('ascii', errors='replace').decode('ascii'))
        print("============================================\n")

        # Also print diff
        import difflib
        diff = difflib.unified_diff(
            expected_standardized.splitlines(),
            report_standardized.splitlines(),
            fromfile="expected",
            tofile="actual"
        )
        print("\n=== DIFF ===")
        print("\n".join(diff).encode('ascii', errors='replace').decode('ascii'))
        print("============\n")

        assert report_standardized == expected_standardized, "Generated report does not match expected_report.md benchmark."
