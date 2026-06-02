import pytest
from sidwell.engine.statements import StatementsEngine
from sidwell.ajp.schema import AJP, AJPMeta
from sidwell.render.workbook import WorkbookRenderer

def test_debt_schedule_levered():
    # Setup a levered company historical data
    hist = {
        "years_annual": ["FY2023", "FY2024", "FY2025"],
        "is": {
            "sales": [100.0, 110.0, 121.0],
            "operating_profit": [20.0, 22.0, 24.2],
            "depreciation": [5.0, 5.5, 6.0],
            "interest": [2.0, 2.5, 3.0],
            "profit_before_tax": [18.0, 19.5, 21.2],
            "net_profit": [13.5, 14.625, 15.9],
            "cogs": [50.0, 55.0, 60.5]
        },
        "bs": {
            "borrowings": [25.0, 31.25, 37.5], # Growing debt
            "lease_liabilities": [],
            "cash_equivalents": [10.0, 12.0, 15.0],
            "equity_capital": [50.0, 50.0, 50.0],
            "reserves": [10.0, 15.0, 25.0],
            "trade_receivables": [15.0, 16.5, 18.0],
            "inventories": [10.0, 11.0, 12.0],
            "trade_payables": [12.0, 13.0, 14.0],
            "fixed_assets": [60.0, 62.0, 65.0]
        },
        "cf": {
            "cash_from_operating_activity": [15.0, 16.0, 18.0],
            "fixed_assets_purchased": [-7.0, -7.5, -9.0],
            "proceeds_from_borrowings": [5.0, 6.25, 6.25],
            "repayment_of_borrowings": [0.0, 0.0, 0.0]
        },
        "ratios": {}
    }
    
    ajp_meta = AJPMeta(
        ticker="TEST", as_of="2025-03-31", currency="INR",
        sources_ingested=[], fiscal_year_end_month=3,
        last_actual_fy="FY2025", is_holdco=False, scenario_active="BASE"
    )
    ajp = AJP(meta=ajp_meta, assumptions=[])
    
    # Run projections
    proj = StatementsEngine.run_projections(hist, ajp, explicit_years=5)
    
    # Check Balance Check is 0 for all projected years
    for i, bc in enumerate(proj["balance_check"]):
        assert abs(bc) < 1e-4, f"Balance check failed in year {i} with {bc}"
        
    # Check CF net cash change == delta BS cash
    # Cash in proj is just cash
    # Cash change = proj["cash"][i] - (proj["cash"][i-1] if i > 0 else hist["bs"]["cash_equivalents"][-1])
    # Which is exactly the cash flow formula: net_income + D&A - capex - dnwc - dividends + net_borrowing
    for i in range(5):
        cash_prev = proj["cash"][i-1] if i > 0 else hist["bs"]["cash_equivalents"][-1]
        delta_cash = proj["cash"][i] - cash_prev
        
        # CF net cash change formula
        cfo = proj["net_income"][i] + proj["da"][i] - proj["nwc_change"][i]
        cfi = -proj["capex"][i]
        cff = proj["debt_proceeds"][i] - proj["debt_repayment"][i] - proj["dividends"][i]
        cf_net = cfo + cfi + cff
        
        assert abs(delta_cash - cf_net) < 1e-4, f"Cash change mismatch in year {i}: {delta_cash} vs {cf_net}"
        
    # Render workbook and check Interest formula
    results = {
        "hist": hist,
        "proj": proj,
        "wacc": {
            "rf": 0.05, "total_erp": 0.05, "median_asset_beta": 1.0, "current_levered_beta": 1.0,
            "current_ke": 0.1, "current_wacc": 0.1, "target_levered_beta": 1.0, "target_ke": 0.1,
            "target_wacc": 0.1, "pretax_kd": 0.08, "after_tax_kd": 0.06, "avg_wacc": 0.1
        },
        "terminal": {
            "terminal_growth": 0.03, "exit_multiple": 10.0, "gordon_tv": 1000.0, "multiple_tv": 1000.0, "avg_tv": 1000.0
        },
        "bridge": {
            "cash": 10.0, "debt": 25.0, "nci": 0.0, "preferred": 0.0, "investments": 0.0, "pension": 0.0, "nols": 0.0
        },
        "shares": {
            "diluted_shares": 10.0
        },
        "dcf": {
            "pv_explicit": 100.0, "terminal_value": 1000.0, "pv_terminal": 800.0,
            "enterprise_value": 900.0, "net_debt": 10.0, "equity_value": 890.0,
            "shares_outstanding": 10.0, "intrinsic_value_per_share": 89.0, "terminal_growth_rate": 0.03
        }
    }
    renderer = WorkbookRenderer(results, ajp)
    renderer.render_is()
    renderer.render_debt()
    wb = renderer.wb
    ws_debt = wb["7_Debt_Schedule"]
    ws_is = wb["4_Income_Statement"]
    
    # Find interest formula in Debt Schedule (Row 9)
    # Projection columns start after historical (which is n=3)
    # So col F (6) is first projection year.
    R_RATE = 8
    R_OPEN = 4
    R_INT = 9
    R_CLOSE = 7
    col_p = "F" # first projection year
    col_hist = "E" # last historical year
    int_formula = ws_debt[f"{col_p}{R_INT}"].value
    assert int_formula == f"={col_p}{R_RATE}*{col_p}{R_OPEN}", f"Unexpected interest formula: {int_formula}"
    
    # Check that OPEN references PRIOR column CLOSING
    open_formula = ws_debt[f"{col_p}{R_OPEN}"].value
    assert open_formula == f"={col_hist}{R_CLOSE}", f"Unexpected opening formula: {open_formula}"
    
    # No same-year reference in Interest since it uses OPEN which uses PRIOR CLOSE
    
    # DCF intrinsic unchanged is verified by the existing snapshot tests (assuming we updated the snapshot correctly)
