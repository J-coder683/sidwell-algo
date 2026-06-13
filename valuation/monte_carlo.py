import logging
import numpy as np
from typing import Dict, Any, Optional
from valuation.dcf import run_dcf_valuation

logger = logging.getLogger("sidwell.valuation.monte_carlo")

# --- Monte Carlo Spread Configuration ---
# Revenue Growth: ±40% relative to base. E.g., 10% base -> [6%, 14%]
MC_REV_GROWTH_REL_SPREAD = 0.40  

# EBIT Margin: ±25% relative to base. E.g., 20% base -> [15%, 25%]
MC_EBIT_MARGIN_REL_SPREAD = 0.25 

# Terminal Growth: ±1.0 percentage point absolute. E.g., 2% base -> [1%, 3%]
MC_TERM_GROWTH_ABS_SPREAD = 0.010 

# Risk-Free Rate: ±0.75 percentage points absolute. E.g., 4% base -> [3.25%, 4.75%]
MC_RF_RATE_ABS_SPREAD = 0.0075 


def run_monte_carlo(
    dcf_results: Dict[str, Any],
    financials: Dict[str, Any],
    macro_data: Dict[str, Any],
    risk_free_rate: float,
    qualitative_results: Optional[Dict[str, Any]] = None,
    n: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Runs a Monte Carlo simulation around the base DCF intrinsic value.
    Perturbs key assumptions using a triangular distribution centered on the base values.
    """
    
    # 1. Guard checks
    if dcf_results.get("not_applicable"):
        return {
            "applicable": False,
            "reason": dcf_results.get("not_applicable_reason", "DCF is not applicable for this ticker.")
        }
        
    point_intrinsic = dcf_results.get("intrinsic_value_per_share")
    if point_intrinsic is None or point_intrinsic <= 0:
        return {
            "applicable": False,
            "reason": f"Base intrinsic value ({point_intrinsic}) is not positive. Simulation aborted."
        }

    current_price = dcf_results.get("current_price", 0.0)
    assumptions = dcf_results.get("assumptions", {})
    base_wacc = assumptions.get("wacc", 0.10)
    
    # Extract base assumptions
    base_rev_g = assumptions.get("revenue_growth", 0.0)
    base_ebit_m = assumptions.get("ebit_margin", 0.0)
    base_term_g = assumptions.get("terminal_growth_rate", 0.0)
    base_rf = assumptions.get("risk_free_rate", 0.0)
    
    rng = np.random.default_rng(seed)
    
    # 2. Generate perturbation arrays
    # Triangular distributions: (left, mode, right)
    
    # Revenue Growth (relative, floored at 0)
    rev_g_min = max(0.0, base_rev_g * (1 - MC_REV_GROWTH_REL_SPREAD))
    rev_g_max = base_rev_g * (1 + MC_REV_GROWTH_REL_SPREAD)
    if rev_g_min == rev_g_max:
        rev_g_draws = np.full(n, base_rev_g)
    else:
        # If base is negative, the bounds flip. Fix ordering for triangular.
        left = min(rev_g_min, rev_g_max)
        right = max(rev_g_min, rev_g_max)
        # If base is exactly 0, left=0, right=0, we'll get an error with triangular if left==right.
        rev_g_draws = rng.triangular(left, base_rev_g, right, n)

    # EBIT Margin (relative, floored at small positive)
    ebit_m_min = max(0.001, base_ebit_m * (1 - MC_EBIT_MARGIN_REL_SPREAD))
    ebit_m_max = base_ebit_m * (1 + MC_EBIT_MARGIN_REL_SPREAD)
    if ebit_m_min == ebit_m_max:
        ebit_m_draws = np.full(n, base_ebit_m)
    else:
        left = min(ebit_m_min, ebit_m_max)
        right = max(ebit_m_min, ebit_m_max)
        ebit_m_draws = rng.triangular(left, base_ebit_m, right, n)
        
    # Terminal Growth (absolute, hard-capped strictly below base WACC - 0.5pp safety)
    # WACC might change due to RF rate, so we cap conservatively.
    cap_tg = max(0.0, base_wacc - 0.005)
    tg_min = min(cap_tg, base_term_g - MC_TERM_GROWTH_ABS_SPREAD)
    tg_max = min(cap_tg, base_term_g + MC_TERM_GROWTH_ABS_SPREAD)
    if tg_min == tg_max:
        tg_draws = np.full(n, min(base_term_g, cap_tg))
    else:
        left = min(tg_min, tg_max)
        right = max(tg_min, tg_max)
        # Ensure mode is within bounds
        mode = min(max(base_term_g, left), right)
        tg_draws = rng.triangular(left, mode, right, n)
        
    # Risk-Free Rate (absolute, floored at 0)
    rf_min = max(0.0, base_rf - MC_RF_RATE_ABS_SPREAD)
    rf_max = base_rf + MC_RF_RATE_ABS_SPREAD
    if rf_min == rf_max:
        rf_draws = np.full(n, base_rf)
    else:
        rf_draws = rng.triangular(rf_min, base_rf, rf_max, n)
        
    # 3. Execution loop
    valid_samples = []
    
    for i in range(n):
        overrides = {
            "stage1_revenue_growth": float(rev_g_draws[i]),
            "normalized_ebit_margin": float(ebit_m_draws[i]),
            "ebit_margin_target": float(ebit_m_draws[i]),
            "terminal_growth": float(tg_draws[i]),
            "risk_free_rate": float(rf_draws[i])
        }
        
        try:
            res = run_dcf_valuation(
                financials=financials,
                macro_data=macro_data,
                risk_free_rate=risk_free_rate,  # will be overridden by the AJP overrides
                qualitative_results=qualitative_results,
                overrides=overrides
            )
            
            val = res.get("intrinsic_value_per_share")
            if val is not None and val > 0:
                valid_samples.append(val)
        except Exception as e:
            # Skip failed draws (cyclical constraints, non-positive EV, etc.)
            logger.debug(f"Draw {i} failed: {e}")
            continue
            
    # 4. Compile statistics
    if not valid_samples:
        return {
            "applicable": False,
            "reason": "All simulation draws failed or produced non-positive intrinsic values."
        }
        
    arr = np.array(valid_samples)
    
    p10 = float(np.percentile(arr, 10))
    p25 = float(np.percentile(arr, 25))
    p50 = float(np.percentile(arr, 50))
    p75 = float(np.percentile(arr, 75))
    p90 = float(np.percentile(arr, 90))
    
    prob_gt_price = float(np.sum(arr > current_price) / len(arr)) if current_price > 0 else 0.0
    
    return {
        "applicable": True,
        "n": len(arr),
        "seed": seed,
        "current_price": float(current_price),
        "point_intrinsic": float(point_intrinsic),
        "percentiles": {
            "p10": p10,
            "p25": p25,
            "p50": p50,
            "p75": p75,
            "p90": p90
        },
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "prob_intrinsic_gt_price": prob_gt_price,
        "samples": valid_samples,
        "drivers_perturbed": ["revenue_growth", "ebit_margin", "terminal_growth_rate", "risk_free_rate"]
    }
