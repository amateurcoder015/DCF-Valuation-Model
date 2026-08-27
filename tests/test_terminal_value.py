"""Unit tests for Terminal Value engine (src/terminal_value.py)."""

import pytest
from src.terminal_value import gordon_growth_terminal_value


def test_tv7_terminal_value():
    """Test Vector 7: Gordon Growth Terminal Value calculation."""
    final_fcff = 257.1324134400001
    g = 0.03
    wacc = 0.11900000000000001
    res = gordon_growth_terminal_value(final_fcff, g, wacc)
    assert pytest.approx(res, abs=1e-6) == 2975.8020881258435


def test_tv9_terminal_growth_greater_or_equal_wacc_raises():
    """Test Vector 9: Invalid input — terminal growth rate >= WACC must raise ValueError."""
    with pytest.raises(ValueError, match="strictly less than WACC"):
        gordon_growth_terminal_value(257.13, 0.12, 0.119)

    # Equal growth rate and WACC
    with pytest.raises(ValueError, match="strictly less than WACC"):
        gordon_growth_terminal_value(257.13, 0.10, 0.10)


def test_terminal_value_negative_fcff_valid():
    """Verify negative final year FCFF is allowed and produces negative terminal value."""
    res = gordon_growth_terminal_value(-100.0, 0.02, 0.10)
    assert res == -100.0 * 1.02 / (0.10 - 0.02)  # -127.5


def test_terminal_value_validation_booleans():
    """Verify boolean inputs are rejected."""
    with pytest.raises((TypeError, ValueError)):
        gordon_growth_terminal_value(True, 0.03, 0.119)


def test_terminal_value_validation_nan_inf():
    """Verify NaN and Infinity inputs are rejected."""
    with pytest.raises(ValueError):
        gordon_growth_terminal_value(257.13, float("nan"), 0.119)
    with pytest.raises(ValueError):
        gordon_growth_terminal_value(257.13, 0.03, float("inf"))
