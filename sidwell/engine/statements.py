from typing import Dict, Any, List, Optional
from sidwell.ajp.schema import AJP, AJPAssumption
from sidwell.ajp.loader import AJPLoader

class StatementsEngine:
    """Handles mapping historical data from fin['statements'] and projecting the 3-statement model."""
    
    @staticmethod
    def map_historical(fin_statements: Dict[str, Any]) -> Dict[str, Any]:
        """Maps scraped fin['statements'] (crore) to model historicals (mm)."""
        # Ensure we have data
        if not fin_statements or "years_annual" not in fin_statements:
            return {"years_annual": [], "is": {}, "bs": {}, "cf": {}, "ratios": {}}
            
        # Strip TTM if present (screener scraper already does this, but double check)
        years_annual = fin_statements.get("years_annual", [])
        
        annual = fin_statements.get("annual", {})
        pl = annual.get("profit_loss", {})
        bs = annual.get("balance_sheet", {})
        cf = annual.get("cash_flow", {})
        ratios = fin_statements.get("ratios", {})

        def convert_row(row: List[Optional[float]], multiplier: float = 10.0) -> List[float]:
            # Convert crore to mm (x 10). If None, 0.0
            return [(val * multiplier) if val is not None else 0.0 for val in row]
            
        def convert_ratio_row(row: List[Optional[float]]) -> List[float]:
            # Ratios are not in crore, just keep as is
            return [val if val is not None else 0.0 for val in row]

        # Income Statement
        mapped_is = {
            "sales": convert_row(pl.get("sales", [])),
            "expenses": convert_row(pl.get("expenses", [])),
            "operating_profit": convert_row(pl.get("operating profit", [])),
            "other_income": convert_row(pl.get("other income", [])),
            "depreciation": convert_row(pl.get("depreciation", [])),
            "interest": convert_row(pl.get("interest", [])),
            "profit_before_tax": convert_row(pl.get("profit before tax", [])),
            "tax": convert_row(pl.get("tax", [])),
            "tax_pct": convert_ratio_row(pl.get("tax %", [])),  # screener's effective tax rate (%)
            "net_profit": convert_row(pl.get("net profit", [])),
            # Bank specific
            "revenue": convert_row(pl.get("revenue", [])),
            "financing_profit": convert_row(pl.get("financing profit", []))
        }
        
        # Balance Sheet
        mapped_bs = {
            "equity_capital": convert_row(bs.get("equity capital", [])),
            "reserves": convert_row(bs.get("reserves", [])),
            "borrowings": convert_row(bs.get("borrowings", [])),
            "lease_liabilities": convert_row(bs.get("lease liabilities", [])),
            "non_controlling_int": convert_row(bs.get("non controlling int", [])),
            "trade_payables": convert_row(bs.get("trade payables", [])),
            "other_liability_items": convert_row(bs.get("other liability items", [])),
            "total_liabilities": convert_row(bs.get("total liabilities", [])),
            
            "fixed_assets": convert_row(bs.get("fixed assets", [])),
            "gross_block": convert_row(bs.get("gross block", [])),
            "accumulated_depreciation": convert_row(bs.get("accumulated depreciation", [])),
            "cwip": convert_row(bs.get("cwip", [])),
            "investments": convert_row(bs.get("investments", [])),
            "inventories": convert_row(bs.get("inventories", [])),
            "trade_receivables": convert_row(bs.get("trade receivables", [])),
            "cash_equivalents": convert_row(bs.get("cash equivalents", [])),
            "loans_n_advances": convert_row(bs.get("loans n advances", [])),
            "other_asset_items": convert_row(bs.get("other asset items", [])),
            "total_assets": convert_row(bs.get("total assets", []))
        }
        
        # Cash Flow
        mapped_cf = {
            "cfo": convert_row(cf.get("cash from operating activity", [])),
            "receivables": convert_row(cf.get("receivables", [])),
            "inventory": convert_row(cf.get("inventory", [])),
            "payables": convert_row(cf.get("payables", [])),
            "working_capital_changes": convert_row(cf.get("working capital changes", [])),
            
            "cfi": convert_row(cf.get("cash from investing activity", [])),
            "fixed_assets_purchased": convert_row(cf.get("fixed assets purchased", [])),
            
            "cff": convert_row(cf.get("cash from financing activity", [])),
            "proceeds_from_borrowings": convert_row(cf.get("proceeds from borrowings", [])),
            "repayment_of_borrowings": convert_row(cf.get("repayment of borrowings", []))
        }

        # Ratios (days, %)
        mapped_ratios = {
            "debtor_days": convert_ratio_row(ratios.get("debtor days", [])),
            "inventory_days": convert_ratio_row(ratios.get("inventory days", [])),
            "days_payable": convert_ratio_row(ratios.get("days payable", []))
        }

        # Annualize transition-period columns (e.g. a 15-month stub when a company
        # changes fiscal year — Nestlé). FLOW items (IS, CF) are scaled to 12 months;
        # STOCK items (balance sheet) are left as-is. Ratios (days/%) are unaffected.
        import re as _re
        factors = []
        for y in years_annual:
            mm = _re.search(r"(\d{1,2})\s*m\b", str(y).lower())
            months = int(mm.group(1)) if mm else 12
            factors.append((12.0 / months) if 0 < months != 12 else 1.0)
        if any(fct != 1.0 for fct in factors):
            flow_is = ["sales", "expenses", "operating_profit", "other_income", "depreciation",
                       "interest", "profit_before_tax", "tax", "net_profit", "revenue", "financing_profit"]
            flow_cf = ["cfo", "cfi", "cff", "fixed_assets_purchased", "receivables", "inventory",
                       "payables", "working_capital_changes", "proceeds_from_borrowings", "repayment_of_borrowings"]
            for k in flow_is:
                mapped_is[k] = [(v * factors[i]) if i < len(factors) else v for i, v in enumerate(mapped_is.get(k, []))]
            for k in flow_cf:
                mapped_cf[k] = [(v * factors[i]) if i < len(factors) else v for i, v in enumerate(mapped_cf.get(k, []))]

        return {
            "years_annual": years_annual,
            "is": mapped_is,
            "bs": mapped_bs,
            "cf": mapped_cf,
            "ratios": mapped_ratios
        }

    @staticmethod
    def run_projections(hist: Dict[str, Any], ajp: AJP, explicit_years: int = 10) -> Dict[str, Any]:
        """
        Runs the 3-statement projection for explicit_years (usually 10).
        Uses fade/convergence for margins and growth.
        """
        years_hist = hist["years_annual"]
        if not years_hist:
            return {}
            
        proj = {
            "years": [f"FY{int(years_hist[-1][-4:]) + i + 1}E" for i in range(explicit_years)],
            "revenue": [],
            "ebit": [],
            "nopat": [],
            "da": [],
            "capex": [],
            "nwc_change": [],
            "ufcf": []
        }
        
        scenario = ajp.meta.scenario_active
        
        # Get AJP assumptions with fallbacks
        def get_val(driver_id: str, default: float) -> float:
            a = AJPLoader.get_assumption_or_fallback(ajp, driver_id, default, "Engine fallback")
            if a.scenario:
                if scenario == "BEAR" and a.scenario.BEAR is not None: return a.scenario.BEAR
                if scenario == "BULL" and a.scenario.BULL is not None: return a.scenario.BULL
                if a.scenario.BASE is not None: return a.scenario.BASE
            return float(a.value) if a.value is not None else default

        # ── Data-derived defaults (company-specific; used when the AJP is silent).
        # Growth/tax/capex/margins reflect the company's own history instead of
        # fixed constants. The AJP (Gemini forward judgment) overrides any of them.
        is_h, bs_h, cf_h, r_h = hist["is"], hist["bs"], hist["cf"], hist["ratios"]

        def _avg(xs):
            xs = [x for x in xs if x is not None]
            return (sum(xs) / len(xs)) if xs else None

        def _clamp(x, lo, hi):
            return max(lo, min(hi, x))

        sales_series = is_h.get("sales") or []
        if not any(sales_series):
            sales_series = is_h.get("revenue") or []
        nz_sales = [s for s in sales_series if s]

        if len(nz_sales) >= 2 and nz_sales[0] > 0:
            hist_cagr = (nz_sales[-1] / nz_sales[0]) ** (1.0 / (len(nz_sales) - 1)) - 1.0
        else:
            hist_cagr = 0.08
        default_growth = _clamp(hist_cagr, 0.0, 0.30)

        # Effective tax rate: prefer screener's "tax %" line (already tax/PBT);
        # fall back to (PBT − net profit)/PBT, then to 25%.
        tax_pcts = [tp / 100.0 for tp in is_h.get("tax_pct", []) if tp]
        if not tax_pcts:
            tax_pcts = [(p - n) / p for p, n in zip(is_h.get("profit_before_tax", []), is_h.get("net_profit", []))
                        if p and p > 0 and n is not None]
        default_tax = _clamp(_avg(tax_pcts) if tax_pcts else 0.25, 0.0, 0.45)

        _ns = nz_sales[-1] if nz_sales else 0.0
        _op = is_h.get("operating_profit") or []
        _margin = (_op[-1] / _ns) if (_op and _ns > 0) else 0.10

        capex_series = [abs(c) for c in cf_h.get("fixed_assets_purchased", [])]
        cs_ratios = [c / s for c, s in zip(capex_series, sales_series) if s and s > 0]
        default_capex_sales = _clamp(_avg(cs_ratios) if cs_ratios else 0.05, 0.0, 0.40)

        nb_series = bs_h.get("fixed_assets") or []
        dep_rates = [d / b for d, b in zip(is_h.get("depreciation", []), nb_series) if b and b > 0 and d]
        default_dep_rate = _clamp(_avg(dep_rates) if dep_rates else 0.08, 0.01, 0.40)
        starting_net_block = nb_series[-1] if nb_series else 0.0

        default_dso = _avg(r_h.get("debtor_days", [])) or 45.0
        default_dio = _avg(r_h.get("inventory_days", [])) or 30.0
        default_dpo = _avg(r_h.get("days_payable", [])) or 45.0

        rev_g_s1 = get_val("stage1_revenue_growth", default_growth)
        term_g = get_val("terminal_growth", 0.02)
        target_margin = get_val("ebit_margin_target", _margin)
        target_capex_sales = get_val("capex_pct_sales_target", default_capex_sales)
        target_da_sales = 0.0  # retained for compatibility; D&A now uses a PP&E schedule
        tax_rate = get_val("tax_rate", default_tax)
        dep_rate = get_val("da_rate_on_block", default_dep_rate)
        
        # Working capital fallbacks
        dso_days = get_val("dso_days", default_dso)
        dio_days = get_val("dio_days", default_dio)
        dpo_days = get_val("dpo_days", default_dpo)

        # Sanity-bound every driver (whether from the AJP/Gemini or the historical
        # default) so an extreme forward assumption can't drive the model negative.
        rev_g_s1 = _clamp(rev_g_s1, -0.05, 0.30)
        term_g = _clamp(term_g, 0.0, 0.06)
        target_margin = _clamp(target_margin, 0.02, 0.50)
        target_capex_sales = _clamp(target_capex_sales, 0.0, 0.22)
        tax_rate = _clamp(tax_rate, 0.0, 0.45)
        dep_rate = _clamp(dep_rate, 0.01, 0.40)
        if term_g >= rev_g_s1:
            term_g = max(0.0, rev_g_s1 - 0.01)

        proj["assumptions_used"] = {
            "stage1_revenue_growth": rev_g_s1, "hist_revenue_cagr": hist_cagr,
            "terminal_growth": term_g, "ebit_margin_start": _margin,
            "ebit_margin_target": target_margin, "tax_rate": tax_rate,
            "capex_pct_sales": target_capex_sales, "da_rate_on_block": dep_rate,
            "dso_days": dso_days, "dio_days": dio_days, "dpo_days": dpo_days,
        }
        
        # Initial values from hist
        last_sales = hist["is"]["sales"][-1] if hist["is"]["sales"] else 0.0
        
        if last_sales == 0.0:
            last_sales = hist["is"]["revenue"][-1] if hist["is"]["revenue"] else 0.0

        last_ebit = hist["is"]["operating_profit"][-1] if hist["is"]["operating_profit"] else 0.0
        last_margin = last_ebit / last_sales if last_sales > 0 else target_margin
        
        last_capex = abs(hist["cf"]["fixed_assets_purchased"][-1]) if hist["cf"]["fixed_assets_purchased"] else 0.0
        last_capex_sales = last_capex / last_sales if last_sales > 0 else target_capex_sales
        
        last_da = hist["is"]["depreciation"][-1] if hist["is"]["depreciation"] else 0.0
        last_da_sales = last_da / last_sales if last_sales > 0 else target_da_sales
        
        # Project 10 years (5 years stage 1, 5 years fade)
        stage1_years = 5
        fade_years = explicit_years - stage1_years
        
        prev_sales = last_sales
        prev_ar = (hist["bs"]["trade_receivables"][-1] if hist["bs"]["trade_receivables"] else (prev_sales * dso_days / 365.0))
        prev_inv = (hist["bs"]["inventories"][-1] if hist["bs"]["inventories"] else (prev_sales * dio_days / 365.0))
        prev_ap = (hist["bs"]["trade_payables"][-1] if hist["bs"]["trade_payables"] else (prev_sales * dpo_days / 365.0))
        
        # To avoid circularity in debt schedule, we will build standard UFCF first.
        # The full 3-statement will be built deterministically here.
        # For simplicity in this core engine logic, we compute the UFCF components explicitly.
        
        proj["ar"] = []
        proj["inv"] = []
        proj["ap"] = []
        proj["nwc"] = []
        proj_net_block = starting_net_block  # opening PP&E for the depreciation schedule

        for i in range(explicit_years):
            # Growth fade
            if i < stage1_years:
                g = rev_g_s1
            else:
                # Linear decay to term_g
                step = (rev_g_s1 - term_g) / (fade_years + 1)
                g = rev_g_s1 - step * (i - stage1_years + 1)
                
            sales = prev_sales * (1 + g)
            proj["revenue"].append(sales)
            
            # Margin fade
            margin_step = (target_margin - last_margin) / explicit_years
            margin = last_margin + margin_step * (i + 1)
            ebit = sales * margin
            proj["ebit"].append(ebit)
            
            # Taxes -> NOPAT
            nopat = ebit * (1 - tax_rate)
            proj["nopat"].append(nopat)
            
            # CapEx & D&A fade
            capex_step = (target_capex_sales - last_capex_sales) / explicit_years
            capex_pct = last_capex_sales + capex_step * (i + 1)
            capex = sales * capex_pct
            proj["capex"].append(capex)
            
            # Depreciation from a PP&E roll-forward schedule:
            # D&A = opening net block × effective dep rate; block rolls with capex − D&A.
            da = proj_net_block * dep_rate
            proj["da"].append(da)
            proj_net_block = proj_net_block + capex - da
            
            # NWC projection via Days
            ar = sales * (dso_days / 365.0)
            inv = sales * (dio_days / 365.0)
            ap = sales * (dpo_days / 365.0)
            
            proj["ar"].append(ar)
            proj["inv"].append(inv)
            proj["ap"].append(ap)
            
            # NWC = AR + Inv - AP
            nwc = ar + inv - ap
            proj["nwc"].append(nwc)
            
            nwc_change = nwc - (prev_ar + prev_inv - prev_ap)
            proj["nwc_change"].append(nwc_change)
            
            # UFCF
            ufcf = nopat + da - capex - nwc_change
            proj["ufcf"].append(ufcf)
            
            # Update prev
            prev_sales = sales
            prev_ar = ar
            prev_inv = inv
            prev_ap = ap
            
        # Complete the 3-statement balance and debt schedule
        # Start with historical ending balances
        cash_balance = hist["bs"]["cash_equivalents"][-1] if hist["bs"]["cash_equivalents"] else 0.0
        debt_balance = (hist["bs"]["borrowings"][-1] if hist["bs"]["borrowings"] else 0.0) + \
                       (hist["bs"]["lease_liabilities"][-1] if hist["bs"]["lease_liabilities"] else 0.0)
        equity_balance = (hist["bs"]["equity_capital"][-1] if hist["bs"]["equity_capital"] else 0.0) + \
                         (hist["bs"]["reserves"][-1] if hist["bs"]["reserves"] else 0.0)
        net_fixed_assets = hist["bs"]["fixed_assets"][-1] if hist["bs"]["fixed_assets"] else 0.0
        
        # We must balance the starting historical balance sheet exactly, 
        # so we calculate a 'net_other_assets' plug representing un-modeled items 
        # (like investments, deferred taxes, other liabilities, etc).
        hist_ar = hist["bs"]["trade_receivables"][-1] if hist["bs"]["trade_receivables"] else 0.0
        hist_inv = hist["bs"]["inventories"][-1] if hist["bs"]["inventories"] else 0.0
        hist_ap = hist["bs"]["trade_payables"][-1] if hist["bs"]["trade_payables"] else 0.0
        
        hist_assets = cash_balance + hist_ar + hist_inv + net_fixed_assets
        hist_liab_eq = hist_ap + debt_balance + equity_balance
        
        net_other_assets = hist_liab_eq - hist_assets
        
        proj["cash"] = []
        proj["debt"] = []
        proj["equity"] = []
        proj["net_fixed_assets"] = []
        proj["balance_check"] = []
        proj["taxes"] = []
        proj["net_income"] = []
        
        # Simple interest rate assumed for schedule
        interest_rate = get_val("pretax_cost_of_debt_override", 0.08)
        
        for i in range(explicit_years):
            # Interest based on beginning debt
            interest_exp = debt_balance * interest_rate
            
            # Recalculate Net Income (levered)
            ebit = proj["ebit"][i]
            pbt = ebit - interest_exp
            tax = pbt * tax_rate if pbt > 0 else 0
            net_income = pbt - tax
            
            proj["taxes"].append(tax)
            proj["net_income"].append(net_income)
            
            # Update Fixed Assets
            net_fixed_assets = net_fixed_assets + proj["capex"][i] - proj["da"][i]
            proj["net_fixed_assets"].append(net_fixed_assets)
            
            # Update Equity
            equity_balance += net_income
            proj["equity"].append(equity_balance)
            
            # Levered Free Cash Flow (for debt sweep)
            cfo = net_income + proj["da"][i] - proj["nwc_change"][i]
            cfi = -proj["capex"][i]
            free_cash_flow = cfo + cfi
            
            # Minimum cash balance constraint (e.g. 5% of sales)
            min_cash = proj["revenue"][i] * 0.05
            
            cash_available_for_debt = cash_balance + free_cash_flow - min_cash
            
            if cash_available_for_debt > 0:
                # Pay down debt
                debt_paydown = min(debt_balance, cash_available_for_debt)
                debt_balance -= debt_paydown
                cash_balance = cash_balance + free_cash_flow - debt_paydown
            else:
                # Borrow from revolver
                revolver_draw = -cash_available_for_debt
                debt_balance += revolver_draw
                cash_balance = min_cash
                
            proj["cash"].append(cash_balance)
            proj["debt"].append(debt_balance)
            
            # Balance Check: Assets - Liabilities - Equity
            total_assets = cash_balance + proj["ar"][i] + proj["inv"][i] + net_fixed_assets + net_other_assets
            total_liab = proj["ap"][i] + debt_balance
            total_equity = equity_balance
            
            balance_check = total_assets - total_liab - total_equity
            proj["balance_check"].append(balance_check)
            
            # Raise ValueError on balance sheet mismatch (NOT assert — assert is stripped in -O mode)
            if abs(balance_check) >= 1.0:
                raise ValueError(
                    f"Balance check failed in year {proj['years'][i]}: "
                    f"assets - liabilities - equity = {balance_check:.4f}mm"
                )
            
        return proj

