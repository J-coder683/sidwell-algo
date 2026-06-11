# Buffett Lens — The Compounder's Framework

A working framework for analyzing any public company **the way Warren Buffett would**: not by quoting his letters, but by applying the lens through which he and Charlie Munger actually see businesses.

## The Buffett Worldview (the lens, not the citations)

Buffett does not analyze companies the way a sell-side analyst does. He analyzes them the way **a private buyer who plans to hold forever** would.

When Buffett looks at a company, he is asking — in this order:

1. **Is this a business I can understand and predict 10–20 years out?** Most companies fail this. Most of what's investable on the stock exchange he will never look at twice. This is the circle of competence filter, and it is the gateway. If you can't model 20-year cash flows with confidence, the rest of the analysis is theatre.

2. **Does this business have a durable competitive advantage that lets it earn high returns on capital indefinitely?** Pricing power without losing volume. Switching costs. Brand. Cost advantage. Network effect. *Buffett does not invest in good businesses. He invests in great businesses with moats so deep that the next 20 years of returns are largely a function of capital they can redeploy at high rates.*

3. **Is the management team allocating capital intelligently?** This is where most Buffett analysis stops short. **Operating excellence is necessary but not sufficient.** A CEO running a great business but reinvesting in dilutive acquisitions or buying back stock at peak prices destroys what the business creates. Buffett spends as much time on capital allocation skill as on operating quality — and so should this framework.

4. **Is management honest, owner-oriented, and aligned with shareholders?** Skin in the game. Candid letters that admit mistakes. No promotion-minded earnings games. Reasonable compensation that doesn't extract value from owners. *"Although our form is corporate, our attitude is partnership."* This is not a soft factor — it is a hard filter. Buffett walks away from talented operators who play games with shareholders.

5. **Only at the end: is the price right?** A wonderful business at a fair price beats a fair business at a wonderful price — but a wonderful business at a wonderful price still requires a margin of safety. Graham's 25% discount to intrinsic value remains the entry hurdle.

This framework codifies that order: **understand → quality → management → price**. Most quantitative screens skip 1, gloss over 3 and 4, and over-weight 5. That is the opposite of how Buffett actually invests.

A company that fails any check in Parts A, B, or C is generally not a Buffett candidate regardless of price. A company that passes A/B/C but fails the margin-of-safety check (Part D) is **WAIT** — quality at the wrong price, set an alert. Only A/B/C/D all passing produces **BUY**.

---

## Framework: 14 Checks Across 4 Parts

Each check has a numeric or hybrid test, a logic explanation, and a source. **Lens code must follow this spec exactly — if a check changes, update the spec first.**

Conventions:
- All standard deviations use `np.std(..., ddof=1)` (sample stdev).
- "Historical" = 4 years of data (the current data layer window).
- "Latest" = most recent fiscal year.
- LLM-driven checks are flagged with **(soft)** and require qualitative input from the v0.2+ Gemini layer.

---

### Part A — Business Quality (Checks 1–4)

These checks answer: *is this fundamentally a great business that will still be great in 20 years?*

#### 1. Durable competitive advantage (moat)
**Proxy:** Gross margin stability over 4 years.
**Test:** `stdev(gross_margin, ddof=1) < 0.03` (less than 3 percentage points of variation)
**Logic:** Stable gross margins through input-cost cycles indicate pricing power — a moat lets the company hold price while costs swing. Volatile margins indicate a commodity-like business. This is a proxy; a richer moat assessment would include market share stability, brand premium, and pricing actions, but stability of gross margin captures the most economically meaningful signal in publicly available data.
**Source:** Berkshire 2007 letter ("great businesses" framework); 2014 letter, See's Candy pricing-power case study.

#### 2. High return on invested capital
**Test:** `mean(roic_4y) > 0.15` where ROIC = `EBIT × (1 − t) / (Debt + Equity − Cash)`
**Logic:** ROIC > cost of capital sustainably is value creation. Buffett targets >15% pre-tax consistently. A company that earns 12% ROIC while reinvesting heavily compounds slower than one earning 25% ROIC; the spread compounds.
**Source:** Berkshire 1979 letter ("primary test of managerial economic performance is the achievement of a high earnings rate on equity capital employed"); 1992 letter on intrinsic value.

