from typing import Dict, Any, List
from sidwell.ajp.schema import AJP
from sidwell.ajp.loader import AJPLoader
import statistics

class WACCEngine:
    @staticmethod
    def calculate(fin: Dict[str, Any], ajp: AJP) -> Dict[str, Any]:
        """Calculates WACC using Hamada unlever/relever and Damodaran fallbacks."""
        
        # Load risk free and equity risk premium
        rf = AJPLoader.get_assumption_or_fallback(ajp, "risk_free_rate", 0.07, "Engine FRED fallback")
        erp = AJPLoader.get_assumption_or_fallback(ajp, "equity_risk_premium", 0.05, "Engine Damodaran fallback")
        crp = AJPLoader.get_assumption_or_fallback(ajp, "country_risk_premium", 0.0, "Engine Damodaran fallback")
        total_erp = float(erp.value) + float(crp.value)
        rf_val = float(rf.value)

        # Peer betas
        peer_betas_val = AJPLoader.get_assumption_or_fallback(ajp, "peer_betas", [], "Engine scraped peers")
        tax_rate = float(AJPLoader.get_assumption_or_fallback(ajp, "tax_rate", 0.25, "Historical average").value)
        
        asset_betas = []
        if peer_betas_val.value and isinstance(peer_betas_val.value, list) and len(peer_betas_val.value) > 0:
            for peer in peer_betas_val.value:
                b = float(peer.get("beta", 1.0))
                debt = float(peer.get("debt", 0.0))
                equity = float(peer.get("equity", 1.0))
                if equity > 0:
                    d_e = debt / equity
                    asset_beta = b / (1 + (1 - tax_rate) * d_e)
                    asset_betas.append(asset_beta)
        
        if asset_betas:
            median_asset_beta = statistics.median(asset_betas)
        else:
            # Condition 4: Fallback to Damodaran industry beta
            median_asset_beta = 1.0  # In real implementation this comes from Damodaran
        
        # Current structure
        current_debt_raw = fin.get("debt", 0.0)
        current_debt = current_debt_raw[-1] if isinstance(current_debt_raw, list) and current_debt_raw else float(current_debt_raw) if not isinstance(current_debt_raw, list) else 0.0
        
        current_equity_raw = fin.get("market_cap", 0.0)
        current_equity = current_equity_raw[-1] if isinstance(current_equity_raw, list) and current_equity_raw else float(current_equity_raw) if not isinstance(current_equity_raw, list) else 0.0
        
        current_d_e = current_debt / current_equity if current_equity > 0 else 0.0
        
        current_levered_beta = median_asset_beta * (1 + (1 - tax_rate) * current_d_e)
        current_ke = rf_val + current_levered_beta * total_erp
        
        # Target structure
        target_debt_to_cap = float(AJPLoader.get_assumption_or_fallback(ajp, "target_debt_to_cap", 0.2, "Market norm").value)
        target_d_e = target_debt_to_cap / (1 - target_debt_to_cap) if target_debt_to_cap < 1 else current_d_e
        
        target_levered_beta = median_asset_beta * (1 + (1 - tax_rate) * target_d_e)
        target_ke = rf_val + target_levered_beta * total_erp
        
        # Cost of debt (synthetic rating)
        pretax_kd = float(AJPLoader.get_assumption_or_fallback(ajp, "pretax_cost_of_debt_override", 0.08, "Interest/Debt or synthetic").value)
        after_tax_kd = pretax_kd * (1 - tax_rate)
        
        current_wacc = (current_equity / (current_debt + current_equity) * current_ke) + \
                       (current_debt / (current_debt + current_equity) * after_tax_kd) if (current_debt + current_equity) > 0 else current_ke
                       
        target_wacc = (1 - target_debt_to_cap) * target_ke + (target_debt_to_cap) * after_tax_kd
        
        avg_wacc = (current_wacc + target_wacc) / 2.0
        
        return {
            "rf": rf_val,
            "total_erp": total_erp,
            "median_asset_beta": median_asset_beta,
            "current_levered_beta": current_levered_beta,
            "current_ke": current_ke,
            "current_wacc": current_wacc,
            "target_levered_beta": target_levered_beta,
            "target_ke": target_ke,
            "target_wacc": target_wacc,
            "pretax_kd": pretax_kd,
            "after_tax_kd": after_tax_kd,
            "avg_wacc": avg_wacc
        }
