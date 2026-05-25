# Fixture inputs for snapshot testing
FIXTURE_RISK_FREE_RATE = 0.06

FIXTURE_MACRO = {
    "mature_market_erp": 0.05,
    "country_risk_premium": 0.02,
    "total_erp": 0.07,
    "industry_unlevered_beta": 0.90,
    "industry_levered_beta": 1.05
}

FIXTURE_INPUTS = {
    "ticker": "FICTITIOUS.NS",
    "current_price": 50.0,
    "shares_outstanding": 10.0,
    "market_cap": 500.0,
    "years": ["2022-12-31", "2023-12-31", "2024-12-31", "2025-12-31"],
    "revenue": [100.0, 110.0, 121.0, 133.1],
    "gross_profit": [40.0, 44.0, 48.4, 53.24],
    "ebit": [20.0, 22.0, 24.2, 26.62],
    "interest_expense": [2.0, 2.0, 2.0, 2.0],
    "tax_provision": [4.5, 5.0, 5.55, 6.155],
    "pretax_income": [18.0, 20.0, 22.2, 24.62],
    "net_income": [13.5, 15.0, 16.65, 18.465],
    "total_assets": [100.0, 110.0, 121.0, 133.1],
    "total_equity": [60.0, 66.0, 72.6, 79.86],
    "cash": [10.0, 11.0, 12.1, 13.31],
    "debt": [20.0, 20.0, 20.0, 20.0],
    "capex": [5.0, 5.5, 6.05, 6.655],
    "depreciation": [3.0, 3.3, 3.63, 3.993],
    "working_capital_change": [0.0, 0.0, 0.0, 0.0],
    "fcf": [11.5, 12.8, 14.23, 15.803]
}
