"""
SEC EDGAR financial data adapter using edgartools (XBRL facts) + stooq/yfinance (price).

CONTRACT: Returns the same dict shape as data/scrapers/screener.py's
fetch_screener_financials so the existing engine values US companies identically.

UNIT CONVENTION (must match engine expectations):
  - fin["statements"]["annual"][*] row values = USD / 1e7
    (screener stores crore = INR/1e7; engine ×10s them to millions;
     so EDGAR USD values must also be divided by 1e7 to keep the same scale)
  - fin["debt"], fin["market_cap"] = absolute USD (same as screener which stores crore*1e7)
  - fin["current_price"] = USD
  - All legacy top-level lists (revenue, net_income, …) = absolute USD (same as screener
    which does crore*1e7 via _crore_to_rupee)
"""

import os
import logging
import requests
from typing import Optional

# Module-level imports so they can be patched in tests
try:
    from edgar import Company, set_identity
except ImportError:  # pragma: no cover
    Company = None  # type: ignore
    set_identity = None  # type: ignore

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None  # type: ignore

from data import cache

logger = logging.getLogger(__name__)

TTL_PRICES = 24 * 60 * 60
TTL_FINANCIALS = 7 * 24 * 60 * 60

# SEC requires a User-Agent string for all API calls.
_EDGAR_IDENTITY = os.environ.get(
    "EDGAR_IDENTITY", "Sidwell research contact@example.com"
)

# SIC code ranges for financial sector classification
# Banks: 6020–6199, broader financials: 6000–6799
_BANK_SIC_RANGE = (6020, 6199)
_FINANCIAL_SIC_RANGE = (6000, 6799)

# Keyword signatures reused from screener.py for is_financial detection
_FINANCIAL_KEYWORDS = (
    "financial services", "broking", "broker", "capital market",
    "asset management", "stock broking", "depositor", "nbfc",
    "non banking financ", "insuranc",
)


def _is_financial_sector(*classification_fields: Optional[str]) -> bool:
    blob = " ".join((f or "").lower() for f in classification_fields)
    return any(kw in blob for kw in _FINANCIAL_KEYWORDS)


