"""
Qualitative analysis layer. Sends document text to Gemini 3.5 Flash and parses
structured JSON output. Caches result keyed on document URL hash + prompt version.

v0.7.6 changes (preserved through v0.7.6.3 revert):
  - Smart annual report extraction: TOC-aware section detection with fallback
  - Concall transcripts use full-text path (no truncation)
  - extraction_metadata field added to output

v0.7.6.3: Reverted from Bedrock/Claude Haiku 4.5 → Gemini.
AWS Marketplace blocked UPI autopay as payment for Anthropic models; subscription
couldn't complete without a credit/debit card on file. Gemini spend cap raised
₹100 → ₹500 to absorb v0.7.6 cache-invalidation churn. All v0.7.6 architectural
work preserved — only the LLM client layer reverts.
"""
import os
import time
import json
import logging
import hashlib
import requests
from io import BytesIO
from pathlib import Path

from openai import OpenAI
import pdfplumber

from data import cache

logger = logging.getLogger("sidwell.analysis.qualitative")

QUALITATIVE_CACHE_TTL = 30 * 24 * 60 * 60  # 30 days
# v0.7.6.4: Swapped Gemini 3.5 Flash → DeepSeek V4 Pro.
# DeepSeek provides superior reasoning for qualitative metrics with a 1M token window.
MODEL_NAME = "deepseek-v4-pro"
PROMPT_VERSION = "v0.11"  # v0.11: historical-context Markdown anchor + normalized_ebit_margin + working_capital_days drivers

# Maximum characters sent to Gemini for annual reports (smart-extracted).
# Concalls use full-text — they are typically short (20-60 pages).
MAX_DOC_CHARS = 200_000

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/pdf,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.screener.in/",
}

# ─── Section detection keyword lists ─────────────────────────────────────────

MDA_KEYWORDS = [
    "management discussion",
    "management's discussion",
    "md&a",
    "management discussion and analysis",
    "management discussion & analysis",
]
RISK_KEYWORDS = [
    "risk factors",
    "risk management",
    "key risks",
    "principal risks",
    "risks and concerns",
    "risks & concerns",
    "risk and governance",       # Reliance pattern
    "risks and governance",      # variant
    "risk review",
    "risks and mitigation",
]
BOARDS_REPORT_KEYWORDS = [
    "board's report",
    "directors' report",
    "directors report",
    "report of the board",
    "report of the directors",
]
RPT_KEYWORDS = [
    "related party transactions",
    "related party disclosure",
    "transactions with related parties",
    "related parties",
]

TOC_SEARCH_RANGE_MAX = 60  # pages; handles large Indian co preambles (AGM notices etc.)


# ─── Annual report section extraction ────────────────────────────────────────

