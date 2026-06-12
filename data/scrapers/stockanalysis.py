import io
import logging
import requests
import pandas as pd
from data import cache
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TTL_FINANCIALS = 7 * 24 * 3600
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

def _parse_float(val):
    if val is None:
        return None
    s = str(val).strip()
    if s in ("-", "", "N/A", "NA"):
        return None
    s = s.replace(",", "").replace("%", "")
    is_neg = False
    if s.startswith("(") and s.endswith(")"):
        is_neg = True
        s = s[1:-1]
    elif s.startswith("-"):
        is_neg = True
        s = s[1:]
    try:
        f = float(s)
        return -f if is_neg else f
    except ValueError:
        return None

def fetch_stockanalysis_financials(ticker: str) -> dict | None:
    t = ticker.upper()
    cache_key = f"financials_stockanalysis_{t}.json"
    cached = cache.get_json(cache_key, TTL_FINANCIALS)
    if cached:
        logger.info(f"Loaded {t} from stockanalysis cache.")
        return cached

    urls = {
        "income": f"https://stockanalysis.com/stocks/{t.lower()}/financials/",
        "balance": f"https://stockanalysis.com/stocks/{t.lower()}/financials/balance-sheet/",
        "cashflow": f"https://stockanalysis.com/stocks/{t.lower()}/financials/cash-flow-statement/",
        "ratios": f"https://stockanalysis.com/stocks/{t.lower()}/financials/ratios/",
        "overview": f"https://stockanalysis.com/stocks/{t.lower()}/"
    }

    try:
        pages = {}
        for key, url in urls.items():
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            pages[key] = r.text
            
        def _parse_table(html):
            dfs = pd.read_html(io.StringIO(html))
            if not dfs: return None
            df = sorted(dfs, key=lambda x: x.size, reverse=True)[0]
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            keep_cols = [c for c in df.columns if isinstance(c, str) and (c.startswith("FY ") or c in ["Current", "TTM"])]
            fy_cols = [c for c in df.columns if isinstance(c, str) and c.startswith("FY ")]
            fy_cols.sort()
            
            label_col = df.columns[0]
            df.set_index(label_col, inplace=True)
            
            # keep the selected columns, ensuring they are ordered correctly with FY cols first, then TTM/Current
            ordered_cols = fy_cols + [c for c in keep_cols if c not in fy_cols]
            df = df[ordered_cols]
            
            # rename FY columns to just years, but keep TTM/Current as is
            new_cols = []
            for c in df.columns:
                if c.startswith("FY "):
                    new_cols.append(c.split(" ")[1])
                else:
                    new_cols.append(c)
            df.columns = new_cols
            return df

        inc_df = _parse_table(pages["income"])
        bal_df = _parse_table(pages["balance"])
        cf_df = _parse_table(pages["cashflow"])
        rat_df = _parse_table(pages["ratios"])
        
        if inc_df is None or bal_df is None or cf_df is None or rat_df is None:
            return None
            
        years_annual = [c for c in inc_df.columns if str(c).isdigit()]
        
        def _get_row(df, label):
            for idx in df.index:
                if str(idx).strip().lower() == label.lower():
                    row = df.loc[idx]
                    if isinstance(row, pd.DataFrame):
                        row = row.iloc[0]
                    return [_parse_float(row[y]) for y in years_annual]
            return [None] * len(years_annual)
            
        def _get_rat_col(df, label, col="Current"):
            for idx in df.index:
                if str(idx).strip().lower() == label.lower():
                    if col in df.columns:
                        row = df.loc[idx]
                        if isinstance(row, pd.DataFrame):
                            row = row.iloc[0]
                        return _parse_float(row[col])
            return None

        def _get_last_n_diluted_shares(df, label, n=4):
            for idx in df.index:
                if str(idx).strip().lower() == label.lower():
                    row = df.loc[idx]
                    if isinstance(row, pd.DataFrame):
                        row = row.iloc[0]
                    vals = [_parse_float(row[y]) for y in years_annual[-n:]]
                    if len(vals) < n:
                        vals = [None] * (n - len(vals)) + vals
                    return vals
            return [None] * n

        inc_map = {
            "sales": "Revenue",
            "cogs": "Cost of Revenue",
            "operating profit": "Operating Income",
            "interest": "Interest Expense",
            "profit before tax": "Pretax Income",
            "tax": "Provision for Income Taxes",
            "net profit": "Net Income"
        }
        
        cf_map = {
            "cash from operating activity": "Operating Cash Flow",
            "fixed assets purchased": "Capital Expenditures",
            "depreciation": "Depreciation & Amortization",
            "receivables": "Change in Receivables",
            "inventory": "Changes in Inventories",
            "payables": "Changes in Accounts Payable",
            "proceeds from borrowings": "Long-Term Debt Issued",
            "repayment of borrowings": "Long-Term Debt Repaid"
        }
        
        bal_map = {
            "cash equivalents": "Cash & Equivalents",
            "trade receivables": "Accounts Receivable",
            "inventories": "Inventory",
            "trade payables": "Accounts Payable",
            "fixed assets": "Net Property, Plant & Equipment",
            "investments": "Long-Term Investments",
            "total assets": "Total Assets",
            "total liabilities": "Total Liabilities",
            "reserves": "Total Common Shareholders' Equity",
            "borrowings": "Total Debt",
            "non controlling int": "Minority Interest"
        }

        def _scale_row(row):
            return [(v * 1e6) / 1e7 if v is not None else None for v in row]

        pl_stmt = {k: _scale_row(_get_row(inc_df, v)) for k, v in inc_map.items()}
        # Interest expense: stockanalysis.com reports it NEGATIVE. Store it POSITIVE to
        # match the screener/contract convention -- the lenses guard with `if interest > 0`,
        # so a negative value makes interest-coverage evaluate to infinity (false pass).
        pl_stmt["interest"] = [abs(v) if v is not None else None for v in pl_stmt["interest"]]
        cf_stmt = {k: _scale_row(_get_row(cf_df, v)) for k, v in cf_map.items()}
        
        cf_stmt["fixed assets purchased"] = [abs(v) if v is not None else None for v in cf_stmt["fixed assets purchased"]]

        bs_stmt = {k: _scale_row(_get_row(bal_df, v)) for k, v in bal_map.items()}
        bs_stmt["equity capital"] = [None] * len(years_annual)
        
        tca = _get_row(bal_df, "Total Current Assets")
        tcl = _get_row(bal_df, "Total Current Liabilities")
        cash = _get_row(bal_df, "Cash & Equivalents")
        std = _get_row(bal_df, "Short-Term Debt")
        sales = _get_row(inc_df, "Revenue")
        
        wc_days = []
        for i in range(len(years_annual)):
            a = tca[i]
            l = tcl[i]
            c = cash[i] if cash[i] is not None else 0.0
            s = std[i] if std[i] is not None else 0.0
            rev = sales[i]
            if a is not None and l is not None and rev:
                op_nwc = (a - c) - (l - s)
                wc_days.append(op_nwc / rev * 365.0)
            else:
                wc_days.append(None)
                
        def _abs_row(df, label):
            return [(v * 1e6) if v is not None else None for v in _get_row(df, label)[-4:]]

        revenue_abs = _abs_row(inc_df, "Revenue")
        cogs_abs = _abs_row(inc_df, "Cost of Revenue")
        gross_profit_abs = [(s - c) if s is not None and c is not None else None for s, c in zip(revenue_abs, cogs_abs)]
        
        ebit_abs = _abs_row(inc_df, "Operating Income")
        interest_abs = _abs_row(inc_df, "Interest Expense")
        # Positive convention (see pl_stmt["interest"] note): lenses read this top-level
        # array and guard with `if interest > 0`.
        interest_abs = [abs(v) if v is not None else None for v in interest_abs]
        tax_abs = _abs_row(inc_df, "Provision for Income Taxes")
        pretax_abs = _abs_row(inc_df, "Pretax Income")
        net_income_abs = _abs_row(inc_df, "Net Income")
        
        total_assets_abs = _abs_row(bal_df, "Total Assets")
        total_equity_abs = _abs_row(bal_df, "Total Common Shareholders' Equity")
        cash_abs = _abs_row(bal_df, "Cash & Equivalents")
        debt_abs = _abs_row(bal_df, "Total Debt")
        
        depr_abs = _abs_row(cf_df, "Depreciation & Amortization")
        cfo_abs = _abs_row(cf_df, "Operating Cash Flow")
        capex_raw_abs = _abs_row(cf_df, "Capital Expenditures")
        capex_abs = [abs(v) if v is not None else None for v in capex_raw_abs]
        
        wc_change_abs = []
        for o, ni, d in zip(cfo_abs, net_income_abs, depr_abs):
            if o is not None and ni is not None and d is not None:
                wc_change_abs.append(o - ni - d)
            else:
                wc_change_abs.append(None)
                
        fcf_abs = []
        for o, cx in zip(cfo_abs, capex_abs):
            if o is not None and cx is not None:
                fcf_abs.append(o - cx)
            else:
                fcf_abs.append(None)
                
        market_cap_raw = _get_rat_col(rat_df, "Market Cap")
        market_cap = (market_cap_raw * 1e6) if market_cap_raw is not None else None
        
        current_price = _get_rat_col(rat_df, "Last Close Price")
        trailing_pe = _get_rat_col(rat_df, "PE Ratio")
        div_yield_raw = _get_rat_col(rat_df, "Dividend Yield")
        dividend_yield = (div_yield_raw / 100.0) if div_yield_raw is not None else 0.0
        
        shares_out_raw = _get_rat_col(inc_df, "Shares Outstanding (Diluted)", "Current")
        if shares_out_raw is None:
            shares_out_raw = _get_row(inc_df, "Shares Outstanding (Diluted)")[-1]
            
        shares_outstanding = (shares_out_raw * 1e6) if shares_out_raw is not None else None
        
        hist_shares_raw = _get_last_n_diluted_shares(inc_df, "Shares Outstanding (Diluted)")
        historical_shares = [(v * 1e6) if v is not None else None for v in hist_shares_raw]
        
        debt_latest_raw = _get_rat_col(bal_df, "Total Debt", "Current")
        if debt_latest_raw is None:
            debt_latest_raw = _get_row(bal_df, "Total Debt")[-1]
        debt_latest = (debt_latest_raw * 1e6) if debt_latest_raw is not None else 0.0
        
        book_value_per_share = 0.0
        if total_equity_abs and total_equity_abs[-1] is not None and shares_outstanding:
            book_value_per_share = total_equity_abs[-1] / shares_outstanding
            
        soup = BeautifulSoup(pages["overview"], 'html.parser')
        scraped_sector = None
        scraped_industry = None
        
        for tr in soup.find_all("tr"):
            if "Sector" in tr.text:
                tds = tr.find_all("td")
                if len(tds) > 1:
                    scraped_sector = tds[1].text.strip()
            if "Industry" in tr.text:
                tds = tr.find_all("td")
                if len(tds) > 1:
                    scraped_industry = tds[1].text.strip()
                    
        if not scraped_sector:
            for div in soup.find_all("div"):
                if div.text.strip() == "Sector":
                    s_div = div.find_next_sibling("div")
                    if s_div: scraped_sector = s_div.text.strip()
                if div.text.strip() == "Industry":
                    i_div = div.find_next_sibling("div")
                    if i_div: scraped_industry = i_div.text.strip()
                    
        if not scraped_sector:
            for a in soup.find_all("a"):
                href = a.get("href", "")
                if "/sector/" in href:
                    scraped_sector = a.text.strip()
                if "/industry/" in href:
                    scraped_industry = a.text.strip()
                    
        is_bank = False
        is_financial = False
        if scraped_industry:
            if "bank" in scraped_industry.lower():
                is_bank = True
        if scraped_sector and "financial" in scraped_sector.lower():
            is_financial = True
        if scraped_industry and any(kw in scraped_industry.lower() for kw in ("financial", "broker", "insurance")):
            is_financial = True

        fin = {
            "statements": {
                "years_annual": years_annual,
                "annual": {
                    "profit_loss": pl_stmt,
                    "balance_sheet": bs_stmt,
                    "cash_flow": cf_stmt
                },
                "ratios": {"working capital days": wc_days}
            },
            "revenue": revenue_abs,
            "gross_profit": gross_profit_abs,
            "ebit": ebit_abs,
            "interest_expense": interest_abs,
            "tax_provision": tax_abs,
            "pretax_income": pretax_abs,
            "net_income": net_income_abs,
            "total_assets": total_assets_abs,
            "total_equity": total_equity_abs,
            "cash": cash_abs,
            "debt": debt_abs,
            "capex": capex_abs,
            "depreciation": depr_abs,
            "working_capital_change": wc_change_abs,
            "fcf": fcf_abs,
            "historical_shares": historical_shares,
            "current_price": current_price,
            "market_cap": market_cap,
            "shares_outstanding": shares_outstanding,
            "trailing_pe": trailing_pe,
            "dividend_yield": dividend_yield,
            "stock_beta": fetch_stockanalysis_beta(ticker) or 1.0,
            "recommendation_mean": None,
            "insider_ownership": 0.0,
            "book_value_per_share": book_value_per_share,
            "debt_latest": debt_latest,
            "scraped_sector": scraped_sector,
            "scraped_broad_industry": None,
            "scraped_industry": scraped_industry,
            "is_bank": is_bank,
            "is_financial": is_financial,
            "source": "stockanalysis",
            "ticker": ticker.upper(),
            "years": years_annual[-4:] if len(years_annual) >= 4 else years_annual
        }
        
        _HIST_NUMERIC_KEYS = (
            "revenue", "gross_profit", "ebit", "interest_expense", "tax_provision",
            "pretax_income", "net_income", "total_assets", "total_equity", "cash",
            "debt", "capex", "depreciation", "working_capital_change", "fcf", "historical_shares"
        )
        for k in _HIST_NUMERIC_KEYS:
            if k in fin and isinstance(fin[k], list):
                fin[k] = [(v if v is not None else 0.0) for v in fin[k]]

        cache.set_json(cache_key, fin)
        return fin

    except Exception as e:
        logger.warning(f"stockanalysis fetch failed for {ticker}: {e}")
        return None

def fetch_stockanalysis_beta(ticker: str) -> float | None:
    t = ticker.upper()
    cache_key = f"beta_stockanalysis_{t}.json"
    cached = cache.get_json(cache_key, TTL_FINANCIALS)
    if cached is not None:
        return cached.get("beta")
        
    url = f"https://stockanalysis.com/stocks/{t.lower()}/statistics/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for td in soup.find_all("td"):
            if "Beta" in td.text:
                nxt = td.find_next_sibling("td")
                if nxt:
                    val = _parse_float(nxt.text)
                    cache.set_json(cache_key, {"beta": val})
                    return val
    except Exception as e:
        logger.warning(f"stockanalysis beta fetch failed for {ticker}: {e}")
        
    cache.set_json(cache_key, {"beta": None})
    return None
