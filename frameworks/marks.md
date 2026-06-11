# Marks Lens — The Risk-First Framework

A working framework for analyzing any public company **the way Howard Marks would**: not by quoting his memos, but by applying the lens through which he and Oaktree actually approach investment opportunities.

## The Marks Worldview (the lens, not the citations)

Marks does not analyze companies the way a growth investor does. He analyzes them the way **a distressed-debt investor with permanent capital** does — where survival is the prerequisite and the shape of the payoff matters more than the expected value.

When Marks looks at a company, he is asking — in this order:

1. **What can go wrong, and is the downside survivable?** Marks's first question is not about upside. *"If you avoid the losers, the winners take care of themselves."* Before any analysis of return, the question is whether the worst plausible scenario destroys the position. A 50% drawdown is recoverable; a 100% loss is not. The framework codifies this: every check in Part C (Risk Architecture) is a filter that must pass before Parts A or D are even meaningful.

2. **Is the payoff structure asymmetric in my favor?** Marks does not invest for expected value; he invests for asymmetric expected value. *"It's not how much you make when you're right — it's how much you don't lose when you're wrong."* Three units of upside per unit of downside is the rough hurdle. A "50/50 coin flip" with equal payoffs is not a Marks investment, even if positive-expected-value, because it requires being right repeatedly.

3. **Where are we in the cycle?** Marks: *"We may never know where we're going, but we ought to know where we are."* Cycle position is the most under-attended variable in mainstream investing. The same company at the same price is a different investment at a credit-cycle trough vs at a peak. Sector cycle, company cycle, market cycle — Marks reads all three. Buying at a trough is the highest-leverage decision in investing; the framework should explicitly check whether we're trying to.

4. **Is the price deeply discounted to intrinsic value, not just modestly?** Marks's margin of safety is wider than Graham's or Buffett's. 25% is the textbook minimum; Marks operates closer to 40%+ when entering positions. *"The most important thing is buying things well, not buying good things."* A great business at fair price does not pass the Marks test; a fair business at a deeply distressed price might.

5. **Is the trade contrarian, or am I joining the crowd?** Marks's central concept is **second-level thinking**: the difference between what everyone thinks and what is true. A "good company" thesis where everyone agrees is, by definition, already in the price. Marks looks for situations where his view is non-consensus AND defensible. *"Being too far ahead of your time is indistinguishable from being wrong."* But going with the consensus is, by construction, never alpha.

This framework codifies that order: **survive → asymmetric → cyclically priced → contrarian**. A company that fails Part C (risk architecture) is not a Marks candidate at any price. A company that passes C/A but is at a cyclical peak (Part B) is **WAIT** — patient opportunism, set a re-rating alert. Only C/A/B/D all favorable produces **BUY**.

---

## Framework: 14 Checks Across 4 Parts

Same conventions as `buffett.md`:
- All standard deviations use `np.std(..., ddof=1)`.
- "Historical" = 4 years of data; "Latest" = most recent fiscal year.
- LLM-driven checks flagged with **(soft)**.

---

### Part A — Margin of Safety & Asymmetric Payoff (Checks 1–4)

These checks answer: *is the price right, and is the payoff shape asymmetric in my favor?*

#### 1. Deep margin of safety
**Test:** `(intrinsic_value − current_price) / intrinsic_value > 0.40`
**Logic:** Marks's margin of safety is deeper than Graham's 25%. *"The most important thing in investing isn't return; it's risk."* A wider entry discount is the primary tool for risk control — it converts ordinary returns into above-average returns and provides cushion for errors in the intrinsic-value estimate itself. 40% is the published Oaktree distressed-investing threshold; for non-distressed equity it remains the appropriate floor because the intrinsic-value estimate is itself uncertain.
**Source:** "The Most Important Thing," ch. 3–4 (Value; Price vs Value); Oaktree memo "Risk Revisited" (2014).

#### 2. Asymmetric upside-to-downside payoff
**Test:** `(upside_scenario − current_price) / (current_price − downside_scenario) > 3.0`
  - `upside_scenario` = intrinsic value under reasonable bull case (revenue growth +200 bps, terminal multiple +20%)
  - `downside_scenario` = intrinsic value under reasonable bear case (revenue growth −200 bps, terminal multiple −30%, OR trough-multiple × trough-earnings, whichever is lower)
