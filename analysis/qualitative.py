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
import re
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


def _safe_json_loads(content: str):
    """Parse model JSON, tolerating two things DeepSeek occasionally emits:
    trailing commas before } or ], and // line-comments on their OWN line
    (URL-safe: only strips lines whose first non-space chars are //). Tries strict
    first. Raises json.JSONDecodeError if still unparseable so callers degrade."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        cleaned = re.sub(r"(?m)^[ \t]*//.*$", "", content)          # whole-line // comments only
        cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)            # trailing commas
        return json.loads(cleaned)

QUALITATIVE_CACHE_TTL = 30 * 24 * 60 * 60  # 30 days
# v0.7.6.4: Swapped Gemini 3.5 Flash → DeepSeek V4 Pro.
# DeepSeek provides superior reasoning for qualitative metrics with a 1M token window.
MODEL_NAME = "deepseek-v4-pro"
PROMPT_VERSION = "v0.16"  # v0.16: strict-JSON rule (single quotes inside strings) to stop parse breaks

def _get_mode() -> str:
    try:
        import streamlit as st
        m = st.secrets.get("QUALITATIVE_MODE")
        if m: return m
    except Exception:
        pass
    return os.getenv("QUALITATIVE_MODE", "monolithic")

QUALITATIVE_MODE = _get_mode()


# ─── Model router ─────────────────────────────────────────────────────────────
# Per-stage model selection. Defaults keep stage-1 and stage-2 on DeepSeek-direct.
# Override any stage — or any individual lens — via a secret WITHOUT a redeploy:
#   MODEL_ROUTE_STAGE1        = "deepseek:deepseek-v4-pro"
#   MODEL_ROUTE_STAGE2        = "nim:deepseek-ai/deepseek-v4"   (free on NVIDIA NIM)
#   MODEL_ROUTE_STAGE2_APOLLO = "nim:qwen/qwen3.5"              (per-lens override)
# Value format is "endpoint:model"; endpoint keys are defined in _ENDPOINTS below.
# The monolithic fallback (_call_deepseek) is intentionally NOT routed — it stays
# the known-good DeepSeek safety net so a bad route can never lose a result.
_ENDPOINTS = {
    # endpoint name -> (base_url, secret/env var holding its API key)
    "deepseek": ("https://api.deepseek.com", "DEEPSEEK_API_KEY"),
    "nim": ("https://integrate.api.nvidia.com/v1", "NVIDIA_NIM_API_KEY"),
}
_DEFAULT_ROUTES = {
    "stage1": f"deepseek:{MODEL_NAME}",
    "stage2": f"deepseek:{MODEL_NAME}",
}


def _get_secret(name: str):
    """Read a secret from st.secrets (Streamlit Cloud / local) then env."""
    try:
        import streamlit as st
        v = st.secrets.get(name)
        if v:
            return v
    except Exception:
        pass
    return os.getenv(name)


def _resolve_route(stage: str):
    """Return (base_url, api_key, model, endpoint) for a pipeline stage.
    For 'stage2_<lens>' the lookup is MODEL_ROUTE_STAGE2_<LENS> ->
    MODEL_ROUTE_STAGE2 -> default; otherwise MODEL_ROUTE_<STAGE> -> default."""
    spec = _get_secret(f"MODEL_ROUTE_{stage.upper()}")
    default_key = stage
    if not spec and stage.startswith("stage2_"):
        spec = _get_secret("MODEL_ROUTE_STAGE2")
        default_key = "stage2"
    if not spec:
        spec = _DEFAULT_ROUTES.get(default_key, _DEFAULT_ROUTES["stage1"])
    endpoint, _, model = spec.partition(":")
    base_url, key_name = _ENDPOINTS.get(endpoint, _ENDPOINTS["deepseek"])
    return base_url, _get_secret(key_name), model, endpoint


def _route_client(stage: str):
    """Return (client_or_None, model, endpoint) for a stage. client is None when
    the endpoint's API key is not configured."""
    base_url, api_key, model, endpoint = _resolve_route(stage)
    if not api_key:
        return None, model, endpoint
    return OpenAI(api_key=api_key, base_url=base_url, timeout=600.0), model, endpoint

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


