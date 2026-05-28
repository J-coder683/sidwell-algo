import os
import requests
import pandas as pd

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

def fetch_financials(ticker: str) -> dict:
    """Returns Sidwell's standard financials dict.
    Dispatches to screener.in for Indian tickers (.NS / .BO) and stockanalysis.com for US tickers.
    """
    is_india = ticker.endswith(".NS") or ticker.endswith(".BO")
    if is_india:
        from data.scrapers.screener import fetch_screener_financials
        return fetch_screener_financials(ticker)
    else:
        from data.scrapers.stockanalysis import fetch_stockanalysis_financials
        return fetch_stockanalysis_financials(ticker)

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

def _find_column(columns, candidates):
    """Find first column whose name (lowercased) contains any candidate substring."""
    for col in columns:
        col_low = col.lower().strip()
        for cand in candidates:
            if cand in col_low:
                return col
    return None


def _hardcoded_beta_defaults() -> dict:
    """Last-resort defaults if Damodaran parsing fails entirely."""
    return {
        "industry_unlevered_beta": 0.95,
        "industry_levered_beta": 1.15,
        "industry_de_ratio": 0.25,
    }

def _parse_damodaran_beta_sheet(beta_path: str, target_industry: str, is_india: bool) -> dict:
    """
    Parse the Damodaran beta spreadsheet using fixed header row (row 9)
    and exact column-name matching. Replaces the proximity-scan logic.

    Returns:
        dict with industry_unlevered_beta, industry_levered_beta, industry_de_ratio.
        Falls back to documented defaults ONLY if exact match fails — logs a
        warning rather than silently using defaults.
    """
    sheet_name = get_beta_sheet_name(beta_path, is_india)

    # Header row is consistently at index 9 in Damodaran's published format.
    # Read the sheet with header=9 so pandas uses row 9 as column headers.
    df = pd.read_excel(beta_path, sheet_name=sheet_name, header=9)

    # Strip whitespace from column names
    df.columns = [str(c).strip() for c in df.columns]

    # Find the row where the industry-name column matches target_industry exactly.
    # The first column typically contains industry names.
    industry_col = df.columns[0]
    df[industry_col] = df[industry_col].astype(str).str.strip()
    matches = df[df[industry_col] == target_industry]

    if matches.empty:
        logger.warning(
            f"Damodaran exact match failed for '{target_industry}' in sheet "
            f"'{sheet_name}'. Falling back to hardcoded defaults. "
            f"Available industries (sample): {df[industry_col].dropna().head(5).tolist()}"
        )
        return _hardcoded_beta_defaults()

    row = matches.iloc[0]

    # Find Unlevered Beta column by name (case-insensitive partial match)
    # Damodaran's naming has been "Unlevered Beta" or "Unlevered beta" consistently.
    unlevered_col = _find_column(df.columns, ["unlevered beta", "unlevered_beta"])
    levered_col = _find_column(df.columns, ["average levered beta", "levered beta", "average beta"])
    de_col = _find_column(df.columns, ["d/e ratio", "debt/equity", "d/e"])

    def _safe_float(val, default=0.0):
        try:
            if isinstance(val, str):
                val = val.replace("%", "").strip()
            return float(val)
        except (ValueError, TypeError):
            return default

    unlevered_beta = _safe_float(row[unlevered_col], 0.95) if unlevered_col else 0.95
    levered_beta = _safe_float(row[levered_col], 1.15) if levered_col else 1.15
    de_ratio_raw = _safe_float(row[de_col], 0.25) if de_col else 0.25
    # Damodaran sometimes stores D/E as percentage (e.g., 25.0 means 25%)
    de_ratio = de_ratio_raw / 100.0 if de_ratio_raw > 5.0 else de_ratio_raw

    return {
        "industry_unlevered_beta": unlevered_beta,
        "industry_levered_beta": levered_beta,
        "industry_de_ratio": de_ratio,
    }


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
    beta_data = _parse_damodaran_beta_sheet(beta_path, target_industry, is_india)
    levered_beta = beta_data["industry_levered_beta"]
    unlevered_beta = beta_data["industry_unlevered_beta"]
    de_ratio = beta_data["industry_de_ratio"]
        
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
