import requests
import json
import logging
import re
from data import cache

logger = logging.getLogger(__name__)

TTL_PRICES = 24 * 60 * 60
TTL_FINANCIALS = 7 * 24 * 60 * 60

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

def _resolve_sveltekit_node(data_array: list, idx):
    """Recursively resolves a SvelteKit devalue node graph."""
    if not isinstance(idx, int):
        return idx
    if idx < 0 or idx >= len(data_array):
        return None
    val = data_array[idx]
    if isinstance(val, list):
        return [_resolve_sveltekit_node(data_array, i) for i in val]
    if isinstance(val, dict):
        return {k: _resolve_sveltekit_node(data_array, v) for k, v in val.items()}
    return val

def _fetch_sveltekit_data(url: str, target_keys: list[str]) -> dict:
    """
    Fetches the __data.json endpoint and scans the node graph for objects
    containing any of the target keys, returning the resolved dictionary.
    """
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    try:
        data = resp.json()
    except json.JSONDecodeError:
        raise ValueError(f"Failed to parse JSON from {url}")
    
    nodes = data.get("nodes", [])
    for node in nodes:
        node_data = node.get("data", [])
        if not node_data:
            continue
        for item in node_data:
            if isinstance(item, dict):
                # If this dictionary contains our target key, resolve and return it
                if any(k in item for k in target_keys):
                    resolved = {k: _resolve_sveltekit_node(node_data, v) for k, v in item.items()}
                    return resolved
    return {}

def _extract_dividend_yield(div_str: str) -> float:
    """Extracts percentage float from a string like '$1.04 (0.33%)'."""
    if not div_str or not isinstance(div_str, str):
        return 0.0
    match = re.search(r'\(([0-9.]+)%\)', div_str)
    if match:
        try:
            return float(match.group(1)) / 100.0
        except ValueError:
            return 0.0
    return 0.0

