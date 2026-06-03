from typing import Dict, Any, List, Optional
from sidwell.ajp.schema import AJP, AJPAssumption
from sidwell.ajp.loader import AJPLoader
import statistics

VOLUME_STAGNANT_THRESHOLD = 0.005   # 0.5% — below this, real volume growth ≈ 0
EBIT_PEAK_MULTIPLE = 1.5              # latest margin > 1.5x historical median => treat as peak
EBIT_MIN_HIST_YEARS = 4              # need at least this many margin points to judge a "norm"

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
            "cogs": convert_row(pl.get("cogs", [])),
            "expenses": convert_row(pl.get("expenses", [])),
            "operating_profit": convert_row(pl.get("operating profit", [])),
            "other_income": convert_row(pl.get("other income", [])),
            "depreciation": convert_row(pl.get("depreciation", [])),
            "interest": convert_row(pl.get("interest", [])),
            "profit_before_tax": convert_row(pl.get("profit before tax", [])),
            "tax": convert_row(pl.get("tax", [])),
            "tax_pct": convert_ratio_row(pl.get("tax %", [])),  # screener's effective tax rate (%)
            "net_profit": convert_row(pl.get("net profit", [])),
            "dividend_payout_pct": convert_ratio_row(pl.get("dividend payout %", [])),  # screener's payout %
            # Bank specific
            "revenue": convert_row(pl.get("revenue", [])),
            "financing_profit": convert_row(pl.get("financing profit", []))
        }
        
        # Balance Sheet
        mapped_bs = {
            "equity_capital": convert_row(bs.get("equity capital", [])),
            "reserves": convert_row(bs.get("reserves", [])),
            "borrowings": convert_row(bs.get("borrowings", [])),
            "short_term_borrowings": convert_row(bs.get("short term borrowings", [])),
            "long_term_borrowings": convert_row(bs.get("long term borrowings", [])),
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

        # Ratios (days, %). Working Capital Days is screener's signed net measure
        # (often negative for capital-light businesses) and captures "other" current
        # items the AR/Inv/AP trade legs miss — used to pin the comprehensive NWC.
        mapped_ratios = {
            "debtor_days": convert_ratio_row(ratios.get("debtor days", [])),
            "inventory_days": convert_ratio_row(ratios.get("inventory days", [])),
            "days_payable": convert_ratio_row(ratios.get("days payable", [])),
            "working_capital_days": convert_ratio_row(ratios.get("working capital days", [])),
        }

        # Derive CapEx mathematically from Net Block and D&A: CapEx(t) = Net_Block(t) - Net_Block(t-1) + D&A(t)
        derived_capex = []
        net_block = mapped_bs["fixed_assets"]
        da = mapped_is["depreciation"]
        cf_capex = mapped_cf["fixed_assets_purchased"]
        for i in range(len(net_block)):
            if i == 0:
                # No t-1, use absolute CF CapEx as a fallback
                derived_capex.append(abs(cf_capex[i]) if i < len(cf_capex) else 0.0)
            else:
                nb_t = net_block[i]
                nb_t_minus_1 = net_block[i-1]
                da_t = da[i] if i < len(da) else 0.0
                derived_capex.append(nb_t - nb_t_minus_1 + da_t)
        mapped_cf["derived_capex"] = derived_capex

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
            flow_is = ["sales", "cogs", "expenses", "operating_profit", "other_income", "depreciation",
                       "interest", "profit_before_tax", "tax", "net_profit", "revenue", "financing_profit"]
            flow_cf = ["cfo", "cfi", "cff", "fixed_assets_purchased", "derived_capex", "receivables", "inventory",
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
    def run_projections(hist: Dict[str, Any], ajp: AJP, explicit_years: int = 10,
                        freeze_working_capital: bool = False) -> Dict[str, Any]:
        """
        Runs the 3-statement projection for explicit_years (usually 10).
        Uses fade/convergence for margins and growth.

        freeze_working_capital: set for financial-sector companies (brokers, NBFCs,
        AMCs, insurers — flagged is_financial in the data layer, like is_bank). Their
        balance sheets are dominated by client/settlement float, not operating working
        capital, and the DSO/DIO/DPO-days framework produces a spurious Year-1 ΔNWC
        (the days-based projection bears no relation to the historical float anchor).
        When set, AR/Inv/AP are held flat at their historical anchor so ΔNWC = 0 every
        year and UFCF reduces to NOPAT + D&A − CapEx.
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

        def _recency_weighted_avg(values, max_years=5):
            xs = [v for v in values if v]      # drop None and 0.0 (blank/de-fabricated);
                                               # negatives (e.g. WC days -116) are kept
            if not xs:
                return None
            xs = xs[-max_years:]               # last up to 5 populated years (oldest->newest)
            w = range(1, len(xs) + 1)          # linear weights: oldest=1 … newest=n
            return sum(wi * xi for wi, xi in zip(w, xs)) / sum(w)

        def _clamp(x, lo, hi):
            return max(lo, min(hi, x))

        sales_series = is_h.get("sales") or []
        if not any(sales_series):
            sales_series = is_h.get("revenue") or []
        nz_sales = [s for s in sales_series if s]

        cogs_series = is_h.get("cogs") or []
        cs_ratios = [c / s for c, s in zip(cogs_series, sales_series) if s and s > 0]
        cogs_margin = _clamp(_recency_weighted_avg(cs_ratios) or 0.50, 0.0, 1.0)

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

        # Days from screener's own ratios. convert_ratio_row turned blank cells into
        # 0.0, so filter those out: a *missing* line means 0 days, never a fabricated
        # 30/45 (which used to invent inventory/payables that don't exist).
        default_dso = _recency_weighted_avg(r_h.get("debtor_days", [])) or 0.0
        default_dio = _recency_weighted_avg(r_h.get("inventory_days", [])) or 0.0
        default_dpo = _recency_weighted_avg(r_h.get("days_payable", [])) or 0.0

        # Per-leg balance fallback: when screener left a ratio blank (0.0 after
        # convert_ratio_row) but the actual balance is non-zero, derive the days
        # from the balance sheet.  Receivables indexed to Revenue; Inv/AP to COGS.
        # This ensures a non-zero Inventory projects non-zero inv even without a
        # screener ratio — it never fabricates days when the balance is truly zero.
        if default_dso == 0.0 and nz_sales:
            _last_ar = (bs_h.get("trade_receivables") or [0.0])[-1] or 0.0
            if _last_ar > 0:
                default_dso = (_last_ar / nz_sales[-1]) * 365.0
        _last_cogs_nz = next((c for c in reversed(cogs_series) if c), None)
        if default_dio == 0.0:
            _last_inv = (bs_h.get("inventories") or [0.0])[-1] or 0.0
            if _last_inv > 0 and _last_cogs_nz:
                default_dio = (_last_inv / _last_cogs_nz) * 365.0
        if default_dpo == 0.0:
            _last_ap = (bs_h.get("trade_payables") or [0.0])[-1] or 0.0
            if _last_ap > 0 and _last_cogs_nz:
                default_dpo = (_last_ap / _last_cogs_nz) * 365.0

        # Working Capital Days: screener's signed net measure (captures "other"
        # current items the trade legs miss). Use the recency-weighted average as the
        # forward net-WC ratio; None when screener doesn't report it.
        _wc_avg = _recency_weighted_avg(r_h.get("working_capital_days", []))
        wc_days_target = _clamp(_wc_avg, -270.0, 270.0) if _wc_avg is not None else None

        # AJP working_capital_days (Priority 1) overrides screener average (Priority 2).
        # Gate: value is not None (fallback's value=None distinguishes missing from set).
        _ajp_wcd = AJPLoader.get_assumption_or_fallback(ajp, "working_capital_days", None, "")
        if _ajp_wcd.value is not None:
            wc_days_target = _clamp(float(_ajp_wcd.value), -270.0, 270.0)

        # Priority 3: NWC/Revenue ratio when no WC-days basis (AJP or screener).
        # Uses the broad BS net WC (AR + Inv + Loans&Adv + OCA − AP − OCL).
        # NOTE: screener's other_asset_items / other_liability_items can mix current
        # and non-current — a caveat is recorded in assumptions_used when this path fires.
        nwc_ratio_target = None
        nwc_ratio_caveat = False
        if wc_days_target is None:
            _ar_s  = bs_h.get("trade_receivables")    or []
            _inv_s = bs_h.get("inventories")           or []
            _la_s  = bs_h.get("loans_n_advances")      or []
            _oca_s = bs_h.get("other_asset_items")     or []
            _ap_s  = bs_h.get("trade_payables")        or []
            _ocl_s = bs_h.get("other_liability_items") or []
            _nwc_hist = [
                (_ar_s[i]  if i < len(_ar_s)  else 0.0)
                + (_inv_s[i] if i < len(_inv_s) else 0.0)
                + (_la_s[i]  if i < len(_la_s)  else 0.0)
                + (_oca_s[i] if i < len(_oca_s) else 0.0)
                - (_ap_s[i]  if i < len(_ap_s)  else 0.0)
                - (_ocl_s[i] if i < len(_ocl_s) else 0.0)
                for i in range(len(sales_series))
            ]
            _nwc_rev = [nw / s for nw, s in zip(_nwc_hist, sales_series) if s and s > 0]
            if _nwc_rev:
                nwc_ratio_target = _recency_weighted_avg(_nwc_rev)
                nwc_ratio_caveat = True

        rev_g_s1 = get_val("stage1_revenue_growth", default_growth)
        term_g = get_val("terminal_growth", 0.02)
        
        _s1_assumption = AJPLoader.get_assumption_or_fallback(ajp, "stage1_revenue_growth", None, "")
        term_g_uncapped = term_g
        term_g_volume_capped = False
        term_g_caveat = ""
        _split = getattr(_s1_assumption, "split", None)
        if isinstance(_split, dict):
            try:
                _vol = float(_split.get("volume"))
                _pri = float(_split.get("price"))
            except (TypeError, ValueError):
                _vol = _pri = None
            if _vol is not None and _pri is not None and _vol <= VOLUME_STAGNANT_THRESHOLD:
                _cap = max(_pri, 0.0)   # floor at 0; perpetual growth ≤ pricing pass-through
                if _cap < term_g:
                    term_g_volume_capped = True
                    term_g_caveat = (
                        f"Terminal growth capped from {term_g_uncapped:.3f} to {_cap:.3f}: "
                        f"near-term volume growth ({_vol:.3f}) is stagnant, so perpetual growth "
                        f"cannot exceed price growth ({_pri:.3f})."
                    )
                    term_g = _cap
        target_margin = get_val("ebit_margin_target", _margin)

        # normalized_ebit_margin: mid-cycle base margin for cyclical names (AI-supplied).
        # When present, overrides last-actual peak/trough as the fade start.
        # Gate: value is not None (AJPLoader fallback returns value=None when driver absent).
        _norm_a = AJPLoader.get_assumption_or_fallback(ajp, "normalized_ebit_margin", None, "")
        _norm_margin = _clamp(float(_norm_a.value), 0.02, 0.50) if _norm_a.value is not None else None

        # Cyclical-peak guardrail: if the latest actual EBIT margin is well above the company's own
        # historical median, the last-actual anchor is probably a peak. Normalize the fade start to the
        # median — but only as a BACKSTOP when the AI did not supply normalized_ebit_margin.
        _sales_hist = is_h.get("sales") or is_h.get("revenue") or []
        _op_hist = is_h.get("operating_profit") or []
        _hist_ebit_margins = [o / s for o, s in zip(_op_hist, _sales_hist)
                              if o is not None and s and s > 0]
        _last_actual_margin = _margin   # = last EBIT / last sales (computed above)
        _engine_normalized_margin = None
        ebit_margin_peak_normalized = False
        ebit_margin_peak_caveat = ""
        if _norm_margin is None and len(_hist_ebit_margins) >= EBIT_MIN_HIST_YEARS:
            _med_margin = statistics.median(_hist_ebit_margins)
            if _med_margin > 0 and _last_actual_margin > EBIT_PEAK_MULTIPLE * _med_margin:
                _engine_normalized_margin = _clamp(_med_margin, 0.02, 0.50)
                ebit_margin_peak_normalized = True
                ebit_margin_peak_caveat = (
                    f"Latest EBIT margin ({_last_actual_margin:.1%}) is over {EBIT_PEAK_MULTIPLE:.1f}x the "
                    f"historical median ({_med_margin:.1%}) — likely a cyclical peak. Fade start normalized "
                    f"to the median ({_engine_normalized_margin:.1%}). Engine guardrail; AI supplied no "
                    f"normalized_ebit_margin."
                )

        target_capex_sales = get_val("capex_pct_sales_target", default_capex_sales)
        target_da_sales = 0.0  # retained for compatibility; D&A now uses a PP&E schedule
        tax_rate = get_val("tax_rate", default_tax)
        dep_rate = get_val("da_rate_on_block", default_dep_rate)

        # Historical interest and borrowings
        hist_interest = is_h.get("interest", [])
        hist_borrowings = bs_h.get("borrowings", [])
        
        # Guard effective_rate against zero prior-year borrowings (skip those years; default ~8% if none usable)
        eff_rates = []
        for i in range(1, len(hist_borrowings)):
            if hist_borrowings[i-1] and hist_borrowings[i-1] > 0:
                # IS interest is an expense (positive in screener usually, but take abs to be sure)
                eff_rates.append(abs(hist_interest[i] if i < len(hist_interest) else 0.0) / hist_borrowings[i-1])
        
        default_eff_rate = _clamp(_recency_weighted_avg(eff_rates) or 0.08, 0.04, 0.15)
        effective_rate = get_val("pretax_cost_of_debt_override", default_eff_rate)

        # Historical Debt/EBITDA
        hist_ebitda = []
        for ebit, da_ in zip(is_h.get("operating_profit", []), is_h.get("depreciation", [])):
            hist_ebitda.append((ebit or 0.0) + (da_ or 0.0))
            
        debt_ebitda_ratios = []
        for d, ebitda in zip(hist_borrowings, hist_ebitda):
            if ebitda > 0 and d is not None:
                debt_ebitda_ratios.append(d / ebitda)
        
        debt_ebitda_ratio = _recency_weighted_avg(debt_ebitda_ratios)

        # Dividend payout ratio: AJP overrides historical average.
        # Source: screener's "dividend payout %" (÷100 to get ratio).
        hist_payout = [p / 100.0 for p in is_h.get("dividend_payout_pct", []) if p]
        default_payout = _clamp(_recency_weighted_avg(hist_payout) or 0.0, 0.0, 1.0)
        _ajp_pay = AJPLoader.get_assumption_or_fallback(ajp, "dividend_payout_ratio", None, "")
        dividend_payout = (
            _clamp(float(_ajp_pay.value), 0.0, 1.0)
            if _ajp_pay.value is not None
            else default_payout
        )
        
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

        # Dynamic Competitive Advantage Period (CAP) = number of stage-1 high-growth years.
        # Priority: AI moat read -> cyclical-peak backstop (short CAP) -> default 5.
        # Clamp to [2, explicit_years-2] so there are always >=2 fade years.
        _cap_hi = max(2, explicit_years - 2)
        _cap_a = AJPLoader.get_assumption_or_fallback(ajp, "cap_years", None, "")
        if _cap_a.value is not None:
            stage1_years = int(_clamp(float(_cap_a.value), 2, _cap_hi))
            cap_source = "ai_moat"
        elif ebit_margin_peak_normalized:
            stage1_years = int(_clamp(3, 2, _cap_hi))   # cyclical peak => short advantage period
            cap_source = "engine_cyclical_backstop"
        else:
            stage1_years = int(_clamp(5, 2, _cap_hi))
            cap_source = "default"
        fade_years = explicit_years - stage1_years

        proj["freeze_working_capital"] = freeze_working_capital
        proj["assumptions_used"] = {
            "stage1_revenue_growth": rev_g_s1, "hist_revenue_cagr": hist_cagr,
            "terminal_growth": term_g,
            "terminal_growth_uncapped": term_g_uncapped,
            "terminal_growth_volume_capped": term_g_volume_capped,
            "terminal_growth_caveat": term_g_caveat,
            "ebit_margin_start": (_norm_margin if _norm_margin is not None
                                  else _engine_normalized_margin if _engine_normalized_margin is not None
                                  else _margin),
            "ebit_margin_target": target_margin,
            "normalized_ebit_margin": _norm_margin,
            "ebit_margin_peak_normalized": ebit_margin_peak_normalized,
            "ebit_margin_peak_caveat": ebit_margin_peak_caveat,
            "ebit_margin_last_actual": _last_actual_margin,
            "tax_rate": tax_rate,
            "capex_pct_sales": target_capex_sales, "da_rate_on_block": dep_rate,
            "dso_days": dso_days, "dio_days": dio_days, "dpo_days": dpo_days,
            "working_capital_days": wc_days_target,
            "nwc_ratio_target": nwc_ratio_target,
            "nwc_caveat": (
                "Net WC estimated from mixed current/non-current balance sheet items "
                "(screener reported no Working Capital Days)."
                if nwc_ratio_caveat else None
            ),
            "freeze_working_capital": freeze_working_capital,
            "dividend_payout_ratio": dividend_payout,
            "effective_rate": effective_rate,
            "debt_ebitda_ratio": debt_ebitda_ratio,
            "cap_years": stage1_years,
            "cap_years_source": cap_source,
        }
        
        # Initial values from hist
        last_sales = hist["is"]["sales"][-1] if hist["is"]["sales"] else 0.0
        
        if last_sales == 0.0:
            last_sales = hist["is"]["revenue"][-1] if hist["is"]["revenue"] else 0.0

        last_ebit = hist["is"]["operating_profit"][-1] if hist["is"]["operating_profit"] else 0.0
        last_margin = last_ebit / last_sales if last_sales > 0 else target_margin
        # Apply normalized_ebit_margin: replaces peak/trough last-actual as the fade start.
        if _norm_margin is not None:
            last_margin = _norm_margin
        elif _engine_normalized_margin is not None:
            last_margin = _engine_normalized_margin
        
        last_capex = hist["cf"].get("derived_capex", [0.0])[-1]
        last_capex_sales = last_capex / last_sales if last_sales > 0 else target_capex_sales
        
        last_da = hist["is"]["depreciation"][-1] if hist["is"]["depreciation"] else 0.0
        last_da_sales = last_da / last_sales if last_sales > 0 else target_da_sales
        
        # stage1_years and fade_years are set dynamically above (CAP block).
        
        prev_sales = last_sales
        prev_cogs = prev_sales * cogs_margin
        hist_ar_0 = (hist["bs"]["trade_receivables"][-1] if hist["bs"]["trade_receivables"] else (prev_sales * dso_days / 365.0))
        hist_inv_0 = (hist["bs"]["inventories"][-1] if hist["bs"]["inventories"] else (prev_cogs * dio_days / 365.0))
        hist_ap_0 = (hist["bs"]["trade_payables"][-1] if hist["bs"]["trade_payables"] else (prev_cogs * dpo_days / 365.0))
        
        prev_ar = hist_ar_0
        prev_inv = hist_inv_0
        prev_ap = hist_ap_0

        # Comprehensive net-WC anchor — SAME 4-way precedence as the projection loop
        # below so ΔNWC is continuous (no Year-1 phantom jump).
        #   P1/2: wc_days_target (AJP or screener WC-Days)
        #   P3:   nwc_ratio_target (broad BS NWC / Revenue; skipped when freeze)
        #   P4:   trade-only AR+Inv−AP (last resort)
        if (not freeze_working_capital) and wc_days_target is not None:
            nwc_net_0 = (wc_days_target / 365.0) * prev_sales
        elif (not freeze_working_capital) and nwc_ratio_target is not None:
            nwc_net_0 = nwc_ratio_target * prev_sales
        else:
            nwc_net_0 = hist_ar_0 + hist_inv_0 - hist_ap_0
        other_wc_0 = nwc_net_0 - (hist_ar_0 + hist_inv_0 - hist_ap_0)
        prev_nwc = nwc_net_0

        # To avoid circularity in debt schedule, we will build standard UFCF first.
        # The full 3-statement will be built deterministically here.
        # For simplicity in this core engine logic, we compute the UFCF components explicitly.

        proj["ar"] = []
        proj["inv"] = []
        proj["ap"] = []
        proj["nwc"] = []
        proj["other_wc"] = []
        proj["cogs"] = []
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
            
            cogs = sales * cogs_margin
            proj["cogs"].append(cogs)
            
            # Margin fade
            margin_step = (target_margin - last_margin) / explicit_years
            margin = last_margin + margin_step * (i + 1)
            ebit = sales * margin
            proj["ebit"].append(ebit)
            
            # Taxes -> NOPAT
            nopat = ebit * (1 - tax_rate)
            proj["nopat"].append(nopat)
            
            # Depreciation from a PP&E roll-forward schedule:
            # D&A = opening net block × effective dep rate
            da = proj_net_block * dep_rate
            proj["da"].append(da)
            
            # CapEx projection & fade
            if i < stage1_years:
                capex_step = (target_capex_sales - last_capex_sales) / stage1_years
                capex_pct = last_capex_sales + capex_step * (i + 1)
                capex = sales * capex_pct
            else:
                # Stage 2 fade: converge CapEx to 1.0x D&A to avoid infinite asset stripping or expansion
                capex_base = sales * target_capex_sales
                capex_target = da * 1.0
                fade_progress = (i - stage1_years + 1) / fade_years
                capex = capex_base * (1 - fade_progress) + capex_target * fade_progress
                
            proj["capex"].append(capex)
            
            # Roll block forward
            proj_net_block = proj_net_block + capex - da
            
            # NWC projection via Days. For financials, freeze AR/Inv/AP at the
            # historical anchor (prev_* are unchanged when frozen) so ΔNWC = 0 —
            # their "receivables/payables" are settlement float, not operating WC.
            if freeze_working_capital:
                ar, inv, ap = prev_ar, prev_inv, prev_ap
            else:
                ar = sales * (dso_days / 365.0)
                inv = cogs * (dio_days / 365.0)
                ap = cogs * (dpo_days / 365.0)
            
            proj["ar"].append(ar)
            proj["inv"].append(inv)
            proj["ap"].append(ap)
            
            # Comprehensive net working capital — same 4-way precedence as the anchor:
            #   P1/2 wc_days_target (AJP / screener) → P3 nwc_ratio_target → P4 trade-only.
            # ALL priority-1/2/3 paths are skipped when freeze_working_capital (financials).
            trade_nwc = ar + inv - ap
            if (not freeze_working_capital) and wc_days_target is not None:
                nwc = (wc_days_target / 365.0) * sales
            elif (not freeze_working_capital) and nwc_ratio_target is not None:
                nwc = nwc_ratio_target * sales
            else:
                nwc = trade_nwc
            other_wc = nwc - trade_nwc
            proj["nwc"].append(nwc)
            proj["other_wc"].append(other_wc)

            nwc_change = nwc - prev_nwc
            proj["nwc_change"].append(nwc_change)

            # UFCF
            ufcf = nopat + da - capex - nwc_change
            proj["ufcf"].append(ufcf)

            # Update prev
            prev_sales = sales
            prev_ar = ar
            prev_inv = inv
            prev_ap = ap
            prev_nwc = nwc
            
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
        hist_ar = hist_ar_0
        hist_inv = hist_inv_0
        hist_ap = hist_ap_0
        
        # other_wc_0 folds the Year-0 "other" current items into the anchor so the
        # plug stays constant and the balance ties as other_wc moves over time.
        hist_assets = cash_balance + hist_ar + hist_inv + other_wc_0 + net_fixed_assets
        hist_liab_eq = hist_ap + debt_balance + equity_balance

        net_other_assets = hist_liab_eq - hist_assets
        
        proj["cash"] = []
        proj["debt"] = []
        proj["debt_opening"] = []
        proj["debt_proceeds"] = []
        proj["debt_repayment"] = []
        proj["interest"] = []
        proj["equity"] = []
        proj["net_fixed_assets"] = []
        proj["balance_check"] = []
        proj["taxes"] = []
        proj["net_income"] = []
        proj["dividends"] = []
        
        for i in range(explicit_years):
            # Deterministic Debt Forecast
            ebitda = proj["ebit"][i] + proj["da"][i]
            
            proj["debt_opening"].append(debt_balance)
            
            if ebitda <= 0 or debt_ebitda_ratio is None:
                closing_debt = debt_balance
            else:
                closing_debt = max(0.0, debt_ebitda_ratio * ebitda)
            
            net_borrowing = closing_debt - debt_balance
            proceeds = max(0.0, net_borrowing)
            repayments = max(0.0, -net_borrowing)
            
            proj["debt_proceeds"].append(proceeds)
            proj["debt_repayment"].append(repayments)
            
            # Interest based on beginning debt
            interest_exp = debt_balance * effective_rate
            proj["interest"].append(interest_exp)
            
            debt_balance = closing_debt
            
            # Recalculate Net Income (levered)
            ebit = proj["ebit"][i]
            pbt = ebit - interest_exp
            tax = pbt * tax_rate if pbt > 0 else 0
            net_income = pbt - tax
            
            proj["taxes"].append(tax)
            proj["net_income"].append(net_income)

            # Dividends: financing outflow = NI × payout ratio.
            dividends = net_income * dividend_payout
            proj["dividends"].append(dividends)
            
            # Update Fixed Assets
            net_fixed_assets = net_fixed_assets + proj["capex"][i] - proj["da"][i]
            proj["net_fixed_assets"].append(net_fixed_assets)
            
            # Update Equity: only retained earnings (NI × (1 − payout))
            equity_balance += net_income * (1.0 - dividend_payout)
            proj["equity"].append(equity_balance)
            
            # Cash Roll: ADD net borrowing as a financing inflow
            cash_balance = cash_balance + net_income + proj["da"][i] - proj["nwc_change"][i] - proj["capex"][i] - dividends + net_borrowing
            
            proj["cash"].append(cash_balance)
            proj["debt"].append(debt_balance)
            
            # Balance Check: Assets - Liabilities - Equity. other_wc carries the
            # "other" current items so the net WC equals Working Capital Days.
            total_assets = cash_balance + proj["ar"][i] + proj["inv"][i] + proj["other_wc"][i] + net_fixed_assets + net_other_assets
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

