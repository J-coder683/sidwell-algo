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

def _get_row_data(table, match_texts, parent_only=True, is_shareholding=False):
    """
    Finds a row by text match in its first td and returns its numeric values.
    If parent_only is True, we only match the top-level label and ignore sub-rows.
    match_texts can be a string or a list of possible matching strings.
    """
    if not table:
        return []
    
    if isinstance(match_texts, str):
        match_texts = [match_texts]
        
    for tr in table.find('tbody').find_all('tr'):
        # In screener, child rows often have class="stripe" or "hover" or are just visually indented.
        # But for strictly matching parent vs child, we can just look at the exact text.
        tds = tr.find_all('td')
        if not tds:
            continue
            
        label = tds[0].text.strip().replace('\xa0', ' ')
        label_clean = label.replace(" +", "").strip()
        
        # Determine if it's a match
        is_match = False
        for text in match_texts:
            # For strict matching
            if label_clean.lower() == text.lower() or label.lower() == text.lower():
                is_match = True
                break
                
        if is_match:
            vals = [_parse_float(td.text) for td in tds[1:]]
            return vals
            
    return []

def _get_expanded_subrow(table, parent_match, child_match_list):
    """
    Finds a parent row, then scans subsequent rows (until the next empty class row) for a child row matching child_match_list.
    Since Screener nests expanded rows immediately after the parent, we can just iterate.
    """
    if not table:
        return []
        
    in_target_parent = False
    for tr in table.find('tbody').find_all('tr'):
        tds = tr.find_all('td')
        if not tds:
            continue
            
        label = tds[0].text.strip().replace('\xa0', ' ')
        label_clean = label.replace(" +", "").strip()
        
        # Detect parent
        if label_clean.lower() == parent_match.lower():
            in_target_parent = True
            continue
            
        # If we are under the target parent, check if it's our child
        if in_target_parent:
            # Check if we hit the next parent (usually has empty class or specific styles in screener, but generally just check if it matches child)
            # Actually, child rows in screener have specific classes or structure. We can just check the label.
            is_child_match = False
            for child_text in child_match_list:
                if child_text.lower() in label_clean.lower():
                    is_child_match = True
                    break
                    
            if is_child_match:
                return [_parse_float(td.text) for td in tds[1:]]
                
            # If we hit another major row (like one with a '+' or a strong label), we might have exited the group.
            # But just scanning all subsequent rows is safe enough if we match text precisely.
            if "+" in label and label_clean.lower() != parent_match.lower():
                in_target_parent = False # Exited the parent group
                
    return []

def _slice_years(arr):
    """Takes the last 4 items of an array, representing the last 4 fiscal years."""
    if not arr or len(arr) < 4:
        # pad with Nones if less than 4
        return ([None] * (4 - len(arr))) + arr
    return arr[-4:]

