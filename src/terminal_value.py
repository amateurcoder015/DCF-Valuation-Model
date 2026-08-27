"""Terminal value engine — implemented in Step 1. Computes Gordon Growth terminal value and enforces g < WACC constraint."""

from src._validators import validate_number


def gordon_growth_terminal_value(
    final_year_fcff: float, terminal_growth_rate: float, wacc: float
) -> float:
    """Calculates Terminal Value at the end of explicit forecast period using the Gordon Growth Model.

    Formula:
        Terminal Value = final_year_fcff * (1 + terminal_growth_rate) / (wacc - terminal_growth_rate)

    Mathematical Constraint:
        terminal_growth_rate MUST be strictly less than WACC (g < WACC). If terminal_growth_rate >= WACC,
        the formula results in division by zero, a negative denominator, or an economically impossible
        assumption of perpetual outgrowth relative to capital costs.

    Args:
        final_year_fcff: Projected FCFF in the final year of the explicit forecast period.
            May be negative in edge cases, which produces a negative terminal value.
        terminal_growth_rate: Perpetual annual growth rate as a decimal (e.g. 0.03 for 3%).
        wacc: Weighted Average Cost of Capital as a decimal (e.g. 0.119 for 11.9%).

    Returns:
        float: Calculated Terminal Value as of the final forecast year.

    Raises:
        TypeError: If any parameter is a boolean or non-numeric type.
        ValueError: If any parameter is NaN/Infinity, or if terminal_growth_rate >= wacc.
    """
    fcff_n = validate_number(final_year_fcff, "final_year_fcff")
    g = validate_number(terminal_growth_rate, "terminal_growth_rate")
    w = validate_number(wacc, "wacc")

    if g >= w:
        raise ValueError(
            f"terminal_growth_rate ({g}) must be strictly less than WACC ({w})."
        )

    return fcff_n * (1.0 + g) / (w - g)
