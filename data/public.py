import os
import requests
import pandas as pd
import yfinance as yf
from fredapi import Fred
import logging
from . import cache

logger = logging.getLogger("sidwell.public")

# TTL definitions (in seconds)
TTL_PRICES = 24 * 60 * 60         # 24 hours
TTL_FINANCIALS = 7 * 24 * 60 * 60   # 7 days
TTL_MACRO = 30 * 24 * 60 * 60       # 30 days

# Ticker → Damodaran industry mapping.
# Values must match Damodaran's category strings EXACTLY.
# Validated by category-string audit (see BUILD_NOTES v0.1.1 Category Audit).
TICKER_INDUSTRY_MAP = {
    # Indian consumer / paints / household
    "ASIANPAINT.NS":  "Household Products",
    "BERGEPAINT.NS":  "Household Products",
    "PIDILITIND.NS":  "Chemical (Diversified)",
    "HINDUNILVR.NS":  "Household Products",
    "NESTLEIND.NS":   "Food Processing",
    "ITC.NS":         "Tobacco",
    "BRITANNIA.NS":   "Food Processing",
    # Indian financials
    "HDFCBANK.NS":    "Bank (Money Center)",
    "ICICIBANK.NS":   "Bank (Money Center)",
    "BAJFINANCE.NS":  "Financial Svcs. (Non-bank & Insurance)",
    # Indian IT
    "TCS.NS":         "Software (System & Application)",
    "INFY.NS":        "Software (System & Application)",
    # US placeholders for testing
    "AAPL":           "Computers/Peripherals",
    "MSFT":           "Software (System & Application)",
}

DEFAULT_INDUSTRY = "Chemical (Specialty)"  # conservative fallback when ticker not mapped

def get_industry_for_ticker(ticker: str) -> tuple:
    """
    Returns (industry_name, source_tag) where source_tag is:
      - "mapped":  ticker found in TICKER_INDUSTRY_MAP
      - "default": fell back to DEFAULT_INDUSTRY
    """
    upper = ticker.upper()
    if upper in TICKER_INDUSTRY_MAP:
        return TICKER_INDUSTRY_MAP[upper], "mapped"
    return DEFAULT_INDUSTRY, "default"

def get_beta_sheet_name(beta_path: str, is_india: bool) -> str:
    """
    Determines which sheet to use from Damodaran's betaGlobal.xls.
    Shared by both fetch_damodaran_data and the category-string audit.
    """
    excel_beta = pd.ExcelFile(beta_path)
    # Look for emerging market sheet if India, else US or Global
    for name in excel_beta.sheet_names:
        if is_india and ("emerging" in name.lower() or "emerge" in name.lower()):
            return name
        elif not is_india and ("us" in name.lower() or "global" in name.lower()):
            return name
    # Fall back: prefer "Industry Averages" if it exists, else first sheet
    for name in excel_beta.sheet_names:
        if "industry" in name.lower() or "average" in name.lower():
            return name
    return excel_beta.sheet_names[0]

DAMODARAN_CRP_URL = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xlsx"
DAMODARAN_BETA_URL = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/betaGlobal.xls"

def get_fred_api_key() -> str:
    """
    Get the FRED API key from the environment.
    """
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        # Check if we can find it in a .env file if loaded
        logger.warning("FRED_API_KEY not found in environment variables.")
    return api_key

