# Sidwell — Personal Investment-Decision Engine (v0.1)

Sidwell is a Python tool that values companies and applies investor frameworks to produce investment recommendations.
Version 0.1 (v0.1) implements the core **DCF (Discounted Cash Flow)** valuation engine and **Warren Buffett's 8 investment checks** for public market equities.

## Directory Structure

```
sidwell/
├── value.py                  # CLI entry point — parses ticker, dispatches
├── data/
│   ├── __init__.py
│   ├── public.py             # yfinance + FRED + Damodaran fetchers with caching
│   ├── alternative.py        # Alternative data stub (earnings calls, news, Trendlyne)
│   ├── private.py            # YAML reader stub (phase 5)
│   └── cache.py              # ~/.sidwell/cache/ TTL-based file cache
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
│   ├── test_buffett.py       # Buffett lens scoring & verdict tests
│   └── test_data.py          # Offline mock-based data tests
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

*Note: If no `.env` file or `FRED_API_KEY` is present, the pipeline will still run if the data is already cached. For `ASIANPAINT.NS`, a pre-populated cache is included.*

## Running the Pipeline

To analyze a public stock ticker (both US and Indian `.NS`/`.BO` markets are supported):
```bash
python value.py ASIANPAINT.NS
```

This will run the DCF valuation and the Buffett lens, print a brief summary to the console, and write the full markdown report to `output/{ticker}_report.md` (e.g. `output/asianpaint_report.md`).

## Verification & Testing

To run the unit tests (which execute completely offline using unittest mocks):
```bash
python -m pytest tests/
```

All 11 tests must be green.
