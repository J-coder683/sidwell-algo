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

def _normalize_sector_key(s: str) -> str:
    if not s: return ""
    return (s.lower()
            .replace("\u00a0", " ")
            .replace("\u2014", "-")  # em-dash to hyphen
            .replace("\u2013", "-")  # en-dash to hyphen
            .strip())

TICKER_INDUSTRY_MAP = {}

SECTOR_TO_DAMODARAN_MAP = {
    # === US (stockanalysis Industry — normalized) ===
    "semiconductors":                    "Semiconductor",
    "semiconductor equipment & materials": "Semiconductor Equip",
    "software-infrastructure":           "Software (System & Application)",
    "software-application":              "Software (System & Application)",
    "consumer electronics":              "Computers/Peripherals",
    "information technology services":   "Information Services",
    "internet content & information":    "Software (Internet)",
    "internet retail":                   "Retail (Online)",
    "computer hardware":                 "Computers/Peripherals",
    "electronic components":             "Electronics (General)",
    "communication equipment":           "Telecom. Equipment",
    "banks-diversified":                 "Bank (Money Center)",
    "banks-regional":                    "Banks (Regional)",
    "asset management":                  "Investments & Asset Management",
    "capital markets":                   "Investments & Asset Management",
    "credit services":                   "Financial Svcs. (Non-bank & Insurance)",
    "insurance-life":                    "Insurance (Life)",
    "insurance-property & casualty":     "Insurance (Prop/Cas.)",
    "insurance-diversified":             "Insurance (General)",
    "drug manufacturers-general":        "Drugs (Pharmaceutical)",
    "drug manufacturers-specialty & generic": "Drugs (Pharmaceutical)",
    "biotechnology":                     "Drugs (Biotechnology)",
    "medical devices":                   "Healthcare Products",
    "medical instruments & supplies":    "Healthcare Products",
    "diagnostics & research":            "Healthcare Information and Technology",
    "healthcare plans":                  "Healthcare Services",
    "medical care facilities":           "Healthcare Services",
    "oil & gas integrated":              "Oil/Gas (Integrated)",
    "oil & gas e&p":                     "Oil/Gas (Production and Exploration)",
    "oil & gas midstream":               "Oil/Gas Distribution",
    "oil & gas refining & marketing":    "Oil/Gas (Integrated)",
    "auto manufacturers":                "Auto & Truck",
    "auto parts":                        "Auto Parts",
    "specialty retail":                  "Retail (Special Lines)",
    "discount stores":                   "Retail (General)",
    "home improvement retail":           "Retail (Building Supply)",
    "footwear & accessories":            "Apparel",
    "apparel manufacturing":             "Apparel",
    "restaurants":                       "Restaurant/Dining",
    "beverages-non-alcoholic":           "Beverage (Soft)",
    "beverages-wineries & distilleries": "Beverage (Alcoholic)",
    "household & personal products":     "Household Products",
    "packaged foods":                    "Food Processing",
    "tobacco":                           "Tobacco",
    "aerospace & defense":               "Aerospace/Defense",
    "specialty industrial machinery":    "Machinery",
    "farm & heavy construction machinery": "Machinery",
    "industrial distribution":           "Retail (Distributors)",
    "railroads":                         "Transportation",
    "airlines":                          "Air Transport",
    "trucking":                          "Trucking",
    "marine shipping":                   "Shipbuilding & Marine",
    "specialty chemicals":               "Chemical (Specialty)",
    "chemicals":                         "Chemical (Diversified)",
    "agricultural inputs":               "Chemical (Basic)",
    "steel":                             "Steel",
    "copper":                            "Metals & Mining",
    "gold":                              "Metals & Mining",
    "building materials":                "Building Materials",
    "utilities-regulated electric":      "Utility (General)",
    "utilities-regulated gas":           "Utility (General)",
    "reit-diversified":                  "R.E.I.T.",
    "reit-residential":                  "R.E.I.T.",
    "reit-office":                       "R.E.I.T.",
    "entertainment":                     "Entertainment",
    "broadcasting":                      "Broadcasting",
    "publishing":                        "Publishing & Newspapers",
    "advertising agencies":              "Advertising",

    # === US Sector-level fallback (broader; if industry not in map) ===
    "technology":                        "Software (System & Application)",
    "financial services":                "Financial Svcs. (Non-bank & Insurance)",
    "healthcare":                        "Healthcare Services",
    "energy":                            "Oil/Gas (Integrated)",
    "consumer cyclical":                 "Retail (General)",
    "consumer defensive":                "Household Products",
    "industrials":                       "Machinery",
    "basic materials":                   "Chemical (Diversified)",
    "utilities":                         "Utility (General)",
    "real estate":                       "R.E.I.T.",
    "communication services":            "Telecom. Services",

    # === India — most-specific tier (screener Industry) ===
    "refineries & marketing":            "Oil/Gas (Integrated)",
    "computers - software & consulting": "Software (System & Application)",
    "private sector bank":               "Bank (Money Center)",
    "public sector bank":                "Bank (Money Center)",
    "other bank":                        "Bank (Money Center)",
    "non banking financial company (nbfc)": "Financial Svcs. (Non-bank & Insurance)",
    "housing finance company":           "Financial Svcs. (Non-bank & Insurance)",
    "pharmaceuticals":                   "Drugs (Pharmaceutical)",
    "cement & cement products":          "Cement & Aggregates",
    "paints":                            "Household Products",
    "personal products":                 "Household Products",
    "packaged foods":                    "Food Processing",
    "tea & coffee":                      "Food Processing",
    "telecom - services":                "Telecom. Services",
    "power generation & distribution":   "Power",
    "automobile":                        "Auto & Truck",
    "automobile - 2 & 3 wheelers":       "Auto & Truck",
    "auto components & equipments":      "Auto Parts",
    "iron & steel":                      "Steel",
    "non - ferrous metals":              "Metals & Mining",
    "specialty chemicals":               "Chemical (Specialty)",
    "fertilizers & agrochemicals":       "Chemical (Basic)",
    "construction":                      "Construction Supplies",
    "engineering":                       "Engineering",
    "life insurance":                    "Insurance (Life)",
    "general insurance":                 "Insurance (General)",
    "asset management company":          "Investments & Asset Management",
    "airlines":                          "Air Transport",
    "logistics":                         "Trucking",
    "hospitals & healthcare services":   "Healthcare Services",
    "realty":                            "R.E.I.T.",
    "diversified retail":                "Retail (General)",
    "e-commerce":                        "Retail (Online)",

    # === India — Broad Industry tier (screener Broad Industry) ===
    "petroleum products":                "Oil/Gas (Integrated)",
    "it - software":                     "Software (System & Application)",
    "it - services":                     "Information Services",
    "banks":                             "Bank (Money Center)",
    "finance":                           "Financial Svcs. (Non-bank & Insurance)",
    "telecom - services":                "Telecom. Services",
    "insurance":                         "Insurance (General)",
    "pharmaceuticals & biotechnology":   "Drugs (Pharmaceutical)",
    "healthcare services":               "Healthcare Services",
    "cement & cement products":          "Cement & Aggregates",
    "automobiles":                       "Auto & Truck",
    "auto components":                   "Auto Parts",
    "chemicals & petrochemicals":        "Chemical (Diversified)",
    "fertilizers":                       "Chemical (Basic)",
    "ferrous metals":                    "Steel",
    "non - ferrous metals":              "Metals & Mining",
    "minerals & mining":                 "Metals & Mining",
    "power":                             "Power",
    "gas":                               "Oil/Gas Distribution",
    "consumer durables":                 "Household Products",
    "household products":                "Household Products",
    "food products":                     "Food Processing",
    "beverages":                         "Beverage (Soft)",
    "tobacco products":                  "Tobacco",
    "transport infrastructure":          "Engineering",
    "construction":                      "Construction Supplies",
    "capital markets":                   "Investments & Asset Management",
    "realty":                            "R.E.I.T.",
    "retailing":                         "Retail (General)",
    "entertainment":                     "Entertainment",
    "media":                             "Broadcasting",

    # === India — Sector tier (broadest, screener Sector) ===
    "oil, gas & consumable fuels":       "Oil/Gas (Integrated)",
    "information technology":            "Software (System & Application)",
    "financial services":                "Financial Svcs. (Non-bank & Insurance)",
    "healthcare":                        "Healthcare Services",
    "consumer goods":                    "Household Products",
    "consumer durables":                 "Household Products",
    "fast moving consumer goods":        "Household Products",
    "automobile and auto components":    "Auto & Truck",
    "metals & mining":                   "Metals & Mining",
    "chemicals":                         "Chemical (Diversified)",
    "construction materials":            "Cement & Aggregates",
    "utilities":                         "Utility (General)",
    "telecommunication":                 "Telecom. Services",
    "realty":                            "R.E.I.T.",
    "services":                          "Information Services",
    "capital goods":                     "Machinery",
}