def _safe_float(val) -> Optional[float]:
    """Convert a value to float, returning None on failure."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _us_price(ticker: str) -> float | None:
    """Reliable US last price: stooq CSV (no key, cloud-friendly) -> yfinance fallback."""
    t = ticker.upper()
    try:
        import requests
        r = requests.get(
            f"https://stooq.com/q/l/?s={t.lower()}.us&f=sd2t2ohlcv&h&e=csv",
            headers={"User-Agent": "Mozilla/5.0 (Sidwell)"}, timeout=15)
        r.raise_for_status()
        lines = r.text.strip().splitlines()
        if len(lines) >= 2:
            cols = lines[1].split(",")          # Symbol,Date,Time,Open,High,Low,Close,Volume
            if len(cols) >= 7 and cols[6] not in ("", "N/D"):
                return float(cols[6])
    except Exception:
        pass
    try:
        import yfinance as yf
        p = _safe_float(getattr(yf.Ticker(t).fast_info, "last_price", None))
        if p:
            return p
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# XBRL concept → row-label mapping
# ---------------------------------------------------------------------------
# Each entry: (screener_label, list_of_us_gaap_concept_names_in_priority_order)
# We try each concept in order and take the first non-empty series.

_PL_CONCEPTS = [
    ("cogs", ["CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold", "CostOfServices"]),
    ("sales", [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet",
    ]),
    ("operating profit", [
        "OperatingIncomeLoss",
    ]),
    ("depreciation", [
        "DepreciationDepletionAndAmortization",
        "DepreciationAndAmortization",
        "Depreciation",
    ]),
    ("interest", [
        "InterestExpense",
        "InterestExpenseDebt",
    ]),
    ("profit before tax", [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
    ]),
    ("tax", [
        "IncomeTaxExpenseBenefit",
    ]),
    ("net profit", [
        "NetIncomeLoss",
        "NetIncome",
    ]),
]

_BS_CONCEPTS = [
    ("equity capital", []),   # US doesn't split par vs retained — always []
    ("reserves", [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ]),
    ("borrowings", [
        # sum of LT + current debt handled specially below
        "LongTermDebtNoncurrent",
    ]),
    ("lease liabilities", [
        "OperatingLeaseLiabilityNoncurrent",
    ]),
    ("non controlling int", [
        "MinorityInterest",
        "NoncontrollingInterestInConsolidatedSubsidiaries",
    ]),
    ("trade payables", [
        "AccountsPayableCurrent",
    ]),
    ("fixed assets", [
        "PropertyPlantAndEquipmentNet",
    ]),
    ("gross block", [
        "PropertyPlantAndEquipmentGross",
    ]),
    ("accumulated depreciation", [
        "AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment",
    ]),
    ("investments", [
        "LongTermInvestments",
        "ShortTermInvestments",
        "MarketableSecurities",
    ]),
    ("inventories", [
        "InventoryNet",
        "Inventories",
    ]),
    ("trade receivables", [
        "AccountsReceivableNetCurrent",
    ]),
    ("cash equivalents", [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsAndShortTermInvestments",
    ]),
    ("total assets", [
        "Assets",
    ]),
    ("total liabilities", [
        "Liabilities",
    ]),
]

_CF_CONCEPTS = [
    ("cash from operating activity", [
        "NetCashProvidedByUsedInOperatingActivities",
    ]),
    ("fixed assets purchased", [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsForCapitalImprovements",
    ]),
    ("cash from investing activity", [
        "NetCashProvidedByUsedInInvestingActivities",
    ]),
    ("cash from financing activity", [
        "NetCashProvidedByUsedInFinancingActivities",
    ]),
    ("proceeds from borrowings", [
        "ProceedsFromIssuanceOfLongTermDebt",
        "ProceedsFromLongTermLinesOfCredit",
    ]),
    ("repayment of borrowings", [
        "RepaymentsOfLongTermDebt",
        "RepaymentsOfNotesPayable",
    ]),
]

# Concepts needed at the top level (not in statements)
_DEBT_LT_CONCEPTS = [
    "LongTermDebtNoncurrent",
    "LongTermDebt",
    "LongTermDebtAndCapitalLeaseObligations",
]
_DEBT_CURRENT_CONCEPTS = [
    "DebtCurrent",
    "LongTermDebtCurrent",
    "ShortTermBorrowings",
    "CommercialPaper",
]
_LEASE_CURRENT_CONCEPTS = [
    "OperatingLeaseLiabilityCurrent",
    "FinanceLeaseLiabilityCurrent",
]
_SHARES_CONCEPTS = [
    "EntityCommonStockSharesOutstanding",
    "CommonStockSharesOutstanding",
    "WeightedAverageNumberOfDilutedSharesOutstanding",
]


# ---------------------------------------------------------------------------
# Core XBRL facts extraction helpers
# ---------------------------------------------------------------------------

def _concept_annual_map(usgaap: dict, concepts: list) -> dict:
    """Return {period_year:int -> val:float} of ANNUAL (10-K, full-year) values.

    Keys by the PERIOD year parsed from each fact's `end` date (NOT the filing `fy`,
    which conflates the filing year with the reported period). For each period year keep
    the value from the most recently FILED 10-K (restatements win). Candidate concepts are
    merged in PRIORITY order: a higher-priority concept's value for a period year is never
    overwritten by a lower-priority one, but lower-priority concepts FILL period years the
    higher-priority concept is missing (handles filers that switch revenue tags across years,
    e.g. Alphabet's Revenues vs RevenueFromContractWithCustomerExcludingAssessedTax)."""
    merged = {}
    for concept in concepts:                       # priority order
        node = usgaap.get(concept)
        if not node:
            continue
        units = node.get("units", {})
        series = units.get("USD") or units.get("USD/shares") or units.get("shares") or []
        per_concept = {}
        for e in series:
            if not str(e.get("form", "")).startswith("10-K"):
                continue
            if e.get("fp") != "FY":
                continue
            end = e.get("end", "")
            if len(end) < 4:
                continue
            try:
                py = int(end[:4])                  # period year, from the period-end date
            except ValueError:
                continue
            filed = e.get("filed", "") or end      # prefer most-recently-filed per period
            if py not in per_concept or filed > per_concept[py][0]:
                per_concept[py] = (filed, e.get("val"))
        for py, (filed, val) in per_concept.items():
            if py not in merged:                   # fill gaps; keep higher-priority concept
                merged[py] = val
    return merged


# ---------------------------------------------------------------------------
# SIC-based classification helpers
# ---------------------------------------------------------------------------

def _sic_to_sector_industry(sic: Optional[int], sic_description: Optional[str]):
    """
    Maps SEC SIC code and description to (scraped_sector, scraped_industry) strings
    that Damodaran routing can use.
    Returns (sector_str, industry_str).
    """
    if sic is None:
        return None, None

    # Map SIC ranges to readable sector strings (for Damodaran routing in public.py)
    # These map to keys in SECTOR_TO_DAMODARAN_MAP in data/public.py
    SIC_MAP = [
        (range(100, 1000),   ("Agriculture", "Agriculture")),
        (range(1000, 1500),  ("Basic Materials", "Metals & Mining")),
        (range(1500, 1800),  ("Industrials", "Construction")),
        (range(2000, 2100),  ("Consumer Defensive", "Packaged Foods")),
        (range(2100, 2200),  ("Consumer Defensive", "Tobacco")),
        (range(2600, 2700),  ("Basic Materials", "Paper & Packaging")),
        (range(2800, 2900),  ("Basic Materials", "Chemicals")),
        (range(2900, 3000),  ("Energy", "Oil & Gas Refining & Marketing")),
        (range(3300, 3400),  ("Basic Materials", "Steel")),
        (range(3500, 3600),  ("Industrials", "Specialty Industrial Machinery")),
        (range(3559, 3560),  ("Industrials", "Semiconductor Equipment & Materials")),
        (range(3600, 3700),  ("Technology", "Electronic Components")),
        (range(3661, 3662),  ("Technology", "Communication Equipment")),
        (range(3669, 3670),  ("Technology", "Communication Equipment")),
        (range(3672, 3680),  ("Technology", "Semiconductors")),
        (range(3700, 3800),  ("Consumer Cyclical", "Auto Manufacturers")),
        (range(3812, 3813),  ("Industrials", "Aerospace & Defense")),
        (range(3820, 3830),  ("Healthcare", "Medical Instruments & Supplies")),
        (range(3841, 3842),  ("Healthcare", "Medical Devices")),
        (range(3900, 4000),  ("Consumer Cyclical", "Specialty Retail")),
        (range(4210, 4220),  ("Industrials", "Trucking")),
        (range(4400, 4500),  ("Industrials", "Marine Shipping")),
        (range(4510, 4520),  ("Industrials", "Airlines")),
        (range(4810, 4820),  ("Communication Services", "Telecom")),
        (range(4911, 4940),  ("Utilities", "Utilities-Regulated Electric")),
        (range(5000, 5100),  ("Industrials", "Industrial Distribution")),
        (range(5200, 5400),  ("Consumer Cyclical", "Specialty Retail")),
        (range(5400, 5500),  ("Consumer Defensive", "Discount Stores")),
        (range(5600, 5700),  ("Consumer Cyclical", "Specialty Retail")),
        (range(5700, 5800),  ("Consumer Cyclical", "Specialty Retail")),
        (range(5900, 6000),  ("Consumer Cyclical", "Specialty Retail")),
        (range(6020, 6200),  ("Financial Services", "Banks-Diversified")),
        (range(6200, 6300),  ("Financial Services", "Capital Markets")),
        (range(6300, 6400),  ("Financial Services", "Insurance-Diversified")),
        (range(6400, 6500),  ("Financial Services", "Insurance-Life")),
        (range(6500, 6600),  ("Real Estate", "REIT-Diversified")),
        (range(6700, 6800),  ("Financial Services", "Asset Management")),
        (range(7011, 7012),  ("Consumer Cyclical", "Restaurants")),
        (range(7370, 7380),  ("Technology", "Software-Application")),
        (range(7372, 7373),  ("Technology", "Software-Infrastructure")),
        (range(7812, 7820),  ("Communication Services", "Entertainment")),
        (range(8000, 8100),  ("Healthcare", "Medical Care Facilities")),
        (range(8011, 8012),  ("Healthcare", "Medical Care Facilities")),
        (range(8049, 8050),  ("Healthcare", "Healthcare Plans")),
        (range(8051, 8052),  ("Healthcare", "Medical Care Facilities")),
        (range(8060, 8070),  ("Healthcare", "Medical Care Facilities")),
        (range(8731, 8735),  ("Healthcare", "Diagnostics & Research")),
        (range(8742, 8743),  ("Technology", "Information Technology Services")),
    ]

    for sic_range, (sector, industry) in SIC_MAP:
        if sic in sic_range:
            return sector, industry

    # Fallback: use SIC description if available
    desc = (sic_description or "").lower()
    if "software" in desc or "computer" in desc:
        return "Technology", "Software-Application"
    if "semiconductor" in desc:
        return "Technology", "Semiconductors"
    if "bank" in desc or "savings" in desc:
        return "Financial Services", "Banks-Diversified"
    if "insurance" in desc:
        return "Financial Services", "Insurance-Diversified"
    if "pharmaceutical" in desc or "drug" in desc:
        return "Healthcare", "Drug Manufacturers-General"
    if "retail" in desc:
        return "Consumer Cyclical", "Specialty Retail"
    if "oil" in desc or "petroleum" in desc or "gas" in desc:
        return "Energy", "Oil & Gas Integrated"

    return sic_description, sic_description


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def fetch_edgar_financials(ticker: str) -> dict:
    """
    Fetches US company financials from SEC EDGAR using edgartools (XBRL facts)
    and yfinance (price), returning the same dict shape as
    data/scrapers/screener.py's fetch_screener_financials.

    The returned dict is compatible with the Sidwell engine without modification.
    """
    ticker_upper = ticker.upper()
    cache_key_fin = f"financials_edgar_{ticker_upper}.json"
    cache_key_price = f"price_edgar_{ticker_upper}.json"

    cached_fin = cache.get_json(cache_key_fin, TTL_FINANCIALS)
    cached_price = cache.get_json(cache_key_price, TTL_PRICES)

    if cached_fin and cached_price:
        logger.info(f"Loaded EDGAR financials for {ticker_upper} from cache.")
        cached_fin["current_price"] = cached_price.get("current_price")
        # Normalize None → 0.0 for legacy numeric arrays (same as screener.py)
        _HIST_NUMERIC_KEYS = (
            "revenue", "gross_profit", "ebit", "interest_expense",
            "tax_provision", "pretax_income", "net_income",
            "total_assets", "total_equity", "cash", "debt",
            "capex", "depreciation", "working_capital_change", "fcf",
            "historical_shares",
        )
        for k in _HIST_NUMERIC_KEYS:
            if k in cached_fin and isinstance(cached_fin[k], list):
                cached_fin[k] = [(v if v is not None else 0.0) for v in cached_fin[k]]
        return cached_fin

    logger.info(f"Fetching {ticker_upper} from SEC EDGAR via edgartools...")

    # ------------------------------------------------------------------
    # 1. Load edgartools Company and facts
    # ------------------------------------------------------------------
    if Company is None or set_identity is None:
        raise ImportError("edgartools is required: pip install edgartools")
    set_identity(_EDGAR_IDENTITY)

    c = Company(ticker_upper)
    if c is None:
        raise ValueError(f"edgartools: no EDGAR company found for ticker '{ticker_upper}'")

    # SIC code for sector/industry classification
    sic = None
    sic_description = None
    try:
        sic = int(c.sic) if c.sic else None
        sic_description = c.sic_description if hasattr(c, "sic_description") else None
    except (AttributeError, ValueError, TypeError):
        pass

    scraped_sector, scraped_industry = _sic_to_sector_industry(sic, sic_description)

    # is_bank: SIC 6020–6199
    is_bank = bool(sic and _BANK_SIC_RANGE[0] <= sic <= _BANK_SIC_RANGE[1])

    # is_financial: SIC 6000–6799 OR keyword match
    is_financial = bool(
        (sic and _FINANCIAL_SIC_RANGE[0] <= sic <= _FINANCIAL_SIC_RANGE[1])
        or _is_financial_sector(scraped_sector, scraped_industry)
    )

    # ------------------------------------------------------------------
    # 2. Load company facts (XBRL us-gaap)
    # ------------------------------------------------------------------
    try:
        cik_int = int(c.cik)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_int:010d}.json"
        headers = {"User-Agent": _EDGAR_IDENTITY}
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        facts_json = resp.json()
        usgaap = facts_json.get("facts", {}).get("us-gaap", {})
        dei = facts_json.get("facts", {}).get("dei", {})
    except Exception as e:
        raise ValueError(f"edgartools/SEC API: failed to fetch XBRL facts for '{ticker_upper}': {e}") from e

    # ------------------------------------------------------------------
    # 3. Extract annual time-series for each statement row
    # ------------------------------------------------------------------

    pl_maps = {label: _concept_annual_map(usgaap, concepts) for label, concepts in _PL_CONCEPTS}
    bs_maps = {label: _concept_annual_map(usgaap, concepts) for label, concepts in _BS_CONCEPTS if concepts}
    cf_maps = {label: _concept_annual_map(usgaap, concepts) for label, concepts in _CF_CONCEPTS}
    
    debt_lt = _concept_annual_map(usgaap, _DEBT_LT_CONCEPTS)
    debt_cur= _concept_annual_map(usgaap, _DEBT_CURRENT_CONCEPTS)
    lease_nc= _concept_annual_map(usgaap, ["OperatingLeaseLiabilityNoncurrent", "FinanceLeaseLiabilityNoncurrent"])
    lease_c = _concept_annual_map(usgaap, _LEASE_CURRENT_CONCEPTS)
    
    shares_map = _concept_annual_map(dei, ["EntityCommonStockSharesOutstanding"])
    if not shares_map:
        shares_map = _concept_annual_map(usgaap, _SHARES_CONCEPTS)

    # fiscal-year axis: union of fys seen in the key anchors, sorted, last 10
    anchor_fys = set()
    for m in (pl_maps.get("sales", {}), pl_maps.get("net profit", {}), bs_maps.get("total assets", {})):
        anchor_fys |= set(m.keys())
    fys = sorted(anchor_fys)[-10:]
    years_annual = [str(fy) for fy in fys]

    def _row(m: dict) -> list:
        return [m.get(fy) for fy in fys]               # aligned, None where missing

    total_debt = {fy: (debt_lt.get(fy, 0) or 0) + (debt_cur.get(fy, 0) or 0)
                  for fy in set(debt_lt) | set(debt_cur)}
    lease_total = {fy: (lease_nc.get(fy, 0) or 0) + (lease_c.get(fy, 0) or 0)
                   for fy in set(lease_nc) | set(lease_c)}

    # ------------------------------------------------------------------
    # 4. Scale rows to USD/1e7 (screener-equivalent crore scale)
    # ------------------------------------------------------------------
    def _scale(row: list) -> list:
        return [(v / 1e7) if v is not None else None for v in row]

    # Build statements dict (screener shape)
    pl_stmt = {label: _scale(_row(pl_maps.get(label, {}))) for label, _ in _PL_CONCEPTS}
    
    bs_stmt = {}
    for label, _ in _BS_CONCEPTS:
        if label == "equity capital":
            bs_stmt[label] = [None] * len(fys)
        else:
            bs_stmt[label] = _scale(_row(bs_maps.get(label, {})))
            
    bs_stmt["borrowings"] = _scale(_row(total_debt))
    bs_stmt["lease liabilities"] = _scale(_row(lease_total))

    cf_stmt = {label: _scale(_row(cf_maps.get(label, {}))) for label, _ in _CF_CONCEPTS}

    ca_map    = _concept_annual_map(usgaap, ["AssetsCurrent"])
    cl_map    = _concept_annual_map(usgaap, ["LiabilitiesCurrent"])
    cash_map  = bs_maps.get("cash equivalents", {})   # already extracted above
    sales_map = pl_maps.get("sales", {})
    _wc_days = []
    for fy in fys:
        ca = ca_map.get(fy); cl = cl_map.get(fy); s = sales_map.get(fy)
        if ca is None or cl is None or not s:
            _wc_days.append(None); continue
        cash  = cash_map.get(fy) or 0.0
        cdebt = debt_cur.get(fy) or 0.0          # current debt already computed above
        op_nwc = (ca - cash) - (cl - cdebt)      # exclude cash from CA and short-term debt from CL
        _wc_days.append((op_nwc / s) * 365.0)    # signed days; negative is valid (e.g. Dell)
    # Comprehensive net WC-days -> engine P2 (same row the India/screener path fills).
    ratios_stmt = {"working capital days": _wc_days}

    # ------------------------------------------------------------------
    # 5. Derive top-level legacy arrays (absolute USD, NOT divided by 1e7,
    #    because screener stores these as crore*1e7 = raw rupees, and the
    #    engine uses them directly in absolute terms)
    # ------------------------------------------------------------------
    def _abs_series(m: dict) -> list:
        """Pad/trim to 4 items (legacy arrays are always 4-element like screener)."""
        return [m.get(fy) for fy in fys[-4:]]

    revenue_abs = _abs_series(pl_maps.get("sales", {}))
    _cogs_abs = _abs_series(pl_maps.get("cogs", {}))
    gross_profit_abs = [
        (s - c) if (s is not None and c is not None) else None
        for s, c in zip(revenue_abs, _cogs_abs)
    ]
    ebit_abs = _abs_series(pl_maps.get("operating profit", {}))
    interest_abs = _abs_series(pl_maps.get("interest", {}))
    tax_abs = _abs_series(pl_maps.get("tax", {}))
    pretax_abs = _abs_series(pl_maps.get("profit before tax", {}))
    net_income_abs = _abs_series(pl_maps.get("net profit", {}))
    total_assets_abs = _abs_series(bs_maps.get("total assets", {}))
    equity_abs = _abs_series(bs_maps.get("reserves", {}))
    cash_abs = _abs_series(bs_maps.get("cash equivalents", {}))
    debt_abs_series = _abs_series(total_debt)
    depreciation_abs = _abs_series(pl_maps.get("depreciation", {}))
    cfo_abs = _abs_series(cf_maps.get("cash from operating activity", {}))
    
    capex_raw_abs = _abs_series(cf_maps.get("fixed assets purchased", {}))
    capex_abs = [abs(v) if v is not None else None for v in capex_raw_abs]

    # Working capital change: CFO - net_income - depreciation (residual method)
    wc_change_abs = []
    for o, ni, d in zip(cfo_abs, net_income_abs, depreciation_abs):
        if o is not None and ni is not None and d is not None:
            wc_change_abs.append(o - ni - d)
        else:
            wc_change_abs.append(None)

    # FCF = CFO - capex
    fcf_abs = []
    for o, cx in zip(cfo_abs, capex_abs):
        if o is not None and cx is not None:
            fcf_abs.append(o - cx)
        else:
            fcf_abs.append(None)

    # ------------------------------------------------------------------
    # 6. Price, shares, market cap
    # ------------------------------------------------------------------
    trailing_pe = None
    dividend_yield = 0.0

    try:
        if globals().get("yf") is not None:
            yf_ticker = globals()["yf"].Ticker(ticker_upper)
            info = yf_ticker.info
            trailing_pe = _safe_float(info.get("trailingPE"))
            div_yield = _safe_float(info.get("dividendYield"))
            dividend_yield = div_yield if div_yield is not None else 0.0
    except Exception as e:
        logger.warning(f"yfinance info unavailable for {ticker_upper}: {e}")

    # Shares: SEC XBRL EntityCommonStockSharesOutstanding (primary)
    shares_outstanding = None
    if shares_map:                                  # {fy: value} parsed from the dei concept
        _vals = [v for v in shares_map.values() if v]
        shares_outstanding = _vals[-1] if _vals else None
    if not shares_outstanding:
        try:
            import yfinance as yf
            shares_outstanding = _safe_float(getattr(yf.Ticker(ticker_upper).fast_info, "shares", None))
        except Exception:
            shares_outstanding = None

    current_price = _us_price(ticker_upper)
    market_cap = (current_price * shares_outstanding
                  if (current_price and shares_outstanding) else None)

    # Historical shares: 4-element list (use shares_outstanding for all, like screener)
    historical_shares = [shares_outstanding] * 4 if shares_outstanding else [None] * 4

    # Latest debt (absolute USD)
    latest_debt = total_debt.get(fys[-1], 0.0) if fys else 0.0

    # book_value_per_share
    last_equity = equity_abs[-1] if equity_abs else None
    book_value_per_share = (
        (last_equity / shares_outstanding)
        if last_equity is not None and shares_outstanding and shares_outstanding > 0
        else 0.0
    )

    # ------------------------------------------------------------------
    # 7. Assemble the fin dict (screener contract)
    # ------------------------------------------------------------------
    _HIST_NUMERIC_KEYS = (
        "revenue", "gross_profit", "ebit", "interest_expense",
        "tax_provision", "pretax_income", "net_income",
        "total_assets", "total_equity", "cash", "debt",
        "capex", "depreciation", "working_capital_change", "fcf",
        "historical_shares",
    )

    fin = {}
    fin["ticker"] = ticker_upper
    fin["source"] = "sec_edgar"

    # Statements block (years_annual is up to 10 years; row values in USD/1e7)
    fin["statements"] = {
        "years_annual": years_annual,
        "quarters": [],
        "annual": {
            "profit_loss": pl_stmt,
            "balance_sheet": bs_stmt,
            "cash_flow": cf_stmt,
        },
        "quarterly": {"profit_loss": {}},
        "ratios": ratios_stmt,
        "shareholding": {},
        "top_ratios": {},
        "peers": [],
    }

    # Years (4-element, like screener's fin["years"])
    fin["years"] = years_annual[-4:] if len(years_annual) >= 4 else years_annual

    # Top-level legacy arrays (absolute USD)
    fin["revenue"] = revenue_abs
    fin["gross_profit"] = gross_profit_abs
    fin["ebit"] = ebit_abs
    fin["interest_expense"] = [abs(v) if v is not None else None for v in interest_abs]
    fin["tax_provision"] = tax_abs
    fin["pretax_income"] = pretax_abs
    fin["net_income"] = net_income_abs
    fin["total_assets"] = total_assets_abs
    fin["total_equity"] = equity_abs
    fin["cash"] = cash_abs
    fin["debt"] = debt_abs_series   # per-year absolute-USD list (screener contract; lenses iterate it)
    fin["capex"] = capex_abs
    fin["depreciation"] = depreciation_abs
    fin["working_capital_change"] = wc_change_abs
    fin["fcf"] = fcf_abs
    fin["historical_shares"] = historical_shares

    # Price / market / metadata
    fin["current_price"] = current_price
    fin["market_cap"] = market_cap
    fin["shares_outstanding"] = shares_outstanding
    fin["trailing_pe"] = trailing_pe
    fin["dividend_yield"] = dividend_yield
    fin["stock_beta"] = 1.0
    fin["recommendation_mean"] = None
    fin["insider_ownership"] = 0.0
    fin["book_value_per_share"] = book_value_per_share

    # Debt top-level (absolute USD, same convention as market_cap)
    fin["debt_latest"] = latest_debt  # raw USD for WACC debt

    # Sector / industry / flags
    fin["scraped_sector"] = scraped_sector
    fin["scraped_broad_industry"] = None
    fin["scraped_industry"] = scraped_industry
    fin["is_bank"] = is_bank
    fin["is_financial"] = is_financial

    # Normalize None → 0.0 in legacy numeric arrays
    for k in _HIST_NUMERIC_KEYS:
        if k in fin and isinstance(fin[k], list):
            fin[k] = [(v if v is not None else 0.0) for v in fin[k]]

    # Cache separately (price has shorter TTL)
    price_dict = {"current_price": current_price}
    cache.set_json(cache_key_fin, fin)
    cache.set_json(cache_key_price, price_dict)

    return fin


