import os, glob, logging
logger = logging.getLogger("sidwell.research_provider")

# Library lives outside git (default under ~/.sidwell, which is already gitignored).
# Override with env SIDWELL_RESEARCH_DIR. Layout: <DIR>/<TICKER>/<anything>.pdf
RESEARCH_LIB_DIR = os.environ.get(
    "SIDWELL_RESEARCH_DIR",
    os.path.join(os.path.expanduser("~"), ".sidwell", "research_library"),
)

def get_research_for_ticker(ticker: str, max_reports: int = 2) -> list:
    """Return up to max_reports most-recent research PDFs for a ticker as
    [{'filename': str, 'bytes': bytes}]. Empty list if none / dir missing.
    Never raises."""
    try:
        safe = (ticker or "").upper().replace("/", "_").replace("\\", "_")
        if not safe:
            return []
        d = os.path.join(RESEARCH_LIB_DIR, safe)
        if not os.path.isdir(d):
            return []
        pdfs = sorted(glob.glob(os.path.join(d, "*.pdf")),
                      key=os.path.getmtime, reverse=True)[:max_reports]
        out = []
        for p in pdfs:
            try:
                with open(p, "rb") as f:
                    out.append({"filename": os.path.basename(p), "bytes": f.read()})
            except Exception as e:
                logger.warning(f"Failed reading {p}: {e}")
        return out
    except Exception as e:
        logger.warning(f"get_research_for_ticker({ticker}) failed: {e}")
        return []
