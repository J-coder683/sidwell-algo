import re
import math
import logging
import pandas as pd
from typing import Dict, List
import simpleeval

from data.public import fetch_financials, fetch_damodaran_data
from data.stooq import fetch_price_history

logger = logging.getLogger(__name__)

def _to_snake_case(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')

def _get_series(data_dict: dict, years: list) -> pd.Series:
    """Helper to convert a list of values to a pandas Series indexed by year."""
    # Ensure years are ints
    int_years = [int(y) for y in years]
    return pd.Series(data_dict, index=int_years)

def build_variables(ticker: str) -> Dict[str, pd.Series]:
    """
    Returns a namespace of TIME-SERIES variables for the ticker.
    Implements explicit token mapping to prevent collisions between statements.
    """
    fin = fetch_financials(ticker)
    if not fin or "statements" not in fin:
        return {}

    statements = fin["statements"]
    years_str = statements.get("years_annual", [])
    if not years_str:
        return {}
        
    years = []
    for y in years_str:
        m = re.search(r'\d{4}', str(y))
        if m:
            years.append(int(m.group()))
            
    if not years:
        return {}
        
    variables: Dict[str, pd.Series] = {}
    annual = statements.get("annual", {})
    
    # Extract all raw rows safely and convert to absolute scale (x 1e7)
    def _extract_stmt(stmt_name: str) -> Dict[str, pd.Series]:
        data = {}
        for row_name, row_values in annual.get(stmt_name, {}).items():
            if not row_values or all(v is None for v in row_values):
                continue
            if len(row_values) == len(years):
                data[_to_snake_case(row_name)] = pd.Series(row_values, index=years) * 1e7
        return data

    pl_raw = _extract_stmt("profit_loss")
    bs_raw = _extract_stmt("balance_sheet")
    cf_raw = _extract_stmt("cash_flow")
    
    # Expose ALL raw rows with collision resolution:
    # 1. Income Statement
    for k, v in pl_raw.items():
        variables[k] = v
        
    # 2. Balance Sheet
    for k, v in bs_raw.items():
        variables[k] = v
        
    # 3. Cash Flow - add change_in_ prefix if it collides with BS or PL
    for k, v in cf_raw.items():
        if k in variables:
            variables[f"change_in_{k}"] = v
        else:
            # Check if it's a known delta from the prompt that requires change_in_
            if k in ["inventory", "receivables", "payables", "working_capital_changes"]:
                variables[f"change_in_{k}"] = v
            else:
                variables[k] = v

    # Explicit Mappings & Aliases
    # Balance Sheet
    def _map(target_token, source_dict, source_keys):
        for sk in source_keys:
            if sk in source_dict:
                variables[target_token] = source_dict[sk]
                break

    _map("inventory", bs_raw, ["inventories", "inventory"])
    _map("accounts_receivable", bs_raw, ["trade_receivables", "receivables"])
    _map("accounts_payable", bs_raw, ["trade_payables", "payables"])
    _map("cash", bs_raw, ["cash_equivalents", "cash"])
    _map("debt", bs_raw, ["borrowings", "debt"])
    _map("equity", bs_raw, ["reserves", "total_equity", "equity"])
    _map("fixed_assets", bs_raw, ["fixed_assets"])
    _map("investments", bs_raw, ["investments"])
    _map("total_assets", bs_raw, ["total_assets"])
    _map("total_liabilities", bs_raw, ["total_liabilities"])
    _map("total_current_assets", bs_raw, ["total_current_assets", "current_assets"])
    _map("total_current_liabilities", bs_raw, ["total_current_liabilities", "current_liabilities"])

    # Cash Flow
    _map("change_in_inventory", cf_raw, ["inventory"])
    _map("change_in_receivables", cf_raw, ["receivables"])
    _map("change_in_payables", cf_raw, ["payables"])
    _map("change_in_working_capital", cf_raw, ["working_capital_changes"])
    _map("cfo", cf_raw, ["cash_from_operating_activity"])
    
    if "fixed_assets_purchased" in cf_raw:
        variables["capex"] = cf_raw["fixed_assets_purchased"].abs()

    # Income Statement & Aliases
    _map("revenue", pl_raw, ["sales", "revenue"])
    if "revenue" in variables: variables["sales"] = variables["revenue"]
    
    _map("cogs", pl_raw, ["cogs", "cost_of_goods_sold", "material_cost"])
    _map("gross_profit", pl_raw, ["gross_profit"])
    
    _map("operating_profit", pl_raw, ["operating_profit", "ebit"])
    if "operating_profit" in variables: variables["ebit"] = variables["operating_profit"]
    
    _map("depreciation", pl_raw, ["depreciation"])
    _map("interest", pl_raw, ["interest"])
    _map("pretax_income", pl_raw, ["profit_before_tax", "pretax_income"])
    _map("tax", pl_raw, ["tax"])
    
    _map("net_profit", pl_raw, ["net_profit", "net_income"])
    if "net_profit" in variables: variables["net_income"] = variables["net_profit"]

    # 2. PRESET RATIOS
    ratios_raw = {}
    for row_name, row_values in statements.get("ratios", {}).items():
        if not row_values or all(v is None for v in row_values): continue
        if len(row_values) == len(years):
            ratios_raw[_to_snake_case(row_name)] = pd.Series(row_values, index=years)
            variables[_to_snake_case(row_name)] = ratios_raw[_to_snake_case(row_name)]

    def get_v(token: str) -> pd.Series:
        return variables.get(token, pd.Series(dtype=float))
        
    def safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
        if a.empty or b.empty: return pd.Series(dtype=float)
        df = pd.DataFrame({"a": a, "b": b}).dropna()
        res = df["a"] / df["b"].replace(0, pd.NA)
        return res.dropna()

    sales = get_v("revenue")
    cogs = get_v("cogs")
    gross_profit = get_v("gross_profit")
    operating_profit = get_v("operating_profit")
    net_profit = get_v("net_profit")
    fcf = get_v("fcf")
    equity = get_v("equity")
    total_assets = get_v("total_assets")
    debt = get_v("debt")
    interest = get_v("interest")
    inventory = get_v("inventory")
    ar = get_v("accounts_receivable")
    ap = get_v("accounts_payable")
    current_assets = get_v("total_current_assets")
    current_liabilities = get_v("total_current_liabilities")

    if not sales.empty:
        if not gross_profit.empty and "gross_margin" not in variables: variables["gross_margin"] = safe_div(gross_profit, sales)
        if not operating_profit.empty and "operating_margin" not in variables: variables["operating_margin"] = safe_div(operating_profit, sales)
        if not net_profit.empty and "net_margin" not in variables: variables["net_margin"] = safe_div(net_profit, sales)
        if not fcf.empty and "fcf_margin" not in variables: variables["fcf_margin"] = safe_div(fcf, sales)
        if not total_assets.empty and "asset_turnover" not in variables: variables["asset_turnover"] = safe_div(sales, total_assets)
            
    if not net_profit.empty:
        if not equity.empty and "roe" not in variables: variables["roe"] = safe_div(net_profit, equity)
        if not total_assets.empty and "roa" not in variables: variables["roa"] = safe_div(net_profit, total_assets)
            
    if not debt.empty and not equity.empty and "debt_to_equity" not in variables:
        variables["debt_to_equity"] = safe_div(debt, equity)
        
    if not operating_profit.empty and not interest.empty and "interest_coverage" not in variables:
        variables["interest_coverage"] = safe_div(operating_profit, interest)

    if not sales.empty and not ar.empty and "dso" not in variables: variables["dso"] = safe_div(ar, sales) * 365
    if not cogs.empty and not inventory.empty and "dio" not in variables: variables["dio"] = safe_div(inventory, cogs) * 365
    if not cogs.empty and not ap.empty and "dpo" not in variables: variables["dpo"] = safe_div(ap, cogs) * 365
        
    dso = get_v("dso")
    dio = get_v("dio")
    dpo = get_v("dpo")
    if not dso.empty and not dio.empty and not dpo.empty and "ccc" not in variables:
        df = pd.DataFrame({"dso": dso, "dio": dio, "dpo": dpo}).dropna()
        variables["ccc"] = df["dio"] + df["dso"] - df["dpo"]
        
    if not current_assets.empty and not current_liabilities.empty:
        if "current_ratio" not in variables: variables["current_ratio"] = safe_div(current_assets, current_liabilities)
        if not inventory.empty and "quick_ratio" not in variables: variables["quick_ratio"] = safe_div(current_assets - inventory, current_liabilities)

    # 3. SCALARS broadcast across years
    try:
        damo = fetch_damodaran_data(ticker, fin)
        beta_val = damo.get("industry_levered_beta") or damo.get("beta")
        if beta_val is not None:
            variables["beta"] = pd.Series([float(beta_val)] * len(years), index=years)
    except Exception as e:
        logger.warning(f"Failed to fetch beta for {ticker}: {e}")

    # 4. PRICE-AWARE
    price_df = fetch_price_history(ticker)
    if not price_df.empty:
        price_df["Year"] = price_df["Date"].dt.year
        last_prices = price_df.sort_values("Date").groupby("Year")["Close"].last()
        
        price_series = pd.Series(index=years, dtype=float)
        for y in years:
            if y in last_prices.index:
                price_series[y] = last_prices[y]
        
        variables["price"] = price_series
        
        shares_val = fin.get("shares_outstanding")
        if shares_val:
            shares = pd.Series([float(shares_val)] * len(years), index=years)
            variables["market_cap_ts"] = price_series * shares
            mcap = variables["market_cap_ts"]
            
            if not net_profit.empty and "pe" not in variables: variables["pe"] = safe_div(mcap, net_profit)
            if not equity.empty and "pb" not in variables: variables["pb"] = safe_div(mcap, equity)
            if not sales.empty and "ev_sales" not in variables:
                cash = get_v("cash")
                if not debt.empty and not cash.empty:
                    variables["ev_sales"] = safe_div(mcap + debt - cash, sales)
                
            cash = get_v("cash")
            depreciation = get_v("depreciation")
            if not debt.empty and not cash.empty and not operating_profit.empty and not depreciation.empty:
                ev = mcap + debt - cash
                ebitda = operating_profit + depreciation
                variables["ev_ebitda"] = safe_div(ev, ebitda)

    return variables

def list_variables(ticker: str) -> Dict[str, List[str]]:
    """Returns grouped token dictionary for the UI."""
    vars_dict = build_variables(ticker)
    tokens = set(vars_dict.keys())
    
    # Grouping definitions
    groups = {
        "Income statement": ["revenue", "sales", "cogs", "gross_profit", "operating_profit", "ebit", "depreciation", "interest", "pretax_income", "tax", "net_profit", "net_income"],
        "Balance sheet (levels)": ["inventory", "accounts_receivable", "accounts_payable", "cash", "debt", "equity", "fixed_assets", "investments", "total_assets", "total_liabilities", "total_current_assets", "total_current_liabilities"],
        "Cash flow (changes)": ["change_in_inventory", "change_in_receivables", "change_in_payables", "change_in_working_capital", "cfo", "capex"],
        "Ratios": ["gross_margin", "operating_margin", "net_margin", "fcf_margin", "roe", "roa", "roic", "asset_turnover", "debt_to_equity", "interest_coverage", "dso", "dio", "dpo", "ccc", "current_ratio", "quick_ratio"],
        "Price-based": ["price", "market_cap_ts", "pe", "pb", "ev_ebitda", "ev_sales", "beta"]
    }
    
    result = {k: [] for k in groups.keys()}
    result["Other (raw)"] = []
    
    categorized = set()
    for group_name, expected_tokens in groups.items():
        for t in expected_tokens:
            if t in tokens:
                result[group_name].append(t)
                categorized.add(t)
                
    for t in sorted(tokens):
        if t not in categorized:
            result["Other (raw)"].append(t)
            
    # Clean up empty groups
    return {k: sorted(v) for k, v in result.items() if v}

def evaluate_formula(formula: str, variables: Dict[str, pd.Series]) -> pd.Series:
    """
    Evaluates a math formula safely over time-series variables.
    Handles offsets like name[t-1].
    """
    if not formula or not formula.strip():
        return pd.Series(dtype=float)
        
    formula = formula.replace("^", "**")
    
    # Find offsets: name[t-1], name[t+2], name[t]
    # We will replace them with synthetic names: name__off_m1, name__off_p2, name__off_0
    
    def offset_replacer(match):
        base_name = match.group(1)
        sign = match.group(2) or ""
        offset_val = match.group(3)
        
        if not offset_val:
            offset = 0
        else:
            offset = int(offset_val)
            if sign == "-":
                offset = -offset
                
        if offset == 0:
            return base_name
        elif offset < 0:
            return f"{base_name}__off_m{abs(offset)}"
        else:
            return f"{base_name}__off_p{offset}"

    processed_formula = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\[t([+-]?)(\d*)\]', offset_replacer, formula)
    
    # Collect all tokens required
    # simpleeval can parse, but we can just provide the namespace for all years.
    # Find union of all years
    all_years = set()
    for s in variables.values():
        all_years.update(s.dropna().index)
    
    if not all_years:
        return pd.Series(dtype=float)
        
    sorted_years = sorted(list(all_years))
    
    functions = {
        "sqrt": math.sqrt,
        "log": math.log,
        "ln": math.log,
        "exp": math.exp,
        "abs": abs,
        "min": min,
        "max": max
    }
    
    # Validate formula syntax and unknown names early
    dummy_names = {}
    formula_tokens = set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', processed_formula))
    for token in formula_tokens:
        if token in functions:
            continue
        # check if it's a synthetic token
        m = re.match(r'(.+)__off_[mp]\d+$', token)
        base = m.group(1) if m else token
        
        if base not in variables:
            raise ValueError(f"Unknown variable: {base}")
            
        dummy_names[token] = 1.0
        
    try:
        simpleeval.simple_eval(processed_formula, names=dummy_names, functions=functions)
    except Exception as e:
        raise ValueError(f"Invalid formula: {str(e)}")
        
    result = {}
    
    for y in sorted_years:
        # Build names for this year
        names = {}
        for base_token, series in variables.items():
            # Add base token
            if y in series.index and not pd.isna(series[y]):
                names[base_token] = series[y]
                
            # Add synthetic offsets if they were requested (we can just proactively add them)
            # Actually, we can just extract what's in the processed formula to avoid generating too many
            # but simpler to just regex search the processed formula for __off_
            
        # To handle offsets accurately, let's parse the processed formula for base_token__off_m/p
        offset_tokens = set(re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)__off_([mp])(\d+)', processed_formula))
        for base_token, sign, val in offset_tokens:
            if base_token in variables:
                offset_int = int(val)
                if sign == 'm':
                    offset_int = -offset_int
                target_year = y + offset_int
                series = variables[base_token]
                synth_name = f"{base_token}__off_{sign}{val}"
                if target_year in series.index and not pd.isna(series[target_year]):
                    names[synth_name] = series[target_year]
                else:
                    # Missing offset -> NaN for this year
                    names[synth_name] = float('nan')

        try:
            # We must be able to evaluate. If a name is missing, simpleeval raises NameNotDefined
            val = simpleeval.simple_eval(processed_formula, names=names, functions=functions)
            if val is not None and not pd.isna(val) and not (isinstance(val, float) and math.isinf(val)):
                result[y] = val
        except simpleeval.NameNotDefined as e:
            # Missing token for this year, skip year
            continue
        except ZeroDivisionError:
            continue
        except Exception as e:
            # For genuinely invalid formula, simpleeval raises Exception.
            # E.g. SyntaxError
            raise ValueError(f"Invalid formula: {str(e)}")
            
    return pd.Series(result)
