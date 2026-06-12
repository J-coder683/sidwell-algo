"""
Offline tests for Phase 3 - unified extend_series_via_ratio gap-filler
inside data/scrapers/macrotrends.py.

All network calls are mocked.  Zero live calls.  Must run green in < 15s.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(autouse=True, scope="module")
def _isolate_cache():
    """
    Redirect the on-disk cache to a fresh temp dir for this whole module.
    Without isolation, fetch_macrotrends_financials() hits the real
    ~/.sidwell/cache BEFORE the mocked network, so a stale/real entry would
    silently bypass the fixtures (non-deterministic). Module scope (not
    per-test) lets a single XOM fetch be reused by the read-only inspection
    tests, keeping the suite < 15s; the graceful-failure test uses a distinct
    ticker so it still cold-fetches.
    """
    import data.cache as cache
    import tempfile
    import shutil

    orig = cache.CACHE_DIR
    tmp = tempfile.mkdtemp(prefix="sidwell_test_cache_")
    cache.CACHE_DIR = tmp
    yield
    cache.CACHE_DIR = orig
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(autouse=True)
def _no_live_calls(monkeypatch):
    """
    Neutralize the price / SIC / yfinance boundaries so the fetch makes ZERO
    live network calls. Pinning these also keeps timing stable.
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


# ---------------------------------------------------------------------------
# Unit tests for extend_series_via_ratio (pure helper)
# ---------------------------------------------------------------------------

from data.scrapers.macrotrends import extend_series_via_ratio


def test_extend_ratio_backfill_clean():
    """
    (a) Clean backfill: 3 native years, 5-year driver.
    Older years are driver * r_bar; native years are preserved exactly.
    """
    native = {2021: 300.0, 2022: 330.0, 2023: 360.0}  # AR
    driver = {                                           # Revenue (15y)
        2019: 800.0, 2020: 850.0,
        2021: 1000.0, 2022: 1100.0, 2023: 1200.0,
    }
    years = [2019, 2020, 2021, 2022, 2023]

    result, meta = extend_series_via_ratio(native, driver, years, ratio_bounds=(0.0, 1.0))

    # Overlap: 2021-2023.  r(t): 0.30, 0.30, 0.30 -> r_bar = 0.30
    assert meta["n_overlap"] == 3
    assert abs(meta["ratio"] - 0.30) < 1e-9

    # Native years preserved exactly
    assert result[2] == 300.0   # 2021
    assert result[3] == 330.0   # 2022
    assert result[4] == 360.0   # 2023

    # Backfilled years: driver * 0.30
    assert abs(result[0] - 800.0 * 0.30) < 1e-6   # 2019
    assert abs(result[1] - 850.0 * 0.30) < 1e-6   # 2020

    assert sorted(meta["backfilled_years"]) == [2019, 2020]
    assert sorted(meta["native_years"]) == [2021, 2022, 2023]


def test_extend_ratio_native_preserved():
    """
    (b) Native values are passed through unchanged even when driver differs.
    """
    native = {2022: 500.0, 2023: 600.0}
    driver = {2021: 1000.0, 2022: 1100.0, 2023: 1200.0}
    years = [2021, 2022, 2023]

    result, meta = extend_series_via_ratio(native, driver, years)

    assert result[1] == 500.0   # 2022 native exactly preserved
    assert result[2] == 600.0   # 2023 native exactly preserved


def test_extend_ratio_clamp_applied():
    """
    (c) ratio_bounds clamp: if the raw r_bar exceeds the ceiling, it is clamped.
    Overlap ratio is 5.0 (say Total/LT=5); bounds=(1.0, 4.0) -> clamped to 4.0.
    """
    native = {2022: 5000.0}   # total debt
    driver = {2021: 900.0, 2022: 1000.0}  # LT debt
    years = [2021, 2022]

    result, meta = extend_series_via_ratio(native, driver, years, ratio_bounds=(1.0, 4.0))

    # r_bar clamped at 4.0
    assert meta["ratio"] == 4.0
    # 2021 backfilled at 900 * 4.0 = 3600
    assert abs(result[0] - 3600.0) < 1e-6
    # 2022 native preserved
    assert result[1] == 5000.0


def test_extend_ratio_empty_overlap_passthrough():
    """
    (d) Empty overlap (driver absent for all native years) -> native passed
    through, no backfill, caveat set.
    """
    native = {2022: 100.0, 2023: 110.0}
    driver = {2019: 800.0, 2020: 850.0}   # no overlap with native
    years = [2019, 2020, 2021, 2022, 2023]

    result, meta = extend_series_via_ratio(native, driver, years)

    assert meta["n_overlap"] == 0
    assert meta["ratio"] is None
    assert meta["backfilled_years"] == []
    # Native years are present; older years that have no driver and no native are None
    assert result[3] == 100.0   # 2022
    assert result[4] == 110.0   # 2023
    assert result[0] is None    # 2019 - no native, but no overlap so no backfill
    assert "caveat" in meta and meta["caveat"]


