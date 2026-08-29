"""Unit tests for dashboard presentation helper functions (src/app_helpers.py)."""

import pytest
from src.app_helpers import (
    compute_wacc_spread,
    format_currency,
    get_cost_of_debt_summary,
    get_currency_symbol,
    get_growth_summary,
    get_sensitivity_caution_message,
)
from src.dcf_engine import DCFValuationResult


def test_get_currency_symbol():
    """Verify symbol mapping for standard and unknown currency codes."""
    assert get_currency_symbol("USD") == "$"
    assert get_currency_symbol("INR") == "₹"
    assert get_currency_symbol("EUR") == "€"
    assert get_currency_symbol("GBP") == "£"
    assert get_currency_symbol("XYZ") == "XYZ "
    assert get_currency_symbol(None) == "$"


def test_format_currency_scaling():
    """Verify formatting and scaling across Thousands, Millions, Billions, and Trillions."""
    assert format_currency(1250.50, "USD") == "$1,250.50"
    assert format_currency(4500000.0, "USD") == "$4.50M"
    assert format_currency(133050000000.0, "USD") == "$133.05B"
    assert format_currency(4591036923904.0, "USD") == "$4.59T"
    assert format_currency(434210504000.0, "INR") == "₹434.21B"
    assert format_currency(-12715000000.0, "USD") == "-$12.71B"


def test_compute_wacc_spread_threshold():
    """Verify WACC spread calculation and sensitivity caution flagging."""
    # Normal spread: 10.0% WACC, 2.5% terminal growth -> 7.5% spread (No caution)
    spread_pct, is_caution = compute_wacc_spread(0.10, 0.025)
    assert pytest.approx(spread_pct, abs=1e-4) == 7.5
    assert is_caution is False

    # Thin spread: 4.81% WACC, 3.0% terminal growth -> 1.81% spread (< 2.0% caution threshold)
    spread_pct_thin, is_caution_thin = compute_wacc_spread(0.0481, 0.03)
    assert pytest.approx(spread_pct_thin, abs=1e-4) == 1.81
    assert is_caution_thin is True


def test_get_sensitivity_caution_message():
    """Verify text content of sensitivity caution alert."""
    msg = get_sensitivity_caution_message(0.0481, 0.03, 1.81, 91.7)
    assert "HIGH SENSITIVITY CAUTION" in msg
    assert "1.81% < 2.00%" in msg
    assert "91.7%" in msg


def test_get_growth_summary():
    """Verify growth rate summary text generation."""
    dummy_res = DCFValuationResult(
        ticker="TST",
        company_name="Test Inc",
        currency="USD",
        data_retrieved_at="2026-08-29T00:00:00Z",
        base_year_fcff=100.0,
        cost_of_equity=0.10,
        cost_of_debt_after_tax=0.04,
        wacc=0.08,
        projected_fcffs=[105.0, 110.0],
        terminal_value=2000.0,
        discounted_terminal_value=1700.0,
        sum_of_discounted_fcffs=200.0,
        enterprise_value=1900.0,
        equity_value=1800.0,
        implied_share_price=18.0,
        current_price=15.0,
        implied_upside_pct=20.0,
        primary_fiscal_year="2025-12-31",
        interest_expense_fiscal_year="2025-12-31",
        interest_expense_vintage_gap_years=0,
        cost_of_debt_flagged=False,
        tax_rate_fallback_used=False,
        fx_rate_applied=1.0,
        manual_cost_of_debt_used=False,
        growth_rate_source="explicit",
        historical_cagr_suggestion=0.065,
        projection_growth_rate=0.05,
        terminal_growth_rate=0.02,
        projection_years=5,
        warnings=[],
    )

    summary = get_growth_summary(dummy_res)
    assert "Projection Growth Rate: 5.00%" in summary
    assert "Source: Explicit Input" in summary
    assert "3-Year Historical Revenue CAGR: 6.50%" in summary


def test_get_cost_of_debt_summary():
    """Verify cost of debt summary text generation across manual, vintage gap, and aligned cases."""
    dummy_res = DCFValuationResult(
        ticker="TST",
        company_name="Test Inc",
        currency="USD",
        data_retrieved_at="2026-08-29T00:00:00Z",
        base_year_fcff=100.0,
        cost_of_equity=0.10,
        cost_of_debt_after_tax=0.04,
        wacc=0.08,
        projected_fcffs=[105.0, 110.0],
        terminal_value=2000.0,
        discounted_terminal_value=1700.0,
        sum_of_discounted_fcffs=200.0,
        enterprise_value=1900.0,
        equity_value=1800.0,
        implied_share_price=18.0,
        current_price=15.0,
        implied_upside_pct=20.0,
        primary_fiscal_year="2025-09-30",
        interest_expense_fiscal_year="2023-09-30",
        interest_expense_vintage_gap_years=2,
        cost_of_debt_flagged=True,
        tax_rate_fallback_used=False,
        fx_rate_applied=1.0,
        manual_cost_of_debt_used=False,
        growth_rate_source="explicit",
        historical_cagr_suggestion=None,
        projection_growth_rate=0.05,
        terminal_growth_rate=0.02,
        projection_years=5,
        warnings=[],
    )

    # Vintage gap case
    summary_gap = get_cost_of_debt_summary(dummy_res)
    assert "FY 2023-09-30" in summary_gap
    assert "2-year gap" in summary_gap

    # Manual override case
    dummy_res.manual_cost_of_debt_used = True
    summary_manual = get_cost_of_debt_summary(dummy_res)
    assert "Manual Cost of Debt Override used" in summary_manual