def fetch_risk_free_rate(ticker: str) -> float:
    """
    Fetch the 10-year risk-free rate from FRED.
    If ticker ends in .NS or .BO, fetches INDIRLTLT01STM (India G-Sec 10Y Yield).
    Otherwise, fetches DGS10 (US 10-Year Treasury yield).
    Values are converted from percentages to decimals (e.g. 7.12% -> 0.0712).
    """
    is_india = ticker.endswith(".NS") or ticker.endswith(".BO")
    series_id = "INDIRLTLT01STM" if is_india else "DGS10"
    cache_key = f"fred_{series_id}.json"
    
    # Try cache
    cached = cache.get_json(cache_key, TTL_MACRO)
    if cached is not None:
        logger.info(f"Loaded risk-free rate for {ticker} ({series_id}) from cache: {cached}%")
        return float(cached) / 100.0
        
    # Fetch from FRED
    api_key = get_fred_api_key()
    if not api_key:
        raise ValueError(
            f"FRED_API_KEY environment variable is required to fetch risk-free rate "
            f"for {ticker} ({series_id}) and no cached data was found."
        )
        
    try:
        logger.info(f"Fetching series {series_id} from FRED...")
        fred = Fred(api_key=api_key)
        series_data = fred.get_series(series_id)
        if series_data.empty:
            raise ValueError(f"FRED returned empty series for {series_id}")
        
        # Drop NaNs and get the latest value
        valid_series = series_data.dropna()
        if valid_series.empty:
            raise ValueError(f"FRED series {series_id} contains only NaNs")
            
        latest_val = float(valid_series.iloc[-1])
        cache.set_json(cache_key, latest_val)
        logger.info(f"Fetched and cached risk-free rate: {latest_val}%")
        return latest_val / 100.0
    except Exception as e:
        logger.error(f"Error fetching risk-free rate from FRED: {e}")
        raise

