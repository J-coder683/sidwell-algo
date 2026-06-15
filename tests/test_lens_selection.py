import os
import sys
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
import pytest

def test_lens_selection_passes_subset_to_analyze():
    mock_res = {
        "financials": {"ticker": "AAPL"},
        "dcf_results": {"current_price": 100.0, "assumptions": {}, "intrinsic_value_per_share": 120.0},
        "qualitative_results": {},
        "damodaran_data": {},
        "rf_rate": 0.05,
        "buffett_results": None,
        "marks_results": None,
        "kkr_results": None,
        "blackstone_results": None,
        "apollo_results": None,
    }
    
    with patch.dict("sys.modules", {"streamlit_searchbox": None}), patch("value.analyze", return_value=mock_res) as mock_analyze:
        at = AppTest.from_file("app.py")
        at.run()
        
        at.text_input[0].set_value("AAPL")
        at.multiselect[0].set_value(["buffett", "marks"])
        
        analyze_btns = [btn for btn in at.button if btn.label == "Analyze"]
        if analyze_btns:
            analyze_btns[0].click().run(timeout=10)
        
        mock_analyze.assert_called_with("AAPL", lenses_to_run=["buffett", "marks"], research_docs=None)

def test_lens_selection_fallback_to_all():
    mock_res = {
        "financials": {"ticker": "AAPL"},
        "dcf_results": {"current_price": 100.0, "assumptions": {}, "intrinsic_value_per_share": 120.0},
        "qualitative_results": {},
        "damodaran_data": {},
        "rf_rate": 0.05,
        "buffett_results": None,
        "marks_results": None,
        "kkr_results": None,
        "blackstone_results": None,
        "apollo_results": None,
    }
    
    with patch.dict("sys.modules", {"streamlit_searchbox": None}), patch("value.analyze", return_value=mock_res) as mock_analyze:
        at = AppTest.from_file("app.py")
        at.run()
        
        at.text_input[0].set_value("AAPL")
        at.multiselect[0].set_value([]) # Deselect all
        
        analyze_btns = [btn for btn in at.button if btn.label == "Analyze"]
        if analyze_btns:
            analyze_btns[0].click().run(timeout=10)
        
        mock_analyze.assert_called_with("AAPL", lenses_to_run=["buffett", "marks", "kkr", "blackstone", "apollo"], research_docs=None)
