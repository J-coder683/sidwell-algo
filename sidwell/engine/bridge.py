from typing import Dict, Any
from sidwell.ajp.schema import AJP
from sidwell.ajp.loader import AJPLoader

class BridgeEngine:
    @staticmethod
    def calculate(ev: float, hist_bs: Dict[str, Any], ajp: AJP) -> Dict[str, Any]:
        """Calculates Equity Value using the full bridge."""
        
        is_holdco = ajp.meta.is_holdco
        
        cash = hist_bs["cash_equivalents"][-1] if hist_bs["cash_equivalents"] else 0.0
        debt = (hist_bs["borrowings"][-1] if hist_bs["borrowings"] else 0.0) + \
               (hist_bs["lease_liabilities"][-1] if hist_bs["lease_liabilities"] else 0.0)
               
        nci = hist_bs["non_controlling_int"][-1] if hist_bs["non_controlling_int"] else 0.0
        investments = hist_bs["investments"][-1] if hist_bs["investments"] else 0.0
        
        # AJP explicit overrides/additions
        preferred = float(AJPLoader.get_assumption_or_fallback(ajp, "preferred_stock", 0.0, "Zero default").value)
        pension = float(AJPLoader.get_assumption_or_fallback(ajp, "unfunded_pension", 0.0, "Zero default").value)
        nols = float(AJPLoader.get_assumption_or_fallback(ajp, "nols", 0.0, "Zero default").value)
        
        # Base EV → Equity
        equity_value_core = ev + cash - debt - nci - preferred + investments - pension + nols
        
        sotp_value = 0.0
        holdco_discount = 0.0
        if is_holdco:
            seg_assumption = AJPLoader.get_assumption_or_fallback(ajp, "segments", [], "Holdco segments")
            if seg_assumption.segments:
                for seg in seg_assumption.segments:
                    sotp_value += seg.value_mm * seg.stake_pct
            
            holdco_discount = float(AJPLoader.get_assumption_or_fallback(ajp, "holdco_discount", 0.0, "Discount").value)
            equity_value_sotp = sotp_value * (1 - holdco_discount)
            equity_value = equity_value_sotp
        else:
            equity_value = equity_value_core
            
        return {
            "cash": cash,
            "debt": debt,
            "nci": nci,
            "investments": investments,
            "preferred": preferred,
            "pension": pension,
            "nols": nols,
            "equity_value_core": equity_value_core,
            "is_holdco": is_holdco,
            "sotp_value": sotp_value,
            "holdco_discount": holdco_discount,
            "equity_value": equity_value
        }
