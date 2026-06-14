"""
test_historical_context.py — tests for analysis.historical_context.build_historical_context_md

All tests are offline — no network, no LLM, no screener calls.
"""
import pytest
from analysis.historical_context import build_historical_context_md


def _base_financials():
    """Minimal financials dict that mirrors what public.fetch_financials returns
    after scraping.  Values are in crore (map_historical multiplies by 10 → mm)."""
    return {
        "ticker": "TEST.NS",
        "statements": {
            "years_annual": ["Mar 2022", "Mar 2023", "Mar 2024"],
            "annual": {
                "profit_loss": {
                    "sales":            [1000.0, 1100.0, 1210.0],   # crore
                    "operating profit": [150.0,  165.0,  181.5],
                    "depreciation":     [50.0,   55.0,   60.5],
                    "interest":         [0.0,    0.0,    0.0],
                    "profit before tax":[100.0,  110.0,  121.0],
                    "tax":              [25.0,   27.5,   30.25],
                    "net profit":       [75.0,   82.5,   90.75],
                    "cogs":             [500.0,  550.0,  605.0],
                },
                "balance_sheet": {
                    "equity capital":   [200.0, 200.0, 200.0],
                    "reserves":         [300.0, 350.0, 400.0],
                    "borrowings":       [100.0, 100.0, 100.0],
                    "fixed assets":     [600.0, 620.0, 640.0],
                    "trade receivables":[120.0, 132.0, 145.2],
                    "inventories":      [60.0,  66.0,  72.6],
                    "trade payables":   [90.0,  99.0,  108.9],
                    "cash equivalents": [50.0,  55.0,  60.5],
                },
                "cash_flow": {
                    "fixed assets purchased": [-60.0, -66.0, -72.6],
                },
            },
            "ratios": {
                "debtor days":          [43.8, 43.8, 43.8],
                "inventory days":       [None, None, None],   # blank
                "days payable":         [65.7, 65.7, 65.7],
                "working capital days": [20.0, 18.0, 22.0],
            },
        },
    }


# ---------------------------------------------------------------------------
# Test 1: Returns Markdown with the 3 required table headings
# ---------------------------------------------------------------------------
def test_build_returns_markdown_with_three_tables():
    fin = _base_financials()
    md = build_historical_context_md(fin)

    assert "## Historical Financials" in md
    assert "### P&L" in md
    assert "### Working-capital days" in md
    assert "### Working-capital balances" in md


# ---------------------------------------------------------------------------
# Test 2: YoY growth is blank ('—') for the first year, numeric thereafter
# ---------------------------------------------------------------------------
def test_yoy_growth_first_year_blank():
    fin = _base_financials()
    md = build_historical_context_md(fin)

    # Extract only the P&L table rows (section-aware, not raw startswith filter)
    pl_rows = []
    in_pl = False
    for line in md.splitlines():
        if line.startswith("### P&L"):
            in_pl = True
        elif in_pl and line.startswith("|") and "|---" not in line and "FY" not in line:
            pl_rows.append(line)
        elif in_pl and line.startswith("###"):  # next section boundary
            break
    assert len(pl_rows) == 3, f"Expected 3 P&L data rows, got: {pl_rows}"

    # Row 0 (oldest year): YoY column must be '—'
    # Columns: FY | Revenue | YoY | EBIT margin | CapEx/Sales | Tax
    cols_y0 = [c.strip() for c in pl_rows[0].split("|") if c.strip()]
    assert cols_y0[2] == "—", (
        f"First-year YoY growth should be '—', got '{cols_y0[2]}'"
    )

    # Row 1 and Row 2: YoY must contain '%'
    for i in range(1, 3):
        cols = [c.strip() for c in pl_rows[i].split("|") if c.strip()]
        assert "%" in cols[2], (
            f"Year {i} YoY should contain '%', got '{cols[2]}'"
        )


# ---------------------------------------------------------------------------
# Test 3: Revenue numbers match the input (scaled to INR mm = crore × 10)
# ---------------------------------------------------------------------------
def test_numbers_match_input():
    fin = _base_financials()
    md = build_historical_context_md(fin)

    # Revenue in Mar 2022 = 1000 crore × 10 = 10,000 mm → displayed as "10,000"
    assert "10,000" in md, "Revenue for Mar 2022 (10,000 mm) should appear in output"
    # Revenue in Mar 2024 = 1210 × 10 = 12,100 mm → "12,100"
    assert "12,100" in md, "Revenue for Mar 2024 (12,100 mm) should appear in output"


# ---------------------------------------------------------------------------
# Test 4: Empty / missing financials returns empty string (no crash)
# ---------------------------------------------------------------------------
def test_empty_financials_returns_empty_string():
    assert build_historical_context_md({}) == ""
    assert build_historical_context_md(None) == ""
    assert build_historical_context_md({"statements": {}}) == ""
    assert build_historical_context_md({"statements": {"years_annual": []}}) == ""


# ---------------------------------------------------------------------------
# Test 5: Blank ratio shows '—', non-blank shows a number
# ---------------------------------------------------------------------------
def test_blank_ratio_displays_dash():
    fin = _base_financials()
    md = build_historical_context_md(fin)

    # inventory_days is all None → should appear as '—' in WC-days table
    # Find the WC-days section rows
    wc_rows = []
    in_wc = False
    for line in md.splitlines():
        if "### Working-capital days" in line:
            in_wc = True
        elif in_wc and line.startswith("| Mar"):
            wc_rows.append(line)
        elif in_wc and line.startswith("###"):
            break
    assert wc_rows, "WC-days table should have data rows"
    for row in wc_rows:
        cols = [c.strip() for c in row.split("|") if c.strip()]
        # cols: FY, DSO, DIO, DPO, WC Days
        assert cols[2] == "—", f"DIO (blank) should be '—', got '{cols[2]}'"
        # DSO and DPO are non-zero → should NOT be '—'
        assert cols[1] != "—", f"DSO should be a number, got '{cols[1]}'"

# ---------------------------------------------------------------------------
# Test 6: Quarterly trend block added when quarterly data is present
# ---------------------------------------------------------------------------
def test_quarterly_trend_block_present():
    fin = _base_financials()
    # Add quarterly data
    fin["quarterly"] = {
        "periods": ["Q1", "Q2", "Q3", "Q4", "Q5"],
        "revenue": [1000.0, 1100.0, 1200.0, 1300.0, 1400.0],
        "operating_profit": [100.0, 110.0, 120.0, 130.0, 140.0],
        "opm": [0.1, 0.1, 0.1, 0.1, 0.1]
    }
    md = build_historical_context_md(fin)
    
    assert "### Quarterly Trend (most recent quarters" in md
    assert "**Quarterly signals**:" in md
    
    # Check YoY calculation: Q5 (1400) vs Q1 (1000) -> 40.0%
    assert "40.0%" in md
    assert "10.0%" in md  # OPM
    
def test_quarterly_trend_absent_safe():
    fin = _base_financials()
    md = build_historical_context_md(fin)
    assert "### Quarterly Trend" not in md
    
    # Also if fewer than 4 periods
    fin["quarterly"] = {
        "periods": ["Q1", "Q2", "Q3"],
        "revenue": [1000.0, 1100.0, 1200.0]
    }
    md2 = build_historical_context_md(fin)
    assert "### Quarterly Trend" not in md2