#### 3. Strong free-cash-flow generation
**Test:** `mean(fcf_margin_4y) > 0.10` AND `fcf_growth_4y > 0`
**Logic:** Owner earnings — Buffett's term for CFO minus maintenance capex — must be material and growing. A business that reports earnings but doesn't generate cash is suspect. FCF margin > 10% with growth across the window indicates a real cash machine.
**Source:** Berkshire 1986 letter (owner-earnings definition); 1996 letter.

#### 4. Earnings predictability
**Test:** `0.05 < revenue_cagr_4y < 0.30` AND `stdev(yoy_revenue_growth_rates, ddof=1) < 0.10`
**Logic:** Buffett avoids both stagnation and hyper-growth he can't predict. A predictable upward slope is what compounds. The second clause measures volatility of *year-over-year growth rates* (3 data points from 4 annual revenues) — not volatility of revenue levels. Any growing company has high CV on levels; that would be a bug, not a test.
**Source:** Berkshire 1996 letter ("circle of competence"); 2014 letter (Dexter Shoe post-mortem on un-predictable disruption).

---

### Part B — Financial Health (Checks 5–7)

These checks answer: *can this business survive any storm and never face existential risk?*

#### 5. Conservative balance sheet
**Test:** `latest_debt / latest_ebitda < 3.0` AND `latest_ebit / latest_interest_expense > 5.0`
**Logic:** Buffett: *"I've never paid attention to debt-paying ability beyond confirming the company has very little of it."* Leverage above 3× EBITDA introduces refinancing risk and removes Buffett's preferred margin of operational error. Interest coverage > 5× confirms the company can service debt through normal-cycle EBIT compression.
**Source:** Berkshire 1990 letter; 2014 letter ("Gibraltar of American business").

#### 6. ROE without excess leverage
**Test:** `mean(roe_4y) > 0.15` AND `latest_equity / latest_assets > 0.4`
**Logic:** ROE > 15% sustained is value creation — but only if achieved with reasonable capital structure. A company at 25% ROE on 80% debt is not a quality compounder; it's a leveraged play. Buffett wants high ROE AND a balance sheet he could sleep through.
**Source:** Berkshire 1987 letter.

#### 7. Liquidity cushion (Gibraltar test)
**Test:** `(latest_cash + latest_short_term_investments) / latest_total_debt > 0.5` OR `latest_total_debt == 0`
**Logic:** Buffett's 2014 letter is explicit: *"At Berkshire, we always maintain at least $20 billion — and usually far more — in cash equivalents. […] When bills come due, only cash is legal tender."* A great business that hits a credit-market freeze can still die. This check confirms the business has at least half a year of debt coverage in cash equivalents.
**Source:** Berkshire 2014 letter ("Financial staying power requires a company to maintain three strengths under all circumstances: a large and reliable stream of earnings; massive liquid assets; and no significant near-term cash requirements.").

---

### Part C — Management & Capital Allocation (Checks 8–11)

These checks answer: *is the management deploying shareholder capital intelligently and behaving like owner-partners?* **This is the stage most Buffett-style frameworks skip. Buffett does not.**