**Logic:** Marks's "asymmetric returns" framing: the shape of the payoff matters more than the central estimate. A 30% upside with 10% downside is a Marks trade; a 50% upside with 50% downside is not, regardless of expected value. *"It's not what you buy, it's what you pay."* Note: this check requires scenario modeling not yet implemented in v0.2 — for now, defaults to using ±20% bands on intrinsic value as a placeholder; tighten in v0.4 with explicit scenario inputs.
**Source:** "The Most Important Thing," ch. 19 (Adding Value); Oaktree memos "What's Behind the Buyout Boom" (2007), "It's All Good… Really?" (2007).

#### 3. Downside protection — tangible book or asset value
**Test:** `latest_tangible_book_equity / market_cap > 0.30` OR sector is asset-heavy AND `replacement_cost_estimate / market_cap > 0.50`
**Logic:** Marks's distressed roots: *"The price you pay is the price."* In a workout or liquidation scenario, what's the recovery? Tangible book is the simplest universal floor. For asset-heavy businesses (banks, REITs, industrials), this can be the dominant valuation reference rather than DCF. For asset-light businesses (software, services), the test still applies but with a lower threshold — the floor is goodwill of customer relationships, not balance-sheet assets. Default threshold of 30% tangible book to market cap is intentionally permissive for high-quality businesses; tighter check for cyclicals.
**Source:** "The Most Important Thing," ch. 17 (Investing Defensively); Oaktree memo "There They Go Again… Again" (2014).

