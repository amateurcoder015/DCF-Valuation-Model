"""Helper functions for Streamlit dashboard presentation, formatting, and sensitivity calculations."""

from typing import Tuple
from src.dcf_engine import DCFValuationResult


CURRENCY_SYMBOLS = {
    "USD": "$",
    "INR": "₹",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CAD": "CA$",
    "AUD": "A$",
}


def get_currency_symbol(currency_code: str) -> str:
    """Returns standard currency symbol for a given currency code."""
    if not currency_code or not isinstance(currency_code, str):
        return "$"
    return CURRENCY_SYMBOLS.get(currency_code.strip().upper(), f"{currency_code.strip().upper()} ")


def format_currency(value: float, currency_code: str = "USD", include_symbol: bool = True) -> str:
    """Formats monetary amounts cleanly with optional scaling (Thousand, Million, Billion, Trillion).

    Args:
        value: Monetary amount float.
        currency_code: ISO currency code (e.g. 'USD', 'INR').
        include_symbol: If True, prefixes currency symbol.

    Returns:
        str: Formatted currency string.
    """
    sym = get_currency_symbol(currency_code) if include_symbol else ""
    abs_val = abs(value)
    sign = "-" if value < 0 else ""

    if abs_val >= 1.0e12:
        return f"{sign}{sym}{abs_val / 1.0e12:,.2f}T"
    elif abs_val >= 1.0e9:
        return f"{sign}{sym}{abs_val / 1.0e9:,.2f}B"
    elif abs_val >= 1.0e6:
        return f"{sign}{sym}{abs_val / 1.0e6:,.2f}M"
    elif abs_val >= 1.0e3:
        return f"{sign}{sym}{abs_val:,.2f}"
    else:
        return f"{sign}{sym}{abs_val:,.2f}"


def compute_wacc_spread(
    wacc: float, terminal_growth_rate: float, caution_threshold_pct: float = 2.0
) -> Tuple[float, bool]:
    """Computes the spread between WACC and Terminal Growth Rate and evaluates sensitivity caution threshold.

    Sensitivity Caution Rule:
        If WACC - terminal_growth_rate < 2.0 percentage points (0.02), Terminal Value becomes extremely
        dominant and volatile. The dashboard must display a prominent caution note to prevent misleading headline interpretation.

    Args:
        wacc: WACC as a decimal proportion (e.g. 0.088 for 8.8%).
        terminal_growth_rate: Perpetual growth rate as a decimal (e.g. 0.025 for 2.5%).
        caution_threshold_pct: Threshold percentage spread triggering sensitivity caution (default 2.0%).

    Returns:
        Tuple[float, bool]: (spread_percentage_points, is_caution_flagged).
    """
    spread_pct = (wacc - terminal_growth_rate) * 100.0
    is_caution = spread_pct < caution_threshold_pct
    return spread_pct, is_caution


def get_sensitivity_caution_message(
    wacc: float, terminal_growth_rate: float, spread_pct: float, tv_share_pct: float
) -> str:
    """Generates sensitivity caution alert text for thin WACC-to-terminal-growth spreads."""
    return (
        f"⚠️ HIGH SENSITIVITY CAUTION: The WACC to Terminal Growth spread is thin "
        f"({spread_pct:.2f}% < 2.00%). Discounted Terminal Value accounts for {tv_share_pct:.1f}% "
        f"of total Enterprise Value. The implied share price and upside/downside percentage are "
        f"mathematically hyper-sensitive to small 25-50 bps shifts in WACC ({wacc * 100:.2f}%) or "
        f"terminal growth ({terminal_growth_rate * 100:.2f}%)."
    )


def get_growth_summary(result: DCFValuationResult) -> str:
    """Generates a text summary of growth rate sources and historical CAGR comparison."""
    source_str = "Explicit Input" if result.growth_rate_source == "explicit" else "Historical Revenue CAGR Suggestion"
    msg = f"Projection Growth Rate: {result.projection_growth_rate * 100:.2f}% (Source: {source_str})."
    if result.historical_cagr_suggestion is not None:
        msg += f" 3-Year Historical Revenue CAGR: {result.historical_cagr_suggestion * 100:.2f}%."
    return msg


def get_cost_of_debt_summary(result: DCFValuationResult) -> str:
    """Generates a text summary of cost of debt vintage status, manual overrides, and flags."""
    if result.manual_cost_of_debt_used:
        return f"Manual Cost of Debt Override used. After-tax Cost of Debt: {result.cost_of_debt_after_tax * 100:.2f}%."
    elif result.interest_expense_vintage_gap_years > 0:
        return (
            f"Cost of Debt derived from FY {result.interest_expense_fiscal_year} interest expense "
            f"({result.interest_expense_vintage_gap_years}-year gap with primary FY {result.primary_fiscal_year}). "
            f"After-tax Cost of Debt: {result.cost_of_debt_after_tax * 100:.2f}%."
        )
    else:
        return f"Cost of Debt derived from current FY {result.primary_fiscal_year} interest expense. After-tax Cost of Debt: {result.cost_of_debt_after_tax * 100:.2f}%."
