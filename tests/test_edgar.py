"""
Offline tests for data/scrapers/edgar.py

All edgartools Company + requests + yfinance calls are mocked - no network required.
Runs in < 5 s.
"""

import datetime
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers to build a mock SEC companyfacts JSON object
# ---------------------------------------------------------------------------

def _make_mock_companyfacts_json():
    """
    Returns a mock JSON object simulating the SEC API response.
    3 FYs of data: 2021, 2022, 2023.
    """
    fiscal_ends = ["2021-09-25", "2022-09-24", "2023-09-30"]
    revenues = [3.6583e11, 3.9441e11, 3.8328e11]
    cogs = [2.1298e11, 2.2355e11, 2.1414e11]
    net_incomes = [9.468e10, 9.996e10, 9.697e10]
    op_incomes = [1.0890e11, 1.1953e11, 1.1401e11]
    total_assets = [3.5187e11, 3.5226e11, 3.5257e11]
    ca = [1.3484e11, 1.3540e11, 1.4357e11]
    cl = [1.2548e11, 1.5398e11, 1.4531e11]
    lt_debt = [1.0919e11, 9.8959e10, 9.5281e10]
    cash = [3.4940e10, 2.3646e10, 2.9965e10]
    cfo = [1.0421e11, 1.2296e11, 1.1054e11]
    capex = [1.1085e10, 1.0708e10, 1.0959e10]

    def make_series(vals, ends, fy_start=2021):
        series = []
        for i, (v, e) in enumerate(zip(vals, ends)):
            series.append({
                "val": v,
                "end": e,
                "fy": fy_start + i,
                "fp": "FY",
                "form": "10-K",
            })
        return series

    return {
        "facts": {
            "dei": {
                "EntityCommonStockSharesOutstanding": {
                    "units": {"shares": make_series([1.55e10, 1.55e10, 1.55e10], fiscal_ends)}
                }
            },
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "units": {"USD": make_series(revenues, fiscal_ends)}
                },
                "CostOfGoodsAndServicesSold": {
                    "units": {"USD": make_series(cogs, fiscal_ends)}
                },
                "NetIncomeLoss": {
                    "units": {"USD": make_series(net_incomes, fiscal_ends)}
                },
                "OperatingIncomeLoss": {
                    "units": {"USD": make_series(op_incomes, fiscal_ends)}
                },
                "Assets": {
                    "units": {"USD": make_series(total_assets, fiscal_ends)}
                },
                "AssetsCurrent": {
                    "units": {"USD": make_series(ca, fiscal_ends)}
                },
                "LiabilitiesCurrent": {
                    "units": {"USD": make_series(cl, fiscal_ends)}
                },
                "CashAndCashEquivalentsAtCarryingValue": {
                    "units": {"USD": make_series(cash, fiscal_ends)}
                },
                "LongTermDebtNoncurrent": {
                    "units": {"USD": make_series(lt_debt, fiscal_ends)}
                },
                "NetCashProvidedByUsedInOperatingActivities": {
                    "units": {"USD": make_series(cfo, fiscal_ends)}
                },
                "PaymentsToAcquirePropertyPlantAndEquipment": {
                    "units": {"USD": make_series(capex, fiscal_ends)}
                },
                "DebtCurrent": {
                    "units": {"USD": make_series([0, 0, 0], fiscal_ends)}
                }
            }
        }
    }


def _make_mock_requests_get():
    mock_resp = MagicMock()
    mock_resp.json.return_value = _make_mock_companyfacts_json()
    mock_resp.raise_for_status = MagicMock()
    return MagicMock(return_value=mock_resp)


def _make_mock_company(ticker="AAPL"):
    mc = MagicMock()
    mc.sic = 3672   # Computer Hardware (AAPL-like)
    mc.sic_description = "Computer Hardware"
    mc.cik = "320193"
    return mc


