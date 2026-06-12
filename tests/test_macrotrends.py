"""
Offline tests for data/scrapers/macrotrends.py.

All network calls are mocked; fixtures are the real HTML pages saved from MacroTrends
for XOM (Income, Balance Sheet, Cash Flow). The test suite must run green in <15s.
"""
import os
import pytest
from unittest.mock import patch, MagicMock

from data.scrapers.macrotrends import fetch_macrotrends_financials
from data.public import fetch_financials

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(autouse=True, scope="module")
def _isolate_cache():
    """
    Redirect the on-disk cache to a temp dir for this module so a stale/real entry
    can't bypass the mocks. Module scope lets the single XOM fetch be reused by the
    later tests (cache hit) instead of re-parsing every time, keeping the suite fast.
    """
    import data.cache as cache
    import tempfile, shutil
    orig = cache.CACHE_DIR
    tmp = tempfile.mkdtemp(prefix="sidwell_test_cache_")
    cache.CACHE_DIR = tmp
    yield
    cache.CACHE_DIR = orig
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(autouse=True)
def _no_live_calls(monkeypatch):
    """
    Pin the price / SIC / yfinance boundaries so the fetch makes ZERO live calls.
    yfinance (yf.Ticker().info) reaches Yahoo directly and is not covered by the
    requests.get mock; without this it was a real, rate-limited network call.
    """
    monkeypatch.setattr("data.scrapers.macrotrends._us_price", lambda t: 103.50)
    monkeypatch.setattr(
        "data.scrapers.macrotrends._get_sic_from_sec",
        lambda t: (2911, "Petroleum Refining"),
    )
    # macrotrends lazily imports fetch_stockanalysis_beta and hits the live stats
    # page; patch the source symbol so it resolves to a stub at call time.
    monkeypatch.setattr("data.scrapers.stockanalysis.fetch_stockanalysis_beta", lambda t: 1.2)
    import yfinance
    monkeypatch.setattr(yfinance, "Ticker", lambda *a, **k: MagicMock(info={}))


