from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
import pytest

from data.scrapers.screener import fetch_screener_documents
from data import cache

MOCK_HTML_WITH_DOCS = """
<html>
<body>
    <section id="documents">
        <div class="annual-reports">
            <h3>Annual reports</h3>
            <ul>
                <li><a href="https://bseindia.com/ar2025.pdf">Financial Year 2025</a></li>
                <li><a href="https://bseindia.com/ar2024.pdf">Financial Year 2024</a></li>
                <li><a href="https://bseindia.com/ar2023.pdf">Financial Year 2023</a></li>
            </ul>
        </div>
        <div class="concalls">
            <h3>Concalls</h3>
            <ul>
                <li><div>Apr 2025</div><a class="concall-link" href="https://bseindia.com/q4.pdf">Transcript</a></li>
                <li><div>Jan 2025</div><a class="concall-link" href="https://bseindia.com/q3.pdf">Transcript</a></li>
                <li><div>Oct 2024</div><a class="concall-link" href="https://bseindia.com/q2.pdf">Transcript</a></li>
            </ul>
        </div>
        <div class="credit-ratings">
            <h3>Credit ratings</h3>
            <ul>
                <li><a href="https://crisil.com/r1.pdf">30 Mar from crisil</a></li>
                <li><a href="https://icra.in/r2.pdf">15 Jan from icra</a></li>
            </ul>
        </div>
    </section>
</body>
</html>
"""

MOCK_HTML_NO_DOCS = "<html><body></body></html>"

@pytest.fixture(autouse=True)
def mock_cache(monkeypatch):
    cache_store = {}
    def fake_get(key, ttl):
        return cache_store.get(key)
    def fake_set(key, val):
        cache_store[key] = val
    monkeypatch.setattr(cache, "get_json", fake_get)
    monkeypatch.setattr(cache, "set_json", fake_set)

@patch('data.scrapers.screener._resolve_screener_slug')
@patch('requests.get')
def test_discover_documents_returns_url_list(mock_get, mock_resolve):
    mock_resolve.return_value = 'MOCKTICKER'
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = MOCK_HTML_WITH_DOCS
    mock_get.return_value = mock_resp

    docs = fetch_screener_documents('MOCKTICKER')
    
    assert len(docs) == 4
    assert docs[0]['url'] == 'https://bseindia.com/ar2025.pdf'
    assert docs[0]['type'] == 'annual_report'
    
    assert docs[1]['url'] == 'https://bseindia.com/q4.pdf'
    assert docs[1]['type'] == 'concall_transcript'
    assert docs[1]['date'] == 'Apr 2025'
    
    assert docs[2]['url'] == 'https://bseindia.com/q3.pdf'
    assert docs[3]['url'] == 'https://crisil.com/r1.pdf'
    assert docs[3]['type'] == 'credit_rating'

@patch('data.scrapers.screener._resolve_screener_slug')
@patch('requests.get')
def test_discover_documents_caches_urls(mock_get, mock_resolve):
    mock_resolve.return_value = 'MOCKTICKER'
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = MOCK_HTML_WITH_DOCS
    mock_get.return_value = mock_resp

    # First call
    docs1 = fetch_screener_documents('MOCKTICKER')
    assert len(docs1) == 4
    assert mock_get.call_count == 1
    
    # Second call
    docs2 = fetch_screener_documents('MOCKTICKER')
    assert len(docs2) == 4
    assert mock_get.call_count == 1  # Should not increase

@patch('data.scrapers.screener._resolve_screener_slug')
@patch('requests.get')
def test_discover_documents_handles_missing_documents_section(mock_get, mock_resolve):
    mock_resolve.return_value = 'MOCKTICKER'
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = MOCK_HTML_NO_DOCS
    mock_get.return_value = mock_resp

    docs = fetch_screener_documents('MOCKTICKER')
    assert docs == []

@patch('data.scrapers.screener._resolve_screener_slug')
@patch('requests.get')
def test_document_selection_policy(mock_get, mock_resolve):
    mock_resolve.return_value = 'MOCKTICKER'
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = MOCK_HTML_WITH_DOCS
    mock_get.return_value = mock_resp

    docs = fetch_screener_documents('MOCKTICKER')
    # Policy: 1 annual, 2 concalls, 1 rating = 4 total
    assert len(docs) == 4
    types = [d['type'] for d in docs]
    assert types.count('annual_report') == 1
    assert types.count('concall_transcript') == 2
    assert types.count('credit_rating') == 1
