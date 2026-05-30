import openpyxl
from openpyxl.utils import get_column_letter
from typing import Dict, Any
from sidwell.render.formats import Formats
from sidwell.ajp.schema import AJP
from sidwell.ajp.loader import AJPLoader

class WorkbookRenderer:
    def __init__(self, engine_results: Dict[str, Any], ajp: AJP):
        self.results = engine_results
        self.ajp = ajp
        self.wb = openpyxl.Workbook()
        self.wb.remove(self.wb.active) # Remove default sheet
        
    def _create_sheet(self, title: str):
        ws = self.wb.create_sheet(title)
        # Apply standard column widths
        ws.column_dimensions['A'].width = 40
        for i in range(2, 20):
            ws.column_dimensions[get_column_letter(i)].width = 15
        return ws
        
    def _write_header(self, ws, row: int, col: int, text: str):
        cell = ws.cell(row=row, column=col, value=text)
        cell.font = Formats.FONT_HEADER
        cell.fill = Formats.FILL_HEADER

    def _proj_header(self, ws, title):
        """Title + projection year columns (FY..E), banker header style."""
        c = ws.cell(row=2, column=2, value=title)
        c.font = Formats.FONT_HEADER
        c.fill = Formats.FILL_HEADER
        for i, y in enumerate(self.results["proj"]["years"]):
            hc = ws.cell(row=2, column=3 + i, value=self._fy_label(y, "E"))
            hc.font = Formats.FONT_HEADER
            hc.fill = Formats.FILL_HEADER
            hc.alignment = Formats.ALIGN_CENTER

    def _row(self, ws, r, label, values, fmt=None, bold=False):
        lc = ws.cell(row=r, column=2, value=label)
        lc.font = Formats.FONT_BOLD if bold else Formats.FONT_NORMAL
        for i, v in enumerate(values):
            cell = ws.cell(row=r, column=3 + i, value=v)
            cell.number_format = fmt or Formats.FMT_NUMBER
        return r + 1

    def _kv(self, ws, r, label, value, fmt=None, blue=False):
        ws.cell(row=r, column=2, value=label).font = Formats.FONT_BOLD
        cell = ws.cell(row=r, column=3, value=value)
        cell.number_format = fmt or Formats.FMT_NUMBER
        if blue:
            cell.font = Formats.FONT_INPUT
        return r + 1

    def _av_header(self, ws, title):
        """Historical actual (FY..A) + projected (FY..E) year columns. Returns n_hist."""
        c = ws.cell(row=2, column=2, value=title)
        c.font = Formats.FONT_HEADER
        c.fill = Formats.FILL_HEADER
        h_years = self.results.get("hist", {}).get("years_annual", [])
        col = 3
        for y in h_years:
            hc = ws.cell(row=2, column=col, value=self._fy_label(y, "A"))
            hc.font = Formats.FONT_HEADER; hc.fill = Formats.FILL_HEADER; hc.alignment = Formats.ALIGN_CENTER
            col += 1
        for y in self.results["proj"]["years"]:
            hc = ws.cell(row=2, column=col, value=self._fy_label(y, "E"))
            hc.font = Formats.FONT_HEADER; hc.fill = Formats.FILL_HEADER; hc.alignment = Formats.ALIGN_CENTER
            col += 1
        return len(h_years)

    def _av_row(self, ws, r, label, hvals, pvals, n_hist, fmt=None, bold=False):
        """Row across historical (blue) + projected (black) columns. Historical
        cells that are missing (0/None from un-scraped years) are left blank."""
        lc = ws.cell(row=r, column=2, value=label)
        lc.font = Formats.FONT_BOLD if bold else Formats.FONT_NORMAL
        c = 3
        for v in (hvals[-n_hist:] if n_hist else hvals):
            if v:  # skip 0/None → not-reported, leave blank
                cell = ws.cell(row=r, column=c, value=v)
                cell.number_format = fmt or Formats.FMT_NUMBER
                cell.font = Formats.FONT_INPUT  # blue = actual
            c += 1
        for v in pvals:
            cell = ws.cell(row=r, column=c, value=v)
            cell.number_format = fmt or Formats.FMT_NUMBER
            cell.font = Formats.FONT_NORMAL  # black = projected
            c += 1
        return r + 1
        
    def render(self) -> openpyxl.Workbook:
        """Renders the full workbook with 13 sheets and live formulas."""
        self.render_cover()
        self.render_drivers()
        self.render_assumptions()
        self.render_is()
        self.render_bs()
        self.render_cf()
        self.render_debt()
        self.render_fcf()
        self.render_wacc()
        self.render_terminal()
        self.render_bridge()
        self.render_sensitivity()
        self.render_sources()
        return self.wb

    def render_cover(self):
        ws = self._create_sheet("1_Cover")
        ws.cell(row=2, column=2, value="Sidwell DCF Valuation").font = Formats.FONT_BOLD
        ws.cell(row=4, column=2, value="Ticker:")
        ws.cell(row=4, column=3, value=self.ajp.meta.ticker).font = Formats.FONT_BOLD
        ws.cell(row=5, column=2, value="Intrinsic Value (Rs):")
        ws.cell(row=5, column=3, value="='11_Valuation_Bridge'!C13").font = Formats.FONT_LINK
        
    def render_drivers(self):
        ws = self._create_sheet("2_Drivers_Scenarios")
        self._write_header(ws, 2, 2, "Scenario Switch")
        ws.cell(row=3, column=2, value="Active Scenario:")
        
        active_cell = ws.cell(row=3, column=3, value=self.ajp.meta.scenario_active)
        active_cell.font = Formats.FONT_INPUT
        
    def render_assumptions(self):
        ws = self._create_sheet("3_Assumptions_Just")
        self._write_header(ws, 2, 2, "Input")
        self._write_header(ws, 2, 3, "Value")
        self._write_header(ws, 2, 4, "Notes / Justification")
        ws.column_dimensions['D'].width = 80
        
        row = 3
        for a in self.ajp.assumptions:
            ws.cell(row=row, column=2, value=a.driver_id)
            val_cell = ws.cell(row=row, column=3, value=a.value)
            val_cell.font = Formats.FONT_INPUT
            
            note_text = f"[{a.source_type}] {a.rationale}"
            if a.verify_flag or a.confidence in ["LOW", "UNVERIFIED"]:
                note_text += f" [VERIFY: {a.verify_flag or 'UNVERIFIED'}]"
                val_cell.fill = Formats.FILL_FLAGGED
                
            ws.cell(row=row, column=4, value=note_text)
            row += 1

        # When no Gemini AJP is supplied, show the engine's data-derived drivers
        # and their historical basis so the assumptions are still justified.
        if not self.ajp.assumptions:
            au = self.results["proj"].get("assumptions_used", {})
            basis = {
                "stage1_revenue_growth": "Historical 10-yr revenue CAGR",
                "hist_revenue_cagr": "Historical 10-yr revenue CAGR",
                "terminal_growth": "Long-run nominal GDP proxy (fallback 2%)",
                "ebit_margin_start": "Latest historical EBIT margin",
                "ebit_margin_target": "Held at latest margin (no AJP expansion view)",
                "tax_rate": "Avg effective tax (tax / PBT) over history",
                "capex_pct_sales": "Avg capex/sales from 'fixed assets purchased'",
                "da_rate_on_block": "Effective depreciation rate on net fixed-asset base",
                "dso_days": "Historical debtor days",
                "dio_days": "Historical inventory days",
                "dpo_days": "Historical payable days",
            }
            pct_keys = {"stage1_revenue_growth", "hist_revenue_cagr", "terminal_growth",
                        "ebit_margin_start", "ebit_margin_target", "tax_rate",
                        "capex_pct_sales", "da_rate_on_block"}
            for k, v in au.items():
                ws.cell(row=row, column=2, value=k)
                vc = ws.cell(row=row, column=3, value=v)
                vc.font = Formats.FONT_INPUT
                vc.number_format = Formats.FMT_PERCENT if k in pct_keys else '0.0'
                ws.cell(row=row, column=4, value=f"[ENGINE-EST] {basis.get(k, 'Derived from historical data')}")
                row += 1

    @staticmethod
    def _fy_label(raw, suffix):
        """'Mar 2025' -> 'FY2025A'. Extracts a real 4-digit year (handles noisy
        labels like 'Mar 2024\\n...15m' which must NOT become FY2415)."""
        import re
        s = str(raw)
        if s.startswith("FY"):
            return s
        m = re.search(r"(19|20)\d{2}", s)
        return f"FY{m.group(0)}{suffix}" if m else (s.strip()[:7] + suffix)

    def render_is(self):
        """Formula-driven Income Statement: projection DRIVER rows are blue editable
        inputs; Revenue/EBIT/NOPAT/CapEx/D&A are live formulas off those drivers and
        the prior column. All references local to this sheet (robust)."""
        from openpyxl.utils import get_column_letter as L
        F = Formats
        ws = self._create_sheet("4_Income_Statement")
        hist = self.results.get("hist", {})
        proj = self.results["proj"]
        au = proj.get("assumptions_used", {})
        h_is = hist.get("is", {})
        h_cf = hist.get("cf", {})
        h_years = hist.get("years_annual", [])
        n = len(h_years)
        hist_rev = h_is.get("sales") or h_is.get("revenue") or []
        hist_ebit = h_is.get("operating_profit") or []
        hist_np = h_is.get("net_profit") or []
        hist_da = h_is.get("depreciation") or []
        hist_capex = [abs(c) for c in (h_cf.get("fixed_assets_purchased") or [])]
        years = proj["years"]
        ny = len(years)

        t = ws.cell(row=2, column=2, value="Income Statement (Rs mm)")
        t.font = F.FONT_HEADER; t.fill = F.FILL_HEADER
        col = 3
        for y in h_years:
            c = ws.cell(row=2, column=col, value=self._fy_label(y, "A"))
            c.font = F.FONT_HEADER; c.fill = F.FILL_HEADER; c.alignment = F.ALIGN_CENTER
            col += 1
        pc0 = col  # first projection column
        for y in years:
            c = ws.cell(row=2, column=col, value=self._fy_label(y, "E"))
            c.font = F.FONT_HEADER; c.fill = F.FILL_HEADER; c.alignment = F.ALIGN_CENTER
            col += 1

        R_G, R_REV, R_MG, R_EBIT, R_TAX, R_NOP, R_CXP, R_CX, R_DAP, R_DA, R_NP = 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13
        for rr, lab in [(R_G, "Revenue growth %"), (R_REV, "Revenue"), (R_MG, "EBIT margin %"),
                        (R_EBIT, "EBIT"), (R_TAX, "Tax rate %"), (R_NOP, "NOPAT"),
                        (R_CXP, "CapEx % sales"), (R_CX, "CapEx"), (R_DAP, "D&A % sales"),
                        (R_DA, "D&A"), (R_NP, "Net Profit")]:
            ws.cell(row=rr, column=2, value=lab).font = F.FONT_BOLD

        def put_hist(row, vals, fmt=F.FMT_NUMBER):
            for i, v in enumerate(vals[-n:] if n else []):
                if not v:   # missing/un-scraped → leave blank
                    continue
                c = ws.cell(row=row, column=3 + i, value=v)
                c.number_format = fmt; c.font = F.FONT_INPUT
        put_hist(R_REV, hist_rev); put_hist(R_EBIT, hist_ebit)
        put_hist(R_NP, hist_np); put_hist(R_DA, hist_da); put_hist(R_CX, hist_capex)
        # Projected Net Profit (engine net income, after the debt schedule)
        net_inc = proj.get("net_income", proj.get("nopat", []))
        for j, v in enumerate(net_inc):
            cc = ws.cell(row=R_NP, column=pc0 + j, value=v)
            cc.number_format = F.FMT_NUMBER; cc.font = F.FONT_NORMAL

        # Per-year projection drivers from the engine (editable blue inputs)
        prev = hist_rev[-1] if hist_rev else (proj["revenue"][0])
        gr = []
        for v in proj["revenue"]:
            gr.append((v / prev - 1.0) if prev else 0.0); prev = v
        mg = [(e / r if r else 0.0) for e, r in zip(proj["ebit"], proj["revenue"])]
        cxp = [(c / r if r else 0.0) for c, r in zip(proj["capex"], proj["revenue"])]
        dap = [(d / r if r else 0.0) for d, r in zip(proj["da"], proj["revenue"])]
        tax = au.get("tax_rate", 0.25)

        for j in range(ny):
            cc = pc0 + j
            Lc, Lp = L(cc), L(cc - 1)
            for row, val in [(R_G, gr[j]), (R_MG, mg[j]), (R_TAX, tax), (R_CXP, cxp[j]), (R_DAP, dap[j])]:
                c = ws.cell(row=row, column=cc, value=val)
                c.number_format = F.FMT_PERCENT; c.font = F.FONT_INPUT  # blue editable driver
            ws.cell(row=R_REV, column=cc, value=f"={Lp}{R_REV}*(1+{Lc}{R_G})").number_format = F.FMT_NUMBER
            ws.cell(row=R_EBIT, column=cc, value=f"={Lc}{R_REV}*{Lc}{R_MG}").number_format = F.FMT_NUMBER
            ws.cell(row=R_NOP, column=cc, value=f"={Lc}{R_EBIT}*(1-{Lc}{R_TAX})").number_format = F.FMT_NUMBER
            ws.cell(row=R_CX, column=cc, value=f"={Lc}{R_REV}*{Lc}{R_CXP}").number_format = F.FMT_NUMBER
            ws.cell(row=R_DA, column=cc, value=f"={Lc}{R_REV}*{Lc}{R_DAP}").number_format = F.FMT_NUMBER

        # Expose cell coordinates for the FCF sheet
        self._is_ref = {"pc0": pc0, "ny": ny, "R_NOP": R_NOP, "R_DA": R_DA,
                        "R_CX": R_CX, "R_EBIT": R_EBIT}
            
    def render_bs(self):
        ws = self._create_sheet("5_Balance_Sheet")
        n = self._av_header(ws, "Balance Sheet (Rs mm)")
        p = self.results["proj"]
        hb = self.results.get("hist", {}).get("bs", {})

        def add(a, b):
            a = a or []; b = b or []
            return [(a[i] if i < len(a) else 0.0) + (b[i] if i < len(b) else 0.0) for i in range(max(len(a), len(b)))]

        r = 3
        r = self._av_row(ws, r, "Cash", hb.get("cash_equivalents"), p["cash"], n)
        r = self._av_row(ws, r, "Trade Receivables", hb.get("trade_receivables"), p["ar"], n)
        r = self._av_row(ws, r, "Inventories", hb.get("inventories"), p["inv"], n)
        r = self._av_row(ws, r, "Net Fixed Assets", hb.get("fixed_assets"), p["net_fixed_assets"], n)
        r += 1
        r = self._av_row(ws, r, "Trade Payables", hb.get("trade_payables"), p["ap"], n)
        r = self._av_row(ws, r, "Debt", add(hb.get("borrowings"), hb.get("lease_liabilities")), p["debt"], n)
        r = self._av_row(ws, r, "Equity", add(hb.get("equity_capital"), hb.get("reserves")), p["equity"], n)
        r += 1
        lr = ws.cell(row=r, column=2, value="Balance Check (proj, ≈0)")
        lr.font = Formats.FONT_BOLD
        for i, val in enumerate(p["balance_check"]):
            cell = ws.cell(row=r, column=3 + n + i, value=val)
            cell.number_format = Formats.FMT_NUMBER
            if abs(val) > 1.0:
                cell.fill = Formats.FILL_FLAGGED

    def render_cf(self):
        """Cash Flow linked to the Income Statement: Net Income, D&A and CapEx are
        formulas pulling from the IS; CFO and FCF are formulas. CapEx is shown as a
        consistent outflow (negative) in both actuals and projections."""
        from openpyxl.utils import get_column_letter as L
        F = Formats
        ws = self._create_sheet("6_Cash_Flow")
        n = self._av_header(ws, "Cash Flow (Rs mm) — linked to Income Statement")
        p = self.results["proj"]
        ref = getattr(self, "_is_ref", {})
        R_NP, R_DA, R_CX = ref.get("R_NP", 13), ref.get("R_DA", 12), ref.get("R_CX", 10)
        ny = len(p["years"])
        ISN = "'4_Income_Statement'"
        h_is = self.results.get("hist", {}).get("is", {})
        hc = self.results.get("hist", {}).get("cf", {})
        hist_ni = h_is.get("net_profit") or []
        hist_da = h_is.get("depreciation") or []
        hist_cfo = hc.get("cfo") or []
        fap = hc.get("fixed_assets_purchased") or []
        hist_capex = [-(abs(x)) if x else 0.0 for x in fap]            # outflow (negative)
        hist_fcf = [(c or 0.0) - abs(x or 0.0) for c, x in zip(hist_cfo, fap)]

        for rr, lab in [(3, "Net Income"), (4, "Add: Depreciation"), (5, "Less: Change in NWC"),
                        (6, "Cash from Operations"), (7, "Less: CapEx"), (8, "Free Cash Flow")]:
            ws.cell(row=rr, column=2, value=lab).font = F.FONT_BOLD

        def hist(row, vals):
            for i, v in enumerate(vals[-n:] if n else []):
                if v:
                    c = ws.cell(row=row, column=3 + i, value=v)
                    c.number_format = F.FMT_NUMBER; c.font = F.FONT_INPUT
        hist(3, hist_ni); hist(4, hist_da); hist(6, hist_cfo); hist(7, hist_capex); hist(8, hist_fcf)

        nwc = p.get("nwc_change", [0.0] * ny)
        for j in range(ny):
            cc = 3 + n + j            # projection column (aligns to the IS projection column)
            col = L(cc)
            nv = ws.cell(row=5, column=cc, value=-(nwc[j] if j < len(nwc) else 0.0))
            nv.number_format = F.FMT_NUMBER; nv.font = F.FONT_INPUT
            l1 = ws.cell(row=3, column=cc, value=f"={ISN}!{col}{R_NP}"); l1.number_format = F.FMT_NUMBER; l1.font = F.FONT_LINK
            l2 = ws.cell(row=4, column=cc, value=f"={ISN}!{col}{R_DA}"); l2.number_format = F.FMT_NUMBER; l2.font = F.FONT_LINK
            ws.cell(row=6, column=cc, value=f"={col}3+{col}4+{col}5").number_format = F.FMT_NUMBER
            l3 = ws.cell(row=7, column=cc, value=f"=-{ISN}!{col}{R_CX}"); l3.number_format = F.FMT_NUMBER; l3.font = F.FONT_LINK
            ws.cell(row=8, column=cc, value=f"={col}6+{col}7").number_format = F.FMT_NUMBER

    def render_debt(self):
        ws = self._create_sheet("7_Debt_Schedule")
        self._proj_header(ws, "Debt Schedule (Rs mm) — Projected")
        p = self.results["proj"]
        hbs = self.results.get("hist", {}).get("bs", {})
        prev = ((hbs.get("borrowings") or [0.0])[-1] or 0.0) + ((hbs.get("lease_liabilities") or [0.0])[-1] or 0.0)
        debt = p["debt"]
        openings = [prev] + list(debt[:-1])
        net = [cl - op for op, cl in zip(openings, debt)]
        r = 3
        r = self._row(ws, r, "Opening Debt (borrowings + leases)", openings)
        r = self._row(ws, r, "Net Draw / (Paydown)", net)
        r = self._row(ws, r, "Closing Debt", debt, bold=True)
        if prev < 1.0 and (not debt or max(abs(x) for x in debt) < 1.0):
            ws.cell(row=r + 1, column=2,
                    value="(Company is effectively debt-free — schedule is nil.)").font = Formats.FONT_NORMAL

    def render_fcf(self):
        """Live DCF: UFCF = NOPAT + D&A − CapEx − ΔNWC (NOPAT/D&A/CapEx linked from the
        Income Statement), discounted at the WACC (linked from 9_WACC) with a Gordon
        terminal at g (linked from 10_Terminal). Editing any IS driver, the WACC, or g
        recomputes the Enterprise Value here."""
        from openpyxl.utils import get_column_letter as L
        F = Formats
        ws = self._create_sheet("8_FCF_DCF")
        p = self.results["proj"]
        ref = getattr(self, "_is_ref", None)
        if not ref:
            # Fallback to plain values if the IS layout wasn't captured
            self._proj_header(ws, "Unlevered FCF & Discounting (Rs mm)")
            self._row(ws, 3, "Unlevered FCF", p["ufcf"], bold=True)
            return
        pc0, ny = ref["pc0"], ref["ny"]
        R_NOP, R_DA, R_CX = ref["R_NOP"], ref["R_DA"], ref["R_CX"]
        ISN = "'4_Income_Statement'"

        c = ws.cell(row=2, column=2, value="Unlevered FCF & DCF (Rs mm)")
        c.font = F.FONT_HEADER; c.fill = F.FILL_HEADER
        for j, y in enumerate(p["years"]):
            hc = ws.cell(row=2, column=3 + j, value=self._fy_label(y, "E"))
            hc.font = F.FONT_HEADER; hc.fill = F.FILL_HEADER; hc.alignment = F.ALIGN_CENTER

        for rr, lab in [(3, "Unlevered FCF"), (4, "Change in NWC"), (5, "Discount period"),
                        (6, "Discount factor"), (7, "PV of UFCF")]:
            ws.cell(row=rr, column=2, value=lab).font = F.FONT_BOLD

        nwc = p.get("nwc_change", [0.0] * ny)
        for j in range(ny):
            cc = pc0 + j          # matching IS column
            isL = L(cc)
            lc = L(3 + j)         # local column
            # ΔNWC (editable value)
            nv = ws.cell(row=4, column=3 + j, value=(nwc[j] if j < len(nwc) else 0.0))
            nv.number_format = F.FMT_NUMBER; nv.font = F.FONT_INPUT
            # UFCF = NOPAT + D&A − CapEx − ΔNWC
            ws.cell(row=3, column=3 + j,
                    value=f"={ISN}!{isL}{R_NOP}+{ISN}!{isL}{R_DA}-{ISN}!{isL}{R_CX}-{lc}4"
                    ).number_format = F.FMT_NUMBER
            # discount period (mid-year), factor, PV
            pcell = ws.cell(row=5, column=3 + j, value=0.5 + j); pcell.number_format = '0.0'
            ws.cell(row=6, column=3 + j, value=f"=1/(1+$C$9)^{lc}5").number_format = '0.000'
            ws.cell(row=7, column=3 + j, value=f"={lc}3*{lc}6").number_format = F.FMT_NUMBER

        last = L(3 + ny - 1)            # last UFCF local column
        isLast = L(pc0 + ny - 1)        # last projection column on the IS sheet
        R_EBIT = ref["R_EBIT"]
        # Summary block (col C). WACC/g/exit-multiple linked from their detailed sheets.
        # Terminal value matches the engine: average of Gordon and exit-multiple TV.
        ws.cell(row=9, column=2, value="WACC (from 9_WACC)").font = F.FONT_BOLD
        w9 = ws.cell(row=9, column=3, value="='9_WACC'!$C$14"); w9.font = F.FONT_LINK; w9.number_format = F.FMT_PERCENT
        ws.cell(row=10, column=2, value="Terminal growth g (from 10_Terminal)").font = F.FONT_BOLD
        g10 = ws.cell(row=10, column=3, value="='10_Terminal'!$C$3"); g10.font = F.FONT_LINK; g10.number_format = F.FMT_PERCENT
        ws.cell(row=11, column=2, value="Exit EV/EBITDA (from 10_Terminal)").font = F.FONT_BOLD
        x11 = ws.cell(row=11, column=3, value="='10_Terminal'!$C$4"); x11.font = F.FONT_LINK; x11.number_format = F.FMT_MULTIPLE
        ws.cell(row=12, column=2, value="Sum PV of UFCF").font = F.FONT_BOLD
        ws.cell(row=12, column=3, value=f"=SUM(C7:{last}7)").number_format = F.FMT_NUMBER
        ws.cell(row=13, column=2, value="Gordon TV").font = F.FONT_BOLD
        ws.cell(row=13, column=3, value=f"={last}3*(1+$C$10)/($C$9-$C$10)").number_format = F.FMT_NUMBER
        ws.cell(row=14, column=2, value="Exit-multiple TV").font = F.FONT_BOLD
        ws.cell(row=14, column=3, value=f"=({ISN}!{isLast}{R_EBIT}+{ISN}!{isLast}{R_DA})*$C$11").number_format = F.FMT_NUMBER
        ws.cell(row=15, column=2, value="Average TV (used)").font = F.FONT_BOLD
        ws.cell(row=15, column=3, value="=(C13+C14)/2").number_format = F.FMT_NUMBER
        ws.cell(row=16, column=2, value="PV of Terminal Value").font = F.FONT_BOLD
        ws.cell(row=16, column=3, value=f"=C15/(1+$C$9)^{ny}").number_format = F.FMT_NUMBER
        ws.cell(row=17, column=2, value="Enterprise Value").font = F.FONT_BOLD
        ws.cell(row=17, column=3, value="=C12+C16").number_format = F.FMT_NUMBER

    def render_wacc(self):
        ws = self._create_sheet("9_WACC")
        self._write_header(ws, 2, 2, "WACC Build")
        w = self.results["wacc"]
        pct = Formats.FMT_PERCENT
        r = 3
        r = self._kv(ws, r, "Risk-free rate", w["rf"], pct, blue=True)
        r = self._kv(ws, r, "Total ERP", w["total_erp"], pct, blue=True)
        r = self._kv(ws, r, "Asset (unlevered) beta", w["median_asset_beta"], '0.00', blue=True)
        r = self._kv(ws, r, "Current levered beta", w["current_levered_beta"], '0.00')
        r = self._kv(ws, r, "Cost of equity (current)", w["current_ke"], pct)
        r = self._kv(ws, r, "WACC (current structure)", w["current_wacc"], pct)
        r = self._kv(ws, r, "Target levered beta", w["target_levered_beta"], '0.00')
        r = self._kv(ws, r, "Cost of equity (target)", w["target_ke"], pct)
        r = self._kv(ws, r, "WACC (target structure)", w["target_wacc"], pct)
        r = self._kv(ws, r, "Pre-tax cost of debt", w["pretax_kd"], pct, blue=True)
        r = self._kv(ws, r, "After-tax cost of debt", w["after_tax_kd"], pct)
        r = self._kv(ws, r, "WACC (average, used)", w["avg_wacc"], pct, blue=True)  # editable driver (C14)

    def render_terminal(self):
        ws = self._create_sheet("10_Terminal")
        self._write_header(ws, 2, 2, "Terminal Value (Rs mm)")
        t = self.results["terminal"]
        r = 3
        r = self._kv(ws, r, "Terminal growth (g)", t["terminal_growth"], Formats.FMT_PERCENT, blue=True)
        r = self._kv(ws, r, "Exit EV/EBITDA multiple", t["exit_multiple"], Formats.FMT_MULTIPLE, blue=True)
        r = self._kv(ws, r, "Gordon-growth TV", t["gordon_tv"])
        r = self._kv(ws, r, "Exit-multiple TV", t["multiple_tv"])
        r = self._kv(ws, r, "Average TV (used)", t["avg_tv"])
                
    def render_bridge(self):
        """Live EV→Equity bridge. EV is linked from the FCF/DCF sheet; the bridge
        items are editable; Equity Value and Intrinsic/Share are formulas. Editing
        any driver upstream flows through to the intrinsic value here (C13)."""
        F = Formats
        ws = self._create_sheet("11_Valuation_Bridge")
        c = ws.cell(row=2, column=2, value="Enterprise → Equity Bridge (Rs mm)")
        c.font = F.FONT_HEADER; c.fill = F.FILL_HEADER
        b = self.results["bridge"]
        shares = self.results["shares"]["diluted_shares"]

        # (label, value, kind)  rows 3..10 sum to Equity Value
        items = [
            ("Enterprise Value", "='8_FCF_DCF'!$C$17", "link"),
            ("Add: Cash", b["cash"], "in"),
            ("Less: Debt", -b["debt"], "in"),
            ("Less: NCI", -b["nci"], "in"),
            ("Less: Preferred", -b["preferred"], "in"),
            ("Add: Investments", b["investments"], "in"),
            ("Less: Pension", -b["pension"], "in"),
            ("Add: NOLs", b["nols"], "in"),
        ]
        r = 3
        for label, val, kind in items:
            ws.cell(row=r, column=2, value=label).font = F.FONT_BOLD
            cell = ws.cell(row=r, column=3, value=val)
            cell.number_format = F.FMT_NUMBER
            cell.font = F.FONT_LINK if kind == "link" else F.FONT_INPUT
            r += 1
        ws.cell(row=11, column=2, value="Equity Value").font = F.FONT_BOLD
        ws.cell(row=11, column=3, value="=SUM(C3:C10)").number_format = F.FMT_NUMBER
        ws.cell(row=12, column=2, value="Diluted Shares").font = F.FONT_BOLD
        sc = ws.cell(row=12, column=3, value=shares); sc.number_format = '#,##0'; sc.font = F.FONT_INPUT
        ws.cell(row=13, column=2, value="Intrinsic Value / Share (Rs)").font = F.FONT_BOLD
        iv = ws.cell(row=13, column=3, value="=C11*1000000/C12")
        iv.number_format = '#,##0.00'; iv.font = F.FONT_BOLD
            
    def render_sensitivity(self):
        ws = self._create_sheet("12_Sensitivity")
        c = ws.cell(row=2, column=2, value="Intrinsic / Share — WACC (rows) x Terminal g (cols)")
        c.font = Formats.FONT_HEADER
        c.fill = Formats.FILL_HEADER
        p, fc, w, t = self.results["proj"], self.results["fcf"], self.results["wacc"], self.results["terminal"]
        ufcf = p["ufcf"]
        n = len(ufcf)
        final_ufcf = ufcf[-1] if ufcf else 0.0
        # Net non-EV adjustments (cash/debt/NCI/…) implied by the bridge, held constant
        bridge_add = self.results["bridge"]["equity_value"] - fc["enterprise_value"]
        shares = self.results["shares"]["diluted_shares"] or 1.0
        base_w, base_g = w["avg_wacc"], t["terminal_growth"]
        waccs = [base_w - 0.02, base_w - 0.01, base_w, base_w + 0.01, base_w + 0.02]
        gs = [base_g - 0.01, base_g - 0.005, base_g, base_g + 0.005, base_g + 0.01]
        ws.cell(row=4, column=2, value="WACC \\ g").font = Formats.FONT_BOLD
        for j, g in enumerate(gs):
            hc = ws.cell(row=4, column=3 + j, value=g)
            hc.number_format = Formats.FMT_PERCENT
            hc.font = Formats.FONT_BOLD
        for i, wc in enumerate(waccs):
            lc = ws.cell(row=5 + i, column=2, value=wc)
            lc.number_format = Formats.FMT_PERCENT
            lc.font = Formats.FONT_BOLD
            for j, g in enumerate(gs):
                pv = sum(cf / ((1 + wc) ** (k + 0.5)) for k, cf in enumerate(ufcf))
                tv = (final_ufcf * (1 + g) / (wc - g)) if wc > g else 0.0
                pv_tv = tv / ((1 + wc) ** (n - 0.5)) if n else 0.0
                eq = pv + pv_tv + bridge_add
                ips = eq * 1e6 / shares
                cell = ws.cell(row=5 + i, column=3 + j, value=ips)
                cell.number_format = Formats.FMT_NUMBER
                if abs(wc - base_w) < 1e-9 and abs(g - base_g) < 1e-9:
                    cell.fill = Formats.FILL_SUBHEADER  # highlight base case

    def render_sources(self):
        ws = self._create_sheet("13_Sources")
        c = ws.cell(row=2, column=2, value="Sources & Assumption Basis")
        c.font = Formats.FONT_HEADER
        c.fill = Formats.FILL_HEADER
        r = 3
        ws.cell(row=r, column=2, value="Documents ingested by Gemini (AJP):").font = Formats.FONT_BOLD
        r += 1
        srcs = list(self.ajp.meta.sources_ingested or [])
        if not srcs:
            srcs = ["(none — engine used historical-data defaults; AJP not supplied)"]
        for s in srcs:
            ws.cell(row=r, column=2, value=str(s))
            r += 1
        r += 1
        ws.cell(row=r, column=2, value="Key assumptions used & basis:").font = Formats.FONT_BOLD
        r += 1
        for k, v in (self.results["proj"].get("assumptions_used") or {}).items():
            ws.cell(row=r, column=2, value=k)
            cell = ws.cell(row=r, column=3, value=v)
            cell.number_format = Formats.FMT_PERCENT if (isinstance(v, float) and abs(v) < 2) else Formats.FMT_NUMBER
            r += 1
        r += 1
        ws.cell(row=r, column=2, value=f"AJP assumptions provided: {len(self.ajp.assumptions)}").font = Formats.FONT_BOLD

def create_workbook(engine_results: Dict[str, Any], ajp: AJP, filepath: str):
    renderer = WorkbookRenderer(engine_results, ajp)
    wb = renderer.render()
    wb.save(filepath)
