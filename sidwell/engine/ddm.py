"""
sidwell/engine/ddm.py — Dividend Discount Model (DDM) cross-check.

A deterministic valuation cross-check that uses projected dividends.
Since DDM can undervalue companies retaining earnings for high-return reinvestment,
it serves as an additive cross-check rather than replacing the primary UFCF DCF.
"""

class DDMEngine:
    @staticmethod
    def calculate(proj: dict, wacc_results: dict, terminal_results: dict, shares_results: dict) -> dict:
        net_income = proj.get("net_income", [])
        payout = proj.get("assumptions_used", {}).get("dividend_payout_ratio", 0.0)
        ke = wacc_results.get("current_ke", 0.0)
        g = terminal_results.get("terminal_growth", 0.0)
        shares = shares_results.get("diluted_shares", 0.0)

        # Basic applicability checks
        reasons = []
        if not net_income:
            reasons.append("no projection data")
        if payout <= 0.01:
            reasons.append("payout is ~0")
        if ke <= g:
            reasons.append("Ke <= g")
        if shares <= 0:
            reasons.append("no shares data")

        if reasons:
            return {
                "ddm_equity_value": 0.0,
                "ddm_intrinsic_per_share": 0.0,
                "applicable": False,
                "reason": "DDM not meaningful: " + ", ".join(reasons)
            }

        # Projected dividends
        dividends = [ni * payout for ni in net_income]
        
        # Discount explicit dividends (using mid-year discounting like FCF, or end-of-year? DDM typically uses end-of-year)
        # Using t+1 for end-of-year cash flow.
        pv_dividends = sum(div / ((1.0 + ke) ** (t + 1)) for t, div in enumerate(dividends))
        
        # Gordon Growth Terminal Value
        last_div = dividends[-1]
        tv = last_div * (1.0 + g) / (ke - g)
        
        # Discount TV from year N
        pv_tv = tv / ((1.0 + ke) ** len(dividends))
        
        ddm_equity_value = pv_dividends + pv_tv
        ddm_intrinsic = ddm_equity_value * 1e6 / shares

        return {
            "ddm_equity_value": ddm_equity_value,
            "ddm_intrinsic_per_share": ddm_intrinsic,
            "applicable": True,
            "reason": "Valid DDM valuation"
        }
