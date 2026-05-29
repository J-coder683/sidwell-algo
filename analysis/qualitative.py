"""
Qualitative analysis layer. Sends document text to Gemini and parses
structured JSON output. Caches result keyed on document hash + prompt version.
"""
import os
import json
import logging
import hashlib
import requests
from io import BytesIO
from pathlib import Path

import pdfplumber
from google import genai
from google.genai import types

from data import cache

logger = logging.getLogger("sidwell.analysis.qualitative")

QUALITATIVE_CACHE_TTL = 30 * 24 * 60 * 60  # 30 days
MODEL_NAME = "gemini-3.5-flash"  # Free tier, sufficient for structured extraction
PROMPT_VERSION = "v0.5"  # Bump when prompt schema changes; invalidates old cache entries

# Maximum characters of PDF text per document sent to Gemini.
# Gemini Flash supports 1M token context; 200k chars is safely within limits.
MAX_DOC_CHARS = 200_000

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/pdf,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.screener.in/",  # some BSE/NSE PDFs check referer
}


def extract_qualitative(ticker: str, documents: list) -> dict:
    """
    Run Gemini extraction across the documents.

    Returns a dict matching the schema in qualitative_extraction.md plus:
      - status: "available" | "unavailable"
      - reason: string (only when status == "unavailable")
      - model: model name used
      - documents_used: list of filenames

    Cached by combined document url hash + prompt version.
    Never raises — all failure modes return an "unavailable" dict.
    """
    if not documents:
        return _unavailable(f"No documents found for {ticker} on screener.in (annual report + concall transcripts not posted)")

    urls = sorted(d["url"] for d in documents)
    combined_url_hash = hashlib.sha256("".join(urls).encode()).hexdigest()[:16]
    cache_key = f"qualitative_{ticker}_{combined_url_hash}_{PROMPT_VERSION}.json"

    cached = cache.get_json(cache_key, QUALITATIVE_CACHE_TTL)
    if cached is not None:
        logger.info(f"Loaded qualitative analysis for {ticker} from cache")
        return cached

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _unavailable("GEMINI_API_KEY not configured")

    extracted_docs = []
    for d in documents:
        url = d["url"]
        try:
            resp = requests.get(url, timeout=30, headers=BROWSER_HEADERS)
            resp.raise_for_status()
            with pdfplumber.open(BytesIO(resp.content)) as pdf:
                text = "\n\n".join(page.extract_text() or "" for page in pdf.pages)
            
            if len(text) > MAX_DOC_CHARS:
                text = text[:MAX_DOC_CHARS // 2] + "\n\n...[TRUNCATED MIDDLE]...\n\n" + text[-(MAX_DOC_CHARS // 2):]
                
            extracted_docs.append({
                "filename": d.get("label", url),
                "type": d.get("type", "unknown"),
                "text": text
            })
        except Exception as e:
            logger.warning(f"Failed to fetch or parse {url}: {type(e).__name__}: {e}")
            continue

    if not extracted_docs:
        return _unavailable(f"All {len(documents)} documents for {ticker} failed to fetch or parse")

    try:
        client = genai.Client(api_key=api_key)
        prompt = _build_prompt(extracted_docs)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )
        result = json.loads(response.text)
        result["status"] = "available"
        result["model"] = MODEL_NAME
        result["documents_used"] = [d["filename"] for d in extracted_docs]
        cache.set_json(cache_key, result)
        logger.info(f"Cached fresh qualitative analysis for {ticker}")
        return result
    except json.JSONDecodeError as e:
        return _unavailable(f"Qualitative extraction failed: {type(e).__name__}")
    except Exception as e:
        logger.error(f"Gemini call failed for {ticker}: {e}")
        return _unavailable(f"Qualitative extraction failed: {type(e).__name__}")


def _build_prompt(extracted_docs: list) -> str:
    prompt_path = Path(__file__).parent / "prompts" / "qualitative_extraction.md"
    template = prompt_path.read_text(encoding="utf-8")
    docs_text = "\n\n---\n\n".join(
        f"### {d['filename']} (type: {d['type']})\n\n{d['text']}"
        for d in extracted_docs
    )
    return template.replace("{documents_text}", docs_text)


def _unavailable(reason: str) -> dict:
    """Return a fully-shaped 'unavailable' result. Matches schema shape so
    downstream code can read fields without KeyError."""
    return {
        "status": "unavailable",
        "reason": reason,
        "forward_guidance": [],
        "risk_callouts": [],
        "strategic_themes": [],
        "tone_assessment": {"current": None, "trajectory": None, "notes": None},
        "coherence_assessment": {"verdict": None, "reasoning": None},
        "owner_orientation_signal": {"verdict": None, "evidence": None},
        "holdability_assessment": {"verdict": None, "reasoning": None},
        "cycle_position": {
            "sector_cycle": None, "company_cycle": None, "reasoning": None
        },
        "variant_perception": {
            "consensus_view": None, "company_view": None,
            "variant_present": None, "specificity": None, "notes": None
        },
        "management_humility": {"verdict": None, "evidence": None},
        "why_now_signal": {
            "verdict": None, "specific_event": None, "notes": None
        },
        "willing_seller_signal": {"verdict": None, "notes": None},
        "ma_platform_potential": {"verdict": None, "notes": None},
        "workforce_stavros_fit": {"verdict": None, "notes": None},
        "mgmt_upgrade_potential": {"verdict": None, "notes": None},
        "wc_optimization_signal": {"verdict": None, "notes": None},
        "structural_tailwind_signal": {"verdict": None, "notes": None},
        "multi_product_engagement_signal": {"verdict": None, "notes": None},
        "chaos_dislocation_catalyst": {"verdict": None, "notes": None},
        "fulcrum_security_signal": {"verdict": None, "notes": None},
        "abf_credit_fit": {"verdict": None, "notes": None},
        "complexity_moat_signal": {"verdict": None, "notes": None},
        "permanent_hold_viable": {"verdict": None, "notes": None},
        "covenant_control_potential": {"verdict": None, "notes": None},
        "documents_used": [],
        "model": None,
    }