def _make_mock_yf_module():
    """Returns a mock yfinance module where yf.Ticker() returns a mock ticker."""
    mock_fi = MagicMock()
    mock_fi.last_price = 189.50
    mock_fi.shares = 1.55e10
    mock_fi.market_cap = 2.935e12

    mock_ticker = MagicMock()
    mock_ticker.fast_info = mock_fi
    mock_ticker.info = {"trailingPE": 29.5, "dividendYield": 0.0051}

    mock_yf = MagicMock()
    mock_yf.Ticker.return_value = mock_ticker
    return mock_yf


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_fetch_edgar_returns_correct_structure():
    """
    Test 1: fetch_edgar_financials returns a dict with all required top-level keys
    and the nested statements structure matching screener.py's contract.
    """
    with patch("data.scrapers.edgar.cache.get_json", return_value=None), \
         patch("data.scrapers.edgar.cache.set_json"), \
         patch("data.scrapers.edgar.Company", return_value=_make_mock_company()), \
         patch("data.scrapers.edgar.requests.get", new_callable=_make_mock_requests_get), \
         patch("data.scrapers.edgar.set_identity"), \
         patch("data.scrapers.edgar._us_price", return_value=189.50), \
         patch("data.scrapers.edgar.yf", new=_make_mock_yf_module()):

        from data.scrapers.edgar import fetch_edgar_financials
        fin = fetch_edgar_financials("AAPL")

    # -- Top-level keys (screener contract) --
    required_top_level = [
        "ticker", "current_price", "market_cap", "shares_outstanding",
        "trailing_pe", "dividend_yield", "stock_beta", "recommendation_mean",
        "insider_ownership", "source", "revenue", "gross_profit", "ebit",
        "interest_expense", "tax_provision", "pretax_income", "net_income",
        "total_assets", "total_equity", "cash", "debt", "capex", "depreciation",
        "working_capital_change", "fcf", "historical_shares", "years",
        "scraped_sector", "scraped_industry", "is_bank", "is_financial",
        "book_value_per_share",
    ]
    for key in required_top_level:
        assert key in fin, f"Missing top-level key: {key}"

    assert fin["source"] == "sec_edgar"
    assert fin["statements"]["years_annual"] == ["2021", "2022", "2023"]

    # -- statements structure --
    stmt = fin["statements"]
    assert "years_annual" in stmt
    assert "annual" in stmt
    assert "profit_loss" in stmt["annual"]
    assert "balance_sheet" in stmt["annual"]
    assert "cash_flow" in stmt["annual"]
    assert "ratios" in stmt

    # -- profit_loss row labels --
    pl = stmt["annual"]["profit_loss"]
    for label in ["sales", "operating profit", "depreciation", "interest",
                  "profit before tax", "tax", "net profit"]:
        assert label in pl, f"Missing P&L row: {label}"

    # -- balance_sheet row labels --
    bs = stmt["annual"]["balance_sheet"]
    for label in ["equity capital", "reserves", "borrowings", "trade payables",
                  "fixed assets", "inventories", "trade receivables",
                  "cash equivalents", "total assets", "total liabilities"]:
        assert label in bs, f"Missing BS row: {label}"

    # -- cash_flow row labels --
    cf = stmt["annual"]["cash_flow"]
    for label in ["cash from operating activity", "fixed assets purchased",
                  "cash from investing activity", "cash from financing activity"]:
        assert label in cf, f"Missing CF row: {label}"


def test_statement_values_are_usd_divided_by_1e7():
    """
    Test 2: Statement row values equal raw_USD / 1e7 (screener crore scale).
    AAPL FY2023 revenue mock = 3.8328e11 -> expected = 3.8328e11 / 1e7 = 38328.0
    """
    with patch("data.scrapers.edgar.cache.get_json", return_value=None), \
         patch("data.scrapers.edgar.cache.set_json"), \
         patch("data.scrapers.edgar.Company", return_value=_make_mock_company()), \
         patch("data.scrapers.edgar.requests.get", new_callable=_make_mock_requests_get), \
         patch("data.scrapers.edgar.set_identity"), \
         patch("data.scrapers.edgar._us_price", return_value=189.50), \
         patch("data.scrapers.edgar.yf", new=_make_mock_yf_module()):

        from data.scrapers.edgar import fetch_edgar_financials
        fin = fetch_edgar_financials("AAPL")

    pl = fin["statements"]["annual"]["profit_loss"]
    sales = pl["sales"]
    assert len(sales) == 3, "sales list should have 3 items"

    last_sales = sales[-1]
    expected = 3.8328e11 / 1e7  # ~= 38328.0
    assert last_sales is not None, "Last sales value is None"
    assert abs(last_sales - expected) < 1.0, (
        f"sales[-1]={last_sales}, expected~={expected}"
    )


