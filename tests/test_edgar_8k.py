import pytest
from unittest.mock import MagicMock
from data.scrapers import edgar

def test_fetch_edgar_8k_shareholder_letters(monkeypatch):
    monkeypatch.setattr(edgar.cache, "get_json", lambda k, ttl: None)
    monkeypatch.setattr(edgar.cache, "set_json", lambda k, v: None)
    monkeypatch.setattr(edgar, "_EDGAR_IDENTITY", "dummy")
    
    class MockAttachment:
        def __init__(self, doc_type, text_content):
            self.document_type = doc_type
            self.description = doc_type
            self._text = text_content
            
        def text(self):
            return self._text
            
    class MockFiling:
        def __init__(self, date, attachments, has_pr=False):
            self.filing_date = date
            self.attachments = attachments
            self._has_pr = has_pr
            
        def obj(self):
            m = MagicMock()
            if self._has_pr:
                pr_mock = MagicMock()
                pr_mock.text.return_value = "PR" * 1500
                m.press_releases = pr_mock
            else:
                m.press_releases = None
            return m

    class MockCompany:
        def __init__(self, ticker):
            pass
            
        def get_filings(self, form):
            # filing 1: press release fallback
            f1 = MockFiling("2026-05-01", [], has_pr=True)
            
            # filing 2: attachment EX-99.1
            f2 = MockFiling("2026-02-01", [MockAttachment("EX-99.1", "EX" * 1500)])
            
            # filing 3: missing ex-99.1
            f3 = MockFiling("2025-11-01", [MockAttachment("EX-10", "10" * 1500)])
            
            # filing 4: short text
            f4 = MockFiling("2025-08-01", [MockAttachment("EX-99.1", "short")])
            
            return [f1, f2, f3, f4]

    monkeypatch.setattr(edgar, "Company", MockCompany)
    monkeypatch.setattr(edgar, "set_identity", lambda x: None)

    docs = edgar.fetch_edgar_8k_shareholder_letters("AAPL", n=2)
    assert len(docs) == 2
    assert "2026-05-01" in docs[0]["filename"]
    assert "PR" in docs[0]["text"]
    assert "2026-02-01" in docs[1]["filename"]
    assert "EX" in docs[1]["text"]

def test_fetch_edgar_8k_empty(monkeypatch):
    monkeypatch.setattr(edgar.cache, "get_json", lambda k, ttl: None)
    monkeypatch.setattr(edgar.cache, "set_json", lambda k, v: None)
    monkeypatch.setattr(edgar, "_EDGAR_IDENTITY", "dummy")
    
    class MockCompany:
        def __init__(self, ticker):
            pass
            
        def get_filings(self, form):
            return []

    monkeypatch.setattr(edgar, "Company", MockCompany)
    monkeypatch.setattr(edgar, "set_identity", lambda x: None)

    docs = edgar.fetch_edgar_8k_shareholder_letters("AAPL", n=2)
    assert len(docs) == 0

def test_fetch_edgar_8k_exception(monkeypatch):
    monkeypatch.setattr(edgar.cache, "get_json", lambda k, ttl: None)
    monkeypatch.setattr(edgar.cache, "set_json", lambda k, v: None)
    monkeypatch.setattr(edgar, "_EDGAR_IDENTITY", "dummy")
    
    class MockCompany:
        def __init__(self, ticker):
            raise ValueError("Oh no")

    monkeypatch.setattr(edgar, "Company", MockCompany)
    monkeypatch.setattr(edgar, "set_identity", lambda x: None)

    docs = edgar.fetch_edgar_8k_shareholder_letters("AAPL", n=2)
    assert len(docs) == 0
