"""Discounting engine — implemented in Step 1. Computes PV of cash flows, Enterprise Value, Equity Value, and Intrinsic Share Price."""

from src._validators import validate_number


def present_value(future_value: float, rate: float, years: int) -> float:
    """Calculates the Present Value (PV) of a single future cash flow.

    Formula:
        PV = future_value / (1 + rate) ** years

    Args:
        future_value: Nominal future cash flow amount.
        rate: Annual discount rate (e.g. WACC) as a decimal (must be > -1.0).
        years: Discounting period in years (must be a non-negative integer >= 0).

    Returns:
        float: Discounted present value of the future cash flow.

    Raises:
        TypeError: If future_value or rate is boolean/non-number, or years is not an int.
        ValueError: If future_value or rate is NaN/Infinity, rate <= -1.0, or years < 0.
    """
    fv = validate_number(future_value, "future_value")
    r = validate_number(rate, "rate")
    if r <= -1.0:
        raise ValueError(f"Argument 'rate' must be > -1.0 to prevent division by zero or negative base. Got {r}.")

    if isinstance(years, bool):
        raise TypeError("Argument 'years' cannot be a boolean.")
    if type(years) is not int:
        raise TypeError(f"Argument 'years' must be an integer, got {type(years).__name__}.")
    if years < 0:
        raise ValueError(f"Argument 'years' must be a non-negative integer (>= 0). Got {years}.")

    return fv / ((1.0 + r) ** years)


def discount_fcff_series(fcff_projection: list[float], wacc: float) -> list[float]:
    """Calculates present values for a projected series of annual Free Cash Flows.

    Element at index i (0-based) is discounted over (i + 1) years using WACC.

    Args:
        fcff_projection: Non-empty list of projected annual FCFF values.
        wacc: Weighted Average Cost of Capital discount rate.

    Returns:
        list[float]: List of present values corresponding to each projected year.

    Raises:
        TypeError: If fcff_projection is not a list or contains invalid numeric types.
        ValueError: If fcff_projection is empty or contains NaN/Infinity values.
    """
    if not isinstance(fcff_projection, list):
        raise TypeError("Argument 'fcff_projection' must be a list.")
    if len(fcff_projection) == 0:
        raise ValueError("Argument 'fcff_projection' cannot be empty.")

    return [
        present_value(fcff, wacc, i + 1)
        for i, fcff in enumerate(fcff_projection)
    ]


def enterprise_value(
    fcff_projection: list[float], terminal_value: float, wacc: float
) -> float:
    """Calculates Enterprise Value (EV) by summing PV of projected FCFF and PV of Terminal Value.

    Formula:
        Enterprise Value = Σ PV(FCFF_t) + PV(Terminal Value)
        where Terminal Value is discounted back over N = len(fcff_projection) years.

    Args:
        fcff_projection: Projected FCFF series over explicit forecast period N.
        terminal_value: Gordon Growth Terminal Value as of year N.
        wacc: Weighted Average Cost of Capital discount rate.

    Returns:
        float: Total Enterprise Value.

    Raises:
        TypeError: If inputs are invalid types.
        ValueError: If fcff_projection is empty or parameters are invalid.
    """
    pv_series = discount_fcff_series(fcff_projection, wacc)
    tv = validate_number(terminal_value, "terminal_value")
    n_years = len(fcff_projection)

    pv_tv = present_value(tv, wacc, n_years)

    return sum(pv_series) + pv_tv


def equity_value(
    enterprise_value: float, total_debt: float, cash_and_equivalents: float
) -> float:
    """Bridges Enterprise Value to Equity Value by adjusting for debt and cash.

    Formula:
        Equity Value = Enterprise Value - Total Debt + Cash & Cash Equivalents

    Args:
        enterprise_value: Total Enterprise Value derived from DCF.
        total_debt: Book value of total interest-bearing debt (must be >= 0).
        cash_and_equivalents: Balance sheet cash and cash equivalents (must be >= 0).

    Returns:
        float: Implied Equity Value.

    Raises:
        TypeError: If any parameter is boolean or non-numeric.
        ValueError: If total_debt or cash_and_equivalents is negative, or values are NaN/Infinity.
    """
    ev = validate_number(enterprise_value, "enterprise_value")
    td = validate_number(total_debt, "total_debt", allow_negative=False)
    cash = validate_number(cash_and_equivalents, "cash_and_equivalents", allow_negative=False)

    return ev - td + cash


def intrinsic_share_price(
    equity_value: float, diluted_shares_outstanding: float
) -> float:
    """Calculates intrinsic value per share from Equity Value and diluted share count.

    Formula:
        Intrinsic Share Price = Equity Value / Diluted Shares Outstanding

    Args:
        equity_value: Implied total Equity Value.
        diluted_shares_outstanding: Total diluted shares outstanding (must be > 0).

    Returns:
        float: Calculated intrinsic value per share.

    Raises:
        TypeError: If parameters are boolean or non-numeric.
        ValueError: If diluted_shares_outstanding <= 0 or inputs are NaN/Infinity.
    """
    eq_val = validate_number(equity_value, "equity_value")
    shares = validate_number(diluted_shares_outstanding, "diluted_shares_outstanding")
    if shares <= 0.0:
        raise ValueError(
            f"diluted_shares_outstanding must be strictly positive (> 0). Got {shares}."
        )

    return eq_val / shares


def margin_of_safety(intrinsic_price: float, market_price: float) -> float:
    """Calculates Margin of Safety comparing intrinsic share price against live market price.

    Formula:
        Margin of Safety = (Intrinsic Price - Market Price) / Market Price

    Sign Convention:
        Positive result (> 0): Undervalued relative to intrinsic value.
        Negative result (< 0): Overvalued relative to intrinsic value.

    Args:
        intrinsic_price: Intrinsic value per share derived from model.
        market_price: Current market share price (must be > 0).

    Returns:
        float: Margin of Safety proportion (e.g. -0.2379 for -23.79% overvaluation).

    Raises:
        TypeError: If parameters are boolean or non-numeric.
        ValueError: If market_price <= 0 or inputs are NaN/Infinity.
    """
    intr = validate_number(intrinsic_price, "intrinsic_price")
    mkt = validate_number(market_price, "market_price")
    if mkt <= 0.0:
        raise ValueError(f"market_price must be strictly positive (> 0). Got {mkt}.")

    return (intr - mkt) / mkt
