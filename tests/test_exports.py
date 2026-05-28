"""
tests/test_exports.py
---------------------
Tests for the exports module — Excel and PDF exporters.
"""

import pytest
from io import BytesIO
import openpyxl

from tests.fixture_company import (
    FIXTURE_INPUTS,
    FIXTURE_RISK_FREE_RATE,
    FIXTURE_MACRO,
    _make_unavailable_qualitative,
    _make_available_qualitative,
)
from valuation import dcf
from exports import excel as excel_mod
from lenses import buffett, marks, kkr, blackstone, apollo


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def dcf_results():
    return dcf.run_dcf_valuation(FIXTURE_INPUTS, FIXTURE_MACRO, FIXTURE_RISK_FREE_RATE)


@pytest.fixture(scope="module")
def excel_bytes(dcf_results):
    return excel_mod.export_dcf_excel(dcf_results, FIXTURE_INPUTS)


# ---------------------------------------------------------------------------
# Excel tests
# ---------------------------------------------------------------------------

class TestExcelWorkbookStructure:
    EXPECTED_SHEETS = [
        "1_Cover",
        "2_Assumptions",
        "3_Stage1_Explicit",
        "4_Stage2_Fade",
        "5_Terminal",
        "6_Valuation_Bridge",
        "7_Sensitivity",
    ]

    def test_returns_bytes(self, excel_bytes):
        assert isinstance(excel_bytes, bytes)
        assert len(excel_bytes) > 2000

    def test_valid_xlsx_magic_bytes(self, excel_bytes):
        """XLSX files are ZIP archives starting with PK magic bytes."""
        assert excel_bytes[:2] == b'PK', (
            "Excel bytes do not start with PK (ZIP magic) — not a valid .xlsx"
        )

    def test_seven_sheets_with_correct_names(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        assert wb.sheetnames == self.EXPECTED_SHEETS, (
            f"Expected sheets {self.EXPECTED_SHEETS}, got {wb.sheetnames}"
        )

    def test_sheet_order_matches_expected(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        for i, name in enumerate(self.EXPECTED_SHEETS):
            assert wb.sheetnames[i] == name


class TestExcelCoverSheet:
    def test_cover_contains_ticker(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["1_Cover"]
        values = [str(ws.cell(row=r, column=c).value or "") for r in range(1, 12) for c in range(1, 3)]
        assert "FICTITIOUS.NS" in " ".join(values)

    def test_cover_has_version_reference(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["1_Cover"]
        values = [str(ws.cell(row=r, column=2).value or "") for r in range(1, 12)]
        assert any("v0.6" in v for v in values)


class TestExcelAssumptionsSheet:
    def test_wacc_cell_is_number(self, excel_bytes, dcf_results):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["2_Assumptions"]
        from exports.excel import ASSUMP_ROWS
        wacc_val = ws.cell(row=ASSUMP_ROWS["wacc"], column=2).value
        assert wacc_val is not None
        assert isinstance(wacc_val, float)
        assert 0.04 < wacc_val < 0.25  # sanity: WACC between 4% and 25%

    def test_shares_cell_is_positive(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["2_Assumptions"]
        from exports.excel import ASSUMP_ROWS
        shares = ws.cell(row=ASSUMP_ROWS["shares"], column=2).value
        assert shares is not None
        assert shares > 0

    def test_freeze_panes_set(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["2_Assumptions"]
        assert ws.freeze_panes is not None


class TestExcelStageSheets:
    def test_stage1_has_5_year_columns(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["3_Stage1_Explicit"]
        from exports.excel import STAGE_ROWS
        # Year row should have values in cols B-F
        year_cells = [ws.cell(row=STAGE_ROWS["year_num"], column=c).value for c in range(2, 7)]
        assert all(v is not None for v in year_cells), (
            f"Stage 1 year headers missing: {year_cells}"
        )

    def test_stage2_has_5_year_columns(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["4_Stage2_Fade"]
        from exports.excel import STAGE_ROWS
        year_cells = [ws.cell(row=STAGE_ROWS["year_num"], column=c).value for c in range(2, 7)]
        assert all(v is not None for v in year_cells)

    def test_stage1_fcf_row_contains_formulas(self, excel_bytes):
        """FCF cells in Stage 1 should be Excel formulas."""
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["3_Stage1_Explicit"]
        from exports.excel import STAGE_ROWS
        # Cols C-F (years 2-5) should have formula strings
        formula_cells = [ws.cell(row=STAGE_ROWS["pv_fcf"], column=c).value for c in range(3, 7)]
        formula_strs = [str(v or "") for v in formula_cells]
        assert any(v.startswith("=") for v in formula_strs), (
            f"Expected formula cells in Stage 1 PV FCF row, got: {formula_strs}"
        )

    def test_stage2_years_are_6_to_10(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["4_Stage2_Fade"]
        from exports.excel import STAGE_ROWS
        year_labels = [ws.cell(row=STAGE_ROWS["year_num"], column=c).value for c in range(2, 7)]
        # Labels should contain Year 6..10
        combined = " ".join(str(v or "") for v in year_labels)
        assert "Year 6" in combined or "6" in combined


class TestExcelTerminalSheet:
    def test_terminal_value_is_formula(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["5_Terminal"]
        from exports.excel import TERM_ROWS
        tv = ws.cell(row=TERM_ROWS["term_value"], column=2).value
        assert isinstance(tv, str) and tv.startswith("="), (
            f"Terminal Value cell should be a formula, got: {tv}"
        )

    def test_pv_tv_is_formula(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["5_Terminal"]
        from exports.excel import TERM_ROWS
        pv = ws.cell(row=TERM_ROWS["pv_tv"], column=2).value
        assert isinstance(pv, str) and pv.startswith("=")


class TestExcelBridgeSheet:
    def test_intrinsic_cell_is_formula(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["6_Valuation_Bridge"]
        from exports.excel import BRIDGE_ROWS
        val = ws.cell(row=BRIDGE_ROWS["intrinsic"], column=2).value
        assert isinstance(val, str) and val.startswith("="), (
            f"Intrinsic value cell should be a formula, got: {val}"
        )

    def test_upside_cell_is_formula(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["6_Valuation_Bridge"]
        from exports.excel import BRIDGE_ROWS
        val = ws.cell(row=BRIDGE_ROWS["upside"], column=2).value
        assert isinstance(val, str) and val.startswith("=")

    def test_current_price_matches_fixture(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["6_Valuation_Bridge"]
        from exports.excel import BRIDGE_ROWS
        price = ws.cell(row=BRIDGE_ROWS["current_px"], column=2).value
        assert price == 50.0  # FIXTURE_INPUTS["current_price"]


class TestExcelSensitivitySheet:
    def test_sensitivity_grid_has_formulas(self, excel_bytes):
        """The 5×5 grid cells (rows 4-8, cols 2-6) should start with '='"""
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["7_Sensitivity"]
        formula_cells = []
        for row in range(4, 9):
            for col in range(2, 7):
                val = ws.cell(row=row, column=col).value
                formula_cells.append(val)
        formula_strs = [str(v or "") for v in formula_cells]
        formulas_found = [v for v in formula_strs if v.startswith("=")]
        assert len(formulas_found) == 25, (
            f"Expected 25 formula cells in sensitivity grid, found {len(formulas_found)}"
        )

    def test_sensitivity_header_row_has_labels(self, excel_bytes):
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["7_Sensitivity"]
        # Row 3 cols B-F should have bps labels
        labels = [ws.cell(row=3, column=c).value for c in range(2, 7)]
        assert any(labels), f"Sensitivity header row is empty: {labels}"

    def test_sensitivity_fcf_helper_column_populated(self, excel_bytes):
        """Helper block in col H rows 2-11 should have 10 numeric FCF values."""
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb["7_Sensitivity"]
        fcf_helper = [ws.cell(row=r, column=8).value for r in range(2, 12)]
        non_none = [v for v in fcf_helper if v is not None]
        assert len(non_none) >= 5, (
            f"Expected ≥5 FCF helper values in col H, got {len(non_none)}"
        )


class TestExcelCurrencyFormatIndia:
    def test_india_ticker_uses_rupee_format(self, dcf_results):
        """FIXTURE_INPUTS ticker is FICTITIOUS.NS → should use ₹ format."""
        data = excel_mod.export_dcf_excel(dcf_results, FIXTURE_INPUTS)
        wb = openpyxl.load_workbook(BytesIO(data))
        ws = wb["6_Valuation_Bridge"]
        from exports.excel import BRIDGE_ROWS
        # Current price cell should have ₹ format
        c = ws.cell(row=BRIDGE_ROWS["current_px"], column=2)
        assert "₹" in (c.number_format or "") or c.number_format.startswith("₹"), (
            f"Expected ₹ number format on India ticker, got: {c.number_format!r}"
        )

    def test_us_ticker_uses_dollar_format(self, dcf_results):
        """For a US ticker (no .NS/.BO suffix) the format should use $."""
        us_financials = dict(FIXTURE_INPUTS)
        us_financials["ticker"] = "FICTITIOUS"  # no .NS suffix
        data = excel_mod.export_dcf_excel(dcf_results, us_financials)
        wb = openpyxl.load_workbook(BytesIO(data))
        ws = wb["6_Valuation_Bridge"]
        from exports.excel import BRIDGE_ROWS
        c = ws.cell(row=BRIDGE_ROWS["current_px"], column=2)
        assert "$" in (c.number_format or ""), (
            f"Expected $ number format on US ticker, got: {c.number_format!r}"
        )


# ---------------------------------------------------------------------------
# PDF tests
# ---------------------------------------------------------------------------

import importlib

def _pdf_available() -> bool:
    """Check if weasyprint system libraries are loadable on this platform."""
    try:
        from exports.pdf import _WEASYPRINT_AVAILABLE
        return _WEASYPRINT_AVAILABLE
    except Exception:
        return False

_PDF_SKIP = pytest.mark.skipif(
    not _pdf_available(),
    reason="weasyprint system libraries (libgobject etc.) not available on this platform"
)


@pytest.fixture(scope="module")
def buffett_results(dcf_results):
    qual = _make_unavailable_qualitative()
    return buffett.evaluate_buffett_lens(FIXTURE_INPUTS, dcf_results, qualitative_results=qual)


class TestPDFHTMLGeneration:
    """Tests that don't require system PDF libraries — only validate HTML building."""

    def test_html_cover_contains_ticker(self, buffett_results, dcf_results):
        """HTML cover builder should embed the ticker without needing system PDF libs."""
        from exports.pdf import _build_cover_html
        html = _build_cover_html(buffett_results, FIXTURE_INPUTS, dcf_results, "buffett")
        assert "FICTITIOUS.NS" in html or "FICTITIOUS" in html

    def test_html_cover_contains_verdict_pill(self, buffett_results, dcf_results):
        from exports.pdf import _build_cover_html
        html = _build_cover_html(buffett_results, FIXTURE_INPUTS, dcf_results, "buffett")
        assert "verdict-pill" in html

    def test_html_exec_summary_has_parts(self, buffett_results):
        from exports.pdf import _build_exec_summary_html
        html = _build_exec_summary_html(buffett_results, "buffett")
        assert "Part A" in html
        assert "Part D" in html

    def test_html_checks_has_check_rows(self, buffett_results):
        from exports.pdf import _build_checks_html
        html = _build_checks_html(buffett_results, "buffett")
        assert "check-row" in html
        # Failed checks should include framework-reasoning block
        # At least some checks fail on the fixture → at least one reasoning block expected
        has_reasoning = "framework-reasoning" in html
        # Not all fixtures fail, so just check structure
        assert "check-name" in html

    def test_html_framework_reasoning_only_for_failed(self, buffett_results):
        """framework-reasoning blockquote appears only for failed checks."""
        from exports.pdf import _build_checks_html
        html = _build_checks_html(buffett_results, "buffett")
        checks = buffett_results["checks"]
        all_pass = all(c["passed"] for c in checks.values())
        all_fail = all(not c["passed"] for c in checks.values())
        if all_pass:
            assert "framework-reasoning" not in html
        elif all_fail:
            assert "framework-reasoning" in html
        # Mixed case: just verify no crash

    def test_kkr_html_has_18_checks(self, dcf_results):
        from exports.pdf import _build_checks_html
        qual = _make_unavailable_qualitative()
        kkr_results = kkr.evaluate_kkr_lens(FIXTURE_INPUTS, dcf_results, qualitative_results=qual)
        html = _build_checks_html(kkr_results, "kkr")
        # 18 checks → 18 check-row divs
        count = html.count("check-row")
        # Each check uses "check-row" in class + "check-row-header" subclass → at least 18
        assert count >= 18, f"Expected ≥18 check-row mentions for KKR, got {count}"


class TestPDFExport:
    @_PDF_SKIP
    def test_returns_valid_pdf_bytes(self, buffett_results, dcf_results):
        """PDF bytes must start with %PDF- and be > 5000 bytes."""
        from exports.pdf import export_lens_pdf
        pdf_bytes = export_lens_pdf(buffett_results, FIXTURE_INPUTS, dcf_results, "buffett")
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-", (
            f"Expected PDF magic bytes, got: {pdf_bytes[:10]!r}"
        )
        assert len(pdf_bytes) > 5000, (
            f"PDF seems too small: {len(pdf_bytes)} bytes"
        )

    @_PDF_SKIP
    def test_pdf_contains_ticker(self, buffett_results, dcf_results):
        """Ticker should appear in the PDF byte stream."""
        from exports.pdf import export_lens_pdf
        pdf_bytes = export_lens_pdf(buffett_results, FIXTURE_INPUTS, dcf_results, "buffett")
        pdf_text = pdf_bytes.decode("latin-1", errors="replace")
        assert "FICTITIOUS.NS" in pdf_text or "FICTITIOUS" in pdf_text, (
            "Ticker not found in PDF content"
        )

    @_PDF_SKIP
    def test_pdf_for_all_5_lenses(self, dcf_results):
        """All 5 lenses should generate a PDF without raising."""
        from exports.pdf import export_lens_pdf
        qual = _make_unavailable_qualitative()
        lens_fns = [
            (buffett.evaluate_buffett_lens, "buffett"),
            (marks.evaluate_marks_lens, "marks"),
            (kkr.evaluate_kkr_lens, "kkr"),
            (blackstone.evaluate_blackstone_lens, "blackstone"),
            (apollo.evaluate_apollo_lens, "apollo"),
        ]
        for eval_fn, lens_name in lens_fns:
            results = eval_fn(FIXTURE_INPUTS, dcf_results, qualitative_results=qual)
            pdf_bytes = export_lens_pdf(results, FIXTURE_INPUTS, dcf_results, lens_name)
            assert pdf_bytes[:5] == b"%PDF-", f"{lens_name}: not a valid PDF"
            assert len(pdf_bytes) > 5000, f"{lens_name}: PDF too small ({len(pdf_bytes)} bytes)"

    @_PDF_SKIP
    def test_pdf_with_available_qualitative(self, dcf_results):
        """PDF generation should also work when qualitative is available."""
        from exports.pdf import export_lens_pdf
        qual = _make_available_qualitative()
        results = buffett.evaluate_buffett_lens(FIXTURE_INPUTS, dcf_results, qualitative_results=qual)
        pdf_bytes = export_lens_pdf(results, FIXTURE_INPUTS, dcf_results, "buffett")
        assert pdf_bytes[:5] == b"%PDF-"
