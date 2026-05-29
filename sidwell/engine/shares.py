from typing import Dict, Any
from sidwell.ajp.schema import AJP
from sidwell.ajp.loader import AJPLoader

class SharesEngine:
    @staticmethod
    def calculate(fin: Dict[str, Any], ajp: AJP) -> Dict[str, Any]:
        """Calculates diluted shares using the treasury stock method."""
        
        current_price = fin.get("current_price", 0.0)
        
        # Scraped basic shares (fallback)
        market_cap = fin.get("market_cap", 0.0)
        scraped_basic_shares = (market_cap / current_price) if (current_price and current_price > 0) else 0.0
        
        options_val = AJPLoader.get_assumption_or_fallback(
            ajp, "options_outstanding", None, "Scraped basic shares fallback"
        )
        
        basic_shares = scraped_basic_shares
        net_dilutive_shares = 0.0
        used_fallback = False
        
        if options_val.options_outstanding and current_price > 0:
            for tranche in options_val.options_outstanding:
                if current_price > tranche.strike_price:
                    # In the money
                    proceeds = tranche.shares * tranche.strike_price
                    shares_repurchased = proceeds / current_price
                    net_dilutive = tranche.shares - shares_repurchased
                    net_dilutive_shares += net_dilutive
        else:
            used_fallback = True
            
        rsus = float(AJPLoader.get_assumption_or_fallback(ajp, "rsus_psus_outstanding", 0.0, "Zero default").value)
        net_dilutive_shares += rsus
        
        diluted_shares = basic_shares + net_dilutive_shares
        
        return {
            "basic_shares": basic_shares,
            "net_dilutive_shares": net_dilutive_shares,
            "diluted_shares": diluted_shares,
            "used_fallback": used_fallback
        }