def fetch_damodaran_data(ticker: str) -> dict:
    """
    Downloads and parses Damodaran's Country Risk Premium (ctryprem.xlsx) and
    Beta by Sector (betaGlobal.xls) spreadsheets.
    Returns a dictionary containing:
      - mature_market_erp: float (e.g. 0.0423)
      - country_risk_premium: float (e.g. 0.0218)
      - total_erp: float (e.g. 0.0641)
      - industry_levered_beta: float (e.g. 1.15)
      - industry_unlevered_beta: float (e.g. 0.95)
      - industry_de_ratio: float (e.g. 0.25)
    """
    is_india = ticker.endswith(".NS") or ticker.endswith(".BO")
    target_country = "India" if is_india else "United States"
    target_industry, industry_source = get_industry_for_ticker(ticker)
    
    cache_key_crp = "damodaran_ctryprem.xlsx"
    cache_key_beta = "damodaran_betaGlobal.xls"
    
    # 1. Handle Country Risk Premium File
    crp_path = cache.get_cache_path(cache_key_crp)
    if cache.is_expired(crp_path, TTL_MACRO) or not os.path.exists(crp_path):
        logger.info(f"Downloading Damodaran CRP file from {DAMODARAN_CRP_URL}...")
        try:
            r = requests.get(DAMODARAN_CRP_URL, headers={"User-Agent": "Sidwell/1.0"}, timeout=30)
            r.raise_for_status()
            cache.set_bytes(cache_key_crp, r.content)
        except Exception as e:
            if os.path.exists(crp_path):
                logger.warning(f"Failed to download CRP file, using expired cache: {e}")
            else:
                raise ValueError(f"Failed to download Damodaran CRP file and no cache exists: {e}")
                
    # 2. Handle Beta File
    beta_path = cache.get_cache_path(cache_key_beta)
    if cache.is_expired(beta_path, TTL_MACRO) or not os.path.exists(beta_path):
        logger.info(f"Downloading Damodaran Beta file from {DAMODARAN_BETA_URL}...")
        try:
            r = requests.get(DAMODARAN_BETA_URL, headers={"User-Agent": "Sidwell/1.0"}, timeout=30)
            r.raise_for_status()
            cache.set_bytes(cache_key_beta, r.content)
        except Exception as e:
            if os.path.exists(beta_path):
                logger.warning(f"Failed to download Beta file, using expired cache: {e}")
            else:
                raise ValueError(f"Failed to download Damodaran Beta file and no cache exists: {e}")

    # 3. Parse CRP
    try:
        # Load sheets
        excel_file = pd.ExcelFile(crp_path)
        # Typically the country premium data is in sheet 1 or a sheet containing 'ERP' or 'country'
        sheet_name = None
        for name in excel_file.sheet_names:
            if "premium" in name.lower() or "erp" in name.lower() or name == excel_file.sheet_names[0]:
                sheet_name = name
                break
        
        df_crp = pd.read_excel(crp_path, sheet_name=sheet_name)
        
        # We need to find the row matching target_country.
        # Often Damodaran's Excel files have title rows at the top, so let's scan for where the country is.
        country_col = None
        country_row_idx = None
        
        # Scan cells to find target country
        for col in df_crp.columns:
            matches = df_crp[df_crp[col].astype(str).str.strip().str.lower() == target_country.lower()]
            if not matches.empty:
                country_col = col
                country_row_idx = matches.index[0]
                break
                
        if country_row_idx is None:
            raise ValueError(f"Could not find country '{target_country}' in Damodaran CRP spreadsheet.")
            
        # Clean headers by looking at the row above or just scanning headers
        # Let's search the row or columns for ERP values.
        # To make it robust, we scan the row containing target_country for numerical values.
        # Typically:
        # - Mature Market ERP is around 4% - 4.5% (0.04 - 0.045)
        # - India CRP is around 2.0% - 2.5% (0.02 - 0.025)
        # - India Total ERP is around 6.0% - 7.5% (0.06 - 0.075)
        # If columns contain names, let's map them.
        row_data = df_crp.loc[country_row_idx]
        
        # Let's inspect the headers to find "Equity Risk Premium" or "Total ERP" or similar.
        # If headers are messy, we'll try to find columns by name.
        col_list = [str(c).lower() for c in df_crp.columns]
        
        # Check if we can find headers in the first few rows
        header_row_idx = None
        for i in range(max(0, country_row_idx - 5), country_row_idx):
            row_str = df_crp.iloc[i].astype(str).str.lower().values
            if any("risk premium" in val or "crp" in val or "erp" in val for val in row_str):
                header_row_idx = i
                break
                
        if header_row_idx is not None:
            headers = df_crp.iloc[header_row_idx].astype(str).str.strip().tolist()
        else:
            headers = [str(c).strip() for c in df_crp.columns]
            
        mature_erp = 0.0423  # Fallback to Jan 2026 estimate if not found
        crp = 0.0218        # Fallback to Jan 2026 estimate if not found
        total_erp = 0.0641
        
        # Locate indices in headers
        mature_col_idx = None
        crp_col_idx = None
        total_col_idx = None
        
        for idx, h in enumerate(headers):
            h_low = h.lower()
            if "mature" in h_low and "premium" in h_low:
                mature_col_idx = idx
            elif ("country risk premium" in h_low or "crp" in h_low or "country premium" in h_low) and not "total" in h_low:
                crp_col_idx = idx
            elif "total equity risk premium" in h_low or "total erp" in h_low or ("equity risk premium" in h_low and "total" in h_low):
                total_col_idx = idx
                
        # If we couldn't find columns by header names, we search values by range
        # Let's look at the cells in row_data
        nums = []
        for val in row_data:
            try:
                # remove % if string
                if isinstance(val, str):
                    val = val.replace("%", "").strip()
                fval = float(val)
                if 0 < fval < 1:
                    nums.append(fval)
                elif 1 <= fval <= 15:
                    nums.append(fval / 100.0)
            except:
                pass
                
        if len(nums) >= 2:
            # Sort numbers. Smallest is typically CRP, middle is Mature ERP, largest is Total ERP (or vice versa).
            # e.g., CRP = 2.18%, Mature ERP = 4.23%, Total ERP = 6.41%
            # Let's map them carefully.
            # In India: CRP = ~2.18%, Mature = ~4.23%, Total = ~6.41%
            nums.sort()
            if len(nums) == 2:
                # We have two rates. Say, CRP and Total ERP. Mature ERP is Total - CRP.
                crp = nums[0]
                total_erp = nums[1]
                mature_erp = total_erp - crp
            else:
                # We have 3 or more rates.
                # Let's assume:
                # CRP is the country premium
                # Mature ERP is mature market
                # Total ERP is sum
                # Let's see: 2.18% + 4.23% = 6.41%.
                # So the largest is total_erp. The other two are mature_erp and crp.
                total_erp = nums[-1]
                # Usually mature_erp is larger than CRP for India. So nums[1] is mature_erp, nums[0] is CRP.
                crp = nums[0]
                mature_erp = nums[1]
        else:
            # Fall back to structured column indices if found
            if mature_col_idx is not None:
                val = row_data.iloc[mature_col_idx]
                mature_erp = float(val.replace("%", "").strip()) / 100.0 if isinstance(val, str) else float(val)
            if crp_col_idx is not None:
                val = row_data.iloc[crp_col_idx]
                crp = float(val.replace("%", "").strip()) / 100.0 if isinstance(val, str) else float(val)
            if total_col_idx is not None:
                val = row_data.iloc[total_col_idx]
                total_erp = float(val.replace("%", "").strip()) / 100.0 if isinstance(val, str) else float(val)
            else:
                total_erp = mature_erp + crp
                
        # If target_country is US, CRP is 0.
        if target_country.lower() == "united states":
            crp = 0.0
            total_erp = mature_erp
            
    except Exception as e:
        logger.error(f"Error parsing Damodaran CRP Excel: {e}")
        # Default fallbacks if parsing failed completely but download succeeded
        if target_country == "India":
            mature_erp = 0.0423
            crp = 0.0218
            total_erp = 0.0641
        else:
            mature_erp = 0.0423
            crp = 0.0
            total_erp = 0.0423
            
    # 4. Parse Betas
    try:
        sheet_beta = get_beta_sheet_name(beta_path, is_india)
            
        df_beta = pd.read_excel(beta_path, sheet_name=sheet_beta)
        
        # Scan for target_industry row
        ind_row_idx = None
        for col in df_beta.columns:
            matches = df_beta[df_beta[col].astype(str).str.strip().str.lower().str.contains(target_industry.lower(), na=False)]
            if not matches.empty:
                ind_row_idx = matches.index[0]
                break
                
        if ind_row_idx is None:
            # Try a broader search for "Chemical"
            for col in df_beta.columns:
                matches = df_beta[df_beta[col].astype(str).str.strip().str.lower().str.contains("chemical", na=False)]
                if not matches.empty:
                    ind_row_idx = matches.index[0]
                    break
                    
        if ind_row_idx is None:
            raise ValueError(f"Could not find industry matching '{target_industry}' in Damodaran beta spreadsheet.")
            
        row_data = df_beta.loc[ind_row_idx]
        
        # Scan the row for numbers to extract levered beta, D/E ratio, and unlevered beta.
        # Typically:
        # Columns in Damodaran beta sheet are:
        # Industry Name, Number of Firms, Beta (Levered), D/E Ratio, Effective Tax Rate, Unlevered Beta...
        # Let's extract numbers.
        nums = []
        for val in row_data:
            try:
                fval = float(val)
                nums.append(fval)
            except:
                pass
                
        # Let's map columns by searching headers.
        # We find headers row:
        header_row_idx = None
        for i in range(max(0, ind_row_idx - 5), ind_row_idx):
            row_str = df_beta.iloc[i].astype(str).str.lower().values
            if any("beta" in val or "unlevered" in val or "d/e" in val for val in row_str):
                header_row_idx = i
                break
                
        headers = []
        if header_row_idx is not None:
            headers = df_beta.iloc[header_row_idx].astype(str).str.strip().tolist()
            
        levered_beta = 1.15      # Specialty Chemical EM default
        unlevered_beta = 0.95    # Specialty Chemical EM default
        de_ratio = 0.25
        
        levered_idx = None
        unlevered_idx = None
        de_idx = None
        
        for idx, h in enumerate(headers):
            h_low = h.lower()
            if "unlevered" in h_low and "beta" in h_low:
                unlevered_idx = idx
            elif "levered" in h_low and "beta" in h_low:
                levered_idx = idx
            elif "beta" in h_low and not "unlevered" in h_low and not "total" in h_low:
                # If both levered and unlevered exist, the simple "beta" or "average beta" is the levered beta.
                if levered_idx is None:
                    levered_idx = idx
            elif "d/e" in h_low or "debt/equity" in h_low:
                de_idx = idx
                
        if levered_idx is not None:
            levered_beta = float(row_data.iloc[levered_idx])
        if unlevered_idx is not None:
            unlevered_beta = float(row_data.iloc[unlevered_idx])
        if de_idx is not None:
            # D/E ratio might be percentage or decimal.
            val = row_data.iloc[de_idx]
            de_ratio = float(val.replace("%", "").strip()) / 100.0 if isinstance(val, str) else float(val)
            if de_ratio > 10.0:  # e.g., 25% written as 25.0
                de_ratio = de_ratio / 100.0
                
    except Exception as e:
        logger.error(f"Error parsing Damodaran Beta Excel: {e}")
        # Default fallbacks
        levered_beta = 1.15
        unlevered_beta = 0.95
        de_ratio = 0.25
        
    res = {
        "mature_market_erp": mature_erp,
        "country_risk_premium": crp,
        "total_erp": total_erp,
        "industry_levered_beta": levered_beta,
        "industry_unlevered_beta": unlevered_beta,
        "industry_de_ratio": de_ratio,
        "target_industry": target_industry,
        "industry_source": industry_source,
        "source": "Damodaran NYU Stern (Jan 2026 update)"
    }
    logger.info(f"Loaded Damodaran data: {res}")
    return res

