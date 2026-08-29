"""DCF Orchestration Engine — implemented in Step 3.

Connects Step 2 (Data Layer) with Step 1 (Valuation Math Engine) to perform end-to-end
DCF valuations with complete transparency on data assumptions, fiscal year vintages, and growth rates.
"""

from dataclasses import dataclass
from typing import Any, Optional
import yfinance as yf

from src.data_fetch import (
    CompanyFinancials,
    UnsupportedSectorError,
    fetch_company_financials,
    historical_revenue_cagr,
)
from src.discounting import (
    discount_fcff_series,
    enterprise_value,
    equity_value,
    intrinsic_share_price,
    margin_of_safety,
    present_value,
)
from src.fcff import calculate_fcff, project_fcff
from src.terminal_value import gordon_growth_terminal_value
from src.wacc import cost_of_debt_after_tax, cost_of_equity, wacc


@dataclass
class DCFValuationResult:
    """Structured end-to-end DCF valuation output containing all intermediate calculations and assumption flags.

    Attributes:
        ticker: Ticker symbol (e.g. 'AAPL').
        company_name: Full corporate name.
        currency: Trading currency code (e.g. 'USD', 'INR').
        data_retrieved_at: ISO 8601 UTC timestamp of financial data retrieval.
        base_year_fcff: Free Cash Flow to Firm calculated for the base year (in trading currency).
        cost_of_equity: Derived Cost of Equity (CAPM) as a decimal.
        cost_of_debt_after_tax: Derived after-tax Cost of Debt as a decimal.
        wacc: Derived Weighted Average Cost of Capital as a decimal.
        projected_fcffs: List of projected FCFF values over the forecast period.
        terminal_value: Nominal Terminal Value as of year N.
        discounted_terminal_value: Present Value of Terminal Value.
        sum_of_discounted_fcffs: Sum of Present Values of projected FCFFs.
        enterprise_value: Total Enterprise Value (in trading currency).
        equity_value: Total Equity Value (in trading currency).
        implied_share_price: Calculated intrinsic share price (in trading currency).
        current_price: Market share price at valuation time (in trading currency).
        implied_upside_pct: Margin of safety percentage (positive = undervalued, negative = overvalued).
        primary_fiscal_year: Date string of primary financial statement column.
        interest_expense_fiscal_year: Date string of column used for interest_expense.
        interest_expense_vintage_gap_years: Difference in years between primary FY and interest_expense FY.
        cost_of_debt_flagged: True if cost of debt calculation uses prior-year interest expense fallback.
        tax_rate_fallback_used: True if tax rate defaulted to 0.25 statutory rate.
        fx_rate_applied: FX rate multiplier applied to statement metrics (1.0 if no conversion).
        manual_cost_of_debt_used: True if user supplied a manual cost of debt override.
        growth_rate_source: 'explicit' or 'historical_cagr_suggestion'.
        historical_cagr_suggestion: Computed historical revenue CAGR (populated for comparison even if explicit used).
        projection_growth_rate: Annual growth rate used during explicit projection period.
        terminal_growth_rate: Perpetual growth rate used for Gordon Growth terminal value.
        projection_years: Explicit forecast horizon in years.
        warnings: List of human-readable warning strings detailing fallbacks, vintage gaps, or FX adjustments.
    """
    ticker: str
    company_name: str
    currency: str
    data_retrieved_at: str
    base_year_fcff: float
    cost_of_equity: float
    cost_of_debt_after_tax: float
    wacc: float
    projected_fcffs: list[float]
    terminal_value: float
    discounted_terminal_value: float
    sum_of_discounted_fcffs: float
    enterprise_value: float
    equity_value: float
    implied_share_price: float
    current_price: float
    implied_upside_pct: float
    primary_fiscal_year: str
    interest_expense_fiscal_year: str
    interest_expense_vintage_gap_years: int
    cost_of_debt_flagged: bool
    tax_rate_fallback_used: bool
    fx_rate_applied: float
    manual_cost_of_debt_used: bool
    growth_rate_source: str
    historical_cagr_suggestion: Optional[float]
    projection_growth_rate: float
    terminal_growth_rate: float
    projection_years: int
    warnings: list[str]


