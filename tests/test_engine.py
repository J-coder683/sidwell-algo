import os
import pytest
from sidwell.ajp.loader import AJPLoader
from sidwell.engine.core import run_engine

def test_engine_end_to_end_bbtc_fixture():
    loader = AJPLoader()
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "BBTC.NS_AJP.json")
    ajp, _ = loader.load(fixture_path)
    
    # Mock scraped fin structure mimicking screener.py output for BBTC
    fin = {
        "ticker": "BBTC.NS",
        "current_price": 2000.0,
        "market_cap": 250000.0,  # crore
        "debt": 1000.0,
        "statements": {
            "years_annual": ["Mar 2023", "Mar 2024", "Mar 2025"],
            "annual": {
                "profit_loss": {
                    "sales": [1000.0, 1100.0, 1200.0],
                    "operating profit": [100.0, 110.0, 120.0],
                    "depreciation": [10.0, 10.0, 10.0],
                    "interest": [50.0, 50.0, 50.0],
                    "profit before tax": [40.0, 50.0, 60.0],
                    "tax": [10.0, 12.0, 15.0],
                    "net profit": [30.0, 38.0, 45.0]
                },
                "balance_sheet": {
                    "equity capital": [10.0, 10.0, 10.0],
                    "reserves": [200.0, 238.0, 283.0],
                    "borrowings": [1000.0, 950.0, 900.0],
                    "non controlling int": [20.0, 20.0, 20.0],
                    "trade payables": [100.0, 110.0, 120.0],
                    "fixed assets": [500.0, 490.0, 480.0],
                    "investments": [50.0, 50.0, 50.0],
                    "inventories": [100.0, 110.0, 120.0],
                    "trade receivables": [150.0, 160.0, 170.0],
                    "cash equivalents": [200.0, 250.0, 300.0]
                },
                "cash_flow": {
                    "cash from operating activity": [50.0, 60.0, 70.0],
                    "working capital changes": [-10.0, -10.0, -10.0],
                    "cash from investing activity": [-50.0, -50.0, -50.0],
                    "fixed assets purchased": [-60.0, -60.0, -60.0]
                }
            },
            "ratios": {
                "debtor days": [45.0, 45.0, 45.0],
                "inventory days": [30.0, 30.0, 30.0],
                "days payable": [45.0, 45.0, 45.0]
            }
        }
    }
    
    results = run_engine(fin, ajp)
    
    # 1. Assert balance check passes strictly (internal assertion would throw if it failed)
    assert all(abs(bc) < 1.0 for bc in results["proj"]["balance_check"])
    
    # 2. Check SOTP was applied because is_holdco = true
    bridge = results["bridge"]
    assert bridge["is_holdco"] is True
    assert bridge["sotp_value"] == (600000.0 * 0.505) + (50000.0 * 1.0)
    assert bridge["equity_value"] == bridge["sotp_value"]
    
    # 3. Check fallbacks were used safely
    shares = results["shares"]
    assert shares["used_fallback"] is True
    assert shares["diluted_shares"] == (250000.0 / 2000.0)
    
    assert results["intrinsic_value_per_share"] > 0
    
    # 4. Check projection fade (revenue should fade)
    # Stage 1 rev growth from AJP is 8.5%
    # Term G fallback is 2%
    proj = results["proj"]
    # We should have 10 years projected
    assert len(proj["years"]) == 10
    
    # First year rev = last actual (1200 * 10 = 12000) * 1.085 = 13020
    assert abs(proj["revenue"][0] - 13020.0) < 1.0