def fetch_financials(ticker: str) -> dict:
    """
    Retrieves 4-year financials and pricing data for a ticker from Yahoo Finance.
    Slices the latest 4 fiscal years and raises ValueError if fewer years are
    available. Implements 7-day cache TTL for financials, 24-hour for price.
    """
    cache_key_fin = f"financials_{ticker}.json"
    cache_key_price = f"price_{ticker}.json"
    
    # Try loading from cache
    cached_fin = cache.get_json(cache_key_fin, TTL_FINANCIALS)
    cached_price = cache.get_json(cache_key_price, TTL_PRICES)
    
    if cached_fin is not None and cached_price is not None:
        logger.info(f"Loaded financials and price for {ticker} from cache.")
        # Combine cache entries
        res = cached_fin.copy()
        res["current_price"] = cached_price["current_price"]
        return res
        
    try:
        logger.info(f"Fetching data for ticker {ticker} from yfinance...")
        yticker = yf.Ticker(ticker)
        
        # Get price and market cap info
        info = yticker.info
        if not info or "currentPrice" not in info and "regularMarketPrice" not in info:
            # Let's fetch history if info fails
            hist = yticker.history(period="1d")
            if hist.empty:
                raise ValueError(f"No price data found for ticker {ticker}")
            current_price = float(hist["Close"].iloc[-1])
        else:
            current_price = float(info.get("currentPrice", info.get("regularMarketPrice", info.get("previousClose", 0.0))))
            
        market_cap = float(info.get("marketCap", 0.0))
        shares_outstanding = float(info.get("sharesOutstanding", 0.0))
        
        if shares_outstanding == 0.0 and market_cap > 0.0 and current_price > 0.0:
            shares_outstanding = market_cap / current_price
        elif market_cap == 0.0 and shares_outstanding > 0.0 and current_price > 0.0:
            market_cap = shares_outstanding * current_price

        # Additional fields for v0.3 lens checks (Buffett 8/9/10, Marks 7/10)
        insider_ownership = float(info.get("heldPercentInsiders", 0.0) or 0.0)
        stock_beta = float(info.get("beta", info.get("beta3Year", 1.0)) or 1.0)
        trailing_pe_raw = info.get("trailingPE", None)
        trailing_pe = float(trailing_pe_raw) if trailing_pe_raw is not None else None
        rec_mean_raw = info.get("recommendationMean", None)  # 1=Strong Buy ... 5=Sell
        recommendation_mean = float(rec_mean_raw) if rec_mean_raw is not None else None
        dividend_yield = float(info.get("dividendYield", 0.0) or 0.0)
            
        # Get statements
        # yfinance returns dataframes where columns are the fiscal year end dates (newest first).
        income = yticker.income_stmt
        balance = yticker.balance_sheet
        cashflow = yticker.cashflow
        
        if income.empty or balance.empty or cashflow.empty:
            # Try financials, balance_sheet, cashflow attributes (sometimes income_stmt is empty but financials works)
            income = yticker.financials if not yticker.financials.empty else income
            balance = yticker.balancesheet if not yticker.balancesheet.empty else balance
            cashflow = yticker.cashflow if not yticker.cashflow.empty else cashflow
            
        if income.empty or balance.empty or cashflow.empty:
            raise ValueError(f"Failed to fetch complete financials for ticker {ticker}. Empty dataframes returned.")
            
        # Extract years (sorted chronologically)
        dates = pd.to_datetime(income.columns)
        sorted_dates = dates.sort_values()
        
        # sorted_dates contains all available years; authoritative 4-year slice is applied below
        years = [d.strftime("%Y-%m-%d") for d in sorted_dates]
        
        # Helper to search for rows in DataFrame
        def get_row(df, possible_names, default=0.0):
            # Check row names case-insensitively and match substrings
            index_clean = [str(idx).strip().lower() for idx in df.index]
            for name in possible_names:
                name_clean = name.strip().lower()
                # Exact match
                if name_clean in index_clean:
                    row_idx = index_clean.index(name_clean)
                    return df.iloc[row_idx]
                # Substring match
                for idx_str in df.index:
                    if name_clean in str(idx_str).lower():
                        return df.loc[idx_str]
            # Return Series of zeros
            return pd.Series(default, index=df.columns)
            
        # Get rows for each year in sorted chronological order
        rev_row = get_row(income, ["Total Revenue", "Revenue"])
        gp_row = get_row(income, ["Gross Profit"])
        ebit_row = get_row(income, ["EBIT", "Operating Income"])
        interest_row = get_row(income, ["Interest Expense", "Interest Expense Income", "Interest Paid"])
        tax_row = get_row(income, ["Tax Provision", "Income Tax Expense"])
        pretax_row = get_row(income, ["Pretax Income", "Income Before Tax"])
        net_inc_row = get_row(income, ["Net Income", "Net Income Common Stockholders"])
        
        assets_row = get_row(balance, ["Total Assets"])
        equity_row = get_row(balance, ["Stockholders Equity", "Total Stockholders Equity", "Common Stock Equity"])
        cash_row = get_row(balance, ["Cash And Cash Equivalents", "Cash Financial", "Cash Cash Equivalents And Short Term Investments"])
        
        # Debt calculation
        # Sum of current debt and long term debt
        lt_debt = get_row(balance, ["Long Term Debt"])
        st_debt = get_row(balance, ["Current Debt", "Short Long Term Debt", "Current Debt And Capital Lease Obligation"])
        total_debt_row = get_row(balance, ["Total Debt"])
        
        # If total debt row is empty or zeros, sum current and long term debt
        calculated_debt = st_debt + lt_debt
        # Replace zero elements in total_debt_row with calculated_debt
        final_debt = []
        for d in sorted_dates:
            td = total_debt_row.get(d, 0.0)
            cd = calculated_debt.get(d, 0.0)
            final_debt.append(float(td if td > 0.0 else cd))
            
        cfo_row = get_row(cashflow, ["Operating Cash Flow", "Cash Flow From Operating Activities"])
        capex_row = get_row(cashflow, ["Capital Expenditure", "Net PPE Purchase And Sale", "Purchase Of Property Plant And Equipment"])
        deprec_row = get_row(cashflow, ["Depreciation And Amortization", "Depreciation Amortization Depletion"])

        # Historical share count — for Buffett check 8 (anti-dilution)
        shares_row = get_row(balance, [
            "Ordinary Shares Number",
            "Share Issued",
            "Common Stock",
        ])
        historical_shares_raw = [float(shares_row.get(d, 0.0)) for d in sorted_dates]
        historical_shares_raw = historical_shares_raw[-4:]

        # NWC change
        nwc_change_row = get_row(cashflow, ["Change In Working Capital", "Working Capital"])
        
        # Collect values chronologically
        revenue = []
        gross_profit = []
        ebit = []
        interest_expense = []
        tax_provision = []
        pretax_income = []
        net_income = []
        total_assets = []
        total_equity = []
        cash = []
        capex = []
        depreciation = []
        working_capital_change = []
        fcf = []
        
        for idx, d in enumerate(sorted_dates):
            r = float(rev_row.get(d, 0.0))
            gp = float(gp_row.get(d, 0.0))
            eb = float(ebit_row.get(d, 0.0))
            ie = float(interest_row.get(d, 0.0))
            tp = float(tax_row.get(d, 0.0))
            pi = float(pretax_row.get(d, 0.0))
            ni = float(net_inc_row.get(d, 0.0))
            
            ast = float(assets_row.get(d, 0.0))
            eq = float(equity_row.get(d, 0.0))
            c = float(cash_row.get(d, 0.0))
            
            cfo = float(cfo_row.get(d, 0.0))
            cx = float(capex_row.get(d, 0.0))
            # Capex is typically negative in yfinance. Ensure it is represented as a positive outflow number here
            cx_abs = abs(cx)
            dep = float(deprec_row.get(d, 0.0))
            
            nwc_chg = float(nwc_change_row.get(d, 0.0))
            
            revenue.append(r)
            gross_profit.append(gp)
            ebit.append(eb)
            # yfinance interest expense is sometimes negative, make it positive
            interest_expense.append(abs(ie))
            tax_provision.append(tp)
            pretax_income.append(pi)
            net_income.append(ni)
            total_assets.append(ast)
            total_equity.append(eq)
            cash.append(c)
            capex.append(cx_abs)
            depreciation.append(dep)
            working_capital_change.append(nwc_chg)
            
            # FCF = CFO - CapEx (capex is outflow, so CFO - cx_abs)
            # If CFO is 0 and we have Net Income, fall back to NI + Dep - CapEx
            f = cfo - cx_abs
            if f == -cx_abs and ni != 0.0:
                f = ni + dep - cx_abs
            fcf.append(f)
            
        # Slice to exactly the last 4 years
        years = years[-4:]
        revenue = revenue[-4:]
        gross_profit = gross_profit[-4:]
        ebit = ebit[-4:]
        interest_expense = interest_expense[-4:]
        tax_provision = tax_provision[-4:]
        pretax_income = pretax_income[-4:]
        net_income = net_income[-4:]
        total_assets = total_assets[-4:]
        total_equity = total_equity[-4:]
        cash = cash[-4:]
        final_debt = final_debt[-4:]
        capex = capex[-4:]
        depreciation = depreciation[-4:]
        working_capital_change = working_capital_change[-4:]
        fcf = fcf[-4:]
        
        # Verify length invariants (raise ValueError for production invariants)
        for list_name, lst in [
            ("years", years), ("revenue", revenue), ("gross_profit", gross_profit),
            ("ebit", ebit), ("interest_expense", interest_expense), ("tax_provision", tax_provision),
            ("pretax_income", pretax_income), ("net_income", net_income), ("total_assets", total_assets),
            ("total_equity", total_equity), ("cash", cash), ("debt", final_debt),
            ("capex", capex), ("depreciation", depreciation), ("working_capital_change", working_capital_change),
            ("fcf", fcf)
        ]:
            if len(lst) != 4:
                raise ValueError(f"Expected exactly 4 years of data for {list_name}, got {len(lst)}")

        financials_data = {
            "ticker": ticker,
            "market_cap": market_cap,
            "shares_outstanding": shares_outstanding,
            "years": years,
            "revenue": revenue,
            "gross_profit": gross_profit,
            "ebit": ebit,
            "interest_expense": interest_expense,
            "tax_provision": tax_provision,
            "pretax_income": pretax_income,
            "net_income": net_income,
            "total_assets": total_assets,
            "total_equity": total_equity,
            "cash": cash,
            "debt": final_debt,
            "capex": capex,
            "depreciation": depreciation,
            "working_capital_change": working_capital_change,
            "fcf": fcf,
            # v0.3 additional fields (degrade to safe defaults if yfinance unavailable)
            "insider_ownership": insider_ownership,
            "stock_beta": stock_beta,
            "trailing_pe": trailing_pe,
            "recommendation_mean": recommendation_mean,
            "dividend_yield": dividend_yield,
            "historical_shares": historical_shares_raw,
            "source": "Yahoo Finance (yfinance)"
        }
        
        # Cache results
        cache.set_json(cache_key_fin, financials_data)
        cache.set_json(cache_key_price, {"current_price": current_price})
        
        res = financials_data.copy()
        res["current_price"] = current_price
        return res
        
    except Exception as e:
        logger.error(f"Error fetching data from Yahoo Finance for ticker {ticker}: {e}")
        # If cache exists, fall back to cache even if expired (offline resiliency)
        cached_fin_fallback = cache.get_json(cache_key_fin, 999999999) # Infinite TTL
        cached_price_fallback = cache.get_json(cache_key_price, 999999999)
        if cached_fin_fallback is not None and cached_price_fallback is not None:
            logger.warning("Failing over to expired cache for financials/price.")
            res = cached_fin_fallback.copy()
            res["current_price"] = cached_price_fallback["current_price"]
            return res
        raise