def _extract_annual_report_sections(pdf_bytes: bytes) -> tuple[str, dict]:
    """Returns (combined_text, metadata_dict).
    Performs TOC-aware section detection via body text-search. Falls back to
    pages 1-80 + last 30 when fewer than 2 sections can be located.
    """
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        total_pages = len(pdf.pages)
        if total_pages == 0:
            return "", {"sections_found": [], "fallback_used": False, "pages_extracted": 0}

        # Step 1: Locate TOC (search first 60 pages for table-of-contents markers).
        toc_page_idx = None
        toc_range = min(TOC_SEARCH_RANGE_MAX, total_pages)
        for i in range(toc_range):
            page = pdf.pages[i]
            page_text = (page.extract_text() or "").lower()
            page.flush_cache()
            if any(marker in page_text for marker in
                   ["table of contents", "contents", "inside this report", "in this report"]):
                # Heuristic: real TOC pages reference at least 2 of our target sections
                if sum(1 for kw_set in [MDA_KEYWORDS, RISK_KEYWORDS, BOARDS_REPORT_KEYWORDS, RPT_KEYWORDS]
                       if any(kw in page_text for kw in kw_set)) >= 2:
                    toc_page_idx = i
                    break

        # Step 2: Find section starts via direct text-search in the body.
        # Start AFTER toc_page_idx + 10 to skip any multi-page TOC content.
        # (Two-page spread PDFs and multi-page TOCs require +10, not +5.)
        search_start = (toc_page_idx if toc_page_idx is not None else 0) + 10

        def _find_section_start(keywords: list, search_from: int = 0) -> int | None:
            for i in range(search_from, total_pages):
                page = pdf.pages[i]
                txt = (page.extract_text() or "").lower().strip()
                page.flush_cache()
                if not txt:
                    continue
                # Only match keyword in first 300 chars of page (section header zone)
                head = txt[:300]
                for kw in keywords:
                    if kw in head:
                        return i
            return None

        sections_found: dict[str, int] = {}
        for name, kw_list in [
            ("MD&A", MDA_KEYWORDS),
            ("Risk Factors", RISK_KEYWORDS),
            ("Board's Report", BOARDS_REPORT_KEYWORDS),
            ("Related Party Transactions", RPT_KEYWORDS),
        ]:
            start_page = _find_section_start(kw_list, search_from=search_start)
            if start_page is not None:
                sections_found[name] = start_page

        n_found = len(sections_found)

        # Step 3: Fallback if fewer than 2 sections detected
        if n_found <= 1:
            text = _extract_fallback(pdf, total_pages)
            fallback_pages = min(80, total_pages) + max(0, total_pages - max(min(80, total_pages), total_pages - 30))
            meta = {
                "sections_found": list(sections_found.keys()),
                "fallback_used": True,
                "fallback_reason": f"Only {n_found} of 4 sections detected",
                "pages_extracted": fallback_pages,
            }
            logger.info(
                f"Annual report extracted (fallback): {n_found} of 4 sections found "
                f"({list(sections_found.keys())}); {fallback_pages} PDF pages; "
                f"~{fallback_pages * 2000} chars"
            )
            return text, meta

        # Step 4: Extract each section through to the next one, or +30 pages if last
        sorted_sections = sorted(sections_found.items(), key=lambda x: x[1])
        chunks = []
        total_pages_extracted = 0
        for idx, (name, start) in enumerate(sorted_sections):
            if idx + 1 < len(sorted_sections):
                end = sorted_sections[idx + 1][1]
            else:
                end = min(total_pages, start + 30)
                
            section_text_parts = []
            for p in range(start, end):
                page = pdf.pages[p]
                section_text_parts.append(page.extract_text() or "")
                page.flush_cache()
                
            section_text = "\n".join(section_text_parts)
            pages_this = end - start
            total_pages_extracted += pages_this
            chunks.append(f"\n\n### {name} (PDF pages {start + 1}-{end})\n\n{section_text}")

        combined = "\n".join(chunks)

        # Apply MAX_DOC_CHARS truncation to annual reports only
        if len(combined) > MAX_DOC_CHARS:
            combined = (combined[:MAX_DOC_CHARS // 2]
                        + "\n\n...[TRUNCATED MIDDLE]...\n\n"
                        + combined[-(MAX_DOC_CHARS // 2):])

        meta = {
            "sections_found": list(sections_found.keys()),
            "fallback_used": False,
            "total_sections_targeted": 4,
            "pages_extracted": total_pages_extracted,
        }
        logger.info(
            f"Annual report extracted: {n_found} of 4 sections found "
            f"({list(sections_found.keys())}); {total_pages_extracted} PDF pages; "
            f"~{total_pages_extracted * 2000} chars"
        )
        return combined, meta


def _extract_fallback(pdf, total_pages: int) -> str:
    """Fallback when section-detection finds <2 sections:
    pages 1-80 + last 30. Captures most chairman letters + start of MD&A
    + risk factors typically appearing toward end."""
    head_end = min(80, total_pages)
    tail_start = max(head_end, total_pages - 30)
    
    head_parts = []
    for p in range(0, head_end):
        page = pdf.pages[p]
        head_parts.append(page.extract_text() or "")
        page.flush_cache()
        
    tail_parts = []
    for p in range(tail_start, total_pages):
        page = pdf.pages[p]
        tail_parts.append(page.extract_text() or "")
        page.flush_cache()
        
    head_text = "\n".join(head_parts)
    tail_text = "\n".join(tail_parts)
    return (f"\n\n### Pages 1-{head_end} (fallback)\n\n{head_text}"
            f"\n\n### Last {total_pages - tail_start} pages (fallback)\n\n{tail_text}")


def _extract_concall(pdf_bytes: bytes) -> tuple[str, dict]:
    """Concall transcripts: full text, no truncation."""
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        total_pages = len(pdf.pages)
        parts = []
        for p in range(total_pages):
            page = pdf.pages[p]
            parts.append(page.extract_text() or "")
            page.flush_cache()
        text = "\n\n".join(parts)
        
    logger.info(f"Concall transcript extracted: {total_pages} PDF pages; ~{len(text)} chars")
    return text, {"sections_found": ["full_text"], "fallback_used": False, "pages_extracted": total_pages}


def _extract_generic(pdf_bytes: bytes) -> tuple[str, dict]:
    """Generic fallback for unknown doc types: pages 1-80 + last 30."""
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        total_pages = len(pdf.pages)
        text = _extract_fallback(pdf, total_pages)
    return text, {"sections_found": [], "fallback_used": True, "pages_extracted": min(80, total_pages) + 30}


# ─── DeepSeek client ──────────────────────────────────────────────────────────

def _call_deepseek(documents_text: str, ticker: str, historical_context: str = "") -> dict:
    """Invoke DeepSeek V4 Pro for structured qualitative extraction.

    historical_context: optional Markdown block (from build_historical_context_md)
    prepended before the prompt template so the model sees real numbers first.
    """
    try:
        import streamlit as st
        api_key = st.secrets.get("DEEPSEEK_API_KEY")
    except Exception:
        api_key = None
        
    if not api_key:
        api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        return _unavailable("DEEPSEEK_API_KEY not configured")

    prompt_path = Path(__file__).parent / "prompts" / "qualitative_extraction.md"
    prompt_template = prompt_path.read_text(encoding="utf-8")
    # Prepend the historical-financials block (if any) before the prompt so the
    # model anchors its forward assumptions before reading management documents.
    hist_prefix = f"{historical_context}\n\n" if historical_context else ""
    prompt = f"{hist_prefix}{prompt_template}\n\n## Documents for {ticker}\n\n{documents_text}"

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            timeout=600.0,  # 10 min — DeepSeek V4 Pro can be slow on large multi-doc payloads
        )
        _t0 = time.perf_counter()
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a top-tier Wall Street buy-side analyst. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        _elapsed = time.perf_counter() - _t0
        # Duration logging so the timeout can be sized from real data (not a guess).
        logger.info(
            f"DeepSeek call for {ticker} completed in {_elapsed:.1f}s "
            f"(model={MODEL_NAME}, prompt_chars={len(prompt)})"
        )

        content = resp.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content.split("```json")[1].rsplit("```", 1)[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].rsplit("```", 1)[0].strip()
            
        return json.loads(content)
    except json.JSONDecodeError as e:
        return _unavailable(f"DeepSeek response not valid JSON: {e}")
    except Exception as e:
        logger.error(f"DeepSeek call failed for {ticker}: {e}")
        return _unavailable(f"DeepSeek error: {type(e).__name__}: {e}")


# ─── Public API ───────────────────────────────────────────────────────────────

MIN_USABLE_DOCS = 1

def extract_qualitative(ticker: str, documents: list, historical_context: str = "") -> dict:
    """
    Run DeepSeek V4 Pro extraction across the documents.

    Returns a dict matching the schema in qualitative_extraction.md plus:
      - status: "available" | "unavailable"
      - reason: string (only when status == "unavailable")
      - model: MODEL_NAME
      - documents_used: list of labels
      - extraction_metadata: per-document extraction details

    Cached by combined document URL hash + prompt version.
    Never raises — all failure modes return an "unavailable" dict.
    """
    if not documents:
        return _unavailable(f"No documents found for {ticker} on screener.in")
        
    high_value_docs = [d for d in documents if d.get("type") in ("annual_report", "concall_transcript")]
    if len(high_value_docs) < MIN_USABLE_DOCS:
        return _unavailable(f"Fewer than {MIN_USABLE_DOCS} high-value document(s) (AR/Concall) found for {ticker}")

    urls = sorted(d["url"] for d in documents)
    combined_url_hash = hashlib.sha256("".join(urls).encode()).hexdigest()[:16]
    cache_key = f"qualitative_{ticker}_{combined_url_hash}_{PROMPT_VERSION}.json"

    cached = cache.get_json(cache_key, QUALITATIVE_CACHE_TTL)
    if cached is not None:
        logger.info(f"Loaded qualitative analysis for {ticker} from cache")
        return cached

    extracted_docs = []
    extraction_metadata_docs = []

    for d in documents:
        url = d["url"]
        doc_type = d.get("type", "unknown")
        label = d.get("label", url)
        try:
            resp = requests.get(url, timeout=30, headers=BROWSER_HEADERS)
            resp.raise_for_status()
            pdf_bytes = resp.content
            
            # Prevent Streamlit Cloud OOM: Skip PDFs larger than 50MB
            if len(pdf_bytes) > 50 * 1024 * 1024:
                logger.warning(f"Skipping {url}: file too large ({len(pdf_bytes)/1024/1024:.1f} MB). Prevents OOM.")
                continue

            if doc_type == "annual_report":
                text, meta = _extract_annual_report_sections(pdf_bytes)
            elif doc_type == "concall_transcript":
                text, meta = _extract_concall(pdf_bytes)
            else:
                text, meta = _extract_generic(pdf_bytes)

            chars_extracted = len(text)
            extraction_metadata_docs.append({
                "url": url,
                "type": doc_type,
                "sections_found": meta.get("sections_found", []),
                "fallback_used": meta.get("fallback_used", False),
                "chars_extracted": chars_extracted,
            })
            extracted_docs.append({
                "filename": label,
                "type": doc_type,
                "text": text,
            })
        except Exception as e:
            logger.warning(f"Failed to fetch or parse {url}: {type(e).__name__}: {e}")
            continue

    if not extracted_docs:
        return _unavailable(f"All {len(documents)} documents for {ticker} failed to fetch or parse")

    documents_text = "\n\n---\n\n".join(
        f"### {d['filename']} (type: {d['type']})\n\n{d['text']}"
        for d in extracted_docs
    )

    logger.info(f"Sending {len(documents_text)} chars to DeepSeek for analysis. This may take a few minutes...")
    result = _call_deepseek(documents_text, ticker, historical_context=historical_context)
    if result.get("status") == "unavailable":
        return result

    result["status"] = "available"
    result["model"] = MODEL_NAME
    result["documents_used"] = [d["filename"] for d in extracted_docs]
    result["extraction_metadata"] = {"documents": extraction_metadata_docs}
    cache.set_json(cache_key, result)
    logger.info(f"Cached fresh qualitative analysis for {ticker} (DeepSeek/{MODEL_NAME})")
    return result


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
        "extraction_metadata": {"documents": []},
        "model": None,
    }