def test_top_level_market_cap_and_debt_are_absolute_usd():
    """
    Test 3: fin["market_cap"] and fin["debt"] are absolute USD (not divided by 1e7).
    market_cap mock = 2.935e12 USD, debt scalar mock ~= 9.53e10 USD.
    """
    with patch("data.scrapers.edgar.cache.get_json", return_value=None), \
         patch("data.scrapers.edgar.cache.set_json"), \
         patch("data.scrapers.edgar.Company", return_value=_make_mock_company()), \
         patch("data.scrapers.edgar.requests.get", new_callable=_make_mock_requests_get), \
         patch("data.scrapers.edgar.set_identity"), \
         patch("data.scrapers.edgar._us_price", return_value=189.50), \
         patch("data.scrapers.edgar.yf", new=_make_mock_yf_module()):

        from data.scrapers.edgar import fetch_edgar_financials
        fin = fetch_edgar_financials("AAPL")

    assert fin["market_cap"] == pytest.approx(189.50 * 1.55e10, rel=1e-2)
    assert fin["current_price"] == pytest.approx(189.50, rel=1e-3)
    assert fin["shares_outstanding"] == pytest.approx(1.55e10, rel=1e-3)
    assert fin["market_cap"] == fin["current_price"] * fin["shares_outstanding"]

    last_debt = fin["debt"]
    assert last_debt is not None
    # LT_debt mock = 9.5281e10, current debt mock = 0 -> total ~= 9.53e10
    assert abs(last_debt[-1] - 9.5281e10) < 1e9, f"debt={last_debt}"


def test_is_bank_and_is_financial_flags():
    """
    Test 4: is_bank and is_financial flags reflect SIC code correctly.
    AAPL SIC 3672 -> not a bank, not financial.
    """
    with patch("data.scrapers.edgar.cache.get_json", return_value=None), \
         patch("data.scrapers.edgar.cache.set_json"), \
         patch("data.scrapers.edgar.Company", return_value=_make_mock_company("AAPL")), \
         patch("data.scrapers.edgar.requests.get", new_callable=_make_mock_requests_get), \
         patch("data.scrapers.edgar.set_identity"), \
         patch("data.scrapers.edgar._us_price", return_value=189.50), \
         patch("data.scrapers.edgar.yf", new=_make_mock_yf_module()):

        from data.scrapers.edgar import fetch_edgar_financials
        fin = fetch_edgar_financials("AAPL")

    assert fin["is_bank"] is False
    assert fin["is_financial"] is False


def test_bank_sic_sets_is_bank_true():
    """
    Test 5: A company with SIC 6022 (State commercial banks) should have is_bank=True.
    """
    bank_company = _make_mock_company("JPM")
    bank_company.sic = 6022
    bank_company.sic_description = "State commercial banks"

    with patch("data.scrapers.edgar.cache.get_json", return_value=None), \
         patch("data.scrapers.edgar.cache.set_json"), \
         patch("data.scrapers.edgar.Company", return_value=bank_company), \
         patch("data.scrapers.edgar.requests.get", new_callable=_make_mock_requests_get), \
         patch("data.scrapers.edgar.set_identity"), \
         patch("data.scrapers.edgar._us_price", return_value=189.50), \
         patch("data.scrapers.edgar.yf", new=_make_mock_yf_module()):

        from data.scrapers.edgar import fetch_edgar_financials
        fin = fetch_edgar_financials("JPM")

    assert fin["is_bank"] is True
    assert fin["is_financial"] is True