#### 4. Multiple expansion not exhausted
**Test:** `current_pe < historical_5y_avg_pe × 1.10` AND `current_pe < sector_median_pe × 1.10`
**Logic:** Marks wants to enter when multiples are compressed, not expanded. *"Most things prove to be cyclical."* Buying a company at 30× P/E when its history is 18× and its sector trades at 16× means future returns must come from operating growth alone — multiple expansion is exhausted. Marks's typical entry is when current multiple is at the LOWER end of historical/peer range — leaving multiple expansion as an additional return driver alongside operating performance.
**Source:** Oaktree memo "On the Couch" (2016); Master_Investment_Compendium.md Part 7.6 (Marc Rowan's "why now").

---

### Part B — Cycle Position (Checks 5–7)

These checks answer: *where are we in the cycle, and does it favor entry now?*

#### 5. Sector cycle position (qualitative)
**Test (soft, LLM-based):** Gemini reads concall transcripts, MD&A, and macro context to judge the sector cycle position. Returns one of: `trough | early_recovery | mid_cycle | late_cycle | peak`.
PASS if `trough | early_recovery | mid_cycle`. FAIL if `late_cycle | peak`.
**Logic:** Marks's central framing: *"The pendulum swings."* Sectors oscillate between euphoria and despair. Buying in despair (trough) and selling in euphoria (peak) is the highest-leverage decision in investing. Most quantitative analysis ignores this entirely; the Marks lens forces an explicit cycle-position read. Excluded from the denominator (N/A) if qualitative unavailable or the cycle read is unclear.
**Source:** "The Most Important Thing," ch. 8 (Being Attentive to Cycles), ch. 9 (Awareness of the Pendulum); "Mastering the Market Cycle" (2018).
**Determinism note:** LLM-dependent. Excluded from the denominator (marked N/A) when qualitative unavailable or unclear. A genuine `late_cycle`/`peak` read still counts as a failure.

#### 6. Company earnings vs cyclical peak
**Test:** `latest_eps / max(historical_4y_eps) > 0.70`
**Logic:** This catches the "company-cycle" position separately from "sector-cycle." A company at 50% of its own peak earnings has obvious mean-reversion optionality if the underlying business is intact. A company at 100% of its own peak is — by construction — running at the high end of its operating cycle, and forward returns require either secular growth or continued cycle strength. The 70% threshold flags companies in the bottom 30% of their own historical earnings — Marks's preferred entry zone for cyclicals.
**Source:** Oaktree memo "It's All a Big Mistake" (2012); Master_Investment_Compendium.md Part 3 (blowups timed at cyclical peaks).

#### 7. Sentiment indicator — going against the crowd
**Test:** Stock has underperformed broad market over trailing 12 months by >5% AND (consensus analyst rating is HOLD/SELL OR insider ownership has increased)
**Logic:** Marks's contrarianism filter. *"Being right at the wrong time is indistinguishable from being wrong."* Stocks that have crushed it for a year are typically attracting consensus buy ratings — exactly when Marks would not initiate. Stocks that have lagged and where the consensus is cautious are where Marks looks. This is not a "buy beaten-down losers" rule; it's combined with Parts A and C to ensure the underperformance is structurally cheap, not fundamentally broken.
**Source:** "The Most Important Thing," ch. 11 (Contrarianism); Oaktree memo "Dare to Be Great II" (2014).

---

### Part C — Risk Architecture (Checks 8–11)

These checks answer: *can this position survive the worst plausible scenario?* **These are pre-conditions. If any fail, the position is excluded regardless of how attractive Parts A/B/D look.**

#### 8. Capital structure resilience
**Test:** `latest_debt / latest_ebitda < 4.0` AND `latest_ebit / latest_interest_expense > 4.0` AND no debt maturity >25% of total debt within 12 months
**Logic:** Marks's distressed-investing background makes him hyper-attentive to refinancing risk. *"Survive first, then thrive."* Companies whose debt has to be refinanced into a tight credit window can become forced sellers — and good companies have died this way. Marks's threshold here is slightly higher than Buffett's because Marks is willing to invest in moderately leveraged companies — but only if maturity profile is clean. (The maturity-clustering check is harder to implement from yfinance; for now, default to PASS on maturity and rely on the leverage and coverage ratios.)
**Source:** "The Most Important Thing," ch. 6 (Recognizing Risk); Oaktree memo "The Long View" (2009); Master_Investment_Compendium.md Part 3 (Caesars, Toys R Us — both died on refinancing).

#### 9. FCF stability through downturn
**Test:** `min(fcf_4y) > 0` (free cash flow never negative across the 4-year window)
**Logic:** A business that generates positive FCF in every observed year — including any cyclical trough captured in the window — has proven through-cycle resilience. A business that has had at least one negative-FCF year may still be a Marks candidate but requires additional scrutiny (the trough year may have been an unusual event or may indicate the business does not earn its capital cost across cycles). This is the simplest universal through-cycle test.
**Source:** "The Most Important Thing," ch. 5 (Understanding Risk); Oaktree memos on through-cycle investing.

#### 10. Volatility / beta within Marks's range
**Test:** `stock_beta < 1.5` (using 3y beta vs market index, or fallback to sector median)
**Logic:** Marks invests in distressed credit which is structurally high-volatility, but for equity application he wants the equity to be moderately defensive. Beta > 1.5 indicates the stock will compound losses in a market drawdown — incompatible with risk-first investing. The threshold is more permissive than a pure defensive screen (which might require beta < 1.0) because Marks accepts cyclicality at the right cycle position. This check works in tandem with Part B: high-beta acceptable IF at cyclical trough; not acceptable at cyclical peak.
**Source:** "The Most Important Thing," ch. 7 (Controlling Risk).

#### 11. No single-point failure mode
**Test:** Customer concentration < 25% of revenue (if disclosed) AND no regulatory single-point dependence (defined as: not a single-licence operator like one toll road, one casino, one telecom spectrum band) AND auditor relationship < 7 years OR rotated within the period
**Logic:** Marks's defensive investing rule: identify the structural failure mode that ends the business. Single customer that could leave. Single regulatory licence whose renewal is uncertain. Auditor in place too long without rotation (governance risk surfacing eventually). The framework cannot test all of these from yfinance alone — defaults to soft via Gemini reading the qualitative inputs for these risks. Hard fail only on explicitly known cases (e.g., crypto-tied tickers, single-state regulated utilities with imminent rate cases).
**Source:** "The Most Important Thing," ch. 18 (Avoiding Pitfalls); Master_Investment_Compendium.md Part 7.2 (Red Flags by Category, especially the Indian governance items).
**Determinism note:** LLM-dependent (reads `risk_callouts`). Excluded from the denominator (marked N/A) when qualitative unavailable — a zero risk-count from a missing extraction is not evidence of a clean risk profile.

---

### Part D — Second-Level Thinking & Contrarianism (Checks 12–14)

These checks answer: *do I have variant perception, and is the trade contrarian-enough to be alpha?* **These are the LLM-driven checks. Marks's most distinctive ideas live here.**

#### 12. Variant perception present
**Test (soft, LLM-based):** Gemini reads transcripts and analyst reports. Returns PASS if there is a clearly articulated **non-consensus thesis** that is **specific and defensible** (not just "the company will grow" — but a specific operational, structural, or cyclical mechanism that consensus is mispricing). FAIL if the bull case is the consensus case (e.g., "AI tailwind," "EV transition," "China reopening" without specificity).
**Logic:** Marks's central concept: *"You can't do the same things others do and expect to outperform."* If everyone agrees the company will grow at 15%, that 15% is in the price. Alpha requires that something specific is mis-modeled — and that you can articulate what. Master_Investment_Compendium.md Part 7.4 (the Variant Perception Test) operationalizes this with three questions: what does the market believe; what do you believe differently and why; what would prove you wrong.
**Source:** "The Most Important Thing," ch. 1 (Second-Level Thinking), ch. 11 (Contrarianism); Master_Investment_Compendium.md Part 7.4.
**Determinism note:** LLM-dependent. Excluded from the denominator (marked N/A) when qualitative unavailable or the model cannot assess (variant_present null). A genuine "no variant perception" read counts as a failure. (Previously defaulted FAIL; under exclude-from-denominator, absence of data no longer penalizes the score directly — but note BUY still requires variant perception to have fired positively.)

#### 13. Knowing what you don't know (management humility)
**Test (soft, LLM-based):** Gemini judges whether management commentary demonstrates appropriate humility — acknowledges what they can't predict, doesn't make bold macro forecasts, doesn't overclaim certainty about future. Returns PASS for humility, FAIL for hubris.
**Logic:** Marks repeatedly emphasizes: *"It ain't what you don't know that gets you into trouble. It's what you know for sure that just ain't so."* A management team that confidently forecasts the next decade is either delusional or selling. A management team that says "we can't predict X but our business is structured to handle scenarios A, B, or C" is the Marks-preferred type. This check is admittedly subjective but maps to a real Marks principle that consistently differentiates great managers from promotional ones.
**Source:** "The Most Important Thing," ch. 14 (Knowing What You Don't Know); Oaktree memos "It Is What It Is" (2006), "The Most Important Thing Is" (2003).
**Determinism note:** LLM-dependent. Excluded from the denominator (marked N/A) when qualitative unavailable or unclear. A genuine hubris read counts as a failure.

#### 14. Patient opportunism — is now actually the right time?
**Test (soft, LLM-based):** Gemini synthesizes Parts A, B, and the qualitative input to answer: *is now the moment of forced selling or temporary dislocation that creates opportunity, or is this just normal-cycle consensus pricing?* PASS if specific dislocation present (post-shock, post-distress, post-management-change, post-regulatory event). FAIL if entry would be at "normal" valuations during normal markets.
**Logic:** Marks's *"best returns follow chaos"* (echoed by Marc Rowan at Apollo). The Marks lens does not just want a cheap company — it wants a cheap company AT THE RIGHT MOMENT. Buying a quality business 25% off in a normal market is a Buffett trade. Buying it 50% off in a panic when the seller is forced is a Marks trade. This check is the temporal version of "why now" — and is the most important of the three soft checks. *Skip this and the lens becomes generic value investing.*
**Source:** Oaktree memo "On Bubble Watch" (2024); Master_Investment_Compendium.md Part 7.6 ("the discipline of why now"); Knowledge at Wharton, Marc Rowan (2009).
**Determinism note:** LLM-dependent. Excluded from the denominator (marked N/A) when qualitative unavailable or unclear. A genuine "no dislocation" read counts as a failure.

---

## Scoring & Verdict Logic

```
score = sum of checks 1–14 that pass (max 14)

VERDICT:
  if score >= 11 and check_1 and check_2 pass:    "BUY"
  elif score >= 9 and (not check_1 or not check_4):  "WAIT (set re-rating alert)"
  elif score >= 9:                                 "WATCH"
  else:                                            "SKIP"
```

**Calibration notes:**
- BUY requires both check 1 (deep MoS) AND check 2 (asymmetric payoff) — non-negotiable for Marks. A company can pass 11 of 14 but if it doesn't have MoS, it's not a buy.
- WAIT semantic: company passes risk filters but is too cyclically expensive or insufficient MoS. Set an alert at price where MoS = 40%.
- WATCH = mixed signals; monitor for change in cycle position.
- SKIP = fails too many of the risk/cycle/MoS hurdles.

**Critical scoring rule (no methodology hacking):** Same rule as Buffett lens. If a check fails, the verdict is what the math produces. Do not adjust thresholds to recover a desired verdict.

---

## How This Lens Differs from Buffett

Both lenses are value-investing tools but they answer different questions:

| Dimension | Buffett | Marks |
|-----------|---------|-------|
| **First question** | Is this a great business I can hold forever? | What's the downside, and is it survivable? |
| **Margin of safety** | 25% discount | 40%+ discount |
| **Hold horizon** | 10–20+ years ("forever") | Until value is realized (could be 1–5 years) |
| **Cycle awareness** | Largely ignores macro/cycles | Cycle position is a primary check |
| **Management focus** | Heavy — owner orientation, capital allocation, character | Lighter — risk architecture matters more than mgmt quality |
| **Asymmetry framing** | Quality businesses produce asymmetric outcomes structurally | Asymmetry is a function of price + structural payoff shape |
| **Contrarianism** | Implicit — buy quality others underrate | Explicit — variant perception is a hard check |
| **Sells when** | Almost never | When margin of safety closes |

**Implication for composite verdict (Phase 3+):** These frameworks will frequently disagree, and the disagreements are informative.

- **Both BUY:** Rare, high-conviction signal. Quality compounder available at deep distress.
- **Buffett BUY, Marks SKIP/WAIT:** Quality business at fair price but no cyclical edge. Buy if you have permanent capital; wait if you have shorter horizon.
- **Marks BUY, Buffett SKIP:** Cyclical opportunity at deep discount but business quality fails Buffett's quality bars. Tradeable trough opportunity but not a forever-hold.
- **Both SKIP:** Don't touch. Either both Quality and Price fail, or both Risk and Quality fail.

The composite logic for Sidwell v0.3+ should preserve both verdicts side-by-side rather than collapsing to a single "Sidwell verdict" — the disagreement IS the insight.

---

## Output Format (each check in the report)

```
[✅/❌] 1. Deep margin of safety        pass: MoS = 47% > 40%
[✅/❌] 2. Asymmetric payoff (3:1)      fail: upside/downside = 1.4
[✅/❌] 3. Downside protection          pass: tangible book / market cap = 33%
...

PART A (Margin of Safety & Asymmetry):  3/4 passed
PART B (Cycle Position):                2/3 passed
PART C (Risk Architecture):             4/4 passed   ← must be all 4
PART D (Second-Level / Contrarianism):  2/3 passed

TOTAL: 11/14
VERDICT: WAIT — risk architecture clean, cycle near mid, but asymmetric payoff
inadequate at current price. Re-rate if price drops 15% from here.
```

---

## Sources for Further Encoding

**Primary (Marks's own writing):**
- "The Most Important Thing Illuminated" — Howard Marks, 2013 (full text in `knowledge/Books/`)
- "Mastering the Market Cycle: Getting the Odds on Your Side" — Howard Marks, 2018
- Oaktree memos, 1990–2024 — selectively in `knowledge/Memos & shareholder leters/Oaktree Capital/`
- Particularly: "Risk Revisited" (2014), "What's Behind the Buyout Boom" (2007), "The Long View" (2009), "On Bubble Watch" (2024)

**Adjacent (related risk-first thinkers):**
- Seth Klarman, "Margin of Safety" (1991) — Marks's intellectual cousin on deep-value investing
- Marc Rowan / Apollo: Knowledge at Wharton (2009) — "best returns follow chaos" — codified in Master_Investment_Compendium.md Part 5.3
- Master_Investment_Compendium.md Part 7.4 (Variant Perception Test) — operationalizes second-level thinking
- Master_Investment_Compendium.md Part 7.6 ("the discipline of why now")

**Operationalization references:**
- EBC Financial Group on Marks — value, risk, cycles ([ebc.com](https://www.ebc.com/forex/howard-marks))
- AmiNext on second-level thinking and market cycles ([aminext.blog](https://www.aminext.blog/en/post/howard-marks-second-level-thinking-market-cycles))
- Quartr on Marks's investment process ([quartr.com](https://quartr.com/insights/edge/inside-the-head-of-howard-marks))
- Picture Perfect Portfolios on mastering market cycles ([pictureperfectportfolios.com](https://pictureperfectportfolios.com/how-to-invest-like-howard-marks-mastering-market-cycles/))
- Oaktree's own "Best of" memo collection ([oaktreecapital.com](https://www.oaktreecapital.com/insights/memo/the-best-of))
