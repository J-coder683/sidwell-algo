"""
Document discovery and text extraction for the qualitative layer.
Reads PDFs from a Drive-synced local folder.
"""
import os
import hashlib
import logging
from pathlib import Path

import pdfplumber

logger = logging.getLogger("sidwell.data.documents")

# Classification keywords. PDFs are classified by filename substring match.
# Multiple keywords per type for flexibility in user file naming.
DOCUMENT_TYPES = {
    "transcript": ["concall", "transcript", "earnings-call", "call", "earnings"],
    "investor_deck": ["deck", "presentation", "investor-presentation", "ip"],
    "mda": ["mda", "md&a", "management-discussion", "annual"],
}


def get_drive_path() -> Path:
    """Resolve the Drive sync root. Configurable via SIDWELL_DRIVE_PATH env var."""
    default = Path.home() / "Sidwell-Drive"
    return Path(os.getenv("SIDWELL_DRIVE_PATH", str(default)))


def discover_documents(ticker: str) -> list:
    """
    Find PDFs for a ticker in the Drive folder.

    Returns:
        list of dicts with keys: path (Path), type (str), filename (str),
        hash (str — first 16 chars of sha256 of file bytes), text (str).

    Returns empty list if the ticker folder doesn't exist or contains no PDFs.
    Never raises on missing folder — graceful degrade is mandatory.
    """
    folder = get_drive_path() / ticker
    if not folder.exists():
        logger.info(f"No Drive folder found for {ticker} at {folder}")
        return []

    docs = []
    for pdf_path in sorted(folder.glob("*.pdf")):
        doc_type = _classify(pdf_path.name)
        text = _extract_text(pdf_path)
        file_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()[:16]
        docs.append({
            "path": pdf_path,
            "type": doc_type,
            "filename": pdf_path.name,
            "hash": file_hash,
            "text": text,
        })

    logger.info(f"Discovered {len(docs)} PDF(s) for {ticker}")
    return docs


def _classify(filename: str) -> str:
    """Classify a PDF by its filename. Returns 'unknown' if no keyword matches."""
    name_low = filename.lower()
    for doc_type, keywords in DOCUMENT_TYPES.items():
        if any(kw in name_low for kw in keywords):
            return doc_type
    return "unknown"


def _extract_text(pdf_path: Path) -> str:
    """
    Extract text from a PDF. Returns empty string on failure (graceful degrade).
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return "\n\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        logger.warning(f"Failed to extract text from {pdf_path}: {e}")
        return ""
