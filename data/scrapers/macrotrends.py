"""
MacroTrends financial data adapter for Sidwell.

CONTRACT: Returns the IDENTICAL dict shape as data/scrapers/stockanalysis.py /
screener.py so the engine, lenses, and workbook work unchanged.

UNIT CONVENTION (must match engine expectations):
  - fin["statements"]["annual"][*] row values = USD / 1e7
    (statement rows are in USD millions on MacroTrends; divide by 1e7 to match scale)
  - top-level legacy arrays (revenue, net_income, ...) = absolute USD (value * 1e6)
  - market_cap = absolute USD
  - current_price = USD per share
  - shares_outstanding = absolute count (value in millions * 1e6)

SECTOR / INDUSTRY: Reuses edgar._sic_to_sector_industry() via lightweight
SEC ticker->CIK->SIC lookup (no edgartools dependency).
"""

import re
import json
import logging
import requests
import time
import random
from typing import Optional

from data import cache
from data.scrapers.edgar import _us_price, _sic_to_sector_industry, _BANK_SIC_RANGE, _FINANCIAL_SIC_RANGE, _is_financial_sector

logger = logging.getLogger(__name__)

TTL_FINANCIALS = 7 * 24 * 3600

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.macrotrends.net/",
    "Upgrade-Insecure-Requests": "1",
    "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1"
}

_SEC_IDENTITY = "Sidwell research contact@example.com"
_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