def _extract_html(html_bytes: bytes) -> tuple[str, dict]:
    """Extract readable text from an HTML document. Screener's credit-rating links
    are HTML rationale pages (CRISIL/ICRA), not PDFs — so they can't go through
    pdfplumber. Strips scripts/styles/nav, returns the visible text."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_bytes, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    if len(text) > MAX_DOC_CHARS:
        text = text[:MAX_DOC_CHARS]
    logger.info(f"HTML document extracted: ~{len(text)} chars")
    return text, {"sections_found": ["html_full"], "fallback_used": False, "pages_extracted": 0}


def _table_to_md(rows: list) -> str:
    """Convert a list-of-lists table (from pdfplumber) to a Markdown table string."""
    rows = [["" if c is None else str(c).replace("\n", " ").strip() for c in r]
            for r in (rows or []) if r]
    if not rows:
        return ""
    header = rows[0] or [""]
    w = len(header)
    out = ["| " + " | ".join(header) + " |",
           "| " + " | ".join(["---"] * w) + " |"]
    for r in rows[1:]:
        r = (r + [""] * w)[:w]
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def _extract_research_markdown(pdf_bytes: bytes) -> tuple[str, dict]:
    """Research/sell-side reports are table-heavy. Emit markdown: page prose + each
    table rendered as a markdown table, so DeepSeek sees structured numbers."""
    parts = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            txt = (page.extract_text() or "").strip()
            if txt:
                parts.append(txt)
            for tbl in (page.extract_tables() or []):
                md = _table_to_md(tbl)
                if md:
                    parts.append(md)
    return "\n\n".join(parts), {}


def _select_documents(documents: list, has_research: bool) -> list:
    """If research is supplied, use only the latest concall (discover returns
    newest-first) plus the research; else use all discovered documents."""
    if has_research:
        concalls = [d for d in documents if d.get("type") == "concall_transcript"]
        return concalls[:1]   # latest only; [] if none
    return documents


# ─── DeepSeek client ──────────────────────────────────────────────────────────

def _call_deepseek(documents_text: str, ticker: str, historical_context: str = "",
                   stream_cb=None) -> dict:
    """Invoke DeepSeek V4 Pro for structured qualitative extraction.

    historical_context: optional Markdown block (from build_historical_context_md)
    prepended before the prompt template so the model sees real numbers first.

    stream_cb: optional callable(chars_received:int). The response is streamed and
    deltas are assembled into the same JSON string parsed before. On a throttled
    (~1/sec) cadence the running character count is reported via stream_cb. This
    surfaces progress and — critically — keeps the Streamlit browser↔server
    websocket warm during the multi-minute call, avoiding the 1011 keepalive
    ping-timeout that silently dropped long runs before the lenses could render.
    The callback is best-effort: any exception inside it is swallowed.
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

    chars = 0  # running response char count (referenced in logging/except)
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            timeout=600.0,  # 10 min — DeepSeek V4 Pro can be slow on large multi-doc payloads
        )
        _t0 = time.perf_counter()
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a top-tier Wall Street buy-side analyst. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            stream=True,
        )

        parts = []
        _last_emit = 0.0
        for chunk in stream:
            # Defensive: real streams emit a final chunk whose delta.content is None,
            # and tool/role-only chunks may carry no choices. Skip anything empty.
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            piece = getattr(delta, "content", None) if delta is not None else None
            if not piece:
                continue
            parts.append(piece)
            chars += len(piece)
            # Throttled heartbeat (~1/sec): enough to keep the websocket alive and
            # animate progress, without flooding Streamlit with reruns per token.
            if stream_cb is not None:
                now = time.perf_counter()
                if now - _last_emit >= 1.0:
                    _last_emit = now
                    try:
                        stream_cb(chars)
                    except Exception:
                        pass  # UI heartbeat must never break the pipeline

        # Final flush so the UI lands on the true total even for short/fast responses.
        if stream_cb is not None:
            try:
                stream_cb(chars)
            except Exception:
                pass

        _elapsed = time.perf_counter() - _t0
        # Duration logging so the timeout can be sized from real data (not a guess).
        logger.info(
            f"DeepSeek stream for {ticker} completed in {_elapsed:.1f}s "
            f"(model={MODEL_NAME}, prompt_chars={len(prompt)}, response_chars={chars})"
        )

        content = "".join(parts).strip()
        if content.startswith("```json"):
            content = content.split("```json")[1].rsplit("```", 1)[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].rsplit("```", 1)[0].strip()

        return _safe_json_loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"DeepSeek stream for {ticker} returned invalid JSON after {chars} chars: {e}")
        return _unavailable(f"DeepSeek response not valid JSON: {e}")
    except Exception as e:
        logger.error(f"DeepSeek call failed for {ticker} after {chars} chars: {e}")
        return _unavailable(f"DeepSeek error: {type(e).__name__}: {e}")



