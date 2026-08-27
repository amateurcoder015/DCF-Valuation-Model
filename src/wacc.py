"""WACC engine — implemented in Step 1. Computes Cost of Equity (CAPM), Cost of Debt, and weighted WACC."""

from src._validators import validate_number


def cost_of_equity(
    risk_free_rate: float, beta: float, equity_risk_premium: float
) -> float:
    """Calculates Cost of Equity using the Capital Asset Pricing Model (CAPM).

    Formula:
        Cost of Equity = Risk-Free Rate + Beta * Equity Risk Premium

    Args:
        risk_free_rate: Benchmark risk-free interest rate (e.g. 0.07 for 7%).
        beta: Equity beta measuring market volatility relative to benchmark index.
        equity_risk_premium: Expected excess market return over risk-free rate (e.g. 0.05 for 5%).

    Returns:
        float: Calculated Cost of Equity as a decimal proportion.

    Raises:
        TypeError: If any parameter is a boolean or non-numeric type.
        ValueError: If any parameter is NaN or Infinity.
    """
    rf = validate_number(risk_free_rate, "risk_free_rate")
    b = validate_number(beta, "beta")
    erp = validate_number(equity_risk_premium, "equity_risk_premium")
    return rf + b * erp


def cost_of_debt_after_tax(
    interest_expense: float, total_debt: float, tax_rate: float
) -> float:
    """Calculates the after-tax Cost of Debt for corporate debt obligations.

    Formula:
        Cost of Debt (after-tax) = (Interest Expense / Total Debt) * (1 - Tax Rate)

    Special Case:
        If total_debt == 0, returns 0.0 rather than dividing by zero.

    Args:
        interest_expense: Annual interest payments on debt obligations (must be non-negative).
        total_debt: Total outstanding interest-bearing debt (must be non-negative).
        tax_rate: Effective corporate tax rate as a decimal in [0, 1].

    Returns:
        float: Calculated after-tax Cost of Debt as a decimal proportion.

    Raises:
        TypeError: If any parameter is a boolean or non-numeric type.
        ValueError: If any parameter is NaN/Infinity, tax_rate is outside [0, 1],
            or interest_expense/total_debt is negative.
    """
    ie = validate_number(interest_expense, "interest_expense", allow_negative=False)
    td = validate_number(total_debt, "total_debt", allow_negative=False)
    tr = validate_number(tax_rate, "tax_rate", min_val=0.0, max_val=1.0)

    if td == 0.0:
        return 0.0

    return (ie / td) * (1.0 - tr)


def wacc(
    market_value_equity: float,
    total_debt: float,
    cost_of_equity: float,
    cost_of_debt_after_tax: float,
) -> float:
    """Calculates Weighted Average Cost of Capital (WACC).

    Formula:
        weight_equity = market_value_equity / (market_value_equity + total_debt)
        weight_debt = total_debt / (market_value_equity + total_debt)
        WACC = weight_equity * cost_of_equity + weight_debt * cost_of_debt_after_tax

    Args:
        market_value_equity: Market capitalization / equity value (must be non-negative).
        total_debt: Book value of total debt (must be non-negative).
        cost_of_equity: Cost of equity derived via CAPM.
        cost_of_debt_after_tax: After-tax cost of debt.

    Returns:
        float: Weighted Average Cost of Capital (WACC) as a decimal proportion.

    Raises:
        TypeError: If any parameter is a boolean or non-numeric type.
        ValueError: If market_value_equity or total_debt is negative, any parameter is NaN/Infinity,
            or both market_value_equity and total_debt are zero (undefined weights).
    """
    mve = validate_number(market_value_equity, "market_value_equity", allow_negative=False)
    td = validate_number(total_debt, "total_debt", allow_negative=False)
    ke = validate_number(cost_of_equity, "cost_of_equity")
    kd = validate_number(cost_of_debt_after_tax, "cost_of_debt_after_tax")

    total_capital = mve + td
    if total_capital == 0.0:
        raise ValueError(
            "market_value_equity and total_debt cannot both be zero (undefined capital structure weights)."
        )

    weight_equity = mve / total_capital
    weight_debt = td / total_capital

    return weight_equity * ke + weight_debt * kd
