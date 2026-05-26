# Sidwell — Personal Investment-Decision Engine (v0.1)

Sidwell is a Python tool that values companies and applies investor frameworks to produce investment recommendations.
Version 0.1 (v0.1) implements the core **DCF (Discounted Cash Flow)** valuation engine and **Warren Buffett's 8 investment checks** for public market equities. Version 0.2 adds a **qualitative ingestion layer** that reads PDF documents (concall transcripts, investor decks, MD&A sections) from a Drive-synced folder and runs structured Gemini extraction, integrating a coherence signal into Buffett check #8.

## Directory Structure

```
sidwell/
├── value.py                  # CLI entry point — parses ticker, dispatches
├── data/
│   ├── __init__.py
│   ├── public.py             # yfinance + FRED + Damodaran fetchers with caching
│   ├── documents.py          # PDF discovery from Drive-synced folder (v0.2)
│   ├── alternative.py        # Alternative data stub (earnings calls, news, Trendlyne)
│   ├── private.py            # YAML reader stub (phase 5)
│   └── cache.py              # ~/.sidwell/cache/ TTL-based file cache
├── analysis/                 # Qualitative analysis layer (v0.2)
│   ├── __init__.py
│   ├── qualitative.py        # Gemini-based structured extraction with 30-day cache
│   └── prompts/
│       └── qualitative_extraction.md  # Version-controlled Gemini prompt
├── valuation/
│   ├── __init__.py
│   ├── dcf.py                # DCF Valuation Engine with WACC sourcing
│   ├── comps.py              # Comparable Companies Analysis (CCA) stub
│   ├── precedent.py          # Precedent Transactions Analysis (PTA) stub
│   └── lbo.py                # LBO valuation engine stub
├── lenses/
│   ├── __init__.py
│   ├── buffett.py            # Warren Buffett's 8 checks & verdict engine
│   ├── marks.py              # Howard Marks lens stub
│   ├── kkr_blackstone.py     # Blackstone/Carlyle/KKR PE lens stub
│   └── distressed.py         # Distressed / Special Situations lens stub
├── reports/
│   ├── __init__.py
│   └── render.py             # Markdown report builder
├── frameworks/               # Investor lens reference documents
├── tests/
│   ├── test_dcf.py           # Valuation & projection unit tests (including hand calc)
│   ├── test_buffett.py       # Buffett lens scoring & verdict tests (incl. hybrid check #8)
│   ├── test_data.py          # Offline mock-based data + documents tests
│   ├── test_qualitative.py   # Qualitative module mock-based tests (v0.2)
│   ├── test_snapshot.py      # Regression snapshot test vs. hand-derived expected output
│   └── expected_calculations.md  # Formula derivations (source of truth)
├── output/                   # Generated reports (markdown format)
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
└── .env.example              # Environment variables template
```

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
- `FRED_API_KEY`: Get a free key from the [FRED API website](https://fred.stlouisfed.org/docs/api/api_key.html) to dynamically pull risk-free rates.
- `GEMINI_API_KEY`: Get a free key from [Google AI Studio](https://aistudio.google.com/apikey) for qualitative analysis (v0.2+). Optional — pipeline degrades gracefully if absent.
- `SIDWELL_DRIVE_PATH`: Path to the Drive-synced folder containing PDF documents (defaults to `~/Sidwell-Drive/`). Place PDFs for a ticker in `<SIDWELL_DRIVE_PATH>/<TICKER>/`.

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

All 24 tests must be green.
