"""
Tests for the two-tier (L1 file + L2 Supabase) cache persistence in data/cache.py
and the remote backend in data/remote_cache.py.

All offline: the local file layer is patched (get_bytes/set_bytes) and the remote
layer is patched or driven by a mocked `requests`, so no disk or network is touched.
"""
import json
from unittest.mock import patch, MagicMock

import pytest

from data import cache, remote_cache


# --- prefix gate ------------------------------------------------------------

def test_remote_eligible_only_qualitative():
    assert cache._remote_eligible("qualitative_AAPL_abc123_v0.13.json")
    assert not cache._remote_eligible("financials_AAPL.json")
    assert not cache._remote_eligible("macro_rf_US.json")
    assert not cache._remote_eligible("documents_AAPL.json")


# --- get_json tiering -------------------------------------------------------

def test_get_json_l1_hit_does_not_touch_remote():
    payload = {"status": "available"}
    raw = json.dumps(payload).encode("utf-8")
    with patch("data.cache.get_bytes", return_value=raw), \
         patch("data.remote_cache.get") as mock_remote_get:
        result = cache.get_json("qualitative_AAPL_x_v0.13.json", 100)
    assert result == payload
    mock_remote_get.assert_not_called()  # L1 hit short-circuits


def test_get_json_l1_miss_falls_back_to_remote_and_writes_through():
    payload = {"status": "available", "model": "deepseek-v4-pro"}
    with patch("data.cache.get_bytes", return_value=None), \
         patch("data.remote_cache.get", return_value=payload) as mock_remote_get, \
         patch("data.cache.set_bytes") as mock_set_bytes:
        result = cache.get_json("qualitative_AAPL_x_v0.13.json", 100)
    assert result == payload
    mock_remote_get.assert_called_once()
    # Write-through to L1 only — must NOT go via set_json (which would re-hit L2).
    mock_set_bytes.assert_called_once()


def test_get_json_ineligible_key_skips_remote():
    with patch("data.cache.get_bytes", return_value=None), \
         patch("data.remote_cache.get") as mock_remote_get:
        result = cache.get_json("financials_AAPL.json", 100)
    assert result is None
    mock_remote_get.assert_not_called()  # non-qualitative keys never hit L2


def test_get_json_remote_miss_returns_none():
    with patch("data.cache.get_bytes", return_value=None), \
         patch("data.remote_cache.get", return_value=None):
        result = cache.get_json("qualitative_AAPL_x_v0.13.json", 100)
    assert result is None


# --- set_json mirroring -----------------------------------------------------

def test_set_json_mirrors_eligible_key_to_remote():
    data = {"status": "available"}
    with patch("data.cache.set_bytes", return_value="/tmp/x") as mock_set_bytes, \
         patch("data.remote_cache.set") as mock_remote_set:
        path = cache.set_json("qualitative_AAPL_x_v0.13.json", data)
    assert path == "/tmp/x"
    mock_set_bytes.assert_called_once()
    mock_remote_set.assert_called_once_with("qualitative_AAPL_x_v0.13.json", data)


def test_set_json_does_not_mirror_ineligible_key():
    with patch("data.cache.set_bytes", return_value="/tmp/x"), \
         patch("data.remote_cache.set") as mock_remote_set:
        cache.set_json("financials_AAPL.json", {"a": 1})
    mock_remote_set.assert_not_called()


# --- remote_cache self-disable (no secrets) ---------------------------------

def test_remote_disabled_without_secrets(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    import streamlit as st
    monkeypatch.setattr(st, "secrets", {}, raising=False)  # {}.get(...) -> None
    remote_cache.reset_config_cache()
    try:
        assert remote_cache.is_enabled() is False
        with patch("data.remote_cache.requests.get") as mock_get, \
             patch("data.remote_cache.requests.post") as mock_post:
            assert remote_cache.get("qualitative_X_v0.13.json", 100) is None
            remote_cache.set("qualitative_X_v0.13.json", {"a": 1})
            mock_get.assert_not_called()
            mock_post.assert_not_called()
    finally:
        remote_cache.reset_config_cache()


# --- remote_cache get/set when configured (requests mocked) -----------------

def _enable_remote(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://proj.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "service-role-key")
    remote_cache.reset_config_cache()


def test_remote_get_returns_value_within_ttl(monkeypatch):
    _enable_remote(monkeypatch)
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat()
    resp = MagicMock()
    resp.json.return_value = [{"value": {"status": "available"}, "created_at": now_iso}]
    resp.raise_for_status.return_value = None
    try:
        with patch("data.remote_cache.requests.get", return_value=resp):
            out = remote_cache.get("qualitative_X_v0.13.json", 3600)
        assert out == {"status": "available"}
    finally:
        remote_cache.reset_config_cache()


def test_remote_get_expired_returns_none(monkeypatch):
    _enable_remote(monkeypatch)
    resp = MagicMock()
    resp.json.return_value = [{"value": {"x": 1}, "created_at": "2000-01-01T00:00:00+00:00"}]
    resp.raise_for_status.return_value = None
    try:
        with patch("data.remote_cache.requests.get", return_value=resp):
            out = remote_cache.get("qualitative_X_v0.13.json", 3600)
        assert out is None  # far older than ttl
    finally:
        remote_cache.reset_config_cache()


def test_remote_get_swallows_errors(monkeypatch):
    _enable_remote(monkeypatch)
    try:
        with patch("data.remote_cache.requests.get", side_effect=RuntimeError("network down")):
            assert remote_cache.get("qualitative_X_v0.13.json", 3600) is None
    finally:
        remote_cache.reset_config_cache()


def test_remote_set_posts_upsert(monkeypatch):
    _enable_remote(monkeypatch)
    resp = MagicMock(); resp.raise_for_status.return_value = None
    try:
        with patch("data.remote_cache.requests.post", return_value=resp) as mock_post:
            remote_cache.set("qualitative_X_v0.13.json", {"status": "available"})
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["Prefer"].startswith("resolution=merge-duplicates")
        assert kwargs["json"]["key"] == "qualitative_X_v0.13.json"
    finally:
        remote_cache.reset_config_cache()
