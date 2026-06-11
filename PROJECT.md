# Sidwell — Personal Investment-Decision Engine

## Vision
A Python tool that applies the frameworks of major investors (Buffett, Marks, Blackstone/KKR, distressed specialists) to companies — public or private — and outputs valuation plus an actionable investment recommendation including deal terms where applicable.

Named after Jonathan Sidwell (Suits), whose proprietary algorithm "saw the world" through a deal-making lens.

## Architecture

```
INPUT (ticker or YAML)
    ↓
DATA LAYER (yfinance / nsepython / EDGAR / Damodaran / FRED — all free)
    ↓
VALUATION ENGINE (DCF, comps, precedent txns, LBO — deterministic Python)
    ↓
INVESTOR LENS ENGINE (Buffett, Marks, KKR/Blackstone, distressed — explicit rule sets)
    ↓
OUTPUT (markdown report: valuation + lens verdicts + final recommendation + terms if private)
```

## Modules (build sequence)
1. **v0 (this run)**: Valuation engine + Buffett lens, working end-to-end on one Indian public co.
2. Marks lens added
3. KKR/Blackstone LBO lens added (requires LBO model first)
4. Distressed / special situations lens
5. Private company path: YAML input + CIM-extraction helper
6. Term-sheet recommendation module (board seats, prefs, anti-dilution, drag/tag — indexed by deal archetype)

## Constraints
- Python 3.11+, no Excel
- Free data sources only — zero API costs
- **Deterministic valuation engine**: same input → same output. The DCF/comps/LBO math has no LLM calls.
  (Updated since v0.2: a DeepSeek qualitative layer now produces structured signals consumed by lens
  "soft" checks — see `analysis/qualitative.py`. The valuation math itself remains deterministic.)
- Indian (NSE/BSE) + US markets supported from day one
- Every assumption in the output report must be traceable to its source

## Non-goals
- No portfolio management, position sizing, real-time monitoring
- No backtesting framework (yet)
- No automated trading, ever

(Updated: the original "CLI only, no web UI" non-goal no longer holds — there is now a Streamlit
frontend in `app.py` alongside the `value.py` CLI entry point.)

## User context
Aspiring PE / investment banker, India-based, learning valuation end-to-end. This tool is both a decision-making system AND a learning vehicle — the act of encoding each investor's framework explicitly is the intellectual work that makes the analyst better, independent of whether the code ever ships.