def test_run_engine_on_mocked_aapl_yields_positive_intrinsic():
    """
    Test 6: The mocked AAPL fin dict, passed through run_engine with a minimal AJP,
    produces intrinsic_value_per_share > 0.
    """
    with patch("data.scrapers.edgar.cache.get_json", return_value=None), \
         patch("data.scrapers.edgar.cache.set_json"), \
         patch("data.scrapers.edgar.Company", return_value=_make_mock_company()), \
         patch("data.scrapers.edgar.requests.get", new_callable=_make_mock_requests_get), \
         patch("data.scrapers.edgar.set_identity"), \
         patch("data.scrapers.edgar._us_price", return_value=189.50), \
         patch("data.scrapers.edgar.yf", new=_make_mock_yf_module()):

        from data.scrapers.edgar import fetch_edgar_financials
        fin = fetch_edgar_financials("AAPL")

    # Build a minimal AJP (in-memory) for AAPL - USD, not holdco
    from sidwell.ajp.schema import AJP, AJPAssumption, AJPMeta
    meta = AJPMeta(
        ticker="AAPL",
        as_of="2024-01-01",
        currency="USD_MM",
        sources_ingested=["10-K_FY2023"],
        fiscal_year_end_month=9,
        last_actual_fy="FY2023",
        is_holdco=False,
        scenario_active="BASE",
    )
    assumptions = [
        AJPAssumption(
            driver_id="stage1_revenue_growth",
            value=0.06,
            unit="ratio",
            source_type="ENGINE_COMPUTED",
            confidence="MEDIUM",
            rationale="Conservative growth estimate",
            interrogation_refs=[],
        ),
    ]
    ajp = AJP(meta=meta, assumptions=assumptions)

    from sidwell.engine.core import run_engine
    results = run_engine(fin, ajp)

    assert "intrinsic_value_per_share" in results
    assert results["intrinsic_value_per_share"] > 0, (
        f"Expected positive intrinsic, got {results['intrinsic_value_per_share']}"
    )


def test_cache_is_written_on_fetch():
    """
    Test 7: cache.set_json is called twice (once for financials, once for price).
    """
    mock_set_json = MagicMock()

    with patch("data.scrapers.edgar.cache.get_json", return_value=None), \
         patch("data.scrapers.edgar.cache.set_json", mock_set_json), \
         patch("data.scrapers.edgar.Company", return_value=_make_mock_company()), \
         patch("data.scrapers.edgar.requests.get", new_callable=_make_mock_requests_get), \
         patch("data.scrapers.edgar.set_identity"), \
         patch("data.scrapers.edgar._us_price", return_value=189.50), \
         patch("data.scrapers.edgar.yf", new=_make_mock_yf_module()):

        from data.scrapers.edgar import fetch_edgar_financials
        fetch_edgar_financials("AAPL")

    assert mock_set_json.call_count == 2
    keys_written = [call.args[0] for call in mock_set_json.call_args_list]
    assert any("financials_edgar_AAPL" in k for k in keys_written)
    assert any("price_edgar_AAPL" in k for k in keys_written)


def test_cache_hit_skips_network():
    """
    Test 8: When cache returns a valid dict, Company() is never called.
    """
    cached_fin = {
        "ticker": "AAPL", "source": "sec_edgar",
        "current_price": None,
        "revenue": [0.0]*4, "gross_profit": [0.0]*4, "ebit": [0.0]*4,
        "interest_expense": [0.0]*4, "tax_provision": [0.0]*4,
        "pretax_income": [0.0]*4, "net_income": [0.0]*4,
        "total_assets": [0.0]*4, "total_equity": [0.0]*4,
        "cash": [0.0]*4, "debt": 0.0, "capex": [0.0]*4,
        "depreciation": [0.0]*4, "working_capital_change": [0.0]*4,
        "fcf": [0.0]*4, "historical_shares": [0.0]*4,
        "is_bank": False, "is_financial": False,
        "statements": {
            "years_annual": ["2023"],
            "annual": {"profit_loss": {}, "balance_sheet": {}, "cash_flow": {}},
            "ratios": {}, "quarterly": {"profit_loss": {}},
            "shareholding": {}, "top_ratios": {}, "peers": [],
        },
    }
    cached_price = {"current_price": 189.50}

    mock_company_class = MagicMock()
    mock_requests = MagicMock()

    def mock_get_json(key, ttl):
        if "financials" in key:
            return cached_fin
        if "price" in key:
            return cached_price
        return None

    with patch("data.scrapers.edgar.cache.get_json", side_effect=mock_get_json), \
         patch("data.scrapers.edgar.Company", mock_company_class), \
         patch("data.scrapers.edgar.requests.get", mock_requests), \
         patch("data.scrapers.edgar.set_identity"), \
         patch("data.scrapers.edgar._us_price", return_value=189.50):

        from data.scrapers.edgar import fetch_edgar_financials
        fin = fetch_edgar_financials("AAPL")

    mock_company_class.assert_not_called()
    mock_requests.assert_not_called()
    assert fin["current_price"] == 189.50


