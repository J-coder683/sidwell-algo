import pytest
from unittest.mock import MagicMock
from sidwell.render.workbook import WorkbookRenderer

def test_workbook_currency_geography():
    engine_results = {
        "proj": {"years": [2024, 2025]},
        "hist": {"years_annual": [2022, 2023]}
    }
    
    # Test India ticker
    mock_ajp_in = MagicMock()
    mock_ajp_in.meta.ticker = "RELIANCE.NS"
    wb_in = WorkbookRenderer(engine_results, mock_ajp_in)
    assert wb_in._cur == "Rs"
    assert wb_in._unit == "Rs mm"
    
    # Test US ticker
    mock_ajp_us = MagicMock()
    mock_ajp_us.meta.ticker = "AAPL"
    wb_us = WorkbookRenderer(engine_results, mock_ajp_us)
    assert wb_us._cur == "$"
    assert wb_us._unit == "$ mm"

