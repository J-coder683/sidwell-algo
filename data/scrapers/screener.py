import requests
import logging
from bs4 import BeautifulSoup
from data import cache
import re

logger = logging.getLogger(__name__)

TTL_PRICES = 24 * 60 * 60
TTL_FINANCIALS = 7 * 24 * 60 * 60

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

def _to_screener_ticker(sidwell_ticker: str) -> str:
    """Strip .NS or .BO suffix from ticker for screener.in"""
    return sidwell_ticker.replace(".NS", "").replace(".BO", "").upper()

def _resolve_screener_slug(ticker: str) -> str | None:
    """Returns the working screener.in slug for a ticker, or None if not findable.
    Tries: bare ticker → standalone variant → screener search API."""
    base_ticker = _to_screener_ticker(ticker)
    cache_key = f"screener_slug_{base_ticker}.json"
    cached_slug = cache.get_json(cache_key, 90 * 24 * 60 * 60)
    if cached_slug and cached_slug.get("slug"):
        return cached_slug["slug"]
    
    session = requests.Session()
    
    # Tier 1: Try /company/{ticker}/consolidated/
    url = f"https://www.screener.in/company/{base_ticker}/consolidated/"
    resp = session.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
    if resp.status_code == 200:
        cache.set_json(cache_key, {"slug": base_ticker})
        return base_ticker
    
    # Tier 2: Try /company/{ticker}/ (no consolidated; some small caps)
    url = f"https://www.screener.in/company/{base_ticker}/"
    resp = session.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
    if resp.status_code == 200:
        cache.set_json(cache_key, {"slug": base_ticker})
        return base_ticker
    
    # Tier 3: Use screener's search API to find the actual slug
    search_url = f"https://www.screener.in/api/company/search/?q={base_ticker}"
    try:
        resp = session.get(search_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            results = resp.json()
            if results and len(results) > 0:
                # Search returns list; take the top match
                url_parts = results[0].get("url", "").strip("/").split("/")
                resolved = url_parts[-2] if url_parts[-1] == "consolidated" else url_parts[-1]
                if resolved and resolved != base_ticker:
                    logger.info(f"Resolved {ticker} → screener slug '{resolved}' via search (likely ticker rename)")
                    cache.set_json(cache_key, {"slug": resolved})
                    return resolved
    except Exception as e:
        logger.warning(f"Screener slug search failed for {ticker}: {e}")
    
    logger.warning(f"Could not resolve screener.in slug for {ticker}")
    return None

def _parse_float(s: str) -> float | None:
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    if s in ("-", "", "NA"):
        return None
    # Strip commas and any percentage signs
    s = s.replace(",", "").replace("%", "")
    try:
        return float(s)
    except ValueError:
        return None

def _normalize_label(text: str) -> str:
    return text.replace("\u00a0", " ").strip().lower().rstrip("-+ ").strip()

def _get_row_data(table, match_texts, parent_only=True, is_shareholding=False):
    """
    Finds a row by text match in its first td and returns its numeric values.
    match_texts can be a string or a list of possible matching strings.
    """
    if not table:
        return []
    
    if isinstance(match_texts, str):
        match_texts = [match_texts]
        
    for tr in table.find('tbody').find_all('tr'):
        tds = tr.find_all('td')
        if not tds:
            continue
            
        label_norm = _normalize_label(tds[0].text)
        
        is_match = False
        for text in match_texts:
            if label_norm == _normalize_label(text):
                is_match = True
                break
                
        if is_match:
            return [_parse_float(td.text) for td in tds[1:]]
            
    return []

def _get_subrows(company_id: str, section: str, parent_match: str):
    """
    Fetches the sub-rows JSON from screener API since they are not rendered in the HTML for anonymous users.
    Returns a dict mapping normalized child labels to their data arrays (last 4 years).
    """
    if not company_id:
        return {}
        
    for p in [parent_match, parent_match + " %"]:
        url = f"https://www.screener.in/api/company/{company_id}/schedules/?parent={p.replace(' ', '+')}&section={section}&consolidated="
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    children = {}
                    for k, d in data.items():
                        vals = [_parse_float(str(v)) for v in list(d.values())[-4:]]
                        if len(vals) < 4:
                            vals = ([None] * (4 - len(vals))) + vals
                        children[_normalize_label(k)] = vals
                    return children
        except Exception as e:
            logger.debug(f"Failed to fetch schedules for {parent_match}: {e}")
            
    return {}

def _slice_years(arr):
    """Takes the last 4 items of an array, representing the last 4 fiscal years."""
    if not arr or len(arr) < 4:
        return ([None] * (4 - len(arr))) + arr
    return arr[-4:]

def fetch_screener_financials(ticker: str) -> dict:
    base = _to_screener_ticker(ticker)
    
    cache_key_fin = f"financials_screener_{base}.json"
    cached_fin = cache.get_json(cache_key_fin, TTL_FINANCIALS)
    
    cache_key_price = f"price_screener_{base}.json"
    cached_price = cache.get_json(cache_key_price, TTL_PRICES)
    
    if cached_fin and cached_price:
        logger.info(f"Loaded financials and price for {ticker.upper()} from screener cache.")
        cached_fin["current_price"] = cached_price.get("current_price")
        # Defensive: normalize None→0.0 on cached payloads too (caches written
        # before the v0.7.4 normalization may still contain None values).
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
        
    logger.info(f"Fetching {ticker.upper()} from screener.in...")
    
    slug = _resolve_screener_slug(ticker)
    if not slug:
        raise ValueError(f"Screener.in has no data for {ticker}. Verify the ticker is NSE-listed.")
    
    url = f"https://www.screener.in/company/{slug}/consolidated/"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    
    if resp.status_code == 404:
        url = f"https://www.screener.in/company/{slug}/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        
    if resp.status_code == 404:
        raise ValueError(f"Screener.in has no data for {ticker} (slug {slug}). Verify the ticker is NSE-listed.")
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    company_id_match = re.search(r'data-company-id=["\'](\d+)["\']', resp.text)
    company_id = company_id_match.group(1) if company_id_match else None
    
    scraped_industry = None
    scraped_broad_industry = None
    scraped_sector = None
    
    for a in soup.find_all('a'):
        href = a.get('href', '')
        if 'market' in str(href):
            title = a.get('title', '')
            if title == 'Industry':
                scraped_industry = a.text.strip()
            elif title == 'Broad Industry':
                scraped_broad_industry = a.text.strip()
            elif title == 'Sector':
                scraped_sector = a.text.strip()
    
    
    pl_table = soup.find('section', id='profit-loss').find('table') if soup.find('section', id='profit-loss') else None
    bs_table = soup.find('section', id='balance-sheet').find('table') if soup.find('section', id='balance-sheet') else None
    cf_table = soup.find('section', id='cash-flow').find('table') if soup.find('section', id='cash-flow') else None
    sh_table = soup.find('section', id='shareholding').find('table') if soup.find('section', id='shareholding') else None
    
    if not pl_table or not bs_table or not cf_table:
        raise ValueError(f"Could not find financial tables on screener.in for {ticker}.")
        
    headers = [th.text.strip() for th in pl_table.find('thead').find_all('th')[1:]]
    has_ttm = len(headers) > 0 and headers[-1].upper() == "TTM"
    
    years_extracted = [h[-4:] if len(h) >= 4 else h for h in headers]
    if has_ttm:
        years_extracted = years_extracted[:-1]
    years_sliced = _slice_years(years_extracted)
    
    def _slice_row(row_data):
        if not row_data:
            return [None, None, None, None]
        if has_ttm:
            row_data = row_data[:-1]
        return _slice_years(row_data)

    def _crore_to_rupee(arr):
        return [(val * 1e7) if val is not None else None for val in arr]

    # Income Statement
    sales = _slice_row(_get_row_data(pl_table, "Sales"))
    expenses = _slice_row(_get_row_data(pl_table, "Expenses"))
    op_profit = _slice_row(_get_row_data(pl_table, "Operating Profit"))
    interest = _slice_row(_get_row_data(pl_table, "Interest"))
    depreciation = _slice_row(_get_row_data(pl_table, "Depreciation"))
    pbt = _slice_row(_get_row_data(pl_table, "Profit before tax"))
    tax_percent = _slice_row(_get_row_data(pl_table, "Tax %"))
    net_profit = _slice_row(_get_row_data(pl_table, "Net Profit"))
    
    tax_provision = []
    for p, tp in zip(pbt, tax_percent):
        tax_provision.append((p * (tp / 100.0)) if p is not None and tp is not None else None)
        
    # Gross Profit Extraction (Fix 8)
    mat_subrows = _get_subrows(company_id, "profit-loss", "Material Cost")
    raw_material_cost = None
    change_in_inventory = None
    
    # scan for raw material
    for k, v in mat_subrows.items():
        if k in ["raw material cost", "cost of materials consumed", "raw materials", "material consumption"]:
            raw_material_cost = v
            break
            
    # scan for change in inventory
    for k, v in mat_subrows.items():
        if k == "change in inventory":
            change_in_inventory = v
            break
            
    gross_profit = []
    if raw_material_cost:
        change_in_inv = change_in_inventory or [0.0] * len(raw_material_cost)
        mat_consum = []
        for rm, ci in zip(raw_material_cost, change_in_inv):
            rm_val = rm if rm is not None else 0.0
            ci_val = ci if ci is not None else 0.0
            mat_consum.append(rm_val + ci_val)
            
        mat_consum = _slice_row(mat_consum)
        for s, mc in zip(sales, mat_consum):
            gross_profit.append(s - mc if s is not None and mc is not None else None)
    else:
        logger.warning(f"Raw material cost not found for {ticker.upper()}; falling back to (revenue - expenses). Note: For banks, this is expected.")
        for s, e in zip(sales, expenses):
            gross_profit.append(s - e if s is not None and e is not None else None)

    # Balance Sheet
    total_assets = _slice_row(_get_row_data(bs_table, "Total Assets"))
    equity_cap = _slice_row(_get_row_data(bs_table, "Equity Capital"))
    reserves = _slice_row(_get_row_data(bs_table, "Reserves"))
    debt = _slice_row(_get_row_data(bs_table, "Borrowings"))
    
    total_equity = []
    for e, r in zip(equity_cap, reserves):
        if e is not None and r is not None:
            total_equity.append(e + r)
        elif e is not None:
            total_equity.append(e)
        elif r is not None:
            total_equity.append(r)
        else:
            total_equity.append(None)
            
    # Cash Extraction (Fix 3)
    other_assets_subrows = _get_subrows(company_id, "balance-sheet", "Other Assets")
    cash_row = None
    for target in ["cash equivalents", "cash & equivalents", "cash and bank", "cash & bank balance", "cash"]:
        if target in other_assets_subrows:
            cash_row = other_assets_subrows[target]
            break
            
    if not cash_row:
        logger.warning(f"Cash equivalents not found in Other Assets sub-rows for {ticker.upper()}; defaulting to 0.0")
        cash = [0.0] * 4
    else:
        cash = _slice_row(cash_row)
        
    # Cash Flow
    cfo = _slice_row(_get_row_data(cf_table, "Cash from Operating Activity"))
    cfi = _slice_row(_get_row_data(cf_table, "Cash from Investing Activity"))
    fcf = _slice_row(_get_row_data(cf_table, "Free Cash Flow"))
    
    # Capex Extraction (Fix 4)
    cfi_subrows = _get_subrows(company_id, "cash-flow", "Cash from Investing Activity")
    fixed_assets_purchased = None
    fixed_assets_sold = None
    
    for k, v in cfi_subrows.items():
        if k in ["fixed assets purchased", "purchase of fixed assets", "capital expenditure", "purchase of property"]:
            fixed_assets_purchased = v
            break
    for k, v in cfi_subrows.items():
        if k == "fixed assets sold":
            fixed_assets_sold = v
            break
            
    if fixed_assets_purchased:
        f_purchased = _slice_row(fixed_assets_purchased)
        f_sold = _slice_row(fixed_assets_sold) if fixed_assets_sold else [0.0]*4
        capex = []
        for p, s in zip(f_purchased, f_sold):
            p_val = p if p is not None else 0.0
            s_val = s if s is not None else 0.0
            capex.append(abs(p_val) - abs(s_val))
    else:
        logger.warning(f"Capex sub-row not found for {ticker.upper()}; falling back to abs(Cash from Investing Activity)")
        capex = [abs(c) if c is not None else None for c in cfi]
        
    # Working Capital Changes (Fix 5)
    cfo_subrows = _get_subrows(company_id, "cash-flow", "Cash from Operating Activity")
    wc_row = None
    for k, v in cfo_subrows.items():
        if k == "working capital changes":
            wc_row = v
            break
            
    if wc_row:
        working_capital_change = _slice_row(wc_row)
    else:
        logger.warning(f"Working capital changes sub-row not found for {ticker.upper()}; falling back to residual method")
        working_capital_change = []
        for o, ni, d in zip(cfo, net_profit, depreciation):
            if o is not None and ni is not None and d is not None:
                working_capital_change.append(o - ni - d)
            else:
                working_capital_change.append(None)
            
    # Shareholding
    insider_ownership = 0.0
    if sh_table:
        promoters = _get_row_data(sh_table, "Promoters")
        if promoters and len(promoters) > 0 and promoters[-1] is not None:
            insider_ownership = promoters[-1] / 100.0

    # Top Ratios
    top_ratios = soup.find('ul', id='top-ratios')
    ratios_dict = {}
    if top_ratios:
        for li in top_ratios.find_all('li'):
            name_span = li.find('span', class_='name')
            num_span = li.find('span', class_='number')
            if name_span and num_span:
                val_text = num_span.text.strip()
                ratios_dict[_normalize_label(name_span.text)] = val_text

    current_price = _parse_float(ratios_dict.get("current price"))
    market_cap_crore = _parse_float(ratios_dict.get("market cap"))
    market_cap = (market_cap_crore * 1e7) if market_cap_crore is not None else None
    
    shares_out = None
    if market_cap is not None and current_price and current_price > 0:
        shares_out = market_cap / current_price
        
    trailing_pe = _parse_float(ratios_dict.get("stock p/e"))
    
    div_yield_val = _parse_float(ratios_dict.get("dividend yield"))
    dividend_yield = 0.0
    if div_yield_val is not None:
        dividend_yield = div_yield_val / 100.0

    logger.info(
        f"Stock beta not directly available on screener.in for {ticker.upper()}; "
        f"WACC will use Damodaran industry levered beta as fallback (standard practice for "
        f"Indian tickers; company-specific beta available in v0.7+ via price-history regression)."
    )
    stock_beta = 1.0
    recommendation_mean = None

    fin = {}
    fin["ticker"] = ticker.upper()
    fin["current_price"] = current_price
    fin["market_cap"] = market_cap
    fin["shares_outstanding"] = shares_out
    fin["trailing_pe"] = trailing_pe
    fin["dividend_yield"] = dividend_yield
    fin["stock_beta"] = stock_beta
    fin["recommendation_mean"] = recommendation_mean
    fin["insider_ownership"] = insider_ownership
    fin["source"] = "screener.in"
    
    fin["years"] = [f"{y}-03-31" if y is not None else "Unknown" for y in years_sliced]
    
    fin["revenue"] = _crore_to_rupee(sales)
    fin["gross_profit"] = _crore_to_rupee(gross_profit)
    fin["ebit"] = _crore_to_rupee(op_profit)
    fin["interest_expense"] = _crore_to_rupee(interest)
    fin["tax_provision"] = _crore_to_rupee(tax_provision)
    fin["pretax_income"] = _crore_to_rupee(pbt)
    fin["net_income"] = _crore_to_rupee(net_profit)
    
    fin["total_assets"] = _crore_to_rupee(total_assets)
    fin["total_equity"] = _crore_to_rupee(total_equity)
    fin["cash"] = _crore_to_rupee(cash)
    fin["debt"] = _crore_to_rupee(debt)
    
    fin["capex"] = _crore_to_rupee(capex)
    fin["depreciation"] = _crore_to_rupee(depreciation)
    fin["working_capital_change"] = _crore_to_rupee(working_capital_change)
    fin["fcf"] = _crore_to_rupee(fcf)
    historical_shares = [shares_out] * 4 if shares_out else [None]*4
    fin["historical_shares"] = historical_shares
    
    fin["scraped_sector"] = scraped_sector
    fin["scraped_broad_industry"] = scraped_broad_industry
    fin["scraped_industry"] = scraped_industry
    
    if not scraped_sector and not scraped_broad_industry and not scraped_industry:
        logger.info(f"Could not extract sector/industry for {ticker} from screener.in")
    
    fin["source"] = "Screener.in"
    fin["book_value_per_share"] = (fin["total_equity"][-1] / shares_out) if shares_out and shares_out > 0 and len(fin["total_equity"]) > 0 and fin["total_equity"][-1] is not None else 0.0

    # Defensive None→0.0 normalization for all historical numeric arrays.
    # Screener.in returns None when a row label doesn't match for a particular
    # year (e.g., NBFCs have no "Raw material cost"; some years missing for
    # newly-listed companies). Downstream DCF and lens code does naked
    # arithmetic and >0 comparisons which crash on None. Normalize once,
    # here at the data layer, so every consumer is safe.
    _HIST_NUMERIC_KEYS = (
        "revenue", "gross_profit", "ebit", "interest_expense",
        "tax_provision", "pretax_income", "net_income",
        "total_assets", "total_equity", "cash", "debt",
        "capex", "depreciation", "working_capital_change", "fcf",
        "historical_shares",
    )
    for k in _HIST_NUMERIC_KEYS:
        if k in fin and isinstance(fin[k], list):
            fin[k] = [(v if v is not None else 0.0) for v in fin[k]]

    price_dict = {"current_price": current_price}
    cache.set_json(cache_key_fin, fin)
    cache.set_json(cache_key_price, price_dict)

    return fin

def fetch_screener_documents(ticker: str) -> list[dict]:
    """
    Returns up to N most-recent documents per ticker, no PDFs downloaded.
    Selection policy: Latest 1 annual report, 2 concalls, 1 credit rating.
    """
    base = _to_screener_ticker(ticker)
    cache_key = f"docs_screener_{base}.json"
    cached = cache.get_json(cache_key, 7 * 24 * 60 * 60)
    if cached is not None:
        logger.info(f"Loaded documents for {ticker} from screener cache.")
        return cached

    slug = _resolve_screener_slug(ticker)
    if not slug:
        logger.warning(f"Could not resolve slug for {ticker}. Returning empty docs.")
        return []

    url = f"https://www.screener.in/company/{slug}/consolidated/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 404:
            url = f"https://www.screener.in/company/{slug}/"
            resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch {ticker} document page from screener: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    docs_section = soup.find('section', id='documents')
    if not docs_section:
        logger.warning(f"No documents section found for {ticker}")
        return []

    documents = []

    # 1. Annual Reports (Max 1)
    annual_div = docs_section.find('div', class_='annual-reports')
    if annual_div:
        ul = annual_div.find('ul')
        if ul:
            for li in ul.find_all('li')[:1]:
                a = li.find('a')
                if a and a.get('href'):
                    documents.append({
                        "url": a['href'],
                        "type": "annual_report",
                        "date": a.text.split("\n")[0].strip() if "\n" in a.text else a.text.strip(),
                        "label": a.text.strip().replace('\n', ' ')
                    })

    # 2. Concalls (Max 2)
    concall_div = docs_section.find('div', class_='concalls')
    if concall_div:
        ul = concall_div.find('ul')
        if ul:
            for li in ul.find_all('li')[:2]:
                a = li.find('a', class_='concall-link')
                date_div = li.find('div')
                date_str = date_div.text.strip() if date_div else "Unknown Date"
                if a and a.get('href'):
                    documents.append({
                        "url": a['href'],
                        "type": "concall_transcript",
                        "date": date_str,
                        "label": f"{date_str} Concall"
                    })

    # 3. Credit Ratings (Max 1)
    rating_div = docs_section.find('div', class_='credit-ratings')
    if rating_div:
        ul = rating_div.find('ul')
        if ul:
            for li in ul.find_all('li')[:1]:
                a = li.find('a')
                if a and a.get('href'):
                    documents.append({
                        "url": a['href'],
                        "type": "credit_rating",
                        "date": "Recent",
                        "label": a.text.strip().replace('\n', ' ')
                    })

    cache.set_json(cache_key, documents)
    return documents
