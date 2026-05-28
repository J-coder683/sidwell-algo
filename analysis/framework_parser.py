"""
analysis/framework_parser.py
----------------------------
Parses all 5 frameworks/*.md files at module import time and caches the
Logic paragraph for each check.

Public API
----------
get_reasoning(lens_name: str, check_num: int) -> str | None

Lens code calls it as:
    framework_parser.get_reasoning("buffett", int(check_id.split("_")[0]))

Design decisions
----------------
* Integer-keyed: parser uses the integer from "#### N. Title" as the key.
  This survives check_id renames as long as the numeric prefix is stable.
* Import-time parsing: all 5 files are parsed once when the module is first
  imported.  Any framework with a missing Logic paragraph raises ValueError
  immediately (loud fail at startup, not silently at request time).
* Strips markdown bold/italic from the returned reasoning strings so the UI
  / PDF layer can apply its own formatting.
"""

import re
import logging
from pathlib import Path

logger = logging.getLogger("sidwell.analysis.framework_parser")

# ---------------------------------------------------------------------------
# Resolve frameworks/ directory relative to this file's location
# ---------------------------------------------------------------------------
_FRAMEWORKS_DIR = Path(__file__).parent.parent / "frameworks"

_LENS_FILES = {
    "buffett": _FRAMEWORKS_DIR / "buffett.md",
    "marks": _FRAMEWORKS_DIR / "marks.md",
    "kkr": _FRAMEWORKS_DIR / "kkr.md",
    "blackstone": _FRAMEWORKS_DIR / "blackstone.md",
    "apollo": _FRAMEWORKS_DIR / "apollo.md",
}

# Expected check counts per lens — used to validate parse completeness
_EXPECTED_CHECKS = {
    "buffett": 14,
    "marks": 14,
    "kkr": 18,
    "blackstone": 14,
    "apollo": 16,
}

# Module-level cache: {lens_name: {check_num (int): reasoning_str}}
_CACHE: dict[str, dict[int, str]] = {}


def _strip_markdown(text: str) -> str:
    """
    Remove markdown bold (**text**) and italic (*text* or _text_) markers
    from a string so the returned reasoning is plain prose.
    """
    # Remove bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__", r"\1", text, flags=re.DOTALL)
    # Remove italic: *text* or _text_  (single star/underscore)
    text = re.sub(r"\*(.+?)\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"_(.+?)_", r"\1", text, flags=re.DOTALL)
    # Collapse multiple whitespace / newlines to single space
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_framework(lens_name: str, path: Path) -> dict[int, str]:
    """
    Parse a single framework markdown file and return
    {check_number (int): reasoning_string}.

    Check sections are identified by lines matching:
        #### N. <Title>
    where N is a positive integer.

    The Logic paragraph is the text immediately following a line that is
    exactly "**Logic:**" (with or without trailing colon and space variants).
    It ends at the next line starting with "**Source:**",
    "**Determinism note:**", or "####".
    """
    if not path.exists():
        raise ValueError(
            f"Framework file for lens '{lens_name}' not found at: {path}"
        )

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    result: dict[int, str] = {}

    # Pattern for check section headers: #### N. Title
    check_header_re = re.compile(r"^####\s+(\d+)\.\s+", re.MULTILINE)

    # Split file into per-check blocks
    # Find all header positions
    header_positions = [
        (int(m.group(1)), m.start())
        for m in check_header_re.finditer(text)
    ]

    if not header_positions:
        raise ValueError(
            f"No '#### N. Title' check headers found in {path}. "
            "The framework file may have been reformatted."
        )

    # For each check block, extract the Logic paragraph
    for i, (check_num, start_pos) in enumerate(header_positions):
        # Block ends at next header's start, or EOF
        end_pos = header_positions[i + 1][1] if i + 1 < len(header_positions) else len(text)
        block = text[start_pos:end_pos]

        # Find Logic: line.  Accepts variants:
        #   **Logic:** ...
        #   **Logic** ...   (no colon)
        logic_re = re.compile(
            r"\*\*Logic:?\*\*\s*(.+?)(?=\*\*Source:?\*\*|\*\*Determinism note:?\*\*|^####)",
            re.DOTALL | re.MULTILINE,
        )
        m = logic_re.search(block)
        if not m:
            raise ValueError(
                f"Lens '{lens_name}' check #{check_num} has no **Logic:** paragraph "
                f"in {path}. This is a framework file bug — fix the framework before shipping."
            )

        reasoning_raw = m.group(1).strip()
        reasoning = _strip_markdown(reasoning_raw)

        if not reasoning:
            raise ValueError(
                f"Lens '{lens_name}' check #{check_num} has an empty Logic paragraph "
                f"after stripping markdown. Framework file: {path}"
            )

        result[check_num] = reasoning
        logger.debug(f"Parsed {lens_name} check #{check_num}: {reasoning[:60]}...")

    return result


def _load_all() -> None:
    """
    Parse all 5 framework files and populate the module-level cache.
    Called once at module import.  Raises ValueError on any problem so
    failures surface immediately rather than at request time.
    """
    for lens_name, path in _LENS_FILES.items():
        logger.info(f"Parsing framework: {lens_name} from {path.name}")
        parsed = _parse_framework(lens_name, path)

        expected = _EXPECTED_CHECKS[lens_name]
        if len(parsed) != expected:
            # Warn but don't raise — some frameworks may have renumbered checks.
            # The missing-check guard in get_reasoning() will catch runtime gaps.
            logger.warning(
                f"Lens '{lens_name}': expected {expected} checks, "
                f"parsed {len(parsed)}. Keys: {sorted(parsed.keys())}"
            )

        _CACHE[lens_name] = parsed
        logger.info(f"Cached {len(parsed)} checks for '{lens_name}'")


# Parse at import time
_load_all()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_reasoning(lens_name: str, check_num: int) -> str | None:
    """
    Return the Logic reasoning string for a specific lens check.

    Parameters
    ----------
    lens_name : str
        One of "buffett", "marks", "kkr", "blackstone", "apollo".
    check_num : int
        The integer check number (1-based), extracted from the check_id
        by calling int(check_id.split("_")[0]).

    Returns
    -------
    str | None
        The reasoning string (plain text, markdown stripped) or None if
        the check number is not found in the parsed cache.

    Usage in lens evaluators
    ------------------------
        from analysis import framework_parser
        check_num = int(check_id.split("_")[0])
        reasoning = framework_parser.get_reasoning("buffett", check_num)
        if reasoning is None:
            raise ValueError(
                f"framework_reasoning missing for buffett check {check_id}"
            )
        checks[check_id]["framework_reasoning"] = reasoning
    """
    lens_cache = _CACHE.get(lens_name)
    if lens_cache is None:
        raise ValueError(
            f"Unknown lens '{lens_name}'. "
            f"Valid lenses: {list(_LENS_FILES.keys())}"
        )
    return lens_cache.get(check_num)


def get_all_reasonings(lens_name: str) -> dict[int, str]:
    """
    Return the full {check_num: reasoning} dict for a lens.
    Primarily used by tests.
    """
    lens_cache = _CACHE.get(lens_name)
    if lens_cache is None:
        raise ValueError(f"Unknown lens '{lens_name}'.")
    return dict(lens_cache)
