"""Bank handling (v0.7.7): banks are scraped and analysed like any other
company, but the FCF-based DCF is skipped. The two valuation-dependent lens
checks (Buffett #12 margin of safety, Marks #1 deep MoS + #2 asymmetric payoff)
are marked N/A and excluded from the denominator, and auto-activate once a bank
valuation model (DDM) supplies an intrinsic value via ddm_results.
"""
import pytest

from valuation.dcf import run_dcf_valuation
from lenses.buffett import evaluate_buffett_lens
from lenses.marks import evaluate_marks_lens
from tests.fixture_company import (
    _make_unavailable_qualitative,
    FIXTURE_INPUTS,
    FIXTURE_MACRO,
    FIXTURE_RISK_FREE_RATE,
)


def _non_bank_financials():
    """A valid non-bank DCF input (the snapshot fixture, is_bank absent)."""
    return dict(FIXTURE_INPUTS)


def _bank_financials(is_bank=True):
    """A bank-shaped fixture with real (non-zero) financials, mirroring how the
    screener now populates revenue/ebit for banks."""
    return {
        "ticker": "TESTBANK.NS",
        "current_price": 100.0,
        "market_cap": 1000.0,
        "shares_outstanding": 10.0,
        "years": ["2022-03-31", "2023-03-31", "2024-03-31", "2025-03-31"],
        "revenue": [110.0, 121.0, 133.1, 146.41],          # ~10% CAGR
        "gross_profit": [55.0, 60.5, 66.55, 73.205],
        "ebit": [16.5, 18.15, 19.965, 21.9615],
        "interest_expense": [40.0, 44.0, 48.0, 52.0],       # large for a bank (cost of funds)
        "tax_provision": [4.15, 4.57, 5.03, 5.53],
        "pretax_income": [16.5, 18.15, 19.965, 21.9615],
        "net_income": [12.35, 13.58, 14.94, 16.43],
        "total_assets": [1000.0, 1100.0, 1210.0, 1331.0],
        "total_equity": [80.0, 88.0, 96.8, 106.48],
        "cash": [20.0, 22.0, 24.2, 26.62],
        "debt": [500.0, 550.0, 605.0, 665.5],
        "capex": [3.3, 3.63, 3.993, 4.39],
        "depreciation": [2.2, 2.42, 2.66, 2.93],
        "working_capital_change": [0.0, 0.0, 0.0, 0.0],
        "fcf": [11.25, 12.37, 13.61, 14.97],
        "insider_ownership": 0.0,
        "stock_beta": 1.0,
        "trailing_pe": 18.0,
        "recommendation_mean": 3.0,
        "dividend_yield": 0.01,
        "historical_shares": [10.0, 10.0, 10.0, 10.0],
        "total_intangibles": [0.0, 0.0, 0.0, 0.0],
        "goodwill": [0.0, 0.0, 0.0, 0.0],
        "book_value_per_share": 10.648,
        "is_bank": is_bank,
    }


def _bank_macro():
    return {
        "mature_market_erp": 0.05,
        "country_risk_premium": 0.02,
        "total_erp": 0.07,
        "industry_levered_beta": 0.5,
        "industry_unlevered_beta": 0.5,
        "industry_de_ratio": 2.0,
        "target_industry": "Bank (Money Center)",
        "industry_source": "scraped_industry",
    }


# ── DCF ───────────────────────────────────────────────────────────────────

def test_dcf_skipped_for_bank_without_raising():
    res = run_dcf_valuation(_bank_financials(), _bank_macro(), 0.07)
    assert res["not_applicable"] is True
    assert res["intrinsic_value_per_share"] is None
    assert res["wacc"] is None
    assert res["projections"] == []
    assert "not_applicable_reason" in res
    # Lenses still need these from assumptions:
    assert res["assumptions"]["target_industry"] == "Bank (Money Center)"
    assert res["assumptions"]["tax_rate"] is not None
    assert res["assumptions"]["revenue_growth"] is not None


def test_dcf_runs_normally_for_non_bank():
    res = run_dcf_valuation(_non_bank_financials(), FIXTURE_MACRO, FIXTURE_RISK_FREE_RATE)
    assert not res.get("not_applicable")
    assert res["intrinsic_value_per_share"] is not None
    assert res["wacc"] is not None


# ── Buffett lens ────────────────────────────────────────────────────────────

def test_buffett_bank_mos_na_and_denominator_13():
    dcf = run_dcf_valuation(_bank_financials(), _bank_macro(), 0.07)
    res = evaluate_buffett_lens(
        _bank_financials(), dcf, qualitative_results=_make_unavailable_qualitative()
    )
    mos = res["checks"]["12_margin_of_safety"]
    assert mos["applicable"] is False
    assert mos["passed"] is False
    assert res["max_score"] == 13
    # A bank can never be BUY/WAIT without a valuation.
    assert res["verdict"] in ("WATCH", "SKIP")


def test_buffett_non_bank_denominator_14():
    dcf = run_dcf_valuation(_non_bank_financials(), FIXTURE_MACRO, FIXTURE_RISK_FREE_RATE)
    res = evaluate_buffett_lens(
        _non_bank_financials(), dcf, qualitative_results=_make_unavailable_qualitative()
    )
    assert res["max_score"] == 14
    assert "applicable" not in res["checks"]["12_margin_of_safety"]


def test_buffett_mos_activates_with_ddm_results():
    dcf = run_dcf_valuation(_bank_financials(), _bank_macro(), 0.07)
    # A future DDM supplies a deeply-discounted intrinsic value → MoS applicable.
    ddm = {"intrinsic_value_per_share": 1000.0}  # vs price 100 → huge MoS
    res = evaluate_buffett_lens(
        _bank_financials(), dcf, qualitative_results=_make_unavailable_qualitative(),
        ddm_results=ddm,
    )
    mos = res["checks"]["12_margin_of_safety"]
    assert mos.get("applicable", True) is True
    assert mos["passed"] is True          # 90% MoS > 25%
    assert res["max_score"] == 14


# ── Marks lens ──────────────────────────────────────────────────────────────

def test_marks_bank_both_valuation_checks_na_denominator_12():
    dcf = run_dcf_valuation(_bank_financials(), _bank_macro(), 0.07)
    res = evaluate_marks_lens(
        _bank_financials(), dcf, qualitative_results=_make_unavailable_qualitative()
    )
    assert res["checks"]["1_deep_mos"]["applicable"] is False
    assert res["checks"]["2_asymmetric_payoff"]["applicable"] is False
    assert res["max_score"] == 12
    assert res["verdict"] in ("WATCH", "SKIP")


def test_marks_non_bank_denominator_14():
    dcf = run_dcf_valuation(_non_bank_financials(), FIXTURE_MACRO, FIXTURE_RISK_FREE_RATE)
    res = evaluate_marks_lens(
        _non_bank_financials(), dcf, qualitative_results=_make_unavailable_qualitative()
    )
    assert res["max_score"] == 14
    assert "applicable" not in res["checks"]["1_deep_mos"]
