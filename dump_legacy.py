import json
import os
from unittest.mock import patch, MagicMock
from data.scrapers.screener import fetch_screener_financials

def main():
    fixture_path = os.path.join("tests", "fixtures", "screener_reliance_consolidated.html")
    with open(fixture_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = html_content

    # We mock _get_subrows to return empty since we don't have network API mocked here.
    # Actually, the user says "dump today's full Reliance fin (legacy keys only) BEFORE your change".
    # Since _get_subrows makes network calls, we can mock requests.get to return HTML for the main page,
    # but the API calls in _get_subrows will fail and fallback to defaults if we don't mock them.
    # Wait, if we mock requests.get completely, _get_subrows will hit the mock and fail to parse JSON.
    # Let's just mock the main HTML call and let _get_subrows hit the real network if possible? No, we shouldn't hit real network if we can avoid it.
    # The requirement is: "dump today's full Reliance fin (legacy keys only) BEFORE your change, and assert it is unchanged AFTER".
    
    def mock_get(url, *args, **kwargs):
        if "schedules" in url:
            # Mock schedules API
            import re
            m = re.search(r'parent=([^&]+)', url)
            parent = m.group(1).replace("+", " ") if m else ""
            resp = MagicMock()
            resp.status_code = 200
            if parent == "Material Cost":
                resp.json.return_value = {"Raw Material Cost": {"Mar 2023": 100, "Mar 2024": 110, "Mar 2025": 120, "Mar 2026": 130}}
            elif parent == "Other Assets":
                resp.json.return_value = {"Cash Equivalents": {"Mar 2023": 50, "Mar 2024": 60, "Mar 2025": 70, "Mar 2026": 80}}
            elif parent == "Cash from Investing Activity":
                resp.json.return_value = {"Fixed assets purchased": {"Mar 2023": -200, "Mar 2024": -210, "Mar 2025": -220, "Mar 2026": -230}}
            elif parent == "Cash from Operating Activity":
                resp.json.return_value = {"Working capital changes": {"Mar 2023": -10, "Mar 2024": 10, "Mar 2025": -5, "Mar 2026": 15}}
            else:
                resp.json.return_value = {}
            return resp
        else:
            return mock_resp
            
    with patch("data.scrapers.screener.requests.get", side_effect=mock_get):
        with patch("data.scrapers.screener._resolve_screener_slug", return_value="RELIANCE"):
            with patch("data.scrapers.screener.cache.get_json", return_value=None):
                with patch("data.scrapers.screener.cache.set_json"):
                    fin = fetch_screener_financials("RELIANCE.NS")
                    
    # Dump legacy keys
    with open("legacy_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(fin, f, indent=2)
    print("Dumped legacy_snapshot.json")

if __name__ == "__main__":
    main()
