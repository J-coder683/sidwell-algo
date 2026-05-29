import os
import pytest
from sidwell.ajp.loader import AJPLoader
from sidwell.ajp.schema import AJP, AJPAssumption

def test_ajp_loader_valid_fixture():
    loader = AJPLoader()
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "BBTC.NS_AJP.json")
    
    ajp, report = loader.load(fixture_path)
    
    assert report["is_valid"] is True
    assert ajp.meta.ticker == "BBTC.NS"
    assert ajp.meta.is_holdco is True
    
    assert report["coverage"]["HIGH"] == 2
    assert report["coverage"]["UNVERIFIED"] == 1
    assert report["coverage"]["FLAGGED"] == 2  # UNVERIFIED + ER verify_flag
    
    # Check segment parsing
    seg_assumption = next(a for a in ajp.assumptions if a.driver_id == "segments")
    assert len(seg_assumption.segments) == 2
    assert seg_assumption.segments[0].name == "Britannia Stake"
    
def test_ajp_loader_fallback():
    loader = AJPLoader()
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "BBTC.NS_AJP.json")
    ajp, _ = loader.load(fixture_path)
    
    # Existing assumption
    rev = AJPLoader.get_assumption_or_fallback(ajp, "stage1_revenue_growth", 0.0, "fb")
    assert rev.value == 0.085
    assert rev.confidence == "HIGH"
    
    # Missing assumption -> Engine Est fallback
    missing = AJPLoader.get_assumption_or_fallback(ajp, "missing_driver", 0.99, "Engine calculation fallback.")
    assert missing.value == 0.99
    assert missing.confidence == "LOW"
    assert missing.verify_flag == "ENGINE-EST"
    assert missing.rationale == "Engine calculation fallback."
    assert missing.source_type == "ENGINE_COMPUTED"
