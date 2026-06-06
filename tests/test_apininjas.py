import pytest
import datetime
from unittest.mock import MagicMock
from data.scrapers import apininjas

def test_recent_quarters(monkeypatch):
    class MockDate(datetime.date):
        @classmethod
        def today(cls):
            return cls(2026, 6, 6)

    monkeypatch.setattr(apininjas.datetime, "date", MockDate)
    
    expected = [(2026, 1), (2025, 4), (2025, 3), (2025, 2), (2025, 1)]
    assert apininjas._recent_quarters(5) == expected

def test_fetch_earnings_transcripts_no_key(monkeypatch):
    monkeypatch.setattr(apininjas, "_API_KEY", None)
    monkeypatch.setattr(apininjas.cache, "get_json", lambda k, ttl: None)
    monkeypatch.setattr(apininjas.cache, "set_json", lambda k, v: None)
    assert apininjas.fetch_earnings_transcripts("AAPL", n=2) == []

def test_fetch_earnings_transcripts_happy(monkeypatch):
    monkeypatch.setattr(apininjas, "_API_KEY", "dummy")
    monkeypatch.setattr(apininjas.cache, "get_json", lambda k, ttl: None)
    monkeypatch.setattr(apininjas.cache, "set_json", lambda k, v: None)
    
    class MockDate(datetime.date):
        @classmethod
        def today(cls):
            return cls(2026, 6, 6)
    monkeypatch.setattr(apininjas.datetime, "date", MockDate)

    def mock_get(url, headers, params, timeout):
        m = MagicMock()
        m.status_code = 200
        # Return long transcript
        m.json.return_value = {"transcript": "A" * 1500}
        return m
        
    monkeypatch.setattr(apininjas.requests, "get", mock_get)
    
    docs = apininjas.fetch_earnings_transcripts("AAPL", n=2)
    assert len(docs) == 2
    assert docs[0]["filename"] == "AAPL earnings call Q1 2026"
    assert len(docs[0]["text"]) == 1500
    assert docs[1]["filename"] == "AAPL earnings call Q4 2025"

def test_fetch_earnings_transcripts_empty_and_4xx(monkeypatch):
    monkeypatch.setattr(apininjas, "_API_KEY", "dummy")
    monkeypatch.setattr(apininjas.cache, "get_json", lambda k, ttl: None)
    monkeypatch.setattr(apininjas.cache, "set_json", lambda k, v: None)
    
    def mock_get(url, headers, params, timeout):
        m = MagicMock()
        if params["quarter"] == 1:
            m.status_code = 403 # gated free tier
        else:
            m.status_code = 200
            m.json.return_value = {"transcript": "short"} # too short, < 1000 chars
        return m
        
    monkeypatch.setattr(apininjas.requests, "get", mock_get)
    
    docs = apininjas.fetch_earnings_transcripts("AAPL", n=2)
    assert len(docs) == 0

def test_fetch_earnings_calendar_happy(monkeypatch):
    monkeypatch.setattr(apininjas, "_API_KEY", "dummy")
    monkeypatch.setattr(apininjas.cache, "get_json", lambda k, ttl: None)
    monkeypatch.setattr(apininjas.cache, "set_json", lambda k, v: None)
    
    class MockDate(datetime.date):
        @classmethod
        def today(cls):
            return cls(2026, 6, 6)
    monkeypatch.setattr(apininjas.datetime, "date", MockDate)
    
    def mock_get(url, headers, params, timeout):
        m = MagicMock()
        m.status_code = 200
        m.json.return_value = [
            {"pricedate": "2026-07-25", "estimated_eps": 1.2, "actual_eps": None},
            {"pricedate": "2026-04-25", "estimated_eps": 1.1, "actual_eps": 1.15},
        ]
        return m
        
    monkeypatch.setattr(apininjas.requests, "get", mock_get)
    
    docs = apininjas.fetch_earnings_calendar("AAPL")
    assert len(docs) == 1
    assert "AAPL earnings calendar" in docs[0]["filename"]
    assert "2026-07-25" in docs[0]["text"]
    assert "NEXT UPCOMING EARNINGS" in docs[0]["text"]