def _call_stage1(documents_text: str, ticker: str, historical_context: str = "",
                 stream_cb=None) -> dict:
    client, model, endpoint = _route_client("stage1")
    if client is None:
        return _unavailable(f"API key not configured for endpoint '{endpoint}'")

    prompt_path = Path(__file__).parent / "prompts" / "stage1_extraction.md"
    prompt_template = prompt_path.read_text(encoding="utf-8")
    hist_prefix = f"{historical_context}\n\n" if historical_context else ""
    prompt = f"{hist_prefix}{prompt_template}\n\n## Documents for {ticker}\n\n{documents_text}"

    chars = 0
    try:
        _t0 = time.perf_counter()
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a top-tier Wall Street buy-side analyst. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            stream=True,
        )

        parts = []
        _last_emit = 0.0
        for chunk in stream:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            piece = getattr(delta, "content", None) if delta is not None else None
            if not piece:
                continue
            parts.append(piece)
            chars += len(piece)
            if stream_cb is not None:
                now = time.perf_counter()
                if now - _last_emit >= 1.0:
                    _last_emit = now
                    try:
                        stream_cb(chars)
                    except Exception:
                        pass

        if stream_cb is not None:
            try:
                stream_cb(chars)
            except Exception:
                pass

        _elapsed = time.perf_counter() - _t0
        logger.info(
            f"Stage 1 stream for {ticker} completed in {_elapsed:.1f}s "
            f"(model={model}@{endpoint}, prompt_chars={len(prompt)}, response_chars={chars})"
        )

        content = "".join(parts).strip()
        if content.startswith("```json"):
            content = content.split("```json")[1].rsplit("```", 1)[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].rsplit("```", 1)[0].strip()

        return _safe_json_loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Stage 1 stream for {ticker} returned invalid JSON after {chars} chars: {e}")
        return _unavailable(f"Stage 1 response not valid JSON: {e}")
    except Exception as e:
        logger.error(f"Stage 1 call failed for {ticker} after {chars} chars: {e}")
        return _unavailable(f"Stage 1 error: {type(e).__name__}: {e}")

def _call_stage2(lens: str, evidence_pack: dict, ticker: str, historical_context: str = "") -> dict:
    client, model, endpoint = _route_client(f"stage2_{lens}")
    if client is None:
        return {}

    prompt_path = Path(__file__).parent / "prompts" / f"stage2_{lens}.md"
    prompt_template = prompt_path.read_text(encoding="utf-8")
    
    evidence_pack_json = json.dumps(evidence_pack, indent=2)
    prompt = prompt_template.replace("{evidence_pack_json}", evidence_pack_json).replace("{historical_context}", historical_context)

    try:
        _t0 = time.perf_counter()
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a top-tier Wall Street buy-side analyst. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            stream=False,
        )
        
        content = resp.choices[0].message.content.strip()
        _elapsed = time.perf_counter() - _t0
        logger.info(
            f"Stage 2 {lens} for {ticker} completed in {_elapsed:.1f}s "
            f"(model={model}@{endpoint})"
        )

        if content.startswith("```json"):
            content = content.split("```json")[1].rsplit("```", 1)[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].rsplit("```", 1)[0].strip()

        return _safe_json_loads(content)
    except Exception as e:
        logger.error(f"Stage 2 call failed for {lens}/{ticker}: {e}")
        return {}


# ─── Public API ───────────────────────────────────────────────────────────────

MIN_USABLE_DOCS = 1

