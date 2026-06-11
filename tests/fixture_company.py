# Fixture inputs for snapshot testing
FIXTURE_RISK_FREE_RATE = 0.07

FIXTURE_MACRO = {
    "mature_market_erp": 0.05,
    "country_risk_premium": 0.00,
    "total_erp": 0.05,
    "industry_unlevered_beta": 1.00,
    "industry_levered_beta": 1.05
}

FIXTURE_INPUTS = {
    "ticker": "FICTITIOUS.NS",
    "current_price": 50.0,
    "shares_outstanding": 10.0,
    "market_cap": 500.0,
    "years": ["2022-12-31", "2023-12-31", "2024-12-31", "2025-12-31"],
    "revenue": [100.0, 110.0, 121.0, 133.1],
    "gross_profit": [40.0, 44.0, 48.4, 53.24],
    "ebit": [20.0, 22.0, 24.2, 26.62],
    "interest_expense": [2.0, 2.0, 2.0, 2.0],
    "tax_provision": [4.5, 5.0, 5.55, 6.155],
    "pretax_income": [18.0, 20.0, 22.2, 24.62],
    "net_income": [13.5, 15.0, 16.65, 18.465],
    "total_assets": [100.0, 110.0, 121.0, 133.1],
    "total_equity": [60.0, 66.0, 72.6, 79.86],
    "cash": [10.0, 11.0, 12.1, 13.31],
    "debt": [20.0, 20.0, 20.0, 20.0],
    "capex": [5.0, 5.5, 6.05, 6.655],
    "depreciation": [3.0, 3.3, 3.63, 3.993],
    "working_capital_change": [0.0, 0.0, 0.0, 0.0],
    "fcf": [11.5, 12.8, 14.23, 15.803],
    # v0.3 additional fields
    "insider_ownership": 0.10,       # 10% > 5% threshold → Buffett check 10 hard PASS
    "stock_beta": 0.85,              # < 1.5 → Marks check 10 PASS
    "trailing_pe": 18.0,             # < 25x → Marks check 4 PASS
    "recommendation_mean": 3.2,      # 2.5-4.0 mixed/cautious → Marks check 7 PASS
    "dividend_yield": 0.02,          # 2% dividend → capital returned PASS
    "historical_shares": [10.0, 10.0, 10.0, 10.0],  # flat share count → anti-dilution PASS
    # v0.5 additional fields for Apollo
    "total_intangibles": [5.0, 5.0, 5.0, 5.0],
    "goodwill": [2.0, 2.0, 2.0, 2.0],
    "book_value_per_share": 7.986,
    "statements": {
        "years_annual": ["2022", "2023", "2024", "2025"],
        "annual": {
            "profit_loss": {
                "sales": [10.0, 11.0, 12.1, 13.31],
                "operating profit": [2.0, 2.2, 2.42, 2.662],
                "depreciation": [0.3, 0.33, 0.363, 0.3993],
                "interest": [0.2, 0.2, 0.2, 0.2],
                "profit before tax": [1.8, 2.0, 2.22, 2.462],
                "tax": [0.45, 0.5, 0.555, 0.6155],
                "net profit": [1.35, 1.5, 1.665, 1.8465]
            },
            "balance_sheet": {
                "equity capital": [6.0, 6.6, 7.26, 7.986],
                "reserves": [0.0, 0.0, 0.0, 0.0],
                "borrowings": [2.0, 2.0, 2.0, 2.0],
                "fixed assets": [5.0, 5.5, 6.05, 6.655],
                "investments": [0.0, 0.0, 0.0, 0.0],
                "inventories": [1.0, 1.1, 1.21, 1.331],
                "trade receivables": [1.0, 1.1, 1.21, 1.331],
                "trade payables": [1.0, 1.1, 1.21, 1.331],
                "cash equivalents": [1.0, 1.1, 1.21, 1.331]
            },
            "cash_flow": {
                "cash from operating activity": [1.65, 1.83, 2.028, 2.2458],
                "working capital changes": [0.0, 0.0, 0.0, 0.0],
                "cash from investing activity": [-0.5, -0.55, -0.605, -0.6655],
                "fixed assets purchased": [-0.5, -0.55, -0.605, -0.6655]
            }
        },
        "ratios": {
            "debtor days": [36.5, 36.5, 36.5, 36.5],
            "inventory days": [36.5, 36.5, 36.5, 36.5],
            "days payable": [36.5, 36.5, 36.5, 36.5]
        }
    }
}