def fetch_edgar_filings_text(ticker: str) -> list:
    """Pull the latest 10-K for a US ticker via edgartools and extract qualitative sections.

    Returns a list with one element: {"filename": str, "text": str}
    The text contains MD&A + Risk Factors + Business sections (or truncated full text if
    those section accessors are unavailable). Returns [] on any failure.

    The result is cached for 7 days so repeat calls are instant (offline).
    """
    key = f"edgar_filing_text_{ticker.upper()}.json"
    cached = cache.get_json(key, 7 * 24 * 3600)
    if cached is not None:
        return cached

    out = []
    try:
        if set_identity is not None:
            set_identity(_EDGAR_IDENTITY)
        if Company is None:
            raise ImportError("edgartools not installed")

        filing = Company(ticker.upper()).get_filings(form="10-K").latest()
        if filing is None:
            raise ValueError(f"No 10-K found for {ticker}")

        parts = []

        # Try structured section accessors first
        try:
            tenk = filing.obj()
            # edgartools TenK object may expose these under different attribute names
            section_candidates = [
                # (attribute_name, section_label)
                ("management_discussion_and_analysis", "MD&A"),
                ("management_discussion", "MD&A"),
                ("mda", "MD&A"),
                ("risk_factors", "Risk Factors"),
                ("business", "Business"),
                ("item_1", "Business"),
                ("item_1a", "Risk Factors"),
                ("item_7", "MD&A"),
                ("item_7a", "Quantitative Disclosures"),
            ]
            seen_labels = set()
            for attr, label in section_candidates:
                if label in seen_labels:
                    continue
                sec = getattr(tenk, attr, None)
                if sec:
                    text_sec = str(sec).strip()
                    if text_sec:
                        parts.append(f"## {label}\n\n{text_sec}")
                        seen_labels.add(label)
        except Exception as sec_err:
            logger.debug(f"Structured 10-K section extraction failed for {ticker}: {sec_err}")

        # Fallback: full filing text, truncated
        if not parts:
            try:
                if hasattr(filing, "text"):
                    full = filing.text()
                elif hasattr(filing, "markdown"):
                    full = filing.markdown()
                else:
                    full = str(filing)
            except Exception:
                full = ""
            if full and full.strip():
                parts.append(full[:150_000])

        text = "\n\n".join(p for p in parts if p)[:200_000]
        if text.strip():
            fdate = getattr(filing, "filing_date", "") or ""
            out = [{"filename": f"{ticker.upper()} 10-K {fdate}".strip(), "text": text}]

    except Exception as e:
        logger.warning(f"fetch_edgar_filings_text({ticker}) failed: {e}")
        out = []

    cache.set_json(key, out)
    return out