def _parse_float(val) -> Optional[float]:
    """Convert a MacroTrends string value to float; return None for empty/null."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if s in ("-", "", "N/A", "NA", "null", "None"):
        return None
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def _extract_originaldata(html: str) -> list:
    """Extract the embedded originalData JSON array from a MacroTrends HTML page."""
    m = re.search(r'var originalData = (\[.*?\]);', html, re.DOTALL)
    if not m:
        return []
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return []


def _build_row_index(rows: list) -> dict:
    """
    Build a dict { clean_field_name -> row_dict } from the originalData list.
    HTML tags are stripped from field_name.
    """
    idx = {}
    for row in rows:
        raw = row.get("field_name", "")
        clean = re.sub(r"<[^<]+?>", "", raw).strip()
        if clean:
            idx[clean] = row
    return idx


def _year_values(row: dict, years_axis: list) -> list:
    """
    Return a list aligned to years_axis, where each element is the float value
    for that year from the row dict (keyed as 'YYYY-MM-DD' or just 'YYYY-12-31').
    Returns None where the key is absent or the value is empty.
    """
    result = []
    for yr in years_axis:
        # MacroTrends uses 'YYYY-12-31' for Dec FY; for non-Dec FY the key varies,
        # but the task says use key[:4] == yr for the year. We find the matching key.
        # Simplest approach: just try 'YYYY-12-31' first, then scan.
        key_dec = f"{yr}-12-31"
        if key_dec in row:
            result.append(_parse_float(row[key_dec]))
        else:
            # Find any key whose first 4 chars equal yr
            found = None
            for k, v in row.items():
                if len(k) >= 4 and k[:4] == yr and k[4:5] == "-":
                    found = _parse_float(v)
                    break
            result.append(found)
    return result


def _get_sic_from_sec(ticker: str):
    """
    Lightweight CIK + SIC lookup via SEC's company_tickers.json + submissions endpoint.
    Returns (sic: int|None, sic_description: str|None).
    No edgartools dependency.
    """
    t = ticker.upper()
    try:
        r = requests.get(
            _COMPANY_TICKERS_URL,
            headers={"User-Agent": _SEC_IDENTITY},
            timeout=15,
        )
        r.raise_for_status()
        tickers_data = r.json()
        cik = None
        for entry in tickers_data.values():
            if entry.get("ticker", "").upper() == t:
                cik = entry["cik_str"]
                break
        if cik is None:
            return None, None
        # Fetch submissions for SIC
        r2 = requests.get(
            f"https://data.sec.gov/submissions/CIK{cik:010d}.json",
            headers={"User-Agent": _SEC_IDENTITY},
            timeout=15,
        )
        r2.raise_for_status()
        sub = r2.json()
        sic_raw = sub.get("sic")
        sic_desc = sub.get("sicDescription")
        sic = int(sic_raw) if sic_raw is not None else None
        return sic, sic_desc
    except Exception as e:
        logger.warning(f"SEC SIC lookup failed for {ticker}: {e}")
        return None, None


# ---------------------------------------------------------------------------
# Phase-3 gap-filler: unified extend_series_via_ratio helper
# ---------------------------------------------------------------------------

def extend_series_via_ratio(
    native_by_year: dict,
    driver_by_year: dict,
    years_axis: list,
    ratio_bounds: tuple = (None, None),
) -> tuple:
    """
    Build a full series aligned to ``years_axis`` by using stockanalysis-native
    values where present and ratio-anchored backfill (to a MacroTrends 15y driver)
    elsewhere.

    Parameters
    ----------
    native_by_year : {year:int -> float}  stockanalysis overlap (~5y); may be sparse
    driver_by_year : {year:int -> float}  MacroTrends 15y driver (sales/cogs/LT-debt/borrowings)
    ratio_bounds   : (lo, hi) clamp for the pure ratio r_bar (None = unclamped)

    Math
    ----
    overlap = years in BOTH native and driver with driver(t) != 0
    r(t)    = native(t) / driver(t)                         per overlap year
    r_bar   = clamp(mean(r over overlap), *ratio_bounds)    representative ratio
    full(t) = native(t)           if t in native_by_year
            = driver(t) * r_bar   elif t in driver_by_year  (backfill)
            = None                else

    Returns
    -------
    (full_series_aligned_to_years_axis, meta)
    meta keys: native_years, backfilled_years, ratio, n_overlap, caveat.

    Pure function: no I/O, no side effects.
    """
    lo, hi = ratio_bounds

    # Compute per-year ratios on the overlap
    overlap_ratios = []
    for yr in years_axis:
        if yr in native_by_year and yr in driver_by_year:
            drv = driver_by_year[yr]
            if drv and drv != 0.0:
                overlap_ratios.append(native_by_year[yr] / drv)

    meta = {
        "native_years":     sorted(y for y in years_axis if y in native_by_year),
        "backfilled_years": [],
        "ratio":            None,
        "n_overlap":        len(overlap_ratios),
        "caveat":           "",
    }

    if not overlap_ratios:
        # No overlap: pass native values through, no backfill possible
        meta["caveat"] = (
            "No overlap between native and driver; native years passed through, "
            "no backfill applied."
        )
        result = [native_by_year.get(yr) for yr in years_axis]
        return result, meta

    r_bar = sum(overlap_ratios) / len(overlap_ratios)
    if lo is not None:
        r_bar = max(lo, r_bar)
    if hi is not None:
        r_bar = min(hi, r_bar)
    meta["ratio"] = r_bar

    result = []
    backfilled = []
    for yr in years_axis:
        if yr in native_by_year:
            result.append(native_by_year[yr])
        elif yr in driver_by_year and driver_by_year[yr] is not None:
            val = driver_by_year[yr] * r_bar
            result.append(val)
            backfilled.append(yr)
        else:
            result.append(None)

    meta["backfilled_years"] = backfilled
    meta["caveat"] = (
        f"Ratio-anchored: r_bar={r_bar:.4f} (n_overlap={len(overlap_ratios)}), "
        f"{len(backfilled)} years backfilled."
    )
    return result, meta


def _extract_sa_row_mm(sa_fin: dict, stmt: str, key: str) -> dict:
    """
    Pull a statement row from the stockanalysis fin dict as {year_int -> float_mm}.

    stmt   : "profit_loss" | "balance_sheet" | "cash_flow"
    key    : the key inside that statement block (e.g. "interest", "borrowings")

    Statement values are stored at (v * 1e6) / 1e7 = v / 10 in scaled form.
    Recover millions: mm = scaled_val * 10.
    """
    sa_years = sa_fin.get("statements", {}).get("years_annual", [])
    row = (
        sa_fin.get("statements", {})
              .get("annual", {})
              .get(stmt, {})
              .get(key, [])
    )
    result = {}
    for i, yr_str in enumerate(sa_years):
        if i >= len(row):
            break
        val = row[i]
        if val is not None:
            result[int(yr_str)] = val * 10.0   # undo /10 scale
    return result


def _mt_row_mm(fin: dict, stmt: str, key: str, years_axis: list) -> dict:
    """
    Pull a MacroTrends statement row from the already-assembled fin dict as
    {year_int -> float_mm}.

    years_axis : list of str 'YYYY' (the fin dict's years_annual).
    Returns only entries where the value is not None.
    """
    row = (
        fin.get("statements", {})
           .get("annual", {})
           .get(stmt, {})
           .get(key, [])
    )
    result = {}
    for i, yr_str in enumerate(years_axis):
        if i >= len(row):
            break
        val = row[i]
        if val is not None:
            result[int(yr_str)] = val * 10.0   # undo /10 scale
    return result


# Config for the 4 gap items; processed in order (borrowings before interest
# so the completed total-debt series can be used as interest's driver).
_GAP_ITEMS = [
    {
        # 1. borrowings: SA Total Debt anchors MT Long Term Debt.
        #    force_complete: MacroTrends already populates this key with LT-debt
        #    ONLY, so the generic skip-if-populated guard would wrongly skip it.
        #    We must always run the completion (LT -> total) unless SA has no data.
        #    ratio_bounds=(1.0, 4.0): Total >= LT so ratio >= 1; cap at 4x.
        "target_stmt":   "balance_sheet",
        "target_key":    "borrowings",
        "sa_stmt":       "balance_sheet",
        "sa_key":        "borrowings",          # SA maps "Total Debt" -> "borrowings"
        "driver_stmt":   "balance_sheet",
        "driver_key":    "borrowings",          # MT "Long Term Debt" (LT only, Phase-1)
        "ratio_bounds":  (1.0, 4.0),
        "force_complete": True,
        "refresh_toplevel": ["debt", "debt_latest"],
    },
    {
        # 2. interest expense: SA Interest Expense anchors completed borrowings driver.
        #    stockanalysis reports interest NEGATIVE; we abs the native so the stored
        #    series is POSITIVE -- the screener/contract convention, and what the
        #    lenses assume (they guard with `if interest > 0`).
        #    ratio_bounds=(0.0001, 0.20): effective rate 0%-20% (positive).
        "target_stmt":   "profit_loss",
        "target_key":    "interest",
        "sa_stmt":       "profit_loss",
        "sa_key":        "interest",
        "abs_native":    True,
        "driver_stmt":   "balance_sheet",
        "driver_key":    "borrowings",          # completed total debt from step 1
        "ratio_bounds":  (0.0001, 0.20),
        "refresh_toplevel": ["interest_expense"],
    },
    {
        # 3. trade receivables: SA Accounts Receivable anchored to sales
        "target_stmt":   "balance_sheet",
        "target_key":    "trade receivables",
        "sa_stmt":       "balance_sheet",
        "sa_key":        "trade receivables",
        "driver_stmt":   "profit_loss",
        "driver_key":    "sales",
        "ratio_bounds":  (0.0, 1.0),
        "refresh_toplevel": [],
    },
    {
        # 4. trade payables: SA Accounts Payable anchored to COGS
        "target_stmt":   "balance_sheet",
        "target_key":    "trade payables",
        "sa_stmt":       "balance_sheet",
        "sa_key":        "trade payables",
        "driver_stmt":   "profit_loss",
        "driver_key":    "cogs",
        "ratio_bounds":  (0.0, 2.0),
        "refresh_toplevel": [],
    },
]


def _merge_stockanalysis_gaps(mt_fin: dict, ticker: str) -> dict:
    """
    Phase-3 gap-filler: for each configured gap item, if the MacroTrends native
    series is absent/empty, fetch stockanalysis ONCE (lazy, cached) and run
    extend_series_via_ratio() to produce a full 15-year series.

    After all items are filled, recompute debtor days, days payable, and CCC.

    Modifies mt_fin in place and returns it. On any error, returns the un-merged
    dict (degrade to MacroTrends-only behavior).

    Writes mt_fin["reconstruction_meta"] = {key: meta, ...}.
    """
    try:
        from data.scrapers.stockanalysis import fetch_stockanalysis_financials

        years_annual = mt_fin.get("statements", {}).get("years_annual", [])
        if not years_annual:
            return mt_fin

        years_axis = [int(y) for y in years_annual]

        # Determine whether we need stockanalysis at all
        needs_sa = False
        for item in _GAP_ITEMS:
            row = (
                mt_fin.get("statements", {})
                      .get("annual", {})
                      .get(item["target_stmt"], {})
                      .get(item["target_key"])
            )
            if row is None or not any(v is not None for v in row):
                needs_sa = True
                break

        sa_fin = fetch_stockanalysis_financials(ticker) if needs_sa else None

        reconstruction_meta = {}

        for item in _GAP_ITEMS:
            t_stmt = item["target_stmt"]
            t_key  = item["target_key"]

            force_complete = item.get("force_complete", False)
            stmt_block = mt_fin["statements"]["annual"][t_stmt]
            existing = stmt_block.get(t_key, [])

            # Skip if MacroTrends native is already populated -- UNLESS the item is
            # present-but-incomplete (force_complete, e.g. borrowings = LT-debt only),
            # which must always be completed to the stockanalysis total.
            if (not force_complete) and any(v is not None for v in existing):
                reconstruction_meta[t_key] = {
                    "native_years":     [],
                    "backfilled_years": [],
                    "ratio":            None,
                    "n_overlap":        0,
                    "caveat":           "Native MacroTrends value used; no gap-fill needed.",
                }
                continue

            if sa_fin is None:
                reconstruction_meta[t_key] = {
                    "native_years":     [],
                    "backfilled_years": [],
                    "ratio":            None,
                    "n_overlap":        0,
                    "caveat":           "stockanalysis unavailable; left empty.",
                }
                continue

            # Native series from stockanalysis (in USD millions)
            native_mm = _extract_sa_row_mm(sa_fin, item["sa_stmt"], item["sa_key"])

            # Some sources report a field with the opposite sign (e.g. stockanalysis
            # interest is negative); store it positive to match the contract.
            if item.get("abs_native"):
                native_mm = {y: abs(v) for y, v in native_mm.items()}

            # Driver series from the CURRENT mt_fin (may be a just-filled item
            # from a prior iteration - e.g. borrowings for the interest step)
            driver_mm = _mt_row_mm(
                mt_fin, item["driver_stmt"], item["driver_key"], years_annual
            )

            full_mm, meta = extend_series_via_ratio(
                native_mm, driver_mm, years_axis, item["ratio_bounds"]
            )

            # Never wipe an existing series (e.g. borrowings = LT-debt) if the
            # gap-fill produced nothing usable because stockanalysis had no data.
            if force_complete and not any(v is not None for v in full_mm):
                reconstruction_meta[t_key] = {
                    "native_years":     [],
                    "backfilled_years": [],
                    "ratio":            None,
                    "n_overlap":        0,
                    "caveat":           "stockanalysis had no data; kept MacroTrends native series.",
                }
                continue

            # Write back scaled /10
            stmt_block[t_key] = [v / 10.0 if v is not None else None for v in full_mm]
            reconstruction_meta[t_key] = meta

            logger.info(
                "_merge_stockanalysis_gaps %s: %s n_overlap=%d backfilled=%d",
                ticker, t_key, meta["n_overlap"], len(meta["backfilled_years"]),
            )

            # Refresh top-level legacy fields that depend on this item
            for field in item.get("refresh_toplevel", []):
                _refresh_toplevel(mt_fin, field, t_stmt, t_key, years_annual)

        # -------------------------------------------------------------------
        # Recompute working-capital day ratios (full 15y, scale-invariant)
        # -------------------------------------------------------------------
        pl     = mt_fin["statements"]["annual"]["profit_loss"]
        bs_all = mt_fin["statements"]["annual"]["balance_sheet"]
        ratios = mt_fin["statements"]["ratios"]
        sales_s = pl.get("sales", [])
        cogs_s  = pl.get("cogs", [])
        ar_s    = bs_all.get("trade receivables", [])
        ap_s    = bs_all.get("trade payables", [])
        inv_s   = bs_all.get("inventories", [])

        ratios["debtor days"] = [
            (ar / sl * 365.0) if (ar is not None and sl and sl != 0) else None
            for ar, sl in zip(ar_s, sales_s)
        ]
        ratios["days payable"] = [
            (ap / cg * 365.0) if (ap is not None and cg and cg > 0) else None
            for ap, cg in zip(ap_s, cogs_s)
        ]
        ratios["inventory days"] = [
            (inv / cg * 365.0) if (inv is not None and cg and cg > 0) else None
            for inv, cg in zip(inv_s, cogs_s)
        ]
        ratios["cash conversion cycle"] = [
            (d + i - p)
            if (d is not None and i is not None and p is not None)
            else None
            for d, i, p in zip(
                ratios["debtor days"],
                ratios["inventory days"],
                ratios["days payable"],
            )
        ]

        mt_fin["reconstruction_meta"] = reconstruction_meta
        return mt_fin

    except Exception as exc:
        logger.warning(
            "_merge_stockanalysis_gaps(%s) failed: %s; returning Phase-1 dict unchanged",
            ticker, exc,
        )
        return mt_fin


def _refresh_toplevel(fin: dict, field: str, stmt: str, key: str, years_annual: list) -> None:
    """
    Refresh a top-level legacy array (absolute USD, last 4 years) or scalar
    after a gap-fill has written into the statements block.
    """
    row_scaled = (
        fin.get("statements", {})
           .get("annual", {})
           .get(stmt, {})
           .get(key, [])
    )
    # Convert scaled values back to absolute USD (millions)
    row_mm = [v * 10.0 if v is not None else None for v in row_scaled]

    if field == "debt":
        last4 = row_mm[-4:] if len(row_mm) >= 4 else row_mm
        fin["debt"] = [(v * 1e6) if v is not None else 0.0 for v in last4]
    elif field == "debt_latest":
        last_val = next((v for v in reversed(row_mm) if v is not None), None)
        fin["debt_latest"] = (last_val * 1e6) if last_val is not None else 0.0
    elif field == "interest_expense":
        # SA interest comes in negative (expense convention); take abs for the
        # top-level array so the engine sees a positive interest cost.
        last4 = row_mm[-4:] if len(row_mm) >= 4 else row_mm
        fin["interest_expense"] = [
            (abs(v) * 1e6) if v is not None else 0.0 for v in last4
        ]


def fetch_macrotrends_financials(ticker: str) -> dict | None:
    """
    Fetch US company financials from MacroTrends and return the Sidwell standard
    financials dict (identical shape to stockanalysis.py / edgar.py / screener.py).

    Returns None on any failure so the caller can fall back to the next source.
    """
    t = ticker.upper()
    cache_key = f"financials_macrotrends_{t}.json"
    cached = cache.get_json(cache_key, TTL_FINANCIALS)
    if cached:
        logger.info(f"Loaded {t} from macrotrends cache.")
        return cached

    slug = t.lower()  # MacroTrends auto-redirects wrong slugs to the correct page
    urls = {
        "income":   f"https://www.macrotrends.net/stocks/charts/{t}/{slug}/income-statement",
        "balance":  f"https://www.macrotrends.net/stocks/charts/{t}/{slug}/balance-sheet",
        "cashflow": f"https://www.macrotrends.net/stocks/charts/{t}/{slug}/cash-flow-statement",
    }

    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        
        # Warm the session to get Cloudflare cookies
        try:
            session.get("https://www.macrotrends.net/", timeout=15)
        except Exception:
            pass  # Best effort warmup
            
        pages = {}
        for key, url in urls.items():
            success = False
            base_sleeps = [0.5, 1.5, 3.0]
            for attempt in range(3):
                try:
                    r = session.get(url, timeout=30, allow_redirects=True)
                    if r.status_code in (403, 429) or r.status_code >= 500:
                        raise requests.exceptions.RequestException(f"Status {r.status_code}")
                    r.raise_for_status()
                    pages[key] = r.text
                    success = True
                    break
                except requests.exceptions.RequestException as e:
                    if attempt < 2:
                        sleep_time = base_sleeps[attempt] * (1.0 + random.random() * 0.5)
                        logger.debug(f"macrotrends fetch {key} failed ({e}), retrying in {sleep_time:.2f}s")
                        time.sleep(sleep_time)
                    else:
                        logger.warning(f"macrotrends fetch {key} failed after 3 attempts: {e}")
                        
            if not success:
                return None

        inc_rows = _extract_originaldata(pages["income"])
        bal_rows = _extract_originaldata(pages["balance"])
        cf_rows  = _extract_originaldata(pages["cashflow"])

        if not inc_rows or not bal_rows or not cf_rows:
            logger.warning(f"macrotrends: no originalData found for {t}")
            return None

        inc = _build_row_index(inc_rows)
        bal = _build_row_index(bal_rows)
        cf  = _build_row_index(cf_rows)

        # ---------------------------------------------------------------
        # Build the unified year axis from Revenue / Net Income / Total Assets
        # (union of all years seen, sorted ascending, as 'YYYY' strings)
        # ---------------------------------------------------------------
        def _collect_years(row_dict: dict) -> set:
            return {k[:4] for k in row_dict.keys() if len(k) >= 4 and k[:4].isdigit() and k[4:5] == "-"}

        year_set = set()
        for field in ("Revenue", "Net Income", "Total Assets"):
            src = inc if field in inc else bal
            if field in src:
                year_set |= _collect_years(src[field])
        years_annual = sorted(year_set)  # ascending list of 'YYYY' strings

        if not years_annual:
            logger.warning(f"macrotrends: no year columns found for {t}")
            return None

        # ---------------------------------------------------------------
        # Row helpers
        # ---------------------------------------------------------------
        def _row(index: dict, field_name: str) -> list:
            """Aligned list for years_annual, None where missing."""
            if field_name not in index:
                return [None] * len(years_annual)
            return _year_values(index[field_name], years_annual)

        def _scale_row(vals: list) -> list:
            """Statement scale: (v * 1e6) / 1e7 = v / 10.  None preserved."""
            return [(v * 1e6) / 1e7 if v is not None else None for v in vals]

        def _abs_last4(vals: list) -> list:
            """Top-level legacy arrays: absolute USD (v * 1e6), last 4 years."""
            raw = vals[-4:] if len(vals) >= 4 else vals
            return [(v * 1e6) if v is not None else None for v in raw]

        # ---------------------------------------------------------------
        # Income statement rows
        # ---------------------------------------------------------------
        rev_row      = _row(inc, "Revenue")
        cogs_row     = _row(inc, "Cost Of Goods Sold")
        opex_row     = _row(inc, "Operating Expenses")
        opinc_row    = _row(inc, "Operating Income")
        other_inc_row= _row(inc, "Other Income")
        pretax_row   = _row(inc, "Pre-Tax Income")
        tax_row      = _row(inc, "Income Taxes")
        netinc_row   = _row(inc, "Net Income")
        shares_row   = _row(inc, "Shares Outstanding")   # in millions

        # Depreciation from cash flow (also written into profit_loss per contract)
        depr_row     = _row(cf, "Total Depreciation And Amortization - Cash Flow")

        # Computed: tax %
        tax_pct_row = []
        for tax, pt in zip(tax_row, pretax_row):
            if pt and pt != 0 and tax is not None:
                tax_pct_row.append(tax / pt * 100.0)
            else:
                tax_pct_row.append(None)

        # Dividends (for payout %)
        div_row = _row(cf, "Common Stock Dividends Paid")

        # Computed: dividend payout %
        div_pct_row = []
        for div, ni in zip(div_row, netinc_row):
            if ni is not None and ni > 0 and div is not None:
                div_pct_row.append(abs(div) / ni * 100.0)
            else:
                div_pct_row.append(0.0)

        pl_stmt = {
            "sales":              _scale_row(rev_row),
            "cogs":               _scale_row(cogs_row),
            "expenses":           _scale_row(opex_row),
            "operating profit":   _scale_row(opinc_row),
            "other income":       _scale_row(other_inc_row),
            "profit before tax":  _scale_row(pretax_row),
            "tax":                _scale_row(tax_row),
            "net profit":         _scale_row(netinc_row),
            "depreciation":       _scale_row(depr_row),   # also in IS per contract
            "tax %":              tax_pct_row,             # ratio, NOT scaled
            "dividend payout %":  div_pct_row,            # ratio, NOT scaled
        }

        # ---------------------------------------------------------------
        # Balance sheet rows
        # ---------------------------------------------------------------
        cash_row     = _row(bal, "Cash On Hand")
        recv_row     = _row(bal, "Receivables")
        inv_row      = _row(bal, "Inventory")
        oca_row      = _row(bal, "Other Current Assets")
        fa_row       = _row(bal, "Property, Plant, And Equipment")
        lt_inv_row   = _row(bal, "Long-Term Investments")
        ta_row       = _row(bal, "Total Assets")
        tl_row       = _row(bal, "Total Liabilities")
        ltd_row      = _row(bal, "Long Term Debt")         # LT only (Phase 1 caveat)
        onl_row      = _row(bal, "Other Non-Current Liabilities")
        eq_row       = _row(bal, "Share Holder Equity")
        tca_row      = _row(bal, "Total Current Assets")
        tcl_row      = _row(bal, "Total Current Liabilities")

        bs_stmt = {
            "cash equivalents":       _scale_row(cash_row),
            "trade receivables":      _scale_row(recv_row),
            "inventories":            _scale_row(inv_row),
            "other asset items":      _scale_row(oca_row),
            "fixed assets":           _scale_row(fa_row),
            "investments":            _scale_row(lt_inv_row),
            "total assets":           _scale_row(ta_row),
            "total liabilities":      _scale_row(tl_row),
            "borrowings":             _scale_row(ltd_row),  # LT only; Phase 2 adds current
            "other liability items":  _scale_row(onl_row),
            "reserves":               _scale_row(eq_row),
            "equity capital":         [None] * len(years_annual),  # not split out
        }

        # ---------------------------------------------------------------
        # Cash flow rows
        # ---------------------------------------------------------------
        cfo_row      = _row(cf, "Cash Flow From Operating Activities")
        capex_raw_row= _row(cf, "Net Change In Property, Plant, And Equipment")  # negative = spend
        cfi_row      = _row(cf, "Cash Flow From Investing Activities")
        cff_row      = _row(cf, "Cash Flow From Financial Activities")
        recv_ch_row  = _row(cf, "Change In Accounts Receivable")
        inv_ch_row   = _row(cf, "Change In Inventories")
        pay_ch_row   = _row(cf, "Change In Accounts Payable")
        wc_total_row = _row(cf, "Total Change In Assets/Liabilities")
        debt_net_row = _row(cf, "Debt Issuance/Retirement Net - Total")

        # capex: abs of the PPE net change (negative = outflow)
        capex_row = [abs(v) if v is not None else None for v in capex_raw_row]

        # Split debt net into proceeds (positive part) and repayments (abs of negative)
        proceeds_row  = [max(v, 0.0) if v is not None else None for v in debt_net_row]
        repayment_row = [abs(min(v, 0.0)) if v is not None else None for v in debt_net_row]

        cf_stmt = {
            "cash from operating activity":  _scale_row(cfo_row),
            "fixed assets purchased":         _scale_row(capex_row),
            "cash from investing activity":   _scale_row(cfi_row),
            "cash from financing activity":   _scale_row(cff_row),
            "depreciation":                   _scale_row(depr_row),
            "receivables":                    _scale_row(recv_ch_row),
            "inventory":                      _scale_row(inv_ch_row),
            "payables":                       _scale_row(pay_ch_row),
            "working capital changes":        _scale_row(wc_total_row),
            "proceeds from borrowings":       _scale_row(proceeds_row),
            "repayment of borrowings":        _scale_row(repayment_row),
        }

        # ---------------------------------------------------------------
        # Ratios block (raw / ratio values, NOT 1e7-scaled)
        # ---------------------------------------------------------------
        # working capital days = (TCA - Cash) - TCL / Revenue * 365
        wc_days = []
        for i in range(len(years_annual)):
            tca = tca_row[i]
            tcl = tcl_row[i]
            csh = cash_row[i] if cash_row[i] is not None else 0.0
            rev = rev_row[i]
            if tca is not None and tcl is not None and rev:
                op_nwc = (tca - csh) - tcl
                wc_days.append(op_nwc / rev * 365.0)
            else:
                wc_days.append(None)

        # debtor days = Receivables / Revenue * 365
        debtor_days = []
        for r_val, rev in zip(recv_row, rev_row):
            if r_val is not None and rev:
                debtor_days.append(r_val / rev * 365.0)
            else:
                debtor_days.append(None)

        # inventory days = Inventory / COGS * 365
        inv_days = []
        for inv, cogs in zip(inv_row, cogs_row):
            if inv is not None and cogs:
                inv_days.append(inv / cogs * 365.0)
            else:
                inv_days.append(None)

        ratios_stmt = {
            "working capital days": wc_days,
            "debtor days":          debtor_days,
            "inventory days":       inv_days,
            "days payable":         [],   # Cannot compute: no AP balance from MacroTrends
        }

        # ---------------------------------------------------------------
        # Top-level legacy arrays (absolute USD, last 4 years)
        # ---------------------------------------------------------------
        revenue_abs     = _abs_last4(rev_row)
        cogs_abs        = _abs_last4(cogs_row)
        gross_profit_abs = [
            (s - c) if (s is not None and c is not None) else None
            for s, c in zip(revenue_abs, cogs_abs)
        ]
        ebit_abs        = _abs_last4(opinc_row)
        pretax_abs      = _abs_last4(pretax_row)
        tax_abs         = _abs_last4(tax_row)
        net_income_abs  = _abs_last4(netinc_row)
        ta_abs          = _abs_last4(ta_row)
        eq_abs          = _abs_last4(eq_row)
        cash_abs        = _abs_last4(cash_row)
        debt_abs        = _abs_last4(ltd_row)     # LT debt (Phase 1)
        depr_abs        = _abs_last4(depr_row)
        cfo_abs         = _abs_last4(cfo_row)
        capex_abs_4     = _abs_last4(capex_row)

        # Interest expense: MacroTrends IS does not have a dedicated interest line;
        # use None (engine handles None gracefully via the WACC proxy).
        interest_abs = [None] * 4

        # Working capital change: CFO - net_income - depreciation (residual)
        wc_change_abs = []
        for o, ni, d in zip(cfo_abs, net_income_abs, depr_abs):
            if o is not None and ni is not None and d is not None:
                wc_change_abs.append(o - ni - d)
            else:
                wc_change_abs.append(None)

        # FCF = CFO - capex
        fcf_abs = []
        for o, cx in zip(cfo_abs, capex_abs_4):
            if o is not None and cx is not None:
                fcf_abs.append(o - cx)
            else:
                fcf_abs.append(None)

        # ---------------------------------------------------------------
        # Shares, price, market cap
        # ---------------------------------------------------------------
        # Shares Outstanding from income table (millions)
        last_shares_mm = None
        for v in reversed(shares_row):
            if v is not None:
                last_shares_mm = v
                break
        shares_outstanding = (last_shares_mm * 1e6) if last_shares_mm is not None else None

        # Historical shares: last 4 years
        hist_shares_raw = shares_row[-4:] if len(shares_row) >= 4 else shares_row
        historical_shares = [(v * 1e6) if v is not None else None for v in hist_shares_raw]

        # Price via stooq -> yfinance (reusing edgar._us_price)
        current_price = _us_price(t)
        market_cap = (
            current_price * shares_outstanding
            if (current_price is not None and shares_outstanding is not None)
            else None
        )

        # trailing_pe and dividend_yield: best-effort via yfinance
        trailing_pe = None
        dividend_yield = 0.0
        try:
            import yfinance as yf
            yf_info = yf.Ticker(t).info
            trailing_pe = yf_info.get("trailingPE")
            dy = yf_info.get("dividendYield")
            dividend_yield = float(dy) if dy is not None else 0.0
        except Exception:
            pass

        # Debt latest (absolute USD, LT only for Phase 1)
        last_ltd_mm = None
        for v in reversed(ltd_row):
            if v is not None:
                last_ltd_mm = v
                break
        debt_latest = (last_ltd_mm * 1e6) if last_ltd_mm is not None else 0.0

        # Book value per share
        last_eq = eq_abs[-1] if eq_abs else None
        book_value_per_share = (
            (last_eq / shares_outstanding)
            if (last_eq is not None and shares_outstanding and shares_outstanding > 0)
            else 0.0
        )

        # ---------------------------------------------------------------
        # Sector / industry via SEC SIC lookup
        # ---------------------------------------------------------------
        sic, sic_desc = _get_sic_from_sec(t)
        scraped_sector, scraped_industry = _sic_to_sector_industry(sic, sic_desc)

        is_bank = bool(sic and _BANK_SIC_RANGE[0] <= sic <= _BANK_SIC_RANGE[1])
        is_financial = bool(
            (sic and _FINANCIAL_SIC_RANGE[0] <= sic <= _FINANCIAL_SIC_RANGE[1])
            or _is_financial_sector(scraped_sector, scraped_industry)
        )

        # ---------------------------------------------------------------
        # Assemble the fin dict (screener / stockanalysis contract)
        # ---------------------------------------------------------------
        # Lazy fetch beta from stockanalysis
        try:
            from data.scrapers.stockanalysis import fetch_stockanalysis_beta
            beta_val = fetch_stockanalysis_beta(t)
        except ImportError:
            beta_val = None

        fin = {
            "statements": {
                "years_annual": years_annual,
                "annual": {
                    "profit_loss":   pl_stmt,
                    "balance_sheet": bs_stmt,
                    "cash_flow":     cf_stmt,
                },
                "ratios": ratios_stmt,
            },
            "revenue":                revenue_abs,
            "gross_profit":           gross_profit_abs,
            "ebit":                   ebit_abs,
            "interest_expense":       interest_abs,
            "tax_provision":          tax_abs,
            "pretax_income":          pretax_abs,
            "net_income":             net_income_abs,
            "total_assets":           ta_abs,
            "total_equity":           eq_abs,
            "cash":                   cash_abs,
            "debt":                   debt_abs,
            "capex":                  capex_abs_4,
            "depreciation":           depr_abs,
            "working_capital_change": wc_change_abs,
            "fcf":                    fcf_abs,
            "historical_shares":      historical_shares,
            "current_price":          current_price,
            "market_cap":             market_cap,
            "shares_outstanding":     shares_outstanding,
            "trailing_pe":            trailing_pe,
            "dividend_yield":         dividend_yield,
            "stock_beta":             beta_val or 1.0,
            "recommendation_mean":    None,
            "insider_ownership":      0.0,
            "book_value_per_share":   book_value_per_share,
            "debt_latest":            debt_latest,
            "scraped_sector":         scraped_sector,
            "scraped_broad_industry": None,
            "scraped_industry":       scraped_industry,
            "is_bank":                is_bank,
            "is_financial":           is_financial,
            "source":                 "macrotrends",
            "ticker":                 t,
            "years":                  years_annual[-4:] if len(years_annual) >= 4 else years_annual,
        }

        # None -> 0.0 normalization for legacy numeric arrays (mirrors stockanalysis.py)
        _HIST_NUMERIC_KEYS = (
            "revenue", "gross_profit", "ebit", "interest_expense", "tax_provision",
            "pretax_income", "net_income", "total_assets", "total_equity", "cash",
            "debt", "capex", "depreciation", "working_capital_change", "fcf",
            "historical_shares",
        )
        for k in _HIST_NUMERIC_KEYS:
            if k in fin and isinstance(fin[k], list):
                fin[k] = [(v if v is not None else 0.0) for v in fin[k]]

        # Phase 3: unified cross-source gap filling
        # (adds interest, total borrowings, trade receivables, trade payables,
        #  and refreshes all dependent ratios and top-level fields)
        fin = _merge_stockanalysis_gaps(fin, t)

        cache.set_json(cache_key, fin)
        return fin

    except Exception as e:
        logger.warning(f"macrotrends fetch failed for {ticker}: {e}")
        return None
