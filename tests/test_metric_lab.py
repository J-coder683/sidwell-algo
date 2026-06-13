import pytest
import pandas as pd
from analysis.metric_lab import build_variables, evaluate_formula, list_variables
import analysis.metric_lab as ml

@pytest.fixture
def mock_financials(monkeypatch):
    fin_data = {
        "statements": {
            "years_annual": ["2021", "2022", "2023"],
            "annual": {
                "profit_loss": {
                    "Sales": [100.0, 110.0, 120.0],
                    "COGS": [50.0, 55.0, 60.0],
                    "Gross Profit": [50.0, 55.0, 60.0],
                    "Net Profit": [20.0, 25.0, 30.0]
                },
                "balance_sheet": {
                    "Total Assets": [1000.0, 1100.0, 1200.0],
                    "Inventories": [100.0, 110.0, 120.0],
                    "Trade Receivables": [50.0, 60.0, 70.0],
                    "Trade Payables": [40.0, 45.0, 50.0]
                },
                "cash_flow": {
                    "FCF": [10.0, 15.0, 20.0],
                    "Inventory": [-5.0, -10.0, -10.0],
                    "Receivables": [-10.0, -10.0, -10.0],
                    "Payables": [5.0, 5.0, 5.0]
                }
            },
            "ratios": {
                "ROE": [15.0, 16.0, 17.0]
            }
        },
        "shares_outstanding": 100000000.0  # 100 million
    }
    
    price_data = pd.DataFrame({
        "Date": pd.to_datetime(["2021-12-31", "2022-12-31", "2023-12-31"]),
        "Close": [150.0, 160.0, 170.0]
    })
    
    monkeypatch.setattr(ml, "fetch_financials", lambda t: fin_data)
    monkeypatch.setattr(ml, "fetch_damodaran_data", lambda t, f: {"beta": 1.2})
    monkeypatch.setattr(ml, "fetch_price_history", lambda t: price_data if t != "EMPTY_PRICE" else pd.DataFrame(columns=["Date", "Close"]))

def test_build_variables(mock_financials):
    variables = build_variables("MOCK")
    
    # Check aliases
    assert "revenue" in variables
    assert "sales" in variables
    assert variables["revenue"].equals(variables["sales"])
    
    # Check absolute scaling (x 1e7)
    assert "inventory" in variables
    assert "change_in_inventory" in variables
    assert not variables["inventory"].equals(variables["change_in_inventory"])
    assert variables["inventory"][2023] == 120.0 * 1e7
    assert variables["change_in_inventory"][2023] == -10.0 * 1e7
    
    assert "accounts_receivable" in variables
    assert "change_in_receivables" in variables
    assert variables["accounts_receivable"][2023] == 70.0 * 1e7
    
    assert "accounts_payable" in variables
    assert "change_in_payables" in variables
    
    # Price-aware metrics
    assert "price" in variables
    assert "pe" in variables
    
    pe_2023 = variables["pe"][2023]
    assert 5 < pe_2023 < 100
    
    # Ratios stay scale-invariant
    ratio = evaluate_formula("inventory/cogs", variables)
    assert ratio[2023] == (120.0 * 1e7) / (60.0 * 1e7)  # 2.0

def test_build_variables_empty_price(mock_financials):
    variables = build_variables("EMPTY_PRICE")
    assert "price" not in variables
    assert "pe" not in variables

def test_list_variables(mock_financials):
    grouped = list_variables("MOCK")
    assert "Balance sheet (levels)" in grouped
    assert "Cash flow (changes)" in grouped
    
    # Assert both inventory forms exist in their correct groups
    assert "inventory" in grouped["Balance sheet (levels)"]
    assert "change_in_inventory" in grouped["Cash flow (changes)"]

def test_evaluate_formula_basic(mock_financials):
    variables = {
        "sales": pd.Series([100, 200], index=[2021, 2022]),
        "cogs": pd.Series([50, 100], index=[2021, 2022])
    }
    
    res = evaluate_formula("sales - cogs", variables)
    assert res[2021] == 50
    assert res[2022] == 100
    
def test_evaluate_formula_lag(mock_financials):
    variables = {
        "sales": pd.Series([100, 200, 300], index=[2021, 2022, 2023]),
    }
    
    res = evaluate_formula("sales[t] / sales[t-1]", variables)
    assert 2021 not in res # t-1 is 2020 which is missing
    assert res[2022] == 2.0
    assert res[2023] == 1.5

def test_evaluate_formula_missing_token(mock_financials):
    variables = {
        "sales": pd.Series([100], index=[2021])
    }
    # It should not crash but return an empty Series or ignore
    with pytest.raises(ValueError):
         evaluate_formula("sales + unknown", variables)
         
def test_evaluate_formula_divide_by_zero(mock_financials):
    variables = {
        "sales": pd.Series([100, 100], index=[2021, 2022]),
        "cogs": pd.Series([0, 50], index=[2021, 2022])
    }
    
    res = evaluate_formula("sales / cogs", variables)
    assert 2021 not in res # Div by zero dropped
    assert res[2022] == 2.0

def test_evaluate_formula_power():
    variables = {
        "val": pd.Series([2, 3], index=[2021, 2022]),
    }
    res = evaluate_formula("val^2", variables)
    assert res[2021] == 4
    assert res[2022] == 9
