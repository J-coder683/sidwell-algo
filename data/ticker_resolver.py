"""
Resolve user input (ticker or company name) to a canonical ticker.

v0.8.0: User can type names. Resolves via a local index (NSE+BSE) for instant lookup
and accurate exchange resolution (.NS vs .BO). Fallbacks to screener.in search API.
US names resolve via hardcoded map + stockanalysis.com fallback.
"""
import csv
import os
import json
import logging
import requests
from io import StringIO
from data import cache

logger = logging.getLogger("sidwell.ticker_resolver")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.5",
}

_RESOLVE_CACHE_TTL = 7 * 24 * 60 * 60
_INDEX_CACHE_TTL = 30 * 24 * 60 * 60


# Hardcoded top-50 US name → ticker map. Covers the most common reviewer
# queries instantly (no HTTP call). Fallback is stockanalysis.com search.
_US_NAME_TO_TICKER = {
    # Tech mega-caps
    "apple": "AAPL", "microsoft": "MSFT", "alphabet": "GOOGL", "google": "GOOGL",
    "amazon": "AMZN", "meta": "META", "facebook": "META", "nvidia": "NVDA",
    "tesla": "TSLA", "netflix": "NFLX", "oracle": "ORCL", "salesforce": "CRM",
    "adobe": "ADBE", "intel": "INTC", "amd": "AMD", "qualcomm": "QCOM",
    "ibm": "IBM", "cisco": "CSCO", "broadcom": "AVGO", "palantir": "PLTR",
    "snowflake": "SNOW", "uber": "UBER", "spotify": "SPOT", "shopify": "SHOP",
    # Financials
    "jpmorgan": "JPM", "jp morgan": "JPM", "bank of america": "BAC",
    "goldman sachs": "GS", "morgan stanley": "MS", "wells fargo": "WFC",
    "berkshire hathaway": "BRK.B", "berkshire": "BRK.B",
    "visa": "V", "mastercard": "MA", "blackrock": "BLK", "blackstone": "BX",
    "kkr": "KKR", "apollo": "APO",
    # Consumer
    "coca cola": "KO", "coca-cola": "KO", "pepsi": "PEP", "pepsico": "PEP",
    "mcdonalds": "MCD", "starbucks": "SBUX", "nike": "NKE", "walmart": "WMT",
    "costco": "COST", "home depot": "HD", "target": "TGT", "disney": "DIS",
    # Healthcare
    "johnson and johnson": "JNJ", "johnson & johnson": "JNJ", "j&j": "JNJ",
    "pfizer": "PFE", "moderna": "MRNA", "merck": "MRK", "eli lilly": "LLY",
    "unitedhealth": "UNH",
    # Energy
    "exxon": "XOM", "exxonmobil": "XOM", "chevron": "CVX",
}


def _normalize(s: str) -> str:
    return s.strip().lower().replace(".", "").replace(",", "")


def _looks_like_ticker(s: str) -> bool:
    """Heuristic: short, all-caps, no spaces, optional .NS/.BO suffix."""
    if not s:
        return False
    s = s.strip()
    # Indian ticker
    if s.upper().endswith((".NS", ".BO", ".BSE")):
        return True
    # US ticker: 1-5 chars, all letters (optionally with one period for BRK.B etc.)
    if " " in s:
        return False
    if 1 <= len(s) <= 6 and s.replace(".", "").isalpha() and s.upper() == s:
        return True
    return False