def test_concept_annual_map_merges_split_tags_and_keys_by_period_year():
    """Reproduces the GOOGL bug: revenue split across two tags, latest year only on the
    lower-priority tag. Must merge + key by period year + prefer latest-filed."""
    from data.scrapers.edgar import _concept_annual_map
    def fact(val, end, fy, filed, form="10-K", fp="FY"):
        return {"val": val, "end": end, "fy": fy, "filed": filed, "form": form, "fp": fp}
    usgaap = {
        "ConceptA": {"units": {"USD": [
            fact(100, "2022-12-31", 2022, "2023-02-01"),       # original 2022
            fact(105, "2022-12-31", 2023, "2024-02-01"),       # 2022 restated, filed later -> wins
            fact(110, "2023-12-31", 2023, "2024-02-01"),
        ]}},
        "ConceptB": {"units": {"USD": [
            fact(120, "2024-12-31", 2024, "2025-02-01"),       # only ConceptB has 2024
            fact(111, "2023-12-31", 2024, "2025-02-01"),       # B's 2023 must NOT override A's 110
        ]}},
    }
    m = _concept_annual_map(usgaap, ["ConceptA", "ConceptB"])
    assert m == {2022: 105, 2023: 110, 2024: 120}, m   # merge fills 2024; restatement; priority


def test_wc_days_and_gross_profit():
    """Test that working capital days, cogs, and gross_profit are calculated correctly."""
    with patch("data.scrapers.edgar.cache.get_json", return_value=None), \
         patch("data.scrapers.edgar.cache.set_json"), \
         patch("data.scrapers.edgar.Company", return_value=_make_mock_company()), \
         patch("data.scrapers.edgar.requests.get", new_callable=_make_mock_requests_get), \
         patch("data.scrapers.edgar.set_identity"), \
         patch("data.scrapers.edgar._us_price", return_value=189.50), \
         patch("data.scrapers.edgar.yf", new=_make_mock_yf_module()):

        from data.scrapers.edgar import fetch_edgar_financials
        fin = fetch_edgar_financials("AAPL")

    stmt = fin["statements"]
    wc_days = stmt["ratios"]["working capital days"]
    assert len(wc_days) == 3
    
    # 2023 values from mock:
    # ca = 1.4357e11, cl = 1.4531e11
    # cash = 2.9965e10
    # current_debt = 0 (DebtCurrent mock)
    # sales = 3.8328e11
    # nwc = (1.4357e11 - 2.9965e10) - (1.4531e11 - 0) = 1.13605e11 - 1.4531e11 = -3.1705e10
    # wc_days = -3.1705e10 / 3.8328e11 * 365.0 ~ -30.19
    expected_wc_days = ((1.4357e11 - 2.9965e10) - (1.4531e11 - 0)) / 3.8328e11 * 365.0
    assert abs(wc_days[-1] - expected_wc_days) < 0.1, f"Expected {expected_wc_days}, got {wc_days[-1]}"

    pl = stmt["annual"]["profit_loss"]
    assert "cogs" in pl
    
    # 2023 cogs scaled = 2.1414e11 / 1e7 = 21414.0
    assert abs(pl["cogs"][-1] - (2.1414e11 / 1e7)) < 1.0

    # gross_profit absolute
    gp = fin["gross_profit"]
    assert len(gp) == 3
    # 2023 revenue = 3.8328e11, cogs = 2.1414e11
    expected_gp = 3.8328e11 - 2.1414e11
    assert abs(gp[-1] - expected_gp) < 1.0

