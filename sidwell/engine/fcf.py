from typing import Dict, Any, List

class FCFEngine:
    @staticmethod
    def calculate(proj: Dict[str, Any], wacc: float, terminal: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates PV of UFCF with mid-year discounting."""
        ufcfs = proj["ufcf"]
        
        pv_ufcf = []
        cum_pv_ufcf = 0.0
        
        for i, cf in enumerate(ufcfs):
            # Mid year discounting: 0.5, 1.5, 2.5...
            discount_period = i + 0.5
            discount_factor = 1.0 / ((1 + wacc) ** discount_period)
            pv = cf * discount_factor
            pv_ufcf.append(pv)
            cum_pv_ufcf += pv
            
        # Terminal value discounting (end of final year)
        final_discount_period = len(ufcfs)
        final_discount_factor = 1.0 / ((1 + wacc) ** final_discount_period)
        
        pv_tv = terminal["avg_tv"] * final_discount_factor
        
        enterprise_value = cum_pv_ufcf + pv_tv
        
        return {
            "discount_factor_list": [1.0 / ((1 + wacc) ** i) for i in range(1, len(proj["ufcf"]) + 1)],
            "pv_ufcf_list": pv_ufcf,
            "cum_pv_ufcf": cum_pv_ufcf,
            "pv_tv": pv_tv,
            "enterprise_value": enterprise_value
        }
