import logging
import pandas as pd
import requests
import io
from data.cache import get_bytes, set_bytes

logger = logging.getLogger(__name__)

def fetch_price_history(ticker: str) -> pd.DataFrame:
    """
    Fetches daily price history as a DataFrame with [Date, Close].
    Uses stockanalysis.com for US and screener.in for India.
    Returns an empty DataFrame on failure.
    """
    cache_key = f"price_history_{ticker}.csv"
    cached_data_bytes = get_bytes(cache_key, 86400) # 1 day TTL
    
    if cached_data_bytes is not None:
        try:
            cached_data = cached_data_bytes.decode('utf-8')
            df = pd.read_csv(io.StringIO(cached_data))
            if "Date" in df.columns and "Close" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"])
                return df[["Date", "Close"]]
        except Exception as e:
            logger.warning(f"Failed to parse cached price data for {ticker}: {e}")

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        if ticker.endswith(".NS") or ticker.endswith(".BO"):
            # India -> Screener
            from data.scrapers.screener import _resolve_screener_slug
            slug = _resolve_screener_slug(ticker)
            if not slug:
                return pd.DataFrame(columns=["Date", "Close"])
                
            # Need to get company_id first
            url_page = f"https://www.screener.in/company/{slug}/consolidated/"
            r = requests.get(url_page, headers=headers, timeout=15)
            if r.status_code == 404:
                url_page = f"https://www.screener.in/company/{slug}/"
                r = requests.get(url_page, headers=headers, timeout=15)
                
            import re
            m = re.search(r'data-company-id=["\'](\d+)["\']', r.text)
            if not m:
                return pd.DataFrame(columns=["Date", "Close"])
                
            company_id = m.group(1)
            url_api = f"https://www.screener.in/api/company/{company_id}/chart/?q=Price-DMA50-Volume&days=10000"
            r = requests.get(url_api, headers=headers, timeout=15)
            r.raise_for_status()
            
            data = r.json()
            prices = []
            for ds in data.get("datasets", []):
                if ds.get("metric") == "Price":
                    for row in ds.get("values", []):
                        if len(row) >= 2:
                            prices.append({"Date": row[0], "Close": float(row[1])})
                    break
                    
            if not prices:
                return pd.DataFrame(columns=["Date", "Close"])
                
            df = pd.DataFrame(prices)
            
        else:
            # US -> Stockanalysis
            base_ticker = ticker.split(".")[0].upper()
            url_api = f"https://stockanalysis.com/api/symbol/s/{base_ticker}/history?range=10Y&period=Daily"
            r = requests.get(url_api, headers=headers, timeout=15)
            r.raise_for_status()
            
            data = r.json()
            if "data" not in data:
                return pd.DataFrame(columns=["Date", "Close"])
                
            prices = []
            for row in data["data"]:
                prices.append({"Date": row["t"], "Close": float(row["c"])})
                
            if not prices:
                return pd.DataFrame(columns=["Date", "Close"])
                
            df = pd.DataFrame(prices)
            
        # Ensure proper formatting
        df["Date"] = pd.to_datetime(df["Date"])
        
        # Save to cache as CSV string
        csv_str = df.to_csv(index=False)
        set_bytes(cache_key, csv_str.encode('utf-8'))
        
        return df[["Date", "Close"]]
        
    except Exception as e:
        logger.debug(f"Price request failed for {ticker}: {e}")
        return pd.DataFrame(columns=["Date", "Close"])
