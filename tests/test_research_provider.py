import os
from data.research_provider import get_research_for_ticker
import data.research_provider as rp

def test_get_research_for_ticker_valid(tmp_path, monkeypatch):
    """If the ticker directory exists with PDFs, it returns the newest ones up to max_reports."""
    monkeypatch.setattr(rp, "RESEARCH_LIB_DIR", str(tmp_path))
    
    ticker_dir = tmp_path / "ABC.NS"
    ticker_dir.mkdir()
    
    p1 = ticker_dir / "r1.pdf"
    p2 = ticker_dir / "r2.pdf"
    p3 = ticker_dir / "r3.pdf"
    
    p1.write_bytes(b"content1")
    p2.write_bytes(b"content2")
    p3.write_bytes(b"content3")
    
    # Touch files so p3 is newest, then p2, then p1
    import time
    os.utime(str(p1), (time.time(), time.time() - 10))
    os.utime(str(p2), (time.time(), time.time() - 5))
    os.utime(str(p3), (time.time(), time.time()))

    res = get_research_for_ticker("ABC.NS", max_reports=2)
    assert len(res) == 2
    assert res[0]["filename"] == "r3.pdf"
    assert res[0]["bytes"] == b"content3"
    assert res[1]["filename"] == "r2.pdf"
    assert res[1]["bytes"] == b"content2"


def test_get_research_for_ticker_missing_dir(tmp_path, monkeypatch):
    """If the directory is missing, it returns an empty list without error."""
    monkeypatch.setattr(rp, "RESEARCH_LIB_DIR", str(tmp_path))
    res = get_research_for_ticker("MISSING")
    assert res == []


def test_get_research_for_ticker_invalid_ticker(tmp_path, monkeypatch):
    """Empty or garbage ticker strings should fail gracefully and return []"""
    monkeypatch.setattr(rp, "RESEARCH_LIB_DIR", str(tmp_path))
    assert get_research_for_ticker("") == []
    assert get_research_for_ticker(None) == []
