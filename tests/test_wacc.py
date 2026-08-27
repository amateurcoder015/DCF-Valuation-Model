"""Unit tests for WACC engine (src/wacc.py)."""

import math
import pytest
from src.wacc import cost_of_equity, cost_of_debt_after_tax, wacc


def test_tv1_cost_of_equity():
    """Test Vector 1: Cost of Equity (CAPM)."""
    rf = 0.07
    beta = 1.2
    erp = 0.05
    res = cost_of_equity(rf, beta, erp)
    assert pytest.approx(res, abs=1e-6) == 0.13


def test_tv2_cost_of_debt_after_tax():
    """Test Vector 2: Cost of Debt (after-tax)."""
    ie = 50.0
    td = 500.0
    tr = 0.25
    res = cost_of_debt_after_tax(ie, td, tr)
    assert pytest.approx(res, abs=1e-6) == 0.07500000000000001


def test_tv3_wacc():
    """Test Vector 3: WACC with standard capital structure."""
    mve = 2000.0
    td = 500.0
    ke = 0.13
    kd = 0.075
    res = wacc(mve, td, ke, kd)
    assert pytest.approx(res, abs=1e-6) == 0.11900000000000001


def test_tv4_wacc_zero_debt():
    """Test Vector 4: WACC with zero debt (must equal cost of equity)."""
    mve = 1000.0
    td = 0.0
    ke = 0.13
    kd = 0.075
    res = wacc(mve, td, ke, kd)
    assert res == 0.13


def test_tv10_wacc_undefined_weights():
    """Test Vector 10: Invalid input — market_value_equity=0 and total_debt=0 must raise ValueError."""
    with pytest.raises(ValueError, match="cannot both be zero"):
        wacc(0.0, 0.0, 0.13, 0.075)


def test_wacc_validation_booleans():
    """Verify boolean arguments are rejected across WACC functions."""
    with pytest.raises((TypeError, ValueError)):
        cost_of_equity(True, 1.2, 0.05)
    with pytest.raises((TypeError, ValueError)):
        cost_of_debt_after_tax(50, True, 0.25)
    with pytest.raises((TypeError, ValueError)):
        wacc(2000, 500, False, 0.075)


def test_wacc_validation_nan_inf():
    """Verify NaN and Infinity inputs are rejected."""
    with pytest.raises(ValueError):
        cost_of_equity(float("nan"), 1.2, 0.05)
    with pytest.raises(ValueError):
        cost_of_debt_after_tax(50, 500, float("inf"))
    with pytest.raises(ValueError):
        wacc(float("nan"), 500, 0.13, 0.075)


def test_wacc_validation_negative_values():
    """Verify negative capital structure or tax rates are rejected."""
    with pytest.raises(ValueError):
        cost_of_debt_after_tax(-10, 500, 0.25)
    with pytest.raises(ValueError):
        cost_of_debt_after_tax(50, -500, 0.25)
    with pytest.raises(ValueError):
        cost_of_debt_after_tax(50, 500, 1.5)  # Tax rate > 1
    with pytest.raises(ValueError):
        cost_of_debt_after_tax(50, 500, -0.1)  # Tax rate < 0
    with pytest.raises(ValueError):
        wacc(-2000, 500, 0.13, 0.075)
    with pytest.raises(ValueError):
        wacc(2000, -500, 0.13, 0.075)