# ---------------------------------------------------------------------------
# Integration test: XOM fixtures - both MT and SA mocked, zero live calls
# ---------------------------------------------------------------------------

def _make_mock_requests(
    sa_income_html="", sa_balance_html="", sa_cashflow_html="",
    sa_ratios_html="", sa_overview_html="",
    mt_income_html="", mt_balance_html="", mt_cashflow_html="",
):
    """Route requests.get by URL substring to the appropriate fixture."""
    def mock_get(url, *args, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status = MagicMock()

        if "macrotrends" in url:
            if "income-statement" in url:
                resp.text = mt_income_html
            elif "balance-sheet" in url:
                resp.text = mt_balance_html
            elif "cash-flow-statement" in url:
                resp.text = mt_cashflow_html
            else:
                resp.text = ""
            resp.json = MagicMock(side_effect=ValueError("not json"))

        elif "stockanalysis.com" in url:
            if "cash-flow-statement" in url:
                resp.text = sa_cashflow_html
            elif "balance-sheet" in url:
                resp.text = sa_balance_html
            elif "ratios" in url:
                resp.text = sa_ratios_html
            elif "/financials/" in url:
                resp.text = sa_income_html
            else:
                resp.text = sa_overview_html or sa_income_html
            resp.json = MagicMock(side_effect=ValueError("not json"))

        elif "company_tickers.json" in url:
            resp.text = ""
            resp.json = MagicMock(return_value={
                "0": {"cik_str": 34088, "ticker": "XOM", "title": "EXXON MOBIL CORP"}
            })
        elif "submissions/CIK" in url:
            resp.text = ""
            resp.json = MagicMock(return_value={
                "sic": "2911", "sicDescription": "Petroleum Refining",
            })
        elif "stooq.com" in url:
            resp.text = (
                "Symbol,Date,Time,Open,High,Low,Close,Volume\n"
                "XOM,2025-06-01,16:00:00,100.0,105.0,99.0,103.50,5000000"
            )
            resp.json = MagicMock(side_effect=ValueError("not json"))
        else:
            resp.text = ""
            resp.json = MagicMock(return_value={})

        return resp

    return mock_get


def _load(fname):
    path = os.path.join(FIXTURE_DIR, fname)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def xom_fixtures():
    return {
        "mt_income":   _load("macrotrends_xom_income.html"),
        "mt_balance":  _load("macrotrends_xom_balance.html"),
        "mt_cashflow": _load("macrotrends_xom_cashflow.html"),
        "sa_income":   _load("stockanalysis_xom_income.html"),
        "sa_balance":  _load("stockanalysis_xom_balance.html"),
        "sa_cashflow": _load("stockanalysis_xom_cashflow.html"),
        "sa_ratios":   _load("stockanalysis_xom_ratios.html"),
    }


def test_integration_phase3_xom(xom_fixtures):
    """
    Integration: XOM fixtures -> Phase-3 merge runs -> all 4 gap items filled,
    full 15y series with backfill for pre-SA years.
    """
    from data.scrapers.macrotrends import fetch_macrotrends_financials

    mock_fn = _make_mock_requests(
        mt_income_html=xom_fixtures["mt_income"],
        mt_balance_html=xom_fixtures["mt_balance"],
        mt_cashflow_html=xom_fixtures["mt_cashflow"],
        sa_income_html=xom_fixtures["sa_income"],
        sa_balance_html=xom_fixtures["sa_balance"],
        sa_cashflow_html=xom_fixtures["sa_cashflow"],
        sa_ratios_html=xom_fixtures["sa_ratios"],
        sa_overview_html=xom_fixtures["sa_income"],
    )

    with patch("data.scrapers.macrotrends.requests.Session", return_value=type("MockSession", (), {"headers": {}, "get": lambda self, url, **kwargs: mock_fn(url, **kwargs)})()), \
         patch("data.scrapers.stockanalysis.requests.get", side_effect=mock_fn):
        fin = fetch_macrotrends_financials("XOM")

    assert fin is not None
    assert fin["source"] == "macrotrends"

    years = fin["statements"]["years_annual"]
    n = len(years)
    pl  = fin["statements"]["annual"]["profit_loss"]
    bs  = fin["statements"]["annual"]["balance_sheet"]
    ratios = fin["statements"]["ratios"]
    meta = fin.get("reconstruction_meta", {})

    # ----------------------------------------------------------------
    # 1. pl["interest"] is now a full 15y series (was absent in Phase 1)
    # ----------------------------------------------------------------
    interest_row = pl.get("interest", [])
    assert len(interest_row) == n, (
        f"pl['interest'] length {len(interest_row)} != years_annual {n}"
    )
    non_none_int = [v for v in interest_row if v is not None]
    assert len(non_none_int) > 0, "pl['interest'] is all None after enrichment"

    # Top-level interest_expense should be non-zero (refreshed)
    ie_top = fin.get("interest_expense", [])
    assert any(v and v != 0.0 for v in ie_top), (
        f"fin['interest_expense'] still zero: {ie_top}"
    )

    # ----------------------------------------------------------------
    # 2. bs["borrowings"] is COMPLETED to total debt (LT + current), not LT-only.
    #    XOM FY2024: SA Total Debt = 41,710 vs MT Long-Term Debt = 36,755.
    #    Statement scale is /10, so the completed 2024 value must == 4171.0,
    #    strictly above the LT-only 3675.5. This is the assertion that catches a
    #    silently-skipped current-debt completion.
    # ----------------------------------------------------------------
    borrow_row = bs.get("borrowings", [])
    assert len(borrow_row) == n
    i2024 = years.index("2024")
    mt_lt_2024_scaled    = 36755.0 / 10.0
    sa_total_2024_scaled = 41710.0 / 10.0
    assert borrow_row[i2024] is not None
    assert abs(borrow_row[i2024] - sa_total_2024_scaled) < 1.0, (
        f"borrowings[2024]={borrow_row[i2024]} should be SA Total Debt "
        f"{sa_total_2024_scaled}, not MT LT-only {mt_lt_2024_scaled} "
        "(current-debt completion did not run)"
    )
    assert borrow_row[i2024] > mt_lt_2024_scaled, "borrowings still LT-only after merge"

    # borrowings completion must have actually run (SA native years recorded)
    assert meta["borrowings"]["native_years"], (
        "borrowings completion was skipped (no native_years in reconstruction_meta)"
    )

    # Top-level debt array should also be refreshed
    debt_top = fin.get("debt", [])
    assert any(v and v != 0.0 for v in debt_top)

    # ----------------------------------------------------------------
    # 3. bs["trade receivables"] populated and spans > SA window (>5 years)
    # ----------------------------------------------------------------
    tr_row = bs.get("trade receivables", [])
    assert len(tr_row) == n
    non_none_tr = [v for v in tr_row if v is not None]
    assert len(non_none_tr) > 0, "trade receivables all None"
    # Backfill should have extended beyond the ~5 SA years
    assert len(non_none_tr) > 5, (
        f"Only {len(non_none_tr)} non-None values in trade receivables - "
        "backfill did not extend beyond SA window"
    )

    # ----------------------------------------------------------------
    # 4. bs["trade payables"] populated and spans > SA window
    # ----------------------------------------------------------------
    tp_row = bs.get("trade payables", [])
    assert len(tp_row) == n
    non_none_tp = [v for v in tp_row if v is not None]
    assert len(non_none_tp) > 5, (
        f"Only {len(non_none_tp)} non-None values in trade payables"
    )

    # ----------------------------------------------------------------
    # 5. Day ratios now span > SA window (full 15y from backfill)
    # ----------------------------------------------------------------
    for ratio_key in ("debtor days", "days payable", "cash conversion cycle"):
        row = ratios.get(ratio_key, [])
        non_none = [v for v in row if v is not None]
        assert len(non_none) > 5, (
            f"ratios['{ratio_key}'] has only {len(non_none)} non-None - "
            "expected >5 (backfill should extend past SA 5y)"
        )

    # ----------------------------------------------------------------
    # 6. reconstruction_meta records all 4 items with native + backfill
    # ----------------------------------------------------------------
    for item_key in ("borrowings", "interest", "trade receivables", "trade payables"):
        assert item_key in meta, f"reconstruction_meta missing '{item_key}'"
        m = meta[item_key]
        assert "native_years" in m, f"meta['{item_key}'] missing 'native_years'"
        assert "backfilled_years" in m, f"meta['{item_key}'] missing 'backfilled_years'"


def test_integration_source_still_macrotrends(xom_fixtures):
    """source key must stay 'macrotrends' after Phase-3 merge."""
    from data.scrapers.macrotrends import fetch_macrotrends_financials

    mock_fn = _make_mock_requests(
        mt_income_html=xom_fixtures["mt_income"],
        mt_balance_html=xom_fixtures["mt_balance"],
        mt_cashflow_html=xom_fixtures["mt_cashflow"],
        sa_income_html=xom_fixtures["sa_income"],
        sa_balance_html=xom_fixtures["sa_balance"],
        sa_cashflow_html=xom_fixtures["sa_cashflow"],
        sa_ratios_html=xom_fixtures["sa_ratios"],
        sa_overview_html=xom_fixtures["sa_income"],
    )

    with patch("data.scrapers.macrotrends.requests.Session", return_value=type("MockSession", (), {"headers": {}, "get": lambda self, url, **kwargs: mock_fn(url, **kwargs)})()), \
         patch("data.scrapers.stockanalysis.requests.get", side_effect=mock_fn):
        fin = fetch_macrotrends_financials("XOM")

    assert fin["source"] == "macrotrends"


def test_integration_merge_fails_gracefully():
    """
    If stockanalysis is completely unavailable, _merge_stockanalysis_gaps
    must return the Phase-1 dict unchanged (no exception raised).
    Uses a distinct ticker (XOMFAIL) so the module-scoped cache does not
    return the already-merged XOM result.
    """
    from data.scrapers.macrotrends import fetch_macrotrends_financials

    mock_fn = _make_mock_requests(
        mt_income_html=_load("macrotrends_xom_income.html"),
        mt_balance_html=_load("macrotrends_xom_balance.html"),
        mt_cashflow_html=_load("macrotrends_xom_cashflow.html"),
    )

    def bad_sa(url, *args, **kwargs):
        if "stockanalysis" in url:
            raise RuntimeError("SA is down")
        return mock_fn(url, *args, **kwargs)

    with patch("data.scrapers.macrotrends.requests.Session", return_value=type("MockSession", (), {"headers": {}, "get": lambda self, url, **kwargs: bad_sa(url, **kwargs)})()), \
         patch("data.scrapers.stockanalysis.requests.get", side_effect=bad_sa):
        fin = fetch_macrotrends_financials("XOMFAIL")

    assert fin is not None, "fetch must not return None on SA failure"
    assert fin["source"] == "macrotrends"


def test_engine_smoke_phase3(xom_fixtures):
    """
    End-to-end: Phase-3 merged fin -> DCF engine -> positive intrinsic value.
    Also verifies that the historical effective cost of debt is populated
    (interest non-zero) so the engine can compute a meaningful cost of debt.
    """
    from data.scrapers.macrotrends import fetch_macrotrends_financials
    from sidwell.engine.core import run_engine
    from sidwell.ajp.schema import AJP

    mock_fn = _make_mock_requests(
        mt_income_html=xom_fixtures["mt_income"],
        mt_balance_html=xom_fixtures["mt_balance"],
        mt_cashflow_html=xom_fixtures["mt_cashflow"],
        sa_income_html=xom_fixtures["sa_income"],
        sa_balance_html=xom_fixtures["sa_balance"],
        sa_cashflow_html=xom_fixtures["sa_cashflow"],
        sa_ratios_html=xom_fixtures["sa_ratios"],
        sa_overview_html=xom_fixtures["sa_income"],
    )

    with patch("data.scrapers.macrotrends.requests.Session", return_value=type("MockSession", (), {"headers": {}, "get": lambda self, url, **kwargs: mock_fn(url, **kwargs)})()), \
         patch("data.scrapers.stockanalysis.requests.get", side_effect=mock_fn):
        fin = fetch_macrotrends_financials("XOM")

    ajp = AJP.from_dict({})

    with patch("data.public.fetch_risk_free_rate", return_value=0.04), \
         patch("data.public.fetch_damodaran_data", return_value={
             "mature_market_erp": 0.045, "country_risk_premium": 0.0,
             "total_erp": 0.045, "industry_levered_beta": 1.1,
             "industry_unlevered_beta": 1.0, "industry_de_ratio": 0.2,
         }), \
         patch("data.public.fetch_damodaran_industry_fundamentals",
               return_value={"available": False}):
        res = run_engine(fin, ajp)

    assert res.get("intrinsic_value_per_share", 0) > 0, (
        f"Expected positive intrinsic value, got: {res.get('intrinsic_value_per_share')}"
    )

    # interest now populated -> effective rate != the clamp floor
    from sidwell.engine.statements import StatementsEngine
    hist = StatementsEngine.map_historical(fin["statements"])
    hist_interest = hist["is"].get("interest", [])
    # The engine's interest row comes from pl["interest"] which we just filled.
    # At least some values should be non-zero (SA provided 5 years; backfill the rest).
    assert any(v != 0.0 for v in hist_interest), (
        "Engine's mapped interest is all zero - interest backfill not reaching the engine"
    )
