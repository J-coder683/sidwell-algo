import logging
from data.documents import fetch_screener_documents
from analysis.qualitative import get_company_qualitative

logger = logging.getLogger("sidwell.analysis.ajp_builder")

def build_ajp(ticker: str) -> dict:
    """
    Builds the Assumption Justification Pack (AJP) by piggybacking on the 
    qualitative extraction pipeline. This ensures documents are read once 
    and Gemini is called once per ticker.
    """
    logger.info(f"Building AJP for {ticker}...")
    
    # 1. Fetch documents in-memory
    docs = fetch_screener_documents(ticker)
    if not docs:
        logger.warning(f"No documents found for {ticker}; returning empty AJP payload.")
        return {"meta": {}, "assumptions": []}
        
    # 2. Extract qualitative + AJP via Gemini
    # The qualitative pipeline prompt has been updated to return an "ajp" key
    extracted = get_company_qualitative(ticker, docs)
    
    # 3. Extract the AJP from the combined payload
    ajp_data = extracted.get("ajp")
    
    if not ajp_data:
        logger.warning(f"Qualitative extraction for {ticker} did not return an 'ajp' block.")
        return {"meta": {}, "assumptions": []}
        
    return ajp_data
