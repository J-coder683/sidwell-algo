# Sidwell — Personal Investment-Decision Engine (v0.6)

Sidwell is a Python tool that values companies and applies investor frameworks to produce investment recommendations.
Version 0.6 adds a **Streamlit web frontend**, **per-lens PDF export** (weasyprint), and a **7-sheet DCF Excel workbook** with live formulas, on top of the v0.5 engine (DCF 2-stage + fade, 5 investor lenses: Buffett/Marks/KKR/Blackstone/Apollo, Gemini qualitative layer).

## Directory Structure

```
├── app.py                    # Streamlit frontend (v0.6)
├── value.py                  # CLI entry point — also exports analyze()
├── data/
│   ├── __init__.py
│   ├── public.py             # screener.in / stockanalysis.com + FRED + Damodaran fetchers with caching
│   ├── documents.py          # PDF discovery from Drive-synced folder (v0.2)
│   └── cache.py              # ~/.sidwell/cache/ TTL-based file cache
├── analysis/                 # Qualitative + framework parsing (v0.2+)
│   ├── __init__.py
│   ├── qualitative.py        # Gemini-based structured extraction with 30-day cache
│   ├── framework_parser.py   # Logic paragraph extractor for all 5 frameworks (v0.6)
│   └── prompts/
│       └── qualitative_extraction.md
├── valuation/
│   ├── __init__.py
│   └── dcf.py                # 2-stage DCF with fade + sector terminal growth
├── lenses/
│   ├── __init__.py
│   ├── buffett.py            # Warren Buffett's 14 checks
│   ├── marks.py              # Howard Marks's 14 checks
│   ├── kkr.py                # KKR's 18 checks
│   ├── blackstone.py         # Blackstone's 14 checks
│   └── apollo.py             # Apollo's 16 checks
├── exports/                  # Export functions (v0.6)
│   ├── __init__.py
│   ├── excel.py              # 7-sheet DCF workbook with live formulas
│   ├── pdf.py                # Per-lens PDF export via weasyprint
│   └── pdf_style.css         # A4 PDF stylesheet
├── reports/
│   ├── __init__.py
│   └── render.py             # Markdown report builder
├── frameworks/               # Investor lens reference documents (.md)
├── tests/
│   ├── fixture_company.py    # Shared test fixtures
│   ├── test_dcf.py
│   ├── test_buffett.py
│   ├── test_marks.py
│   ├── test_kkr.py
│   ├── test_blackstone.py
│   ├── test_apollo.py
│   ├── test_framework_parser.py   # 21 tests (v0.6)
│   ├── test_framework_reasoning_integration.py  # 10 tests (v0.6)
│   ├── test_exports.py            # 29 pass + 4 skip on Windows (v0.6)
│   ├── test_data.py
│   ├── test_qualitative.py
│   ├── test_snapshot.py
│   └── expected_report.md         # Hand-derived snapshot
├── .streamlit/
│   ├── config.toml                # Theme + server config (v0.6)
│   └── secrets.toml.example       # API key template (v0.6)
├── packages.txt              # Streamlit Cloud system packages (v0.6)
├── output/                   # Generated markdown reports
├── requirements.txt
└── README.md
```

## Streamlit App (v0.6)

Run the web frontend locally:
```bash
streamlit run app.py
```

Deploy to [Streamlit Community Cloud](https://share.streamlit.io):
1. Push this repo to GitHub.
2. Connect at share.streamlit.io → select `app.py` as entrypoint.
3. Configure secrets (`GEMINI_API_KEY`, `FRED_API_KEY`) in app settings.

The app shows 6 tabs: DCF Valuation, Buffett, Marks, KKR, Blackstone, Apollo.
Each lens tab shows check expanders (with framework reasoning for failed checks),
and export buttons for PDF (Linux/Cloud only) and Excel.

## Installation

Ensure you have Python 3.11+ installed.

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
2. Activate the virtual environment:
   - On Windows (PowerShell):
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - On Linux/macOS:
     ```bash
     source .venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Copy `.env.example` to `.env` and fill in your details:
```bash
cp .env.example .env
```
- `FRED_API_KEY`: **Required.** Get a free key from [Federal Reserve Economic Data](https://fred.stlouisfed.org/docs/api/api_key.html). Used for retrieving the US 10-year treasury yield (risk-free rate).
- `GEMINI_API_KEY`: Get a free key from [Google AI Studio](https://aistudio.google.com/apikey) for qualitative analysis (v0.2+). Optional — pipeline degrades gracefully if absent.
Qualitative analysis automatically fetches public documents from screener.in for Indian tickers; US ticker qualitative coverage via SEC EDGAR planned for v0.8.

*Note: If no `.env` file or `FRED_API_KEY` is present, the pipeline will still run if the data is already cached.*

## Running the Pipeline

To analyze a public stock ticker (both US and Indian `.NS`/`.BO` markets are supported):
```bash
python value.py ASIANPAINT.NS
```

This will run the DCF valuation, Buffett lens (with hybrid check #8 if PDFs are available), and qualitative analysis, print a brief summary to the console, and write the full markdown report to `output/{ticker}_report.md` (e.g. `output/asianpaint_report.md`).

## Verification & Testing

To run the unit tests (all offline using unittest mocks — no live API calls):
```bash
python -m pytest tests/
```

All 167 tests must be green (4 PDF tests skip on Windows — they pass on Streamlit Cloud Linux).