def fetch_screener_financials(ticker: str) -> dict:
    base = _to_screener_ticker(ticker)
    
    # 1. Cache Check
    cache_key_fin = f"financials_screener_{base}.json"
    cached_fin = cache.get_json(cache_key_fin, TTL_FINANCIALS)
    
    cache_key_price = f"price_screener_{base}.json"
    cached_price = cache.get_json(cache_key_price, TTL_PRICES)
    
    if cached_fin and cached_price:
        logger.info(f"Loaded financials and price for {ticker.upper()} from screener cache.")
        cached_fin["current_price"] = cached_price.get("current_price")
        return cached_fin
        
    logger.info(f"Fetching {ticker.upper()} from screener.in...")
    
    # 2. Fetch HTML
    url = f"https://www.screener.in/company/{base}/consolidated/"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    
    if resp.status_code == 404:
        url = f"https://www.screener.in/company/{base}/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        
    if resp.status_code == 404:
        raise ValueError(f"Screener.in has no data for {ticker}. Verify the ticker is NSE-listed.")
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Extract headers (to find out which columns are which year)
    pl_table = soup.find('section', id='profit-loss').find('table') if soup.find('section', id='profit-loss') else None
    bs_table = soup.find('section', id='balance-sheet').find('table') if soup.find('section', id='balance-sheet') else None
    cf_table = soup.find('section', id='cash-flow').find('table') if soup.find('section', id='cash-flow') else None
    sh_table = soup.find('section', id='shareholding').find('table') if soup.find('section', id='shareholding') else None
    
    if not pl_table or not bs_table or not cf_table:
        raise ValueError(f"Could not find financial tables on screener.in for {ticker}.")
        
    # Get years (drop TTM if present)
    headers = [th.text.strip() for th in pl_table.find('thead').find_all('th')[1:]]
    # If the last column is TTM, drop it from headers and from data arrays we parse later
    has_ttm = len(headers) > 0 and headers[-1].upper() == "TTM"
    
    years_extracted = [h[-4:] if len(h) >= 4 else h for h in headers]
    if has_ttm:
        years_extracted = years_extracted[:-1]
    years_sliced = _slice_years(years_extracted)
    
    # Helper to slice rows, dropping TTM if present
    def _slice_row(row_data):
        if not row_data:
            return [None, None, None, None]
        if has_ttm:
            row_data = row_data[:-1]
        return _slice_years(row_data)

    # Convert crore to raw rupees
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
    
    # Compute derived P&L
    gross_profit = []
    for s, e in zip(sales, expenses):
        gross_profit.append(s - e if s is not None and e is not None else None)
        
    tax_provision = []
    for p, tp in zip(pbt, tax_percent):
        tax_provision.append((p * (tp / 100.0)) if p is not None and tp is not None else None)
        
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
            
    cash_row = _get_expanded_subrow(bs_table, "Other Assets", ["Cash & Bank", "Cash Equivalents", "Cash"])
    if not cash_row:
        logger.warning(f"Cash not found in Other Assets sub-rows for {ticker.upper()}; defaulting to 0.0")
        cash = [0.0] * 4
    else:
        cash = _slice_row(cash_row)
        
    # Cash Flow
    cfo = _slice_row(_get_row_data(cf_table, "Cash from Operating Activity"))
    cfi = _slice_row(_get_row_data(cf_table, "Cash from Investing Activity"))
    fcf = _slice_row(_get_row_data(cf_table, "Free Cash Flow"))
    
    capex_row = _get_expanded_subrow(cf_table, "Cash from Investing Activity", ["Fixed asset purchases", "Purchase of fixed assets", "Capital work", "Capex"])
    if not capex_row:
        logger.warning(f"Capex sub-row not found for {ticker.upper()}; falling back to abs(Cash from Investing Activity)")
        capex = [abs(c) if c is not None else None for c in cfi]
    else:
        capex = _slice_row([abs(c) if c is not None else None for c in capex_row])
        
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
            # Dividers are already handled in _parse_float (strips '%')
            # But we must divide by 100 to get decimal
            insider_ownership = promoters[-1] / 100.0

    # Top Ratios
    top_ratios = soup.find('ul', id='top-ratios')
    ratios_dict = {}
    if top_ratios:
        for li in top_ratios.find_all('li'):
            name_span = li.find('span', class_='name')
            num_span = li.find('span', class_='number')
            if name_span and num_span:
                # Stock P/E might be empty if there are no earnings
                val_text = num_span.text.strip()
                ratios_dict[name_span.text.strip().lower()] = val_text

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
        # Check if the raw text had a % sign to avoid double dividing, although _parse_float strips it.
        # Dividend Yield is usually provided as a percentage (e.g. 0.41), so divide by 100.
        dividend_yield = div_yield_val / 100.0

    logger.warning(f"Stock beta not available on screener.in; defaulting to 1.0 for {ticker.upper()}")
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
    
    # Dates
    fin["years"] = [f"{y}-03-31" if y is not None else "Unknown" for y in years_sliced]
    
    # Apply Crore -> Rupee conversion
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
    
    fin["historical_shares"] = [shares_out] * 4 if shares_out else [None]*4
    fin["book_value_per_share"] = (fin["total_equity"][-1] / shares_out) if shares_out and shares_out > 0 and len(fin["total_equity"]) > 0 and fin["total_equity"][-1] is not None else 0.0

    # Save to Cache
    price_dict = {"current_price": current_price}
    cache.set_json(cache_key_fin, fin)
    cache.set_json(cache_key_price, price_dict)

    return fin