@pytest.fixture
def mock_requests():
    """
    Intercepts requests.get calls inside macrotrends.py and the SEC SIC helpers.
    MacroTrends HTML pages are served from local fixtures.
    SEC company_tickers.json and submissions endpoints return minimal stubs so
    the test makes ZERO live network calls.
    """
    def _mock_get(url, *args, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status = MagicMock()

        # MacroTrends pages
        if "income-statement" in url:
            with open(os.path.join(FIXTURE_DIR, "macrotrends_xom_income.html"), "r", encoding="utf-8") as f:
                resp.text = f.read()
            resp.json = MagicMock(side_effect=ValueError("not json"))
        elif "balance-sheet" in url:
            with open(os.path.join(FIXTURE_DIR, "macrotrends_xom_balance.html"), "r", encoding="utf-8") as f:
                resp.text = f.read()
            resp.json = MagicMock(side_effect=ValueError("not json"))
        elif "cash-flow-statement" in url:
            with open(os.path.join(FIXTURE_DIR, "macrotrends_xom_cashflow.html"), "r", encoding="utf-8") as f:
                resp.text = f.read()
            resp.json = MagicMock(side_effect=ValueError("not json"))
        # SEC company_tickers.json
        elif "company_tickers.json" in url:
            resp.text = ""
            resp.json = MagicMock(return_value={
                "0": {"cik_str": 34088, "ticker": "XOM", "title": "EXXON MOBIL CORP"}
            })
        # SEC submissions (CIK lookup for SIC)
        elif "submissions/CIK" in url:
            resp.text = ""
            resp.json = MagicMock(return_value={
                "sic": "2911",
                "sicDescription": "Petroleum Refining",
            })
        # stooq price (called by _us_price)
        elif "stooq.com" in url:
            resp.text = "Symbol,Date,Time,Open,High,Low,Close,Volume\nXOM,2025-06-01,16:00:00,100.0,105.0,99.0,103.50,5000000"
            resp.json = MagicMock(side_effect=ValueError("not json"))
        else:
            resp.text = ""
            resp.json = MagicMock(return_value={})

        return resp

    with patch("data.scrapers.macrotrends.requests.Session", return_value=type("MockSession", (), {"headers": {}, "get": lambda self, url, **kwargs: _mock_get(url, **kwargs)})()) as mock:
        yield mock


def test_macrotrends_parser(mock_requests):
    """Core parser: shape, scale, and key values from XOM fixtures."""
    with patch("data.scrapers.stockanalysis.fetch_stockanalysis_financials", return_value=None):
        fin = fetch_macrotrends_financials("XOM")

    assert fin is not None, "fetch_macrotrends_financials returned None"
    assert fin["source"] == "macrotrends"
    assert fin["ticker"] == "XOM"

    # years_annual must be ascending, >= 10 years (fixtures have 2011-2025)
    years = fin["statements"]["years_annual"]
    assert len(years) >= 10, f"Expected >= 10 years, got {len(years)}: {years}"
    assert years == sorted(years), "years_annual must be ascending"

    pl = fin["statements"]["annual"]["profit_loss"]

    # Revenue 2025: 332238 USD MM -> scaled = 332238 / 10 = 33223.8
    assert pl["sales"] is not None
    assert len(pl["sales"]) == len(years)
    expected_rev_scaled = 332238.0 / 10.0
    assert abs(pl["sales"][-1] - expected_rev_scaled) < 1.0, (
        f"sales[-1] = {pl['sales'][-1]}, expected ~{expected_rev_scaled}"
    )

    # COGS 2025: 251839 -> 25183.9
    expected_cogs_scaled = 251839.0 / 10.0
    assert abs(pl["cogs"][-1] - expected_cogs_scaled) < 1.0, (
        f"cogs[-1] = {pl['cogs'][-1]}, expected ~{expected_cogs_scaled}"
    )

    # Ratios block
    ratios = fin["statements"]["ratios"]
    assert "working capital days" in ratios
    assert len(ratios["working capital days"]) == len(years)
    # At least the last year should compute (balance sheet has TCA and TCL)
    non_none = [v for v in ratios["working capital days"] if v is not None]
    assert len(non_none) > 0, "working capital days is all None"

    # debtor days and inventory days present
    assert "debtor days" in ratios
    assert "inventory days" in ratios

    # Top-level arrays must be 4-element
    for key in ("revenue", "gross_profit", "ebit", "net_income", "total_assets",
                "total_equity", "cash", "debt", "capex", "depreciation", "fcf"):
        assert key in fin, f"Missing top-level key: {key}"
        assert len(fin[key]) == 4, f"{key} should be 4-element, got {len(fin[key])}"

    # Top-level scale: revenue 2025 = 332238 * 1e6 = 3.32238e11
    assert abs(fin["revenue"][-1] - 332238.0 * 1e6) < 1e6, (
        f"revenue[-1] = {fin['revenue'][-1]}, expected ~{332238.0 * 1e6}"
    )

    # Sector / industry via SEC SIC (mocked SIC 2911 -> Energy / Oil & Gas)
    assert fin["scraped_sector"] is not None
    assert fin["scraped_industry"] is not None
    assert fin["is_bank"] is False

    # price was mocked via stooq
    assert fin["current_price"] == pytest.approx(103.50, abs=0.01)

    # shares outstanding (2025: 4305 MM * 1e6)
    assert fin["shares_outstanding"] == pytest.approx(4305.0 * 1e6, rel=0.01)

    # None->0.0 normalization applied
    for key in ("revenue", "net_income", "capex"):
        assert all(v is not None for v in fin[key]), f"None found in {key} after normalization"


def test_fetch_financials_uses_macrotrends_primary(mock_requests):
    """fetch_financials should prefer macrotrends when it succeeds."""
    fin = fetch_financials("XOM")
    assert fin is not None
    assert fin["source"] == "macrotrends"


def test_fetch_financials_falls_back_to_edgar():
    """If macrotrends and stockanalysis return None, fetch_financials falls back to EDGAR."""
    with patch("data.scrapers.macrotrends.fetch_macrotrends_financials", return_value=None):
        with patch("data.scrapers.stockanalysis.fetch_stockanalysis_financials", return_value=None):
            with patch("data.scrapers.edgar.fetch_edgar_companyfacts_financials",
                       return_value={"source": "sec_edgar", "statements": {"years_annual": ["2024"], "annual": {"profit_loss": {}, "balance_sheet": {}, "cash_flow": {}}}}) as mock_edgar:
                fin = fetch_financials("XOM")
                assert fin["source"] == "sec_edgar"
                mock_edgar.assert_called_once_with("XOM")


def test_fetch_financials_falls_back_to_stockanalysis():
    """If macrotrends and EDGAR return None, fetch_financials falls back to stockanalysis."""
    with patch("data.scrapers.macrotrends.fetch_macrotrends_financials", return_value=None):
        with patch("data.scrapers.edgar.fetch_edgar_companyfacts_financials", return_value=None):
            with patch("data.scrapers.stockanalysis.fetch_stockanalysis_financials",
                       return_value={"source": "stockanalysis", "statements": {"years_annual": ["2024"]}}) as mock_sa:
                fin = fetch_financials("XOM")
                assert fin["source"] == "stockanalysis"
                mock_sa.assert_called_once_with("XOM")

def test_fetch_financials_falls_back_to_merged():
    """If macrotrends is None, and both SA and EDGAR succeed, it merges."""
    with patch("data.scrapers.macrotrends.fetch_macrotrends_financials", return_value=None):
        with patch("data.scrapers.stockanalysis.fetch_stockanalysis_financials", return_value={
            "source": "stockanalysis",
            "statements": {
                "years_annual": ["2023", "2024"],
                "annual": {"profit_loss": {"sales": [100, 110]}, "balance_sheet": {}, "cash_flow": {}},
                "quarters": ["Q1", "Q2"],
                "shareholding": {}
            }
        }):
            with patch("data.scrapers.edgar.fetch_edgar_companyfacts_financials", return_value={
                "source": "sec_edgar",
                "statements": {
                    "years_annual": ["2022", "2023"],
                    "annual": {"profit_loss": {"sales": [90, 95]}, "balance_sheet": {}, "cash_flow": {}}
                }
            }):
                fin = fetch_financials("XOM")
                assert fin["source"] == "stockanalysis+edgar"
                assert fin["statements"]["years_annual"] == ["2022", "2023", "2024"]
                # SA is preferred, so 2023 sales should be 100, not 95
                assert fin["statements"]["annual"]["profit_loss"]["sales"] == [90, 100, 110]
                assert "quarters" in fin["statements"]
                assert "shareholding" in fin["statements"]


def test_engine_smoke(mock_requests):
    """End-to-end: macrotrends data -> DCF engine -> positive intrinsic value."""
    from sidwell.engine.core import run_engine
    from sidwell.ajp.schema import AJP

    fin = fetch_macrotrends_financials("XOM")
    ajp = AJP.from_dict({})

    with patch("data.public.fetch_risk_free_rate", return_value=0.04):
        with patch("data.public.fetch_damodaran_data", return_value={
            "mature_market_erp": 0.045,
            "country_risk_premium": 0.0,
            "total_erp": 0.045,
            "industry_levered_beta": 1.1,
            "industry_unlevered_beta": 1.0,
            "industry_de_ratio": 0.2,
        }):
            with patch("data.public.fetch_damodaran_industry_fundamentals",
                       return_value={"available": False}):
                res = run_engine(fin, ajp)
                assert res.get("intrinsic_value_per_share", 0) > 0, (
                    f"Expected positive intrinsic value, got: {res.get('intrinsic_value_per_share')}"
                )