def fetch_edgar_8k_shareholder_letters(ticker: str, n: int = 2) -> list:
    """Pull recent 8-K Exhibit 99.1 shareholder letters for a US ticker via edgartools."""
    key = f"edgar_8k_ex99_{ticker.upper()}.json"
    cached = cache.get_json(key, 7 * 24 * 3600)
    if cached is not None:
        return cached

    out = []
    try:
        if set_identity is not None:
            set_identity(_EDGAR_IDENTITY)
        if Company is None:
            raise ImportError("edgartools not installed")

        filings = Company(ticker.upper()).get_filings(form="8-K")
        if not filings:
            raise ValueError(f"No 8-K found for {ticker}")

        for filing in list(filings)[:25]:
            if len(out) >= n:
                break
                
            ex_text = None
            try:
                eightk = filing.obj()
                pr = getattr(eightk, "press_releases", None)
                if pr:
                    try:
                        if hasattr(pr, "text"):
                            ex_text = pr.text()
                        elif hasattr(pr, "__len__") and len(pr) > 0 and hasattr(pr[0], "text"):
                            ex_text = pr[0].text()
                    except Exception:
                        pass
            except Exception:
                pass
                
            if not ex_text:
                try:
                    attachments = getattr(filing, "attachments", [])
                    for att in attachments:
                        dt = (getattr(att, "document_type", "") or "").upper()
                        desc = (getattr(att, "description", "") or "").upper()
                        if dt.startswith("EX-99") or dt.startswith("99.1") or desc.startswith("EX-99") or desc.startswith("99.1"):
                            try:
                                ex_text = att.text() if hasattr(att, "text") else str(att)
                            except Exception:
                                pass
                            break
                except Exception:
                    pass
            
            if ex_text and len(ex_text) > 2000:
                fdate = getattr(filing, "filing_date", "") or ""
                out.append({
                    "filename": f"{ticker.upper()} 8-K Ex-99.1 {fdate}".strip(),
                    "text": ex_text[:200_000]
                })

    except Exception as e:
        logger.warning(f"fetch_edgar_8k_shareholder_letters({ticker}) failed: {e}")
        out = []

    cache.set_json(key, out)
    return out