def run_dcf_valuation(
    ticker: str,
    projection_years: int,
    terminal_growth_rate: float,
    projection_growth_rate: Optional[float] = None,
    use_historical_cagr_suggestion: bool = False,
    manual_cost_of_debt: Optional[float] = None,
    risk_free_rate: float = 0.0425,
    equity_risk_premium: float = 0.055,
    ticker_obj: Optional[Any] = None,
    fx_rate_override: Optional[float] = None,
) -> DCFValuationResult:
    """Executes a single-stage Discounted Cash Flow (DCF) valuation pipeline for a non-financial company.

    Pipeline Steps:
        1. Fetch & normalize company financials via Step 2 (fetch_company_financials).
        2. Derive base-year FCFF via Step 1 (calculate_fcff).
        3. Compute WACC via Step 1 (cost_of_equity, cost_of_debt_after_tax, wacc), checking vintage alignment.
        4. Project FCFF over projection_years via Step 1 (project_fcff).
        5. Calculate Terminal Value via Step 1 (gordon_growth_terminal_value).
        6. Discount FCFF series and Terminal Value via Step 1 (enterprise_value).
        7. Bridge Enterprise Value to Equity Value & Intrinsic Share Price via Step 1 (equity_value, intrinsic_share_price).
        8. Compute Margin of Safety / Implied Upside Percentage via Step 1 (margin_of_safety).

    Args:
        ticker: Ticker symbol string (e.g. 'AAPL', 'MSFT', 'INFY.NS').
        projection_years: Forecast period in years (e.g. 5).
        terminal_growth_rate: Perpetual terminal growth rate as a decimal (e.g. 0.025 for 2.5%).
        projection_growth_rate: Optional explicit annual FCFF growth rate (e.g. 0.08 for 8%).
        use_historical_cagr_suggestion: If True, computes historical revenue CAGR as growth rate suggestion.
        manual_cost_of_debt: Optional manual pre-tax cost of debt override as a decimal (e.g. 0.045 for 4.5%).
        risk_free_rate: Benchmark risk-free interest rate (default 0.0425 = 4.25%).
        equity_risk_premium: Equity risk premium (default 0.055 = 5.5%).
        ticker_obj: Optional pre-constructed yfinance Ticker object (useful for testing/mocking).
        fx_rate_override: Optional manual exchange rate override (useful for testing/mocking).

    Returns:
        DCFValuationResult: Structured valuation result dataclass.

    Raises:
        ValueError: If ticker/inputs are invalid, or terminal_growth_rate >= WACC.
        UnsupportedSectorError: If company belongs to the financial sector.
    """
    # 1. Fetch & Normalize Data via Step 2
    fin: CompanyFinancials = fetch_company_financials(
        ticker=ticker, ticker_obj=ticker_obj, fx_rate_override=fx_rate_override
    )

    warnings: list[str] = []

    # 2. Determine Growth Rate Source & Value
    cagr_suggestion: Optional[float] = None
    if use_historical_cagr_suggestion:
        try:
            cagr_suggestion = historical_revenue_cagr(ticker=ticker, years=3, ticker_obj=ticker_obj)
        except Exception:
            cagr_suggestion = None

    if projection_growth_rate is not None:
        effective_proj_growth = float(projection_growth_rate)
        growth_source = "explicit"
        if use_historical_cagr_suggestion and cagr_suggestion is not None:
            warnings.append(
                f"Historical CAGR suggestion computed ({cagr_suggestion * 100:.2f}%) but explicit "
                f"projection growth rate ({effective_proj_growth * 100:.2f}%) took precedence."
            )
    elif use_historical_cagr_suggestion:
        if cagr_suggestion is None:
            raise ValueError(
                f"Could not compute historical revenue CAGR suggestion for ticker '{ticker}'. "
                "Please provide an explicit projection_growth_rate."
            )
        effective_proj_growth = cagr_suggestion
        growth_source = "historical_cagr_suggestion"
    else:
        raise ValueError(
            "projection_growth_rate must be explicitly specified when use_historical_cagr_suggestion is False."
        )

    # 3. Base Year FCFF Calculation via Step 1
    base_fcff = calculate_fcff(
        ebit=fin.ebit,
        tax_rate=fin.effective_tax_rate,
        depreciation_amortization=fin.depreciation_amortization,
        capex=fin.capex,
        change_in_nwc=fin.change_in_nwc,
    )

    # 4. WACC Calculation & Vintage Check via Step 1
    ke = cost_of_equity(
        risk_free_rate=risk_free_rate,
        beta=fin.beta,
        equity_risk_premium=equity_risk_premium,
    )

    # Vintage gap assessment
    primary_yr = int(fin.primary_fiscal_year[:4]) if len(fin.primary_fiscal_year) >= 4 and fin.primary_fiscal_year[:4].isdigit() else 0
    interest_yr = int(fin.interest_expense_fiscal_year[:4]) if len(fin.interest_expense_fiscal_year) >= 4 and fin.interest_expense_fiscal_year[:4].isdigit() else 0
    vintage_gap_years = max(0, primary_yr - interest_yr) if primary_yr > 0 and interest_yr > 0 else 0

    manual_cost_of_debt_used = False
    if manual_cost_of_debt is not None:
        manual_kd_pretax = float(manual_cost_of_debt)
        kd_after_tax = manual_kd_pretax * (1.0 - fin.effective_tax_rate)
        manual_cost_of_debt_used = True
        cost_of_debt_flagged = False
    else:
        kd_after_tax = cost_of_debt_after_tax(
            interest_expense=fin.interest_expense,
            total_debt=fin.total_debt,
            tax_rate=fin.effective_tax_rate,
        )
        cost_of_debt_flagged = fin.interest_expense_fallback_used or (vintage_gap_years > 0)

    if vintage_gap_years > 0:
        warnings.append(
            f"Interest expense was drawn from fiscal year {fin.interest_expense_fiscal_year}, "
            f"creating a {vintage_gap_years}-year vintage gap with primary fiscal year {fin.primary_fiscal_year}."
        )

    if fin.tax_rate_fallback_used:
        warnings.append("Effective tax rate defaulted to 0.25 statutory rate fallback due to negative/zero pretax income.")

    if fin.fx_rate_applied != 1.0:
        warnings.append(
            f"Financial statement figures converted to trading currency '{fin.currency}' "
            f"using exchange rate multiplier {fin.fx_rate_applied}."
        )

    wacc_val = wacc(
        market_value_equity=fin.market_cap,
        total_debt=fin.total_debt,
        cost_of_equity=ke,
        cost_of_debt_after_tax=kd_after_tax,
    )

    # 5. FCFF Projection via Step 1
    projected_fcffs = project_fcff(
        base_fcff=base_fcff,
        growth_rate=effective_proj_growth,
        years=projection_years,
    )

    # 6. Terminal Value Calculation via Step 1
    final_fcff = projected_fcffs[-1]
    tv_nominal = gordon_growth_terminal_value(
        final_year_fcff=final_fcff,
        terminal_growth_rate=terminal_growth_rate,
        wacc=wacc_val,
    )

    # 7. Discounting & Valuation Bridges via Step 1
    ev_val = enterprise_value(
        fcff_projection=projected_fcffs,
        terminal_value=tv_nominal,
        wacc=wacc_val,
    )

    pv_fcffs = discount_fcff_series(projected_fcffs, wacc_val)
    sum_pv_fcffs = sum(pv_fcffs)
    pv_tv = present_value(tv_nominal, wacc_val, projection_years)

    eq_val = equity_value(
        enterprise_value=ev_val,
        total_debt=fin.total_debt,
        cash_and_equivalents=fin.cash_and_equivalents,
    )

    implied_price = intrinsic_share_price(
        equity_value=eq_val,
        diluted_shares_outstanding=fin.diluted_shares_outstanding,
    )

    upside_ratio = margin_of_safety(
        intrinsic_price=implied_price,
        market_price=fin.current_price,
    )
    upside_pct = upside_ratio * 100.0

    return DCFValuationResult(
        ticker=fin.ticker,
        company_name=fin.company_name,
        currency=fin.currency,
        data_retrieved_at=fin.data_retrieved_at,
        base_year_fcff=base_fcff,
        cost_of_equity=ke,
        cost_of_debt_after_tax=kd_after_tax,
        wacc=wacc_val,
        projected_fcffs=projected_fcffs,
        terminal_value=tv_nominal,
        discounted_terminal_value=pv_tv,
        sum_of_discounted_fcffs=sum_pv_fcffs,
        enterprise_value=ev_val,
        equity_value=eq_val,
        implied_share_price=implied_price,
        current_price=fin.current_price,
        implied_upside_pct=upside_pct,
        primary_fiscal_year=fin.primary_fiscal_year,
        interest_expense_fiscal_year=fin.interest_expense_fiscal_year,
        interest_expense_vintage_gap_years=vintage_gap_years,
        cost_of_debt_flagged=cost_of_debt_flagged,
        tax_rate_fallback_used=fin.tax_rate_fallback_used,
        fx_rate_applied=fin.fx_rate_applied,
        manual_cost_of_debt_used=manual_cost_of_debt_used,
        growth_rate_source=growth_source,
        historical_cagr_suggestion=cagr_suggestion,
        projection_growth_rate=effective_proj_growth,
        terminal_growth_rate=terminal_growth_rate,
        projection_years=projection_years,
        warnings=warnings,
    )
