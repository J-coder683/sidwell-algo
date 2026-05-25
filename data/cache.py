import os
import time
import json
import logging

CACHE_DIR = os.path.expanduser("~/.sidwell/cache")
os.makedirs(CACHE_DIR, exist_ok=True)

logger = logging.getLogger("sidwell.cache")

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
    """
    raw = get_bytes(key, ttl_seconds)
    if raw is None:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as e:
        logger.warning(f"Failed to decode cached JSON for key {key}: {e}")
        return None

def set_json(key: str, data: dict) -> str:
    """
    Save dict as JSON to cache.
    """
    raw = json.dumps(data, indent=2, default=str).encode("utf-8")
    return set_bytes(key, raw)