def fetch_stockanalysis_financials(ticker: str) -> dict:
    """
    Returns Sidwell's standard financials dict, scraped from stockanalysis.com.
    Integrates with existing data/cache.py TTL caching.
    """
    ticker = ticker.lower()
    
    # 1. Cache Check
    cache_key_fin = f"financials_stockanalysis_{ticker}.json"
    cached_fin = cache.get_json(cache_key_fin, TTL_FINANCIALS)
    
    cache_key_price = f"price_stockanalysis_{ticker}.json"
    cached_price = cache.get_json(cache_key_price, TTL_PRICES)
    
    if cached_fin and cached_price:
        logger.info(f"Loaded financials and price for {ticker.upper()} from stockanalysis cache.")
        # Merge price into financials
        cached_fin["current_price"] = cached_price.get("current_price")
        return cached_fin
    
    logger.info(f"Fetching {ticker.upper()} from stockanalysis.com...")
    
    # 2. Fetch the 4 endpoints
    base_url = f"https://stockanalysis.com/stocks/{ticker}"
    
    # Income Statement
    inc_data = _fetch_sveltekit_data(f"{base_url}/financials/__data.json", ["financialData"])
    if not inc_data or "financialData" not in inc_data:
        raise ValueError(f"Could not find financialData on {ticker} income statement.")
    inc = inc_data["financialData"]
    
    # Balance Sheet
    bs_data = _fetch_sveltekit_data(f"{base_url}/financials/balance-sheet/__data.json", ["financialData"])
    bs = bs_data.get("financialData", {})
    
    # Cash Flow
    cf_data = _fetch_sveltekit_data(f"{base_url}/financials/cash-flow-statement/__data.json", ["financialData"])
    cf = cf_data.get("financialData", {})
    
    # Overview (Quote and Stats)
    # The quote and stats are spread out across multiple dictionaries in the overview page's data nodes.
    overview_data = _fetch_sveltekit_data(f"{base_url}/__data.json", ["marketCap", "peRatio", "sharesOut", "beta", "quote", "info"])
    
    # We might need to pull the specific nodes manually since overview is fragmented, 
    # so let's do a broader fetch for overview to ensure we capture quote and stats.
    resp_overview = requests.get(f"{base_url}/__data.json", headers=HEADERS, timeout=15)
    overview_json = resp_overview.json()
    overview_nodes = overview_json.get("nodes", [])
    
    market_cap, shares_out, stock_beta, trailing_pe, dividend_yield = None, None, 1.0, None, 0.0
    current_price = None
    
    for node in overview_nodes:
        node_data = node.get("data", [])
        if not node_data: continue
        for item in node_data:
            if isinstance(item, dict):
                res = {k: _resolve_sveltekit_node(node_data, v) for k, v in item.items()}
                if "marketCap" in res:
                    dividend_yield = _extract_dividend_yield(res.get("dividend"))
                    try:
                        stock_beta = float(res.get("beta", 1.0)) if res.get("beta") is not None else 1.0
                    except (ValueError, TypeError):
                        stock_beta = 1.0
                if "quote" in res and isinstance(res["quote"], dict):
                    current_price = res["quote"].get("p")
    
    # Compute stats cleanly from Income Statement to avoid T/B/M string parsing
    try:
        shares_out = inc.get("sharesDiluted", [0])[0]
        if shares_out is None: shares_out = inc.get("sharesDiluted", [0])[1]
    except (IndexError, TypeError):
        shares_out = 0.0
        
    if shares_out and current_price:
        market_cap = float(shares_out * current_price)
        
    try:
        eps_ttm = inc.get("epsDiluted", [0])[0]
        if eps_ttm is None: eps_ttm = inc.get("epsDiluted", [0])[1]
        if current_price and eps_ttm and eps_ttm > 0:
            trailing_pe = float(current_price / eps_ttm)
    except (IndexError, TypeError):
        trailing_pe = None
    
    # 3. Period Slicing
    # Drop TTM (index 0), take next 4 (indices 1-4), reverse to chronological
    def _slice(arr):
        if not arr or not isinstance(arr, list) or len(arr) < 5:
            return [None, None, None, None]
        return arr[1:5][::-1]
    
    def _slice_sum(arrs):
        # sum multiple arrays element-wise after slicing
        sliced = [_slice(a) for a in arrs]
        res = []
        for i in range(4):
            val = sum(a[i] if a[i] is not None else 0 for a in sliced)
            res.append(val)
        return res

    # 4. Map to Sidwell Financials Dict
    fin = {}
    
    # Overview
    fin["market_cap"] = market_cap
    fin["shares_outstanding"] = shares_out
    fin["current_price"] = current_price
    fin["stock_beta"] = stock_beta
    fin["trailing_pe"] = trailing_pe
    fin["dividend_yield"] = dividend_yield
    fin["insider_ownership"] = 0.0
    fin["recommendation_mean"] = None
    
    # Income
    fin["ticker"] = ticker.upper()
    
    date_keys = _slice(inc.get("datekey"))
    fin["years"] = [str(d)[:10] if d is not None else "Unknown" for d in date_keys]
    
    fin["revenue"] = _slice(inc.get("revenue"))
    fin["gross_profit"] = _slice(inc.get("grossProfit"))
    fin["ebit"] = _slice(inc.get("operatingIncome"))
    
    # Interest expense proxy if missing
    debt_sliced = _slice(bs.get("debt"))
    fin["interest_expense"] = []
    for d in debt_sliced:
        if d is not None:
            fin["interest_expense"].append(d * 0.05)
        else:
            fin["interest_expense"].append(0.0)
    logger.warning(f"interest_expense not available from stockanalysis.com; using proxy = debt × 0.05 for {ticker.upper()}")
    
    fin["tax_provision"] = _slice(inc.get("income_statement_provision_for_income_taxes"))
    fin["pretax_income"] = _slice(inc.get("pretax"))
    fin["net_income"] = _slice(inc.get("netIncome"))
    
    # Balance Sheet
    fin["total_assets"] = _slice(bs.get("assets"))
    fin["total_equity"] = _slice(bs.get("equity"))
    fin["cash"] = _slice(bs.get("totalcash"))
    fin["debt"] = debt_sliced
    
    # Cash Flow
    capex_raw = _slice(cf.get("capex"))
    fin["capex"] = [abs(c) if c is not None else None for c in capex_raw]
    
    fin["depreciation"] = _slice(cf.get("cash_flow_statement_depreciation_and_amortization"))
    
    fin["working_capital_change"] = _slice_sum([
        cf.get("changeInReceivables", []),
        cf.get("cash_flow_statement_changes_in_inventories", []),
        cf.get("cash_flow_statement_changes_in_accounts_payable", []),
        cf.get("cash_flow_statement_changes_in_other_operating_activities", [])
    ])
    
    fin["fcf"] = _slice(cf.get("fcf"))
    fin["historical_shares"] = _slice(inc.get("sharesDiluted"))
    fin["source"] = "stockanalysis.com"
    fin["book_value_per_share"] = fin["total_equity"][-1] / shares_out if shares_out and shares_out > 0 and len(fin["total_equity"]) > 0 and fin["total_equity"][-1] is not None else 0.0

    # 5. Save to Cache
    price_dict = {"current_price": current_price}
    cache.set_json(cache_key_fin, fin)
    cache.set_json(cache_key_price, price_dict)

    return fin
