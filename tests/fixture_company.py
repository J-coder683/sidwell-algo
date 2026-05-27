# Fixture inputs for snapshot testing
FIXTURE_RISK_FREE_RATE = 0.06

FIXTURE_MACRO = {
    "mature_market_erp": 0.05,
    "country_risk_premium": 0.02,
    "total_erp": 0.07,
    "industry_unlevered_beta": 0.90,
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
        "coherence_assessment": {"verdict": coherence_verdict, "reasoning": "Because."},
        "owner_orientation_signal": {"verdict": owner_verdict, "evidence": "Partners framing."},
        "holdability_assessment": {"verdict": holdability_verdict, "reasoning": "Durable demand."},
        "cycle_position": {"sector_cycle": sector_cycle, "company_cycle": "mid", "reasoning": "Mid band."},
        "variant_perception": {"consensus_view": "Strong growth.", "company_view": "Modest.",
                               "variant_present": variant_present, "specificity": specificity, "notes": "Specific mechanism."},
        "management_humility": {"verdict": humility_verdict, "evidence": "No multi-year forecasts."},
        "why_now_signal": {"verdict": why_now_verdict, "specific_event": "Sector de-rated.", "notes": "FII selling."},
        # v0.5 Apollo/Blackstone signals
        "structural_tailwind_signal": {"verdict": "tailwind"},
        "multi_product_engagement_signal": {"verdict": "multi_product_potential"},
        "chaos_dislocation_catalyst": {"verdict": "chaos_present"},
        "fulcrum_security_signal": {"verdict": "fulcrum_identified"},
        "abf_credit_fit": {"verdict": "abf_primary_opportunity"},
        "complexity_moat_signal": {"verdict": "high"},
        "covenant_control_potential": {"verdict": "covenant_rich_opportunity"},
    }

def _make_asianpaints_qualitative():
    qual = _make_available_qualitative()
    qual.update({
        "chaos_dislocation_catalyst": {"verdict": "normal"},
        "fulcrum_security_signal": {"verdict": "clean_structure"},
        "abf_credit_fit": {"verdict": "not_credit_compatible"},
        "complexity_moat_signal": {"verdict": "straightforward"},
        "permanent_hold_viable": {"verdict": "permanent_hold_viable"},
        "covenant_control_potential": {"verdict": "covenant_lite_existing"},
        "willing_seller_signal": {"verdict": "strategic_holdout"},
        "ma_platform_potential": {"verdict": "not_applicable"},
        "workforce_stavros_fit": {"verdict": "mixed"},
        "mgmt_upgrade_potential": {"verdict": "management_best_in_class"},
        "wc_optimization_signal": {"verdict": "already_optimized"},
        "structural_tailwind_signal": {"verdict": "tailwind"},
        "multi_product_engagement_signal": {"verdict": "single_product_only"},
    })
    return qual
