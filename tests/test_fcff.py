"""Unit tests for FCFF engine (src/fcff.py)."""

import pytest
from src.fcff import calculate_fcff, project_fcff


def test_tv5_calculate_fcff():
    """Test Vector 5: Base FCFF calculation."""
    ebit = 300.0
    tax_rate = 0.25
    da = 50.0
    capex = 80.0
    nwc = 20.0
    res = calculate_fcff(ebit, tax_rate, da, capex, nwc)
    assert pytest.approx(res, abs=1e-6) == 175.0


def test_tv6_project_fcff():
    """Test Vector 6: 5-Year FCFF projection."""
    base_fcff = 175.0
    growth_rate = 0.08
    years = 5
    expected = [
        189.0,
        204.12,
        220.44960000000003,
        238.08556800000005,
        257.1324134400001,
    ]
    res = project_fcff(base_fcff, growth_rate, years)
    assert len(res) == 5
    for r, e in zip(res, expected):
        assert pytest.approx(r, abs=1e-6) == e


def test_fcff_negative_inputs_valid():
    """Verify negative growth rates and negative FCFF are valid."""
    res_neg_base = project_fcff(-100.0, 0.05, 3)
    expected_neg_base = [-105.0, -110.25, -115.7625]
    for r, e in zip(res_neg_base, expected_neg_base):
        assert pytest.approx(r, abs=1e-6) == e

    res_neg_growth = project_fcff(100.0, -0.10, 2)
    expected_neg_growth = [90.0, 81.0]
    for r, e in zip(res_neg_growth, expected_neg_growth):
        assert pytest.approx(r, abs=1e-6) == e


def test_fcff_validation_booleans():
    """Verify boolean inputs are rejected."""
    with pytest.raises((TypeError, ValueError)):
        calculate_fcff(300, True, 50, 80, 20)
    with pytest.raises((TypeError, ValueError)):
        project_fcff(175.0, 0.08, True)


def test_fcff_validation_years():
    """Verify invalid year parameters are rejected."""
    with pytest.raises((TypeError, ValueError)):
        project_fcff(175.0, 0.08, 0)
    with pytest.raises((TypeError, ValueError)):
        project_fcff(175.0, 0.08, -5)
    with pytest.raises((TypeError, ValueError)):
        project_fcff(175.0, 0.08, 5.0)  # float not int


def test_fcff_validation_nan_inf():
    """Verify NaN and Infinity inputs are rejected."""
    with pytest.raises(ValueError):
        calculate_fcff(float("nan"), 0.25, 50, 80, 20)
    with pytest.raises(ValueError):
        project_fcff(175.0, float("inf"), 5)
