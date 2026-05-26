# Buffett Lens — Explicit Framework

Buffett's investment philosophy across his Berkshire letters (1977–2024), distilled into 8 testable checks. Each check has a numeric threshold, a logic explanation, and a source. Lens code must follow this spec exactly — if a check changes, update the spec first.

## The 8 checks

### 1. Durable competitive advantage (moat)
**Proxy:** Gross margin stability over 4 years.
**Test:** `gross_margin_std_4y < 0.03` (stdev of last 4 annual gross margins < 3 percentage points)
**Logic:** Stable gross margins indicate pricing power — a moat lets the company hold price through cost cycles. Volatile margins = commodity-like.
**Source:** Berkshire 2007 letter, "great businesses" framework.

### 2. High return on invested capital
**Test:** `roic_4y_avg > 0.15`
**Logic:** ROIC > cost of capital sustainably = value creation. Buffett targets >15% pre-tax consistently.
**Source:** Berkshire 1979 letter, "primary test of managerial economic performance is the achievement of a high earnings rate on equity capital employed."

### 3. Strong free-cash-flow generation
**Test:** `fcf_margin_4y_avg > 0.10` AND `fcf_growth_4y > 0` (no decline)
**Logic:** Owner earnings (Buffett's term for CFO − maintenance capex) must be material and growing.
**Source:** Berkshire 1986 letter, owner-earnings definition.

### 4. Conservative balance sheet
**Test:** `debt_to_ebitda < 3.0` AND `interest_coverage > 5.0`
**Logic:** Buffett: "I've never paid attention to debt-paying ability beyond confirming the company has very little of it." High leverage = removed from consideration.
**Source:** Berkshire 1990 letter.

### 5. High return on equity without excess leverage
**Test:** `roe_4y_avg > 0.15` AND `equity_to_assets > 0.4`
**Logic:** ROE > 15% achieved with a reasonable capital structure — not leverage-juiced ROE.
**Source:** Berkshire 1987 letter.

### 6. Earnings predictability
**Test:** `0.05 < revenue_cagr_4y < 0.30` AND `stdev(yoy_revenue_growth_rates) < 0.10`
**Logic:** Buffett avoids both stagnation and hyper-growth he can't predict. Wants predictable upward slope. The second clause measures volatility of *year-over-year growth rates* (3 data points from 4 annual revenues), NOT volatility of revenue levels. Any growing company has high CV on levels — that would be a bug, not a test.
**Source:** Berkshire 1996 letter, "circle of competence."

### 7. Margin of safety
**Test:** `(dcf_intrinsic_value − current_price) / dcf_intrinsic_value > 0.25`
**Logic:** 25% discount to intrinsic value. Graham's rule, retained by Buffett throughout.
**Source:** "Intelligent Investor" ch. 20; Berkshire 1992 letter.

### 8. Understandable business
**Hybrid test (v0.2+):** Hard deterministic blacklist AND soft LLM-based
coherence assessment. Check passes only if both signals pass.

**Hard signal (deterministic):** Ticker not in avoided-sector blacklist
(currently: BTC, ETH, COIN prefixes — fast-changing or speculative
categories Buffett historically avoids).

**Soft signal (LLM-based, v0.2+):** When qualitative analysis is available,
Gemini reads concall transcripts, IR decks, and MD&A sections and produces
a binary "coherent | incoherent" judgment based on:
  - Whether management commentary is internally consistent
  - Whether numeric claims across the documents tie out
  - Whether strategy shifts are acknowledged
  - Whether evasion or contradiction is evident
Defaults to "coherent" when qualitative analysis is unavailable, preserving
pre-v0.2 behavior.

**Logic:** Buffett's "circle of competence" requires both — a business in
a category you can model (hard), AND management whose statements you can
trust as a basis for that modeling (soft).

**Source:** Berkshire 1996 letter (circle of competence); Berkshire 2003
letter on management quality.

**Determinism note:** This is the ONLY Buffett check with LLM dependence.
Checks 1-7 remain pure deterministic Python. Verdicts may shift run-to-run
for the same inputs if the LLM's coherence read drifts. Report displays
BOTH signals so non-determinism is visible, not hidden.

## Scoring & verdict logic

```
score = sum of checks 1–8 that pass (max 8)

if score >= 7 and check_7_passes:     verdict = "BUY"
elif score >= 6 and not check_7_passes: verdict = "WAIT (set alert at MoS price)"
elif score >= 6:                       verdict = "WATCH"
else:                                   verdict = "SKIP"
```

## Output format (each check in the report)
```
[✅/❌] 1. Moat (GM stability)         pass: stdev = 1.8% < 3%
[✅/❌] 2. ROIC                        pass: 5y avg = 24.3% > 15%
...
SCORE: 6/8
VERDICT: WAIT — quality business at wrong price. Alert when price drops to ₹X (= 75% of intrinsic ₹Y).
```

## Sources for further encoding
- Berkshire Hathaway annual letters: https://www.berkshirehathaway.com/letters/letters.html
- "The Essays of Warren Buffett" — Lawrence Cunningham (organizes the letters thematically)
- "Buffettology" — Mary Buffett (operational checklist version)
- "The Warren Buffett Way" — Robert Hagstrom
