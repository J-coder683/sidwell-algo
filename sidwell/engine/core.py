from typing import Dict, Any
from sidwell.ajp.schema import AJP
from sidwell.engine.statements import StatementsEngine
from sidwell.engine.wacc import WACCEngine
from sidwell.engine.terminal import TerminalEngine
from sidwell.engine.fcf import FCFEngine
from sidwell.engine.bridge import BridgeEngine
from sidwell.engine.shares import SharesEngine

def run_engine(financials: Dict[str, Any], ajp: AJP) -> Dict[str, Any]:
    """
    The deterministic core of the DCF engine.
    Receives quantitative scraped data (financials) and qualitative AI assignments (ajp).
    Returns a complete result dictionary for rendering.
    """
    
    # 1. Map Historical Data (crore to mm)
    fin_statements = financials.get("statements", {})
    hist = StatementsEngine.map_historical(fin_statements)
    
    # 2. Run 3-Statement Projections (IS, BS, CF, Debt Schedule, Balance Check).
    # Financial-sector companies (is_financial, set in the data layer like is_bank)
    # freeze operating working capital — their AR/AP are settlement float, not WC.
    proj = StatementsEngine.run_projections(
        hist, ajp, freeze_working_capital=financials.get("is_financial", False)
    )
    if not proj:
        raise ValueError(f"Insufficient historical data to run projections for {financials.get('ticker')}. The company may have no usable statements on screener.")
    
    # 3. Calculate WACC
    wacc_results = WACCEngine.calculate(financials, ajp)
    wacc = wacc_results["avg_wacc"]
    
    # 4. Calculate Terminal Value
    terminal_results = TerminalEngine.calculate(proj, wacc, ajp)
    
    # 5. Discount UFCF & TV to Enterprise Value
    fcf_results = FCFEngine.calculate(proj, wacc, terminal_results)
    ev = fcf_results["enterprise_value"]
    
    # 6. Bridge to Equity Value
    bridge_results = BridgeEngine.calculate(ev, hist["bs"], ajp)
    equity_value = bridge_results["equity_value"]
    
    # 7. Diluted Shares
    shares_results = SharesEngine.calculate(financials, ajp)
    diluted_shares = shares_results["diluted_shares"]
    
    # 8. Intrinsic Value Per Share
    # Equity value is in standard scale (millions). Shares are raw.
    intrinsic_value_per_share = (equity_value * 1e6 / diluted_shares) if diluted_shares > 0 else 0.0
    
    return {
        "hist": hist,
        "proj": proj,
        "wacc": wacc_results,
        "terminal": terminal_results,
        "fcf": fcf_results,
        "bridge": bridge_results,
        "shares": shares_results,
        "intrinsic_value_per_share": intrinsic_value_per_share
    }