#### 8. Anti-dilution discipline
**Test:** `shares_outstanding_latest / shares_outstanding_4y_ago <= 1.02` (share count flat or shrinking, allowing up to 2% normal SBC dilution)
**Logic:** Buffett's most consistent management screen is the share-count test. *"Mistakes of that kind are deadly. Trading shares of a wonderful business — which Berkshire most certainly is — for ownership of a so-so business irreparably destroys value."* A company whose share count grows >2% per year is either issuing equity to fund operations (a tell) or making acquisitions with overvalued stock (the Buffett-Dexter mistake). A company shrinking its share count — and especially one buying back below intrinsic value — is acting like an owner-operator.
**Source:** Berkshire 2014 letter, Dexter Shoe / acquisition post-mortems; "owner-related business principles" Berkshire (https://www.berkshirehathaway.com/ownman.pdf).

#### 9. Capital allocation track record
**Test:** `mean(roic_4y) - mean(roic_prior_4y) > -0.03` AND `dividend_or_buyback_yield > 0` (ROIC not deteriorating materially over 8 years; capital returned to shareholders)
**Logic:** Capital allocation is *the* CEO job in Buffett's framing. A CEO who reinvests cash at a declining ROIC is destroying value, even if reported earnings rise. Conversely, a CEO who pays appropriate dividends or buys back stock at sensible prices is signaling discipline. Note: this check requires 8 years of ROIC data; if data layer only provides 4, default to PASS with a "data unavailable" flag.
**Source:** Berkshire 1987 letter; 2014 letter on the conglomerate's capital reallocation advantage; Validea quantitative Buffett strategy ([Validea blog](https://blog.validea.com/building-a-quantitative-strategy-based-on-warren-buffetts-approach/)).

#### 10. Owner orientation
**Test:** `insider_ownership > 0.05` (insiders own >5% of shares) OR **(soft)** LLM judges shareholder letters as owner-oriented (uses "owners/partners" framing, admits past mistakes by name, no GAAP-vs-adjusted earnings games)
**Logic:** Buffett's clearest cultural signal is whether management speaks to shareholders as owners or as a constituency to be managed. High insider ownership is the hardest quantitative proxy. The soft signal — letter tone — captures companies whose insiders may have diluted out but whose management still operates the partnership ethos.
**Source:** "Owner-related business principles" Berkshire (Buffett's own articulation, written 1996, updated 2014); 2014 letter ("Although our form is corporate, our attitude is partnership").

#### 11. Management coherence (qualitative)
**Test (soft, LLM-based):** Gemini reads concall transcripts, IR decks, and MD&A sections. Returns **coherent | incoherent** based on:
  - Whether management commentary is internally consistent across periods
  - Whether numeric claims tie out
  - Whether strategy shifts are acknowledged rather than papered over
  - Whether evasion or contradiction is evident
**Logic:** Buffett's 2014 letter on character: *"A Berkshire CEO must be 'all in' for the company, not for himself. […] If it's clear to them that shareholders' interests are paramount to him, they will, with few exceptions, also embrace that way of thinking."* Coherent commentary across multiple quarters under hostile analyst questioning is a hard test of integrity. This check inherits the v0.2 hybrid coherence signal.
**Source:** Berkshire 2003 letter on management quality; v0.2 qualitative ingestion layer (`analysis/qualitative.py`).
**Determinism note:** One of the two LLM-dependent checks in this lens. Excluded from the denominator (marked N/A) when qualitative input is unavailable or the verdict is unclear — neither inflates the score (default-PASS) nor penalizes missing data (default-FAIL). A genuine `incoherent` verdict still counts as a failure.

---

### Part D — Margin of Safety & Holdability (Checks 12–14)

These checks answer: *given everything above, can I buy this today at a price that gives me margin of safety, AND would I still want to own it in 20 years?*

#### 12. Margin of safety
**Test:** `(intrinsic_value − current_price) / intrinsic_value > 0.25`
**Logic:** Graham's 25% discount to intrinsic value, retained by Buffett throughout. This is the price gate. A wonderful business is still a bad investment if you overpay. Buffett's preferred margin is wider than Graham's in many cases, but 25% is the published floor.
**Source:** "Intelligent Investor" ch. 20; Berkshire 1992 letter (intrinsic value definition).

#### 13. Hard understandability blacklist
**Test:** `not any(financials["ticker"].startswith(p) for p in ["BTC", "ETH", "COIN"])`
**Logic:** Deterministic blacklist for fast-changing or speculative categories Buffett historically avoids. Crypto, complex derivatives books, pre-revenue biotech. Hard exclusion; no LLM override.
**Source:** Berkshire 1996 letter ("circle of competence"); Buffett's repeated public statements on crypto.

#### 14. Holdability — 20-year test (qualitative)
**Test (soft, LLM-based):** Gemini reads the qualitative inputs and answers: *would a fund manager with a 20-year mandate want to own this business at any price?* PASS if yes (durable customer need, hard-to-disrupt economics, no obvious technological obsolescence risk in 20 years). FAIL if the business depends on a single technology cycle, regulatory regime that may shift, or fashion-cycle category. Excluded from the denominator (N/A) if qualitative unavailable or unclear.
**Logic:** Buffett's actual final filter is the 20-year test. *"Our favorite holding period is forever."* He has never sold See's Candy. He held Coca-Cola for 30+ years. A great business he'd sell in 5 years isn't a Buffett candidate — it's a Marks candidate (right tool, wrong lens).
**Source:** Berkshire 1988 letter (Coca-Cola entry rationale); 2014 letter ("if our non-economic values were to be lost, much of Berkshire's economic value would collapse as well").
**Determinism note:** Second LLM-dependent check. Excluded from the denominator (marked N/A) when qualitative unavailable or unclear. A genuine `not_holdable_20y` verdict still counts as a failure.

---

## Scoring & Verdict Logic

```
score = sum of checks 1–14 that pass (max 14)

VERDICT:
  if score >= 12 and check_12_passes:              "BUY"
  elif score >= 10 and not check_12_passes:        "WAIT (set alert at MoS price)"
  elif score >= 10:                                "WATCH"
  else:                                            "SKIP"
```

**Calibration notes:**
- BUY threshold (12/14) is intentionally high. Buffett buys 1–3 new positions per decade.
- WAIT preserves the v0.1 semantic: high-quality business, wrong price. The user wants an alert at the price where MoS = 25%.
- WATCH = passes most quality bars but has more than 2 failed checks — usually means a moderate-quality business or one with management concerns. Worth monitoring but not aggressive accumulation.
- SKIP = fails too many quality bars to be a Buffett candidate regardless of price.

**Critical scoring rule (no methodology hacking):** If a check fails, the verdict is what the math produces. Do not adjust thresholds to recover a desired verdict. The framework codifies Buffett's lens; the verdict is the lens's output.

---

## Output Format (each check in the report)

```
[✅/❌] 1. Moat (GM stability)            pass: stdev = 1.8% < 3%
[✅/❌] 2. ROIC                           pass: 4y avg = 24.3% > 15%
...
[✅/❌] 14. Holdability (20-year test)    pass: LLM judged business model durable

PART A (Business Quality):       3/4 passed
PART B (Financial Health):       3/3 passed
PART C (Mgmt & Capital Alloc):   2/4 passed   ← weakness here
PART D (Price & Holdability):    2/3 passed

TOTAL: 10/14
VERDICT: WATCH — quality business with management concerns; revisit after capital-allocation track record stabilizes.
```

---

## How This Lens Differs from a Generic Quality Screen

A standard quality screen (Magic Formula, F-Score, etc.) measures profitability and balance sheet. This Buffett lens adds three things they typically omit:

1. **Capital allocation explicit checks (8, 9).** Most screens never look at share count or M&A track record.
2. **Owner orientation as a hard filter (10, 11).** Most screens never read shareholder letters.
3. **Holdability test (14).** Most screens are 12-month horizon; Buffett's is 20-year.

If a generic quality screen and this lens disagree on a name, the disagreement is almost always in Parts C and D — and that disagreement is the point.

---

## Sources for Further Encoding

**Primary (Buffett's own writing):**
- Berkshire Hathaway annual letters, 1977–2024 (full text in `knowledge/Memos & shareholder leters/Berkshire Hathaway/`)
- "Owner-related Business Principles" — Buffett's own framework, 1996/2014 ([berkshirehathaway.com/ownman.pdf](https://www.berkshirehathaway.com/ownman.pdf))
- 2014 letter ("Past, Present and Future") — 50-year retrospective with explicit framework articulation
- Charlie Munger's 2014 vice-chairman letter — complementary framing on quality vs cigar-butt

**Synthesized:**
- "The Essays of Warren Buffett" — Lawrence Cunningham (letters organized thematically)
- "Buffettology" — Mary Buffett (operational checklist version, weaker than primary sources)
- "The Warren Buffett Way" — Robert Hagstrom
- Master_Investment_Compendium.md Part 5.1 (Henry Kravis lens — useful contrast point)
- Validea's quantitative Buffett strategy — operationalized version ([blog.validea.com](https://blog.validea.com/building-a-quantitative-strategy-based-on-warren-buffetts-approach/))

**Operationalization references:**
- Picture Perfect Portfolios — Buffett's investment criteria ([pictureperfectportfolios.com](https://pictureperfectportfolios.com/warren-buffetts-investment-criteria-an-in-depth-analysis/))
- Shortform — three metrics for evaluating management like Buffett ([shortform.com](https://www.shortform.com/blog/how-to-evaluate-management/))