def _make_unavailable_qualitative():
    return {
        "status": "unavailable",
        "reason": "No documents found",
        "forward_guidance": [],
        "risk_callouts": [],
        "strategic_themes": [],
        "tone_assessment": {"current": None, "trajectory": None, "notes": None},
        "coherence_assessment": {"verdict": None, "reasoning": None},
        "owner_orientation_signal": {"verdict": None, "evidence": None},
        "holdability_assessment": {"verdict": None, "reasoning": None},
        "cycle_position": {"sector_cycle": None, "company_cycle": None, "reasoning": None},
        "variant_perception": {"consensus_view": None, "company_view": None,
                               "variant_present": None, "specificity": None, "notes": None},
        "management_humility": {"verdict": None, "evidence": None},
        "why_now_signal": {"verdict": None, "specific_event": None, "notes": None},
        # v0.5 Apollo/Blackstone signals
        "structural_tailwind_signal": {"verdict": None},
        "multi_product_engagement_signal": {"verdict": None},
        "chaos_dislocation_catalyst": {"verdict": None},
        "fulcrum_security_signal": {"verdict": None},
        "abf_credit_fit": {"verdict": None},
        "complexity_moat_signal": {"verdict": None},
        "covenant_control_potential": {"verdict": None},
        "documents_used": [],
        "model": None,
    }

def _make_available_qualitative(
    coherence_verdict="coherent",
    owner_verdict="owner_oriented",
    holdability_verdict="holdable_20y",
    sector_cycle="mid_cycle",
    variant_present=True,
    specificity="high",
    humility_verdict="humble",
    why_now_verdict="dislocation_present",
):
    return {
        "status": "available",
        "model": "gemini-3.5-flash",
        "documents_used": ["test.pdf"],
        "forward_guidance": [],
        "risk_callouts": [],
        "strategic_themes": [],
        "tone_assessment": {"current": "confident", "trajectory": "stable", "notes": "Fine."},
        "coherence_assessment": {
            "verdict": coherence_verdict,
            "reasoning": "Because.",
            "evidence_quote": "Numeric claims tie to filings [test.pdf]",
            "confidence": "high",
        },
        "owner_orientation_signal": {
            "verdict": owner_verdict,
            "evidence": "Partners framing.",
            "evidence_quote": "We think of shareholders as partners [test.pdf]",
            "confidence": "high",
        },
        "holdability_assessment": {
            "verdict": holdability_verdict,
            "reasoning": "Durable demand.",
            "evidence_quote": "Category demand structurally enduring [test.pdf]",
            "confidence": "high",
        },
        "cycle_position": {
            "sector_cycle": sector_cycle,
            "company_cycle": "mid",
            "reasoning": "Mid band.",
            "evidence_quote": "Capacity utilization mid-range [test.pdf]",
            "confidence": "high",
        },
        "variant_perception": {
            "consensus_view": "Strong growth.",
            "company_view": "Modest.",
            "variant_present": variant_present,
            "specificity": specificity,
            "notes": "Specific mechanism.",
            "evidence_quote": "Management guides 10% vs consensus 18% [test.pdf]",
            "confidence": "high",
        },
        "management_humility": {
            "verdict": humility_verdict,
            "evidence": "No multi-year forecasts.",
            "evidence_quote": "We cannot predict beyond one quarter [test.pdf]",
            "confidence": "high",
        },
        "why_now_signal": {
            "verdict": why_now_verdict,
            "specific_event": "Sector de-rated.",
            "notes": "FII selling.",
            "evidence_quote": "Sector has de-rated 25% in 12 months [test.pdf]",
            "confidence": "high",
        },
        # v0.5 Apollo/Blackstone signals
        "structural_tailwind_signal": {
            "verdict": "tailwind",
            "notes": "Structural growth.",
            "evidence_quote": "Urbanization driving demand [test.pdf]",
            "confidence": "high",
        },
        "multi_product_engagement_signal": {
            "verdict": "multi_product_potential",
            "notes": "Cross-sell opportunity.",
            "evidence_quote": "Adjacent product categories identified [test.pdf]",
            "confidence": "high",
        },
        "chaos_dislocation_catalyst": {
            "verdict": "chaos_present",
            "notes": "Sector stress.",
            "evidence_quote": "FII redemptions creating forced selling [test.pdf]",
            "confidence": "high",
        },
        "fulcrum_security_signal": {
            "verdict": "fulcrum_identified",
            "notes": "Senior secured tranche.",
            "evidence_quote": "Senior lenders hold first charge on assets [test.pdf]",
            "confidence": "high",
        },
        "abf_credit_fit": {
            "verdict": "abf_primary_opportunity",
            "notes": "Asset-backed opportunity.",
            "evidence_quote": "Tangible fixed assets back the borrowing [test.pdf]",
            "confidence": "high",
        },
        "complexity_moat_signal": {
            "verdict": "high",
            "notes": "Regulatory complexity.",
            "evidence_quote": "Multi-jurisdiction licensing creates barrier [test.pdf]",
            "confidence": "high",
        },
        "covenant_control_potential": {
            "verdict": "covenant_rich_opportunity",
            "notes": "Private borrower.",
            "evidence_quote": "Company primarily bank-funded with maintenance covenants [test.pdf]",
            "confidence": "high",
        },
    }