def extract_qualitative(
    ticker: str,
    documents: list,
    historical_context: str = "",
    research_docs: list | None = None,
    stream_cb=None,
    lenses_to_run: list | None = None,
) -> dict:
    """
    Run DeepSeek V4 Pro extraction across the documents.

    Parameters
    ----------
    ticker : str
        Stock ticker.
    documents : list
        Discovered documents (each: {url, type, label}) from doc_module.discover_documents.
    historical_context : str
        Optional Markdown block prepended before the prompt.
    research_docs : list[{"filename": str, "bytes": bytes}] | None
        User-uploaded equity research PDFs (or other docs). When supplied:
        - Only the latest concall (newest-first from discover) + these research
          docs are sent to DeepSeek (discovery still runs to get the concall).
        - The MIN_USABLE_DOCS gate is bypassed (research is itself high-value).
        - Cache key incorporates a hash of the uploaded bytes so a stale
          no-research result is never served.

    Returns a dict matching the schema in qualitative_extraction.md plus:
      - status: "available" | "unavailable"
      - reason: string (only when status == "unavailable")
      - model: MODEL_NAME
      - documents_used: list of labels
      - extraction_metadata: per-document extraction details

    Cached by combined document URL hash + prompt version.
    Never raises — all failure modes return an "unavailable" dict.
    """
    research_docs = research_docs or []
    has_research = len(research_docs) > 0
    selected = _select_documents(documents, has_research)

    # Gate: require high-value docs only when no user research is supplied.
    if not has_research:
        if not documents:
            return _unavailable(f"No documents found for {ticker} on screener.in")
        high_value_docs = [d for d in documents if d.get("type") in ("annual_report", "concall_transcript")]
        if len(high_value_docs) < MIN_USABLE_DOCS:
            return _unavailable(
                f"Fewer than {MIN_USABLE_DOCS} high-value document(s) (AR/Concall) found for {ticker}"
            )
    else:
        # With research: still return unavailable if we have absolutely nothing to send.
        if not selected and not research_docs:
            return _unavailable(f"No documents found for {ticker} on screener.in")

    # Cache key must vary with uploaded research content so a stale no-research
    # result is never returned when research is added.
    url_src = "".join(sorted(d["url"] for d in selected))
    research_src = b"".join(
        r.get("bytes", b"") + r.get("text", "").encode("utf-8")
        for r in research_docs
    )
    combined = hashlib.sha256(url_src.encode() + research_src).hexdigest()[:16]
    cache_key = f"qualitative_{ticker}_{combined}_{PROMPT_VERSION}.json"

    # Add selected lenses to cache key so we don't return a monolithic cache 
    # that doesn't have the newly requested lenses if we change selection.
    # Wait, the spec says "The new keys reuse the same `combined` doc-hash so selection changes reuse cached stage-1 + per-lens results." 
    # It does not say to add lenses_to_run to the qualitative_ cache key. 
    # I will stick to the exact cache_key as before, but if using monolithic fallback, it's just the combined hash.
    # In two_stage mode the per-stage caches (qualpack_/quallens_) are the cache.
    # The lens-agnostic monolithic cache_key would wrongly return a partial result
    # built for a DIFFERENT lens selection (unselected lenses' signals = None), so
    # skip it here and let the per-stage caches handle reuse.
    if QUALITATIVE_MODE != "two_stage":
        cached = cache.get_json(cache_key, QUALITATIVE_CACHE_TTL)
        if cached is not None:
            logger.info(f"Loaded qualitative analysis for {ticker} from cache")
            return cached

    extracted_docs = []
    extraction_metadata_docs = []

    # --- Fetch and extract selected discovered documents (URL path) ---
    for d in selected:
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

            # Detect format by magic bytes: real PDFs start with "%PDF". Non-PDFs
            # (screener credit-rating links are HTML rationale pages) go to the HTML
            # extractor so they aren't silently dropped by pdfplumber.
            if not pdf_bytes[:5].startswith(b"%PDF"):
                text, meta = _extract_html(pdf_bytes)
            elif doc_type == "annual_report":
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

    # --- Extract user-uploaded research docs (bytes path, no network) ---
    for r in research_docs:
        # Pre-extracted text path (e.g., from EDGAR 10-K integration)
        pre_extracted_text = r.get("text")
        if pre_extracted_text:
            extracted_docs.append({
                "filename": r.get("filename", "document.txt"),
                "type": r.get("type", "regulatory_filing"),
                "text": pre_extracted_text,
            })
            extraction_metadata_docs.append({
                "url": r.get("filename", "document.txt"),
                "type": r.get("type", "regulatory_filing"),
                "chars_extracted": len(pre_extracted_text),
                "sections_found": ["pre_extracted"],
                "fallback_used": False,
            })
            continue

        b = r.get("bytes", b"")
        if not b:
            continue
        if len(b) > 50 * 1024 * 1024:  # OOM guard, same as URL path
            logger.warning(
                f"Skipping uploaded research {r.get('filename')}: "
                f"file too large ({len(b)/1024/1024:.1f} MB). Prevents OOM."
            )
            continue
        try:
            if b[:5].startswith(b"%PDF"):
                text, meta = _extract_research_markdown(b)
            else:
                text, meta = _extract_html(b)
            extracted_docs.append({
                "filename": r.get("filename", "research.pdf"),
                "type": "research_report",
                "text": text,
            })
            extraction_metadata_docs.append({
                "url": r.get("filename", "research.pdf"),
                "type": "research_report",
                "chars_extracted": len(text),
                "sections_found": [],
                "fallback_used": False,
            })
        except Exception as e:
            logger.warning(f"Failed to parse uploaded research {r.get('filename')}: {e}")

    if not extracted_docs:
        return _unavailable(f"All documents for {ticker} failed to fetch or parse")

    documents_text = "\n\n---\n\n".join(
        f"### {d['filename']} (type: {d['type']})\n\n{d['text']}"
        for d in extracted_docs
    )

    logger.info(f"Sending {len(documents_text)} chars to DeepSeek for analysis. This may take a few minutes...")
    
    result = None
    if QUALITATIVE_MODE == "two_stage":
        try:
            import concurrent.futures
            
            l2r = lenses_to_run if lenses_to_run is not None else ["buffett", "marks", "kkr", "blackstone", "apollo"]
            
            pack_key = f"qualpack_{ticker}_{combined}_{PROMPT_VERSION}.json"
            stage1_res = cache.get_json(pack_key, QUALITATIVE_CACHE_TTL)
            if not stage1_res:
                stage1_res = _call_stage1(documents_text, ticker, historical_context=historical_context, stream_cb=stream_cb)
                if stage1_res.get("status") != "unavailable":
                    cache.set_json(pack_key, stage1_res)

            if stage1_res.get("status") == "unavailable":
                raise Exception("Stage 1 unavailable")

            evidence_pack = stage1_res.get("evidence_pack", {})
            
            lens_results = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_lens = {}
                for lens in l2r:
                    lens_key = f"quallens_{lens}_{ticker}_{combined}_{PROMPT_VERSION}.json"
                    cached_lens = cache.get_json(lens_key, QUALITATIVE_CACHE_TTL)
                    if cached_lens:
                        lens_results[lens] = cached_lens
                    else:
                        future_to_lens[executor.submit(_call_stage2, lens, evidence_pack, ticker, historical_context)] = (lens, lens_key)
                
                for future in concurrent.futures.as_completed(future_to_lens):
                    lens, lens_key = future_to_lens[future]
                    res = future.result()
                    if not res:
                        raise Exception(f"Stage 2 failed to produce results for {lens}")
                    lens_results[lens] = res
                    cache.set_json(lens_key, res)

            result = _unavailable("")
            for k, v in stage1_res.items():
                if k in result and k != "status" and k != "reason" and k != "evidence_pack":
                    result[k] = v
            
            for lens, res in lens_results.items():
                if res:
                    for k, v in res.items():
                        if k in result:
                            result[k] = v
                            
            result["status"] = "available"
            
        except Exception as e:
            logger.warning(f"Two-stage pipeline failed, falling back to monolithic: {e}")
            result = None

    if result is None or result.get("status") == "unavailable":
        result = _call_deepseek(documents_text, ticker, historical_context=historical_context,
                                stream_cb=stream_cb)

    if result.get("status") == "unavailable":
        return result

    result["status"] = "available"
    result["model"] = MODEL_NAME
    result["documents_used"] = [d["filename"] for d in extracted_docs]
    result["extraction_metadata"] = {"documents": extraction_metadata_docs}
    # Only the monolithic path writes the lens-agnostic cache_key; two_stage relies
    # on its per-stage caches so a selection change can't read back a stale partial.
    if QUALITATIVE_MODE != "two_stage":
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