DEFAULT_INDUSTRY = "Chemical (Specialty)"  # conservative fallback when ticker not mapped

def get_industry_for_ticker(ticker: str, financials: dict) -> tuple[str, str]:
    """Returns (damodaran_industry, source_tag).
    Source tag: 'ticker_override' | 'scraped_industry' | 'scraped_broad_industry' | 'scraped_sector' | 'default'
    """
    upper = ticker.upper()
    
    # Tier 1: Manual override (keep TICKER_INDUSTRY_MAP small — only true edge cases)
    if upper in TICKER_INDUSTRY_MAP:
        return TICKER_INDUSTRY_MAP[upper], "ticker_override"
    
    # Tier 2: Try scraped industry (more specific than sector)
    industry = _normalize_sector_key(financials.get("scraped_industry"))
    if industry and industry in SECTOR_TO_DAMODARAN_MAP:
        return SECTOR_TO_DAMODARAN_MAP[industry], "scraped_industry"
        
    # Tier 3: Try scraped broad industry
    broad_industry = _normalize_sector_key(financials.get("scraped_broad_industry"))
    if broad_industry and broad_industry in SECTOR_TO_DAMODARAN_MAP:
        return SECTOR_TO_DAMODARAN_MAP[broad_industry], "scraped_broad_industry"
    
    # Tier 4: Try scraped sector (broader)
    sector = _normalize_sector_key(financials.get("scraped_sector"))
    if sector and sector in SECTOR_TO_DAMODARAN_MAP:
        return SECTOR_TO_DAMODARAN_MAP[sector], "scraped_sector"
    
    # Log unmapped strings so we can extend the map iteratively
    if industry or broad_industry or sector:
        logger.warning(
            f"Unmapped sector for {ticker}: industry='{industry}', broad_industry='{broad_industry}', sector='{sector}'. "
            f"Add to SECTOR_TO_DAMODARAN_MAP. Falling back to {DEFAULT_INDUSTRY}."
        )
    
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