def _build_local_index() -> tuple[dict, dict]:
    """
    Downloads NSE EQUITY_L.csv and BSE Scrip master, merges on ISIN.
    Returns: (index_dict, status_dict)
    """
    index_by_isin = {}
    nse_count = 0
    bse_count = 0

    # 1. Fetch NSE
    try:
        r = requests.get('https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv', headers=HEADERS, timeout=10)
        if r.status_code == 200:
            reader = csv.DictReader(StringIO(r.text))
            for row in reader:
                symbol = row.get("SYMBOL", "").strip()
                name = row.get("NAME OF COMPANY", "").strip()
                isin = row.get(" ISIN NUMBER", "").strip()
                if symbol and name and isin:
                    index_by_isin[isin] = {"name": name, "nse_symbol": symbol}
                    nse_count += 1
    except Exception as e:
        logger.warning(f"NSE download error: {e}")

    # 2. Fetch BSE
    bse_headers = {
        **HEADERS,
        'Referer': 'https://www.bseindia.com/',
        'Origin': 'https://www.bseindia.com',
    }
    try:
        r = requests.get('https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?Group=&Scripcode=&industry=&segment=Equity&status=Active', headers=bse_headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for item in data:
                scrip_code = str(item.get("SCRIP_CD", "")).strip()
                name = item.get("Scrip_Name", "").strip()
                isin = item.get("ISIN_NUMBER", "").strip()
                if scrip_code and name and isin:
                    if isin in index_by_isin:
                        index_by_isin[isin]["bse_code"] = scrip_code
                    else:
                        index_by_isin[isin] = {"name": name, "bse_code": scrip_code}
                    bse_count += 1
    except Exception as e:
        logger.warning(f"BSE download error: {e}")

    # Re-key by company name
    final_index = {}
    for isin, info in index_by_isin.items():
        name = info.pop("name")
        final_index[name] = info

    status = {
        "nse": nse_count >= 1500,
        "bse": bse_count >= 3000
    }
    return final_index, status


_STATIC_INDEX_PATH = os.path.join(os.path.dirname(__file__), "universe_index.json")


def _load_static_index() -> dict:
    """Load the committed NSE+BSE universe snapshot shipped in the repo.

    This is the PRIMARY source: it loads instantly and works OFFLINE — critical on
    Streamlit Cloud, where NSE/BSE block server IPs so the live download fails and
    the search dropdown would otherwise come back empty. Returns {} if the file is
    missing or unreadable (dev environments can still fall back to a live build).
    """
    try:
        with open(_STATIC_INDEX_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data:
            return data
    except Exception as e:
        logger.warning(f"Could not load static universe index: {e}")
    return {}


def get_local_index() -> dict:
    """Returns the local NSE+BSE universe index.

    Order: committed static snapshot (instant, offline) → runtime cache → live build.
    The live build only runs in environments where no snapshot/cache exists AND
    NSE/BSE are reachable (e.g. a dev laptop refreshing the snapshot)."""
    # 1. Committed static snapshot — works on cloud, no network dependency.
    static = _load_static_index()
    if static:
        return static

    # 2. Runtime cache (a prior successful live build).
    cache_key = "local_universe_index.json"
    cached = cache.get_json(cache_key, _INDEX_CACHE_TTL)
    if cached and any("bse_code" in v for v in cached.values()):
        return cached

    # 3. Live build (dev only; never trusted partial — see _build_local_index status).
    logger.info("Building local universe index...")
    index, status = _build_local_index()
    if index and status.get("nse") and status.get("bse"):
        logger.info("Index build complete. Caching to disk.")
        cache.set_json(cache_key, index)
    else:
        logger.warning(f"Index build partial {status}. NOT caching to disk.")

    return index


def search_companies(query: str) -> list[tuple[str, str]]:
    """
    Search callback for st_searchbox.
    Returns list of (label, value) e.g. [("Reliance Industries (RELIANCE.NS)", "RELIANCE.NS")]
    """
    if not query or len(query) < 2:
        return []

    q = query.lower()
    index = get_local_index()
    results = []

    # 1. Search local index
    for name, info in index.items():
        nse = info.get("nse_symbol", "")
        bse = info.get("bse_code", "")
        
        match = False
        if q in name.lower():
            match = True
        elif nse and q in nse.lower():
            match = True
        elif bse and q in bse.lower():
            match = True
            
        if match:
            if nse:
                ticker = f"{nse}.NS"
                label = f"{name} ({ticker})"
            else:
                ticker = f"{bse}.BO"
                label = f"{name} ({ticker})"
            results.append((label, ticker))
            if len(results) >= 15:
                break

    # 2. Search US hardcoded map
    for us_name, us_ticker in _US_NAME_TO_TICKER.items():
        if q in us_name or q in us_ticker.lower():
            label = f"{us_name.title()} ({us_ticker})"
            if not any(t == us_ticker for _, t in results):
                results.append((label, us_ticker))

    # 3. If few results, fallback to screener live search
    if len(results) < 5:
        try:
            resp = requests.get(
                f"https://www.screener.in/api/company/search/?q={requests.utils.quote(query)}",
                headers=HEADERS,
                timeout=5,
            )
            if resp.status_code == 200:
                screener_results = resp.json()
                for sr in screener_results:
                    sr_name = sr.get("name", "")
                    url = sr.get("url", "")
                    if url.startswith("/company/"):
                        parts = url.strip("/").split("/")
                        if len(parts) >= 2:
                            slug = parts[1].upper()
                            
                            # Determine exchange suffix
                            ticker = f"{slug}.NS"
                            for n, i in index.items():
                                if i.get("nse_symbol") == slug:
                                    ticker = f"{slug}.NS"
                                    break
                                elif i.get("bse_code") == slug:
                                    ticker = f"{slug}.BO"
                                    break
                                    
                            label = f"{sr_name} ({ticker})"
                            if not any(t == ticker for _, t in results):
                                results.append((label, ticker))
                                if len(results) >= 15:
                                    break
        except Exception as e:
            logger.warning(f"Screener fallback search failed: {e}")

    # 4. Always provide the exact input as a fallback option so users can search unlisted or international tickers
    raw_ticker = query.upper()
    if not any(t == raw_ticker for _, t in results):
        results.append((f"Use exact: {raw_ticker}", raw_ticker))

    return results


def _resolve_via_screener_search(name: str) -> str | None:
    """Search screener.in for an Indian company name. Returns 'TICKER' (no suffix) or None."""
    try:
        resp = requests.get(
            f"https://www.screener.in/api/company/search/?q={requests.utils.quote(name)}",
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        results = resp.json()
        if not results:
            return None
        url = results[0].get("url", "")
        if url.startswith("/company/"):
            parts = url.strip("/").split("/")
            if len(parts) >= 2:
                slug = parts[1]
                return slug.upper()
    except Exception as e:
        logger.warning(f"Screener search failed for '{name}': {type(e).__name__}: {e}")
    return None


def _resolve_via_stockanalysis_search(name: str) -> str | None:
    """Search stockanalysis.com for a US company name. Returns 'TICKER' or None."""
    try:
        # Their internal search endpoint
        resp = requests.get(
            "https://api.stockanalysis.com/api/search",
            params={"q": name, "t": "stocks"},
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        # Shape: {"data": [{"s": "AAPL", "n": "Apple Inc.", ...}, ...]}
        results = data.get("data", []) if isinstance(data, dict) else data
        if results and isinstance(results, list):
            top = results[0]
            ticker = top.get("s") or top.get("symbol") or top.get("ticker")
            if ticker:
                return ticker.upper()
    except Exception as e:
        logger.info(f"Stockanalysis search failed for '{name}': {type(e).__name__}: {e}")
    return None


def resolve_ticker_from_input(user_input: str) -> tuple[str, str]:
    """
    Resolve user input to a canonical ticker.

    Returns (resolved_ticker, source) where source is one of:
      - "ticker": input was already a ticker, returned uppercased
      - "indian_name": resolved via local index or screener.in search
      - "us_name_hardcoded": resolved via hardcoded top-50 US map
      - "us_name_search": resolved via stockanalysis.com search
      - "unresolved": returned input uppercased (downstream will fail with clear error)
    """
    raw = (user_input or "").strip()
    if not raw:
        return raw, "ticker"

    # Already looks like a ticker — pass through
    if _looks_like_ticker(raw):
        return raw.upper(), "ticker"

    # Treat as a name. Check cache first.
    norm = _normalize(raw)
    cache_key = f"ticker_resolved_{norm.replace(' ', '_')}.json"
    cached = cache.get_json(cache_key, _RESOLVE_CACHE_TTL)
    if cached and isinstance(cached, dict) and cached.get("ticker"):
        return cached["ticker"], cached.get("source", "cached")

    # Try local index exact match
    index = get_local_index()
    for name, info in index.items():
        if _normalize(name) == norm:
            nse = info.get("nse_symbol")
            bse = info.get("bse_code")
            if nse:
                ticker = f"{nse}.NS"
            else:
                ticker = f"{bse}.BO"
            cache.set_json(cache_key, {"ticker": ticker, "source": "indian_name"})
            logger.info(f"Resolved name '{raw}' → {ticker} via local index")
            return ticker, "indian_name"

    # Try Indian fallback (user is India-based; default bias)
    indian = _resolve_via_screener_search(raw)
    if indian:
        ticker = f"{indian}.NS" # Default
        for name, info in index.items():
            if info.get("nse_symbol") == indian:
                ticker = f"{indian}.NS"
                break
            elif info.get("bse_code") == indian:
                ticker = f"{indian}.BO"
                break
        cache.set_json(cache_key, {"ticker": ticker, "source": "indian_name"})
        logger.info(f"Resolved name '{raw}' → {ticker} via screener.in")
        return ticker, "indian_name"

    # Try US hardcoded map
    if norm in _US_NAME_TO_TICKER:
        ticker = _US_NAME_TO_TICKER[norm]
        cache.set_json(cache_key, {"ticker": ticker, "source": "us_name_hardcoded"})
        logger.info(f"Resolved name '{raw}' → {ticker} via hardcoded US map")
        return ticker, "us_name_hardcoded"

    # Try stockanalysis.com search
    us = _resolve_via_stockanalysis_search(raw)
    if us:
        cache.set_json(cache_key, {"ticker": us, "source": "us_name_search"})
        logger.info(f"Resolved name '{raw}' → {us} via stockanalysis.com search")
        return us, "us_name_search"

    # Fall through — return uppercased; downstream will fail with clear error
    logger.warning(f"Could not resolve name '{raw}' to any ticker; passing through as-is")
    return raw.upper(), "unresolved"
