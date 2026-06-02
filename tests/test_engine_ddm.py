"""
test_engine_ddm.py — DDM cross-check module tests.
"""

import pytest
from sidwell.engine.ddm import DDMEngine

def _make_results(payout, ke, g, net_income, shares):
    proj = {
        "net_income": net_income,
        "assumptions_used": {"dividend_payout_ratio": payout}
    }
    wacc = {"current_ke": ke}
    terminal = {"terminal_growth": g}
    sh = {"diluted_shares": shares}
    return proj, wacc, terminal, sh

def test_ddm_basic_hand_calc():
    """
    payout = 0.5
    ke = 0.10, g = 0.05
    net_income = [100, 100, 100]
    shares = 10
    
    dividends = [50, 50, 50]
    pv_divs = 50/(1.1) + 50/(1.1**2) + 50/(1.1**3) 
            = 45.4545 + 41.3223 + 37.5657 = 124.3426
    
    tv = 50 * 1.05 / (0.10 - 0.05) = 1050
    pv_tv = 1050 / (1.1**3) = 788.8805
    
    ddm_equity = 124.3426 + 788.8805 = 913.2231
    ddm_intrinsic = 913.2231 * 1e6 / 10 = 91,322,314.05
    """
    proj, wacc, terminal, sh = _make_results(0.5, 0.10, 0.05, [100.0, 100.0, 100.0], 10.0)
    res = DDMEngine.calculate(proj, wacc, terminal, sh)
    
    assert res["applicable"] is True
    assert res["ddm_equity_value"] == pytest.approx(913.2231, rel=1e-4)
    assert res["ddm_intrinsic_per_share"] == pytest.approx(91322314.05, rel=1e-4)

def test_ddm_rises_with_payout():
    """DDM value should rise if payout increases, all else equal."""
    proj30, wacc, terminal, sh = _make_results(0.30, 0.10, 0.05, [100.0]*5, 10.0)
    res30 = DDMEngine.calculate(proj30, wacc, terminal, sh)
    
    proj60, _, _, _ = _make_results(0.60, 0.10, 0.05, [100.0]*5, 10.0)
    res60 = DDMEngine.calculate(proj60, wacc, terminal, sh)
    
    assert res30["applicable"] is True
    assert res60["applicable"] is True
    assert res60["ddm_equity_value"] > res30["ddm_equity_value"]
    
def test_ddm_not_applicable_when_ke_le_g():
    proj, wacc, terminal, sh = _make_results(0.5, 0.04, 0.05, [100.0]*3, 10.0)
    res = DDMEngine.calculate(proj, wacc, terminal, sh)
    
    assert res["applicable"] is False
    assert res["ddm_equity_value"] == 0.0
    assert "Ke <= g" in res["reason"]

def test_ddm_not_applicable_when_payout_zero():
    proj, wacc, terminal, sh = _make_results(0.0, 0.10, 0.05, [100.0]*3, 10.0)
    res = DDMEngine.calculate(proj, wacc, terminal, sh)
    
    assert res["applicable"] is False
    assert res["ddm_equity_value"] == 0.0
    assert "payout" in res["reason"]

def test_ddm_not_applicable_when_no_net_income():
    proj, wacc, terminal, sh = _make_results(0.5, 0.10, 0.05, [], 10.0)
    res = DDMEngine.calculate(proj, wacc, terminal, sh)
    
    assert res["applicable"] is False
    assert "no projection data" in res["reason"]
