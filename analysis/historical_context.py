"""
Build a compact Markdown summary of historical financials to prepend to the
DeepSeek prompt so the model anchors its forward assumptions to reality.

Source: StatementsEngine.map_historical — same numbers the engine uses.
Units:  INR mm (crore × 10, already done by map_historical).
"""
from sidwell.engine.statements import StatementsEngine


def build_historical_context_md(financials: dict) -> str:
    """Return a Markdown block with three tables (P&L, WC-days, WC-balances).

    Returns "" when financials has no usable statements (safe to prepend to
    any prompt without error-handling at the call site).
    """
    stmts = (financials or {}).get("statements")
    if not stmts or not stmts.get("years_annual"):
        return ""

    hist  = StatementsEngine.map_historical(stmts)
    years = hist["years_annual"]
    if not years:
        return ""

    is_h  = hist["is"]
    bs_h  = hist["bs"]
    cf_h  = hist["cf"]
    r_h   = hist["ratios"]

    # ── helpers ───────────────────────────────────────────────────────────────

    def _fmt(v):
        """Format a value in INR mm as an integer, or '—' when absent/zero."""
        return "—" if (v is None) else f"{v:,.0f}"

    def _pct1(v):
        """Format a ratio as a percentage with one decimal, or '—'."""
        return "—" if (v is None) else f"{v * 100:.1f}%"

    def _day(series, i):
        """Return a screener day-count, '—' when blank (None → 0.0 after mapping)."""
        v = series[i] if i < len(series) else None
        # 0.0 means screener left it blank (convert_ratio_row maps None→0.0);
        # negatives (WC days −116) are valid and displayed.
        return "—" if (v is None or v == 0.0) else f"{v:.0f}"

    def _recency_weighted_avg(values):
        xs = [v for v in values if v]   # drop None and 0.0
        if not xs:
            return None
        xs = xs[-5:]
        w  = range(1, len(xs) + 1)
        return sum(wi * xi for wi, xi in zip(w, xs)) / sum(w)

    # ── source series ─────────────────────────────────────────────────────────

    sales = is_h.get("sales") or []
    if not any(sales):
        sales = is_h.get("revenue") or []

    op    = is_h.get("operating_profit") or []
    dep   = is_h.get("depreciation") or []
    capex = cf_h.get("derived_capex") or []
    tax   = is_h.get("tax") or []
    pbt   = is_h.get("profit_before_tax") or []
    cogs  = is_h.get("cogs") or []
    divp  = is_h.get("dividend_payout_pct") or []   # screener's payout % (not ratio)

    ar_bs  = bs_h.get("trade_receivables") or []
    inv_bs = bs_h.get("inventories") or []
    ap_bs  = bs_h.get("trade_payables") or []

    dso_s = r_h.get("debtor_days", [])
    dio_s = r_h.get("inventory_days", [])
    dpo_s = r_h.get("days_payable", [])
    wcd_s = r_h.get("working_capital_days", [])

    # ── summary stats ─────────────────────────────────────────────────────────

    def _cagr(series, years_back):
        nz = [s for s in series if s]
        if len(nz) < years_back + 1:
            return None
        w = nz[-(years_back + 1):]
        return (w[-1] / w[0]) ** (1.0 / years_back) - 1.0

    def _avg_ratio(num_s, den_s):
        vals = [n / d for n, d in zip(num_s, den_s) if d and n is not None and d > 0]
        return sum(vals) / len(vals) if vals else None

    cagr3 = _cagr(sales, 3)
    cagr5 = _cagr(sales, 5)
    avg_ebit = _avg_ratio(op, sales)
    avg_cx   = _avg_ratio(capex, sales) if capex else None
    avg_tax  = _avg_ratio(tax, pbt) if pbt else None

    avg_pay_vals = [p / 100.0 for p in divp if p]
    avg_pay = sum(avg_pay_vals) / len(avg_pay_vals) if avg_pay_vals else None

    parts = []
    if cagr3 is not None:
        parts.append(f"3y rev CAGR {cagr3 * 100:.1f}%")
    if cagr5 is not None:
        parts.append(f"5y rev CAGR {cagr5 * 100:.1f}%")
    if avg_ebit is not None:
        parts.append(f"avg EBIT margin {avg_ebit * 100:.1f}%")
    if avg_cx is not None:
        parts.append(f"avg CapEx/Sales {avg_cx * 100:.1f}%")
    if avg_tax is not None:
        parts.append(f"avg tax rate {avg_tax * 100:.1f}%")
    if avg_pay is not None:
        parts.append(f"avg payout {avg_pay * 100:.1f}%")
    summary = " | ".join(parts) if parts else "Insufficient data"

    # ── build output ──────────────────────────────────────────────────────────

    lines = [
        "## Historical Financials (anchor your forecasts to these)",
        f"**Summary**: {summary}",
        "",
        "### P&L",
        "| FY | Revenue (INR mm) | YoY Growth % | EBIT margin % | CapEx/Sales % | Tax % | Dividend payout % |",
        "|---|---|---|---|---|---|---|",
    ]

    for i, fy in enumerate(years):
        rev_v  = sales[i] if i < len(sales) else None
        prev_v = sales[i - 1] if i > 0 and (i - 1) < len(sales) else None
        if i == 0 or prev_v is None or not prev_v or rev_v is None:
            yoy = "—"
        else:
            yoy = f"{(rev_v / prev_v - 1) * 100:.1f}%"

        op_v  = op[i]    if i < len(op)    else None
        cx_v  = capex[i] if i < len(capex) else None
        tax_v = tax[i]   if i < len(tax)   else None
        pbt_v = pbt[i]   if i < len(pbt)   else None

        ebit_m = _pct1(op_v  / rev_v  if (op_v  is not None and rev_v)           else None)
        cx_s   = _pct1(cx_v  / rev_v  if (cx_v  is not None and rev_v)           else None)
        tax_p  = _pct1(tax_v / pbt_v  if (tax_v is not None and pbt_v and pbt_v > 0) else None)

        dp_v = divp[i] if i < len(divp) else None
        div_s = _pct1(dp_v / 100.0 if (dp_v is not None and dp_v) else None)

        lines.append(f"| {fy} | {_fmt(rev_v)} | {yoy} | {ebit_m} | {cx_s} | {tax_p} | {div_s} |")

    lines += [
        "",
        "### Working-capital days (from screener ratios; '—' when blank)",
        "| FY | DSO | DIO | DPO | Working Capital Days |",
        "|---|---|---|---|---|",
    ]
    for i, fy in enumerate(years):
        lines.append(
            f"| {fy} | {_day(dso_s, i)} | {_day(dio_s, i)} |"
            f" {_day(dpo_s, i)} | {_day(wcd_s, i)} |"
        )

    lines += [
        "",
        "### Working-capital balances (use to derive days when ratio is blank)",
        "| FY | Trade Receivables | Inventory | Trade Payables | COGS |",
        "|---|---|---|---|---|",
    ]
    for i, fy in enumerate(years):
        ar_v   = ar_bs[i]  if i < len(ar_bs)  else None
        inv_v  = inv_bs[i] if i < len(inv_bs) else None
        ap_v   = ap_bs[i]  if i < len(ap_bs)  else None
        cogs_v = cogs[i]   if i < len(cogs)   else None
        lines.append(
            f"| {fy} | {_fmt(ar_v)} | {_fmt(inv_v)} | {_fmt(ap_v)} | {_fmt(cogs_v)} |"
        )

    return "\n".join(lines)
