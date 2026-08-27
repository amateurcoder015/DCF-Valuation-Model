"""FCFF engine — implemented in Step 1. Calculates historical Free Cash Flow to Firm (FCFF) and projects forward FCFF over the forecast period."""

from src._validators import validate_number, validate_positive_int


def calculate_fcff(
    ebit: float,
    tax_rate: float,
    depreciation_amortization: float,
    capex: float,
    change_in_nwc: float,
) -> float:
    """Calculates Free Cash Flow to Firm (FCFF) from core operating performance.

    Formula:
        FCFF = EBIT * (1 - Tax Rate) + D&A - CapEx - ΔNWC

    Args:
        ebit: Earnings Before Interest and Taxes / Operating Income.
        tax_rate: Effective corporate tax rate as a decimal in [0, 1].
        depreciation_amortization: Depreciation and Amortization non-cash expense add-back.
        capex: Capital expenditures (investments in fixed assets).
        change_in_nwc: Change in Net Working Capital.

    Returns:
        float: Calculated Free Cash Flow to Firm (FCFF). Can be negative.

    Raises:
        TypeError: If any parameter is a boolean or non-numeric type.
        ValueError: If tax_rate is outside [0, 1], or any input is NaN/Infinity.
    """
    e = validate_number(ebit, "ebit")
    tr = validate_number(tax_rate, "tax_rate", min_val=0.0, max_val=1.0)
    da = validate_number(depreciation_amortization, "depreciation_amortization")
    cx = validate_number(capex, "capex")
    nwc = validate_number(change_in_nwc, "change_in_nwc")

    return e * (1.0 - tr) + da - cx - nwc


def project_fcff(base_fcff: float, growth_rate: float, years: int) -> list[float]:
    """Projects FCFF forward over a fixed forecast horizon at a constant annual growth rate.

    Formula:
        FCFF_t = base_fcff * (1 + growth_rate) ** t   for t = 1..years

    Args:
        base_fcff: Starting base-year Free Cash Flow to Firm (can be negative).
        growth_rate: Expected annual forecast growth rate as a decimal (e.g. 0.08 for 8%, can be negative).
        years: Forecast projection horizon in years (must be a positive integer > 0).

    Returns:
        list[float]: Projected FCFF for year 1 through year `years`.

    Raises:
        TypeError: If base_fcff or growth_rate is a boolean/non-number, or years is not an int.
        ValueError: If base_fcff or growth_rate is NaN/Infinity, or years <= 0.
    """
    base = validate_number(base_fcff, "base_fcff")
    g = validate_number(growth_rate, "growth_rate")
    n_years = validate_positive_int(years, "years")

    return [base * ((1.0 + g) ** t) for t in range(1, n_years + 1)]