def _make_asianpaints_qualitative():
    qual = _make_available_qualitative()
    qual.update({
        "chaos_dislocation_catalyst": {
            "verdict": "normal",
            "notes": "No dislocation.",
            "evidence_quote": "Business progressing normally [test.pdf]",
            "confidence": "high",
        },
        "fulcrum_security_signal": {
            "verdict": "clean_structure",
            "notes": "Investment-grade.",
            "evidence_quote": "Investment-grade rated, no stress [test.pdf]",
            "confidence": "high",
        },
        "abf_credit_fit": {
            "verdict": "not_credit_compatible",
            "notes": "Equity only.",
            "evidence_quote": "Pure equity play, not asset-backed [test.pdf]",
            "confidence": "high",
        },
        "complexity_moat_signal": {
            "verdict": "straightforward",
            "notes": "Simple structure.",
            "evidence_quote": "Straightforward business model [test.pdf]",
            "confidence": "high",
        },
        "permanent_hold_viable": {
            "verdict": "permanent_hold_viable",
            "notes": "Long-duration.",
            "evidence_quote": "Category demand enduring for decades [test.pdf]",
            "confidence": "high",
        },
        "covenant_control_potential": {
            "verdict": "covenant_lite_existing",
            "notes": "Bond market.",
            "evidence_quote": "Covenant-lite public bond structure [test.pdf]",
            "confidence": "high",
        },
        "willing_seller_signal": {
            "verdict": "strategic_holdout",
            "notes": "No seller pressure.",
            "evidence_quote": "Promoters retaining full stake [test.pdf]",
            "confidence": "high",
        },
        "ma_platform_potential": {
            "verdict": "not_applicable",
            "notes": "Leader in consolidated market.",
            "evidence_quote": "Market is consolidated, no roll-up [test.pdf]",
            "confidence": "high",
        },
        "workforce_stavros_fit": {
            "verdict": "mixed",
            "notes": "Mixed workforce.",
            "evidence_quote": "Mix of plant and sales workforce [test.pdf]",
            "confidence": "high",
        },
        "mgmt_upgrade_potential": {
            "verdict": "management_best_in_class",
            "notes": "Best-in-class.",
            "evidence_quote": "Management consistently cited as sector benchmark [test.pdf]",
            "confidence": "high",
        },
        "wc_optimization_signal": {
            "verdict": "already_optimized",
            "notes": "Already lean.",
            "evidence_quote": "Working capital already best-in-class [test.pdf]",
            "confidence": "high",
        },
        "structural_tailwind_signal": {
            "verdict": "tailwind",
            "notes": "Urbanization.",
            "evidence_quote": "Urbanization driving demand [test.pdf]",
            "confidence": "high",
        },
        "multi_product_engagement_signal": {
            "verdict": "single_product_only",
            "notes": "Paint only.",
            "evidence_quote": "Revenue 95% from decorative paints [test.pdf]",
            "confidence": "high",
        },
    })
    return qual
