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
        seg_assumption = AJPLoader.get_assumption_or_fallback(ajp, "segments", [], "Holdco segments")
        
        sotp_used = False
        valuation_method = "EV_bridge"
        valuation_caveat = None

        # SOTP only when the ticker is a holdco AND we actually have segment values.
        # If holdco is flagged but no segments are supplied (e.g. Gemini set the
        # flag from subsidiary mentions but gave no stake values), fall back to the
        # standard EV→equity bridge so the valuation isn't zeroed out.
        if is_holdco and seg_assumption.segments:
            for seg in seg_assumption.segments:
                sotp_value += seg.value_mm * seg.stake_pct
            
            # Sanity guard: SOTP total must be plausible relative to core equity bridge
            if equity_value_core > 0 and sotp_value < 0.25 * equity_value_core:
                equity_value = equity_value_core
                valuation_caveat = "SOTP segment values sum to an implausibly low amount (< 25% of standard core equity value). Segments may be incomplete (e.g. missing core). Falling back to standard EV bridge."
            else:
                holdco_discount = float(AJPLoader.get_assumption_or_fallback(ajp, "holdco_discount", 0.0, "Discount").value)
                equity_value = sotp_value * (1 - holdco_discount)
                sotp_used = True
                valuation_method = "SOTP"
        else:
            equity_value = equity_value_core
            if is_holdco:
                valuation_caveat = "Holdco flagged but segments are missing or empty. Falling back to standard EV bridge."
            else:
                base_val = max(ev, equity_value_core)
                if base_val > 0 and debt > (base_val * 0.5) and (investments + nci) > (base_val * 0.1):
                    valuation_caveat = "Consolidated debt is very large relative to EV/Equity, and investments/NCI are material. The consolidated equity bridge may understate value (possible consolidated financial subsidiary). SOTP inputs are recommended."
            
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
            "equity_value": equity_value,
            "sotp_used": sotp_used,
            "valuation_method": valuation_method,
            "valuation_caveat": valuation_caveat
        }
