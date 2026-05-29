import os
import requests
import pdfplumber
from io import BytesIO
import sys

from data.scrapers.screener import fetch_screener_documents, HEADERS

def main():
    ticker = 'RELIANCE.NS'
    docs = fetch_screener_documents(ticker)
    annual_reports = [d for d in docs if d['type'] == 'annual_report']
    if not annual_reports:
        print("No annual reports found for", ticker)
        sys.exit(1)
        
    latest_ar = annual_reports[0]
    url = latest_ar['url']
    print(f"Fetching: {url}")
    
    resp = requests.get(url, headers=HEADERS, timeout=20)
    if resp.status_code != 200:
        print("Failed to download PDF. Status:", resp.status_code)
        sys.exit(1)
        
    print(f"Downloaded {len(resp.content)} bytes.")
    
    with pdfplumber.open(BytesIO(resp.content)) as pdf:
        num_pages = len(pdf.pages)
        print(f"Total PDF pages: {num_pages}")
        
        # Output the first 20 pages of text so we can find TOC manually
        with open('discovery_output.txt', 'w', encoding='utf-8') as f:
            for i in range(min(20, num_pages)):
                text = pdf.pages[i].extract_text() or ""
                f.write(f"\n--- PDF Page {i} ---\n")
                f.write(text)
                
        # Look for Chairman's message and Risk factors or MD&A directly
        # Just dump the first 50 pages to look at offsets.
        with open('discovery_output_full.txt', 'w', encoding='utf-8') as f:
            for i in range(min(100, num_pages)):
                text = pdf.pages[i].extract_text() or ""
                f.write(f"\n--- PDF Page {i} ---\n")
                f.write(text)

    print("Discovery output written to discovery_output.txt and discovery_output_full.txt")

if __name__ == '__main__':
    main()
