"""
Resolve user input (ticker or company name) to a canonical ticker.

v0.7.5: User can type "Reliance" or "Apple" instead of "RELIANCE.NS" or "AAPL".
Indian names resolve via screener.in's search API (already integrated for slug
resolution). US names resolve via a hardcoded top-50 mapping plus a
stockanalysis.com search fallback.
"""
import json
import logging
import requests
from data import cache

logger = logging.getLogger("sidwell.ticker_resolver")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.5",
}

# Resolved name → ticker mappings cached for 7 days so repeat queries are
# instant and don't hammer the search APIs.
_RESOLVE_CACHE_TTL = 7 * 24 * 60 * 60


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
        # results[0] is best match. URL like "/company/RELIANCE/"
        url = results[0].get("url", "")
        if "/company/" in url:
            slug = url.strip("/").split("/")[-1]
            return slug.upper() if slug else None
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
      - "indian_name": resolved via screener.in search
      - "us_name_hardcoded": resolved via hardcoded top-50 US map
      - "us_name_search": resolved via stockanalysis.com search
      - "unresolved": returned input uppercased (downstream will fail with clear error)

    The (ticker, source) tuple lets the UI display "Resolved 'Reliance' → RELIANCE.NS"
    when source != "ticker", helping the user confirm what got matched.
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

    # Try Indian first (user is India-based; default bias)
    indian = _resolve_via_screener_search(raw)
    if indian:
        ticker = f"{indian}.NS"
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