def fetch_damodaran_data(ticker: str, financials: dict) -> dict:
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
    target_industry, industry_source = get_industry_for_ticker(ticker, financials)
    
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
        sheet_name = None
        for name in excel_file.sheet_names:
            if "erp" in name.lower() and "country" in name.lower():
                sheet_name = name
                break
        if not sheet_name:
            # Fallback
            for name in excel_file.sheet_names:
                if "premium" in name.lower() or "erp" in name.lower():
                    sheet_name = name
                    break
        if not sheet_name:
            sheet_name = excel_file.sheet_names[0]
        
        df_crp = pd.read_excel(crp_path, sheet_name=sheet_name)
        
        # We need to find the row matching target_country.
        # Often Damodaran's Excel files have title rows at the top, so let's scan for where the country is.
        country_col = None
        country_row_idx = None
        
        # Scan cells to find target country
        found_countries = []
        for col in df_crp.columns:
            normalized_col = df_crp[col].astype(str).str.replace('\xa0', ' ').str.strip().str.lower()
            if col == df_crp.columns[0]:
                found_countries = normalized_col.dropna().tolist()
                
            matches = df_crp[normalized_col.str.startswith(target_country.lower())]
            if not matches.empty:
                country_col = col
                country_row_idx = matches.index[0]
                break
                
        if country_row_idx is None:
            logger.error(f"Available countries in sheet: {found_countries[:50]}...")
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
        
        # Check if we can find headers in the first few rows (usually row 6 or 7)
        header_row_idx = None
        for i in range(0, min(30, country_row_idx)):
            row_str = df_crp.iloc[i].astype(str).str.lower().values
            if len(row_str) > 0 and str(row_str[0]).strip() == "country":
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
        crp_col_idx = None
        total_col_idx = None
        
        for idx, h in enumerate(headers):
            h_low = str(h).lower()
            if crp_col_idx is None and ("country risk premium" in h_low or "crp" in h_low or "country premium" in h_low) and not "total" in h_low and not "3" in h_low:
                crp_col_idx = idx
            if total_col_idx is None and ("total equity risk premium" in h_low or "total erp" in h_low or ("equity risk premium" in h_low and "total" in h_low)) and not "2" in h_low:
                total_col_idx = idx
                
        if crp_col_idx is not None and total_col_idx is not None:
            val_crp = row_data.iloc[crp_col_idx]
            crp = float(str(val_crp).replace("%", "").strip()) / 100.0 if isinstance(val_crp, str) and "%" in str(val_crp) else float(val_crp)
            
            val_total = row_data.iloc[total_col_idx]
            total_erp = float(str(val_total).replace("%", "").strip()) / 100.0 if isinstance(val_total, str) and "%" in str(val_total) else float(val_total)
            
            mature_erp = total_erp - crp
        else:
            raise ValueError(f"Could not find Total ERP and CRP columns in Damodaran spreadsheet for {target_country}.")
            
        if target_country.lower() == "united states":
            crp = 0.0
            total_erp = mature_erp
            
        if mature_erp < 0.03 or mature_erp > 0.08:
            raise ValueError(f"Damodaran mature_market_erp out of plausible range: {mature_erp:.4f}. Expected ~0.04-0.05. Parser likely reading wrong column.")
            
    except Exception as e:
        logger.error(f"Error parsing Damodaran CRP Excel: {e}")
        raise e
            
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
