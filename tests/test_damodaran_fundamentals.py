import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from data.public import fetch_damodaran_industry_fundamentals, format_industry_benchmark_doc

# Realistic 'Industry Averages' data per file, mirroring Damodaran's ACTUAL columns
# (margin.xls / histgr.xls / fundgrEB.xls). These are what the live workbooks contain.
_MARGIN = pd.DataFrame({
    "Industry Name": ["Computers/Peripherals", "Software (System & Application)"],
    "Gross Margin": ["40.0%", "70.0%"],
    "Net Margin": ["20.0%", "25.0%"],
    "Pre-tax, Pre-stock compensation Operating Margin": ["30.0%", "35.0%"],
    "Pre-tax Unadjusted Operating Margin": ["25.5%", "28.0%"],
    "EBITDA/Sales": ["33.0%", "40.0%"],
})
_HISTGR = pd.DataFrame({
    "Industry Name": ["Computers/Peripherals", "Software (System & Application)"],
    "CAGR in Revenues- Last 5 years": ["10.0%", "18.0%"],
    "Expected Growth in Revenues - Next 2 years": ["7.0%", "12.0%"],
    "Expected Growth in Revenues - Next 5 years": ["8.5%", "14.0%"],
})
_FUND = pd.DataFrame({
    "Industry Name": ["Computers/Peripherals", "Software (System & Application)"],
    "ROC": ["12.5%", "20.0%"],
    "Reinvestment Rate": ["40.0%", "55.0%"],
    "Expected Growth in EBIT": ["6.0%", "10.0%"],
})


def _which(path):
    p = str(path)
    if "margin" in p:
        return _MARGIN
    if "histgr" in p:
        return _HISTGR
    if "fundgrEB" in p:
        return _FUND
    return pd.DataFrame({"Industry Name": []})


def _make_side_effect(found=True, header_row=8):
    """Mimic the real workbook: a probe read (header=None) whose first column holds
    metadata rows then 'Industry Name' at header_row, then the data read (header=int)."""
    def side_effect(path, sheet_name=None, header=None, nrows=None, **kw):
        if header is None:                                   # probe to locate header row
            col0 = ["metadata"] * header_row + ["Industry Name"]
            return pd.DataFrame({0: col0})
        data = _which(path)                                  # data read
        if not found:
            data = data.copy()
            data["Industry Name"] = ["Some Other Industry"] * len(data)
        return data
    return side_effect


@pytest.fixture
def patched():
    xl = MagicMock()
    xl.sheet_names = ["Variables & FAQ", "Industry Averages"]   # glossary first, data second
    with patch("data.public.requests.get"), \
         patch("data.public.cache.is_expired", return_value=False), \
         patch("data.public.cache.get_cache_path", side_effect=lambda k: f"/tmp/{k}"), \
         patch("data.public.cache.set_bytes"), \
         patch("os.path.exists", return_value=True), \
         patch("data.public.pd.ExcelFile", return_value=xl), \
         patch("data.public.pd.read_excel") as mock_excel:
        yield mock_excel


def test_us_success_real_columns(patched):
    patched.side_effect = _make_side_effect()
    res = fetch_damodaran_industry_fundamentals("AAPL", {"scraped_industry": "consumer electronics"})
    assert res["available"] is True
    assert res["geography"] == "us"
    assert res["target_industry"] == "Computers/Peripherals"
    # Prefers 'Pre-tax Unadjusted Operating Margin' (0.255), NOT the pre-stock-comp 0.30
    assert abs(res["industry_operating_margin"] - 0.255) < 1e-6
    assert abs(res["industry_net_margin"] - 0.20) < 1e-6
    # Prefers forward 'Next 5 years' (0.085), NOT next-2y (0.07) or last-5y CAGR (0.10)
    assert abs(res["industry_revenue_growth"] - 0.085) < 1e-6
    assert abs(res["industry_roic"] - 0.125) < 1e-6
    assert abs(res["industry_reinvestment_rate"] - 0.40) < 1e-6


def test_reads_data_sheet_not_glossary(patched):
    """Regression for the sheet-selection bug: must read 'Industry Averages',
    never the 'Variables & FAQ' glossary (which was being read as sheet 0)."""
    patched.side_effect = _make_side_effect()
    fetch_damodaran_industry_fundamentals("AAPL", {"scraped_industry": "consumer electronics"})
    sheets_used = {kw.get("sheet_name") for _, kw in patched.call_args_list}
    assert "Industry Averages" in sheets_used
    assert "Variables & FAQ" not in sheets_used


def test_india_uses_india_files(patched):
    patched.side_effect = _make_side_effect()
    res = fetch_damodaran_industry_fundamentals("RELIANCE.NS", {"scraped_industry": "refineries & marketing"})
    assert res["geography"] == "india"
    paths = [a[0][0] for a in patched.call_args_list]
    assert any("marginIndia.xls" in p for p in paths)
    assert any("histgrIndia.xls" in p for p in paths)
    assert any("fundgrEBIndia.xls" in p for p in paths)


def test_industry_not_found(patched):
    patched.side_effect = _make_side_effect(found=False)
    res = fetch_damodaran_industry_fundamentals("AAPL", {"scraped_industry": "consumer electronics"})
    assert res["available"] is False
    assert res["industry_operating_margin"] is None
    assert res["industry_revenue_growth"] is None


def test_header_row_detection_varies(patched):
    # histgr/fundgr put the header on row 7, margin on row 8 — both must be found.
    patched.side_effect = _make_side_effect(header_row=7)
    res = fetch_damodaran_industry_fundamentals("AAPL", {"scraped_industry": "consumer electronics"})
    assert res["available"] is True


def test_format_industry_benchmark_doc():
    assert format_industry_benchmark_doc({"available": False}) is None
    assert format_industry_benchmark_doc(None) is None
    fund = {
        "available": True,
        "target_industry": "Software",
        "geography": "us",
        "industry_operating_margin": 0.25,
        "industry_revenue_growth": 0.15,
    }
    doc = format_industry_benchmark_doc(fund)
    assert doc is not None
    assert doc["filename"] == "Damodaran_Industry_Benchmarks.md"
    assert "INDUSTRY BENCHMARKS: Software (US)" in doc["text"]
    assert "25.00%" in doc["text"]
    assert "15.00%" in doc["text"]
    assert "CURRENT INDUSTRY MEDIANS" in doc["text"]
