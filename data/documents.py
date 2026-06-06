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
        logger.info(f"US ticker {ticker}: concall-style docs (10-K text, 8-K Ex-99.1, transcripts, calendar) are supplied via research_docs in value.analyze; discover_documents returns [].")
        return []
