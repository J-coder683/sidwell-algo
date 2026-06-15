import os
import time
import json
import logging

from data import remote_cache

CACHE_DIR = os.path.expanduser("~/.sidwell/cache")
os.makedirs(CACHE_DIR, exist_ok=True)

logger = logging.getLogger("sidwell.cache")

# Keys eligible for the remote (L2) persistence tier. Only the expensive
# DeepSeek qualitative result is persisted remotely for now; every other entry
# is a sub-second scrape that stays in the local file cache. Widen this tuple to
# extend L2 coverage (e.g. add "financials_") — no other change required.
_REMOTE_PREFIXES = ("qualitative_", "qualpack_", "quallens_")


def _remote_eligible(key: str) -> bool:
    return key.startswith(_REMOTE_PREFIXES)

def get_cache_path(key: str) -> str:
    """
    Get the absolute path to a cache file. Replaces characters that are invalid in file names.
    """
    safe_key = key.replace("/", "_").replace("\\", "_").replace(":", "_")
    return os.path.join(CACHE_DIR, safe_key)

def is_expired(filepath: str, ttl_seconds: int) -> bool:
    """
    Check if the file at filepath has exceeded the TTL.
    """
    if not os.path.exists(filepath):
        return True
    mtime = os.path.getmtime(filepath)
    age = time.time() - mtime
    return age > ttl_seconds

def get_bytes(key: str, ttl_seconds: int) -> bytes | None:
    """
    Retrieve raw bytes from cache if they exist and are not expired.
    """
    path = get_cache_path(key)
    if os.path.exists(path):
        if is_expired(path, ttl_seconds):
            logger.info(f"Cache expired for key: {key}")
            return None
        logger.info(f"Cache hit for key: {key}")
        with open(path, "rb") as f:
            return f.read()
    logger.info(f"Cache miss for key: {key}")
    return None

def set_bytes(key: str, data: bytes) -> str:
    """
    Save raw bytes to cache. Returns the path to the cached file.
    """
    path = get_cache_path(key)
    with open(path, "wb") as f:
        f.write(data)
    logger.info(f"Saved cache key: {key} to {path}")
    return path

def get_json(key: str, ttl_seconds: int) -> dict | None:
    """
    Retrieve JSON data from cache if it exists and is not expired.

    Two-tier: the local file cache (L1) is checked first. On an L1 miss for a
    remote-eligible key, the Supabase L2 tier is consulted; a remote hit is
    written through to L1 so subsequent reads in the same container are local.
    L2 is a no-op when unconfigured, so this reduces to file-only behavior.
    """
    raw = get_bytes(key, ttl_seconds)
    if raw is not None:
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception as e:
            logger.warning(f"Failed to decode cached JSON for key {key}: {e}")
            return None

    # L1 miss → try the remote tier for eligible keys.
    if _remote_eligible(key):
        remote_val = remote_cache.get(key, ttl_seconds)
        if remote_val is not None:
            # Write through to L1 only (set_bytes, not set_json) so we don't echo
            # the value straight back to L2.
            try:
                set_bytes(key, json.dumps(remote_val, indent=2, default=str).encode("utf-8"))
            except Exception as e:
                logger.warning(f"Write-through to L1 failed for {key}: {e}")
            return remote_val

    return None

def set_json(key: str, data: dict) -> str:
    """
    Save dict as JSON to cache (L1), and mirror to the remote L2 tier for
    remote-eligible keys. The remote write is best-effort and never raises.
    """
    raw = json.dumps(data, indent=2, default=str).encode("utf-8")
    path = set_bytes(key, raw)
    if _remote_eligible(key):
        remote_cache.set(key, data)
    return path
