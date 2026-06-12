import logging
import pandas as pd
import yfinance as yf
from curl_cffi import requests as creq
from data import cache

logger = logging.getLogger(__name__)

TTL_CONSENSUS = 24 * 3600

def fetch_analyst_consensus(ticker: str) -> dict | None:
    cache_key = f"consensus_yfinance_{ticker.upper()}.json"
    cached = cache.get_json(cache_key, TTL_CONSENSUS)
    if cached:
        logger.info(f"Loaded {ticker} consensus from cache.")
        return cached

    logger.info(f"Fetching {ticker} consensus from yfinance (curl_cffi)...")
    try:
        sess = creq.Session(impersonate="chrome")
        t = yf.Ticker(ticker, session=sess)
        
        res = {
            "consensus_revenue_estimate_next_year": None,
            "consensus_revenue_growth_next_year": None,
            "consensus_eps_estimate_next_year": None,
            "consensus_eps_growth_next_year": None,
            "analyst_price_target_mean": None,
            "recommendation_mean": None
        }
        
        rev_est = t.revenue_estimate
        if rev_est is not None and not rev_est.empty and "+1y" in rev_est.index:
            row = rev_est.loc["+1y"]
            if "avg" in row and pd.notna(row["avg"]): res["consensus_revenue_estimate_next_year"] = float(row["avg"])
            if "growth" in row and pd.notna(row["growth"]): res["consensus_revenue_growth_next_year"] = float(row["growth"])

        eps_est = t.earnings_estimate
        if eps_est is not None and not eps_est.empty and "+1y" in eps_est.index:
            row = eps_est.loc["+1y"]
            if "avg" in row and pd.notna(row["avg"]): res["consensus_eps_estimate_next_year"] = float(row["avg"])
            if "growth" in row and pd.notna(row["growth"]): res["consensus_eps_growth_next_year"] = float(row["growth"])
            
        targets = t.analyst_price_targets
        if targets:
            if targets.get("mean") is not None: res["analyst_price_target_mean"] = float(targets.get("mean"))
            
        info = t.info
        if info:
            if info.get("recommendationMean") is not None: res["recommendation_mean"] = float(info.get("recommendationMean"))
            
        cache.set_json(cache_key, res)
        return res
    except Exception as e:
        logger.warning(f"Failed to fetch yfinance consensus for {ticker}: {e}")
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("AAPL:", fetch_analyst_consensus("AAPL"))
    print("GE:", fetch_analyst_consensus("GE"))
