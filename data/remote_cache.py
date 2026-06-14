"""
Remote (L2) cache backend — Supabase PostgREST over plain `requests`.

This is the persistence tier behind data/cache.py. The local file cache (L1) at
~/.sidwell/cache is wiped on every Streamlit Cloud restart/redeploy/wake, which
made production re-run the multi-minute DeepSeek qualitative call every cold start.
L2 survives those events.

Design constraints honored:
  - No new dependency: uses `requests` (already required), not supabase-py.
  - Self-disabling: if SUPABASE_URL / SUPABASE_KEY are not configured, every
    function is a no-op returning None, so behavior is identical to file-only.
  - Best-effort: every network/parse error is swallowed and logged. The cache is
    an optimization — it must never raise into the pipeline.

Credentials (server-side only; service_role key bypasses RLS so the public anon
key stays locked out of the table):
  SUPABASE_URL  e.g. https://abcd.supabase.co
  SUPABASE_KEY  the service_role secret key (kept in st.secrets / env, never client)

Table (create once in Supabase):
  create table if not exists sidwell_cache (
    key        text        primary key,
    value      jsonb       not null,
    created_at timestamptz not null default now()
  );
  alter table sidwell_cache enable row level security;  -- no policy: only service_role
"""
import os
import logging
from datetime import datetime, timezone

import requests

logger = logging.getLogger("sidwell.remote_cache")

_TABLE = "sidwell_cache"
_TIMEOUT = 8  # seconds — short; L2 is an optimization, never block the pipeline on it

# Cache the resolved (url, key) so we don't re-read secrets on every call.
# None  = not yet resolved; ("", "") = resolved-but-unconfigured (disabled).
_CONFIG = None


def _resolve_config():
    """Return (base_url, api_key) or ("", "") when unconfigured. Reads st.secrets
    first (Streamlit Cloud / local secrets.toml), then environment — mirrors the
    DEEPSEEK_API_KEY resolution in analysis/qualitative.py."""
    url = key = None
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except Exception:
        pass
    if not url:
        url = os.getenv("SUPABASE_URL")
    if not key:
        key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return "", ""
    return url.rstrip("/"), key


def _config():
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = _resolve_config()
    return _CONFIG


def reset_config_cache():
    """Test hook: force re-resolution of secrets on the next call."""
    global _CONFIG
    _CONFIG = None


def is_enabled() -> bool:
    return bool(_config()[0])


def _headers(api_key: str) -> dict:
    return {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _age_seconds(created_at: str) -> float | None:
    """Parse a PostgREST timestamptz ('2026-06-15T12:00:00+00:00' / '...Z') and
    return its age in seconds, or None if unparseable."""
    try:
        ts = created_at.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds()
    except Exception:
        return None


def get(key: str, ttl_seconds: int) -> dict | None:
    """Fetch a cached JSON value if present and within ttl_seconds. Returns the
    stored dict/list, or None on miss/expiry/disabled/error."""
    base_url, api_key = _config()
    if not base_url:
        return None
    try:
        resp = requests.get(
            f"{base_url}/rest/v1/{_TABLE}",
            headers=_headers(api_key),
            params={"key": f"eq.{key}", "select": "value,created_at", "limit": 1},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            logger.info(f"Remote cache miss for key: {key}")
            return None
        row = rows[0]
        age = _age_seconds(row.get("created_at", ""))
        if age is None or age > ttl_seconds:
            logger.info(f"Remote cache expired for key: {key} (age={age})")
            return None
        logger.info(f"Remote cache hit for key: {key}")
        return row.get("value")
    except Exception as e:
        logger.warning(f"Remote cache get failed for {key}: {type(e).__name__}: {e}")
        return None


def set(key: str, value: dict) -> None:
    """Upsert a JSON value with a fresh created_at. Best-effort; never raises."""
    base_url, api_key = _config()
    if not base_url:
        return
    try:
        headers = _headers(api_key)
        headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
        body = {
            "key": key,
            "value": value,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        resp = requests.post(
            f"{base_url}/rest/v1/{_TABLE}",
            headers=headers,
            json=body,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        logger.info(f"Remote cache wrote key: {key}")
    except Exception as e:
        logger.warning(f"Remote cache set failed for {key}: {type(e).__name__}: {e}")
