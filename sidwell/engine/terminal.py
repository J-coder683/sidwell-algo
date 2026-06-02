from typing import Dict, Any
from sidwell.ajp.schema import AJP
from sidwell.ajp.loader import AJPLoader

class TerminalEngine:
    @staticmethod
    def calculate(proj: Dict[str, Any], wacc: float, ajp: AJP) -> Dict[str, Any]:
        _au = proj.get("assumptions_used", {})
        if "terminal_growth" in _au:
            term_g = float(_au["terminal_growth"])
        else:
            term_g = float(AJPLoader.get_assumption_or_fallback(ajp, "terminal_growth", 0.02, "Nominal GDP").value)
        exit_mult = float(AJPLoader.get_assumption_or_fallback(ajp, "exit_ev_ebitda_multiple", 10.0, "Peer median").value)
        
        final_ufcf = proj["ufcf"][-1]
        final_ebitda = proj["ebit"][-1] + proj["da"][-1]
        
        gordon_tv = final_ufcf * (1 + term_g) / (wacc - term_g) if wacc > term_g else 0.0
        multiple_tv = final_ebitda * exit_mult
        
        avg_tv = (gordon_tv + multiple_tv) / 2.0
        
        return {
            "terminal_growth": term_g,
            "exit_multiple": exit_mult,
            "gordon_tv": gordon_tv,
            "multiple_tv": multiple_tv,
            "avg_tv": avg_tv
        }
