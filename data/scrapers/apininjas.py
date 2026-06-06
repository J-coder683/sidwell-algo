import os
import logging
import requests
import datetime
from data import cache

logger = logging.getLogger(__name__)

_API_KEY = os.environ.get("API_NINJAS_KEY")
_TRANSCRIPT_URL = "https://api.api-ninjas.com/v1/earningstranscript"
_CALENDAR_URL   = "https://api.api-ninjas.com/v1/earningscalendar"
TTL_TRANSCRIPT = 7 * 24 * 3600
TTL_CALENDAR   = 24 * 3600

def _recent_quarters(n_back: int) -> list[tuple[int, int]]:
    today = datetime.date.today()
    y = today.year
    q = (today.month - 1) // 3 + 1
    
    out = []
    for _ in range(n_back):
        q -= 1
        if q == 0:
            q = 4
            y -= 1
        out.append((y, q))
    return out

def fetch_earnings_transcripts(ticker: str, n: int = 2) -> list[dict]:
    key = f"transcript_apininjas_{ticker.upper()}_last{n}.json"
    cached = cache.get_json(key, TTL_TRANSCRIPT)
    if cached is not None:
        return cached
        
    out = []
    try:
        if not _API_KEY:
            logger.info("API_NINJAS_KEY not set; skipping transcripts")
            cache.set_json(key, out)
            return out
            
        for yr, q in _recent_quarters(n + 3):
            if len(out) >= n:
                break
            try:
                resp = requests.get(
                    _TRANSCRIPT_URL,
                    headers={"X-Api-Key": _API_KEY},
                    params={"ticker": ticker.upper(), "year": yr, "quarter": q},
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    transcript = data.get("transcript", "")
                    if len(transcript) > 1000:
                        out.append({
                            "filename": f"{ticker.upper()} earnings call Q{q} {yr}",
                            "text": transcript[:200_000]
                        })
                else:
                    logger.debug(f"API Ninjas transcript non-200 for {ticker.upper()} {yr} Q{q}: {resp.status_code}")
            except Exception as e:
                logger.debug(f"Exception fetching transcript for {ticker.upper()} {yr} Q{q}: {e}")
                continue
                
    except Exception as outer_e:
        logger.debug(f"Outer exception in fetch_earnings_transcripts: {outer_e}")
        out = []

    cache.set_json(key, out)
    return out

def fetch_earnings_calendar(ticker: str) -> list[dict]:
    key = f"earnings_calendar_{ticker.upper()}.json"
    cached = cache.get_json(key, TTL_CALENDAR)
    if cached is not None:
        return cached

    out = []
    try:
        if not _API_KEY:
            cache.set_json(key, out)
            return out
            
        resp = requests.get(
            _CALENDAR_URL,
            headers={"X-Api-Key": _API_KEY},
            params={"ticker": ticker.upper()},
            timeout=30
        )
        if resp.status_code == 200:
            events = resp.json()
            if events:
                events = events[:6]
                today_str = datetime.date.today().isoformat()
                
                md = []
                upcoming = [e for e in events if str(e.get("pricedate", e.get("date", ""))) >= today_str]
                if upcoming:
                    next_date = upcoming[-1].get("pricedate", upcoming[-1].get("date", ""))
                    md.append(f"**NEXT UPCOMING EARNINGS:** {next_date}\n")
                
                md.append("| Date | Est EPS | Act EPS | Est Rev | Act Rev |")
                md.append("|---|---|---|---|---|")
                for e in events:
                    date = e.get("pricedate", e.get("date", ""))
                    est_eps = e.get("estimated_eps", "")
                    act_eps = e.get("actual_eps", "")
                    est_rev = e.get("estimated_revenue", "")
                    act_rev = e.get("actual_revenue", "")
                    md.append(f"| {date} | {est_eps} | {act_eps} | {est_rev} | {act_rev} |")
                
                out = [{"filename": f"{ticker.upper()} earnings calendar", "text": "\n".join(md)}]
    except Exception as e:
        logger.debug(f"Exception fetching calendar for {ticker.upper()}: {e}")
        out = []
        
    cache.set_json(key, out)
    return out
