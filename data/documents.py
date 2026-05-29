import logging

logger = logging.getLogger("sidwell.data.documents")

def discover_documents(ticker: str) -> list[dict]:
    """
    Returns document references for the ticker, dispatching by region:
    - Indian (.NS / .BO) → screener.in
    - US (any other) → empty list (EDGAR is v0.8; graceful degrade until then)
    """
    is_india = ticker.endswith(".NS") or ticker.endswith(".BO")
    if is_india:
        from data.scrapers.screener import fetch_screener_documents
        return fetch_screener_documents(ticker)
    else:
        # US: EDGAR auto-fetch is v0.8. For now, return empty → qualitative falls to graceful "unavailable" default.
        logger.info(f"No qualitative document source wired for US ticker {ticker} yet (EDGAR in v0.8); soft checks default per framework rules.")
        return []
