import numpy as np

def derive_quarterly_signals(quarterly: dict) -> dict:
    """
    Derives quarterly signals (TTM values, YoY growth, seasonality, QoQ acceleration)
    from the raw quarterly financials.
    
    Expected quarterly dict shape:
    {
        "periods": ["Q1 2024", ...],  # length N, last element is most recent
        "revenue": [...],
        "operating_profit": [...],
        "net_income": [...],
        "opm": [...]
    }
    
    Returns a dict with derived signals. Values are None if data is insufficient.
    """
    result = {
        "ttm_revenue": None,
        "ttm_operating_profit": None,
        "latest_q_yoy_growth": None,
        "ttm_yoy_growth": None,
        "qoq_accel_sign": None,
        "seasonality_flag": None,
    }
    
    if not quarterly or "revenue" not in quarterly:
        return result
        
    rev = quarterly["revenue"]
    op = quarterly.get("operating_profit", [])
    
    n = len(rev)
    if n == 0:
        return result
        
    # Helper to sum safely (ignoring None)
    def _safe_sum(arr):
        vals = [v for v in arr if v is not None]
        return sum(vals) if len(vals) == len(arr) and len(arr) > 0 else None

    # TTM sums
    if n >= 4:
        result["ttm_revenue"] = _safe_sum(rev[-4:])
        if len(op) >= n:
            result["ttm_operating_profit"] = _safe_sum(op[-4:])
            
    # YoY Growth
    if n >= 5:
        curr_q = rev[-1]
        prev_yr_q = rev[-5]
        if curr_q is not None and prev_yr_q is not None and prev_yr_q != 0:
            result["latest_q_yoy_growth"] = (curr_q - prev_yr_q) / abs(prev_yr_q)
            
    # TTM YoY Growth
    if n >= 8:
        curr_ttm = _safe_sum(rev[-4:])
        prev_ttm = _safe_sum(rev[-8:-4])
        if curr_ttm is not None and prev_ttm is not None and prev_ttm != 0:
            result["ttm_yoy_growth"] = (curr_ttm - prev_ttm) / abs(prev_ttm)
            
    # QoQ Acceleration Sign (+1, 0, -1)
    if n >= 3:
        q0 = rev[-1]
        q1 = rev[-2]
        q2 = rev[-3]
        if all(x is not None for x in (q0, q1, q2)) and q1 != 0 and q2 != 0:
            g0 = (q0 - q1) / abs(q1)
            g1 = (q1 - q2) / abs(q2)
            if g0 > g1 + 1e-4:
                result["qoq_accel_sign"] = 1
            elif g0 < g1 - 1e-4:
                result["qoq_accel_sign"] = -1
            else:
                result["qoq_accel_sign"] = 0
                
    # Seasonality Flag
    if n >= 8:
        shares = []
        for i in range(4):
            q_shares = []
            idx = n - 1 - i
            while idx >= 3:
                year_sum = _safe_sum(rev[idx-3:idx+1])
                q_val = rev[idx]
                if year_sum and year_sum != 0 and q_val is not None:
                    q_shares.append(q_val / year_sum)
                idx -= 4
            if q_shares:
                shares.append(np.mean(q_shares))
                
        if len(shares) == 4:
            stdev = np.std(shares)
            result["seasonality_flag"] = bool(stdev > 0.05)

    return result
