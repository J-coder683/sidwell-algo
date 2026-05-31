import pytest
from unittest.mock import patch
import value

@patch("value.public.fetch_financials")
@patch("value.public.fetch_risk_free_rate", return_value=0.07)
@patch("value.public.fetch_damodaran_data", return_value={})
@patch("value.doc_module.discover_documents")
@patch("value.qualitative.extract_qualitative")
def test_analyze_fails_fast_on_missing_financials(
    mock_extract_qualitative, mock_discover_docs,
    mock_damodaran, mock_rf, mock_fetch_financials
):
    # Setup financials with empty years_annual
    mock_fetch_financials.return_value = {
        "ticker": "NODATA.BO",
        "statements": {"years_annual": []}
    }
    
    with pytest.raises(ValueError, match="Insufficient historical data to run projections"):
        value.analyze("NODATA.BO")
        
    # Assert fast-fail bypassed qualitative steps
    mock_discover_docs.assert_not_called()
    mock_extract_qualitative.assert_not_called()
