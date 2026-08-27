"""Unit tests for Discounting Bridge engine (src/discounting.py)."""

import pytest
from src.discounting import (
    present_value,
    discount_fcff_series,
    enterprise_value,
    equity_value,
    intrinsic_share_price,
    margin_of_safety,
)


def test_tv8_full_discounting_bridge():
    """Test Vector 8: Full discounting bridge components and values."""
    fcff_proj = [
        189.0,
        204.12,
        220.44960000000003,
        238.08556800000005,
        257.1324134400001,
    ]
    wacc_val = 0.11900000000000001
    terminal_val = 2975.8020881258435

    # 1. Discounted FCFF series
    expected_pv_series = [
        168.90080428954423,
        163.01418108374241,
        157.3327216894029,
        151.849275625161,
        146.55694162213933,
    ]
    pv_series = discount_fcff_series(fcff_proj, wacc_val)
    assert len(pv_series) == 5
    for r, e in zip(pv_series, expected_pv_series):
        assert pytest.approx(r, abs=1e-6) == e

    # 2. Sum of PV(FCFF)
    assert pytest.approx(sum(pv_series), abs=1e-6) == 787.6539243099899

    # 3. PV of Terminal Value
    pv_tv = present_value(terminal_val, wacc_val, 5)
    assert pytest.approx(pv_tv, abs=1e-6) == 1696.108425514646

    # 4. Enterprise Value
    ev = enterprise_value(fcff_proj, terminal_val, wacc_val)
    assert pytest.approx(ev, abs=1e-6) == 2483.7623498246357

    # 5. Equity Value
    total_debt = 500.0
    cash = 150.0
    eq_val = equity_value(ev, total_debt, cash)
    assert pytest.approx(eq_val, abs=1e-6) == 2133.7623498246357

    # 6. Intrinsic Share Price
    shares = 100.0
    price = intrinsic_share_price(eq_val, shares)
    assert pytest.approx(price, abs=1e-6) == 21.33762349824636

    # 7. Margin of Safety
    mkt_price = 28.0
    mos = margin_of_safety(price, mkt_price)
    assert pytest.approx(mos, abs=1e-6) == -0.2379420179197729


def test_discounting_validation_empty_series():
    """Verify empty projection list is rejected."""
    with pytest.raises(ValueError, match="cannot be empty"):
        discount_fcff_series([], 0.119)
    with pytest.raises(ValueError, match="cannot be empty"):
        enterprise_value([], 2975.8, 0.119)


def test_discounting_validation_shares_and_price():
    """Verify non-positive shares or market prices are rejected."""
    with pytest.raises(ValueError):
        intrinsic_share_price(2133.76, 0.0)
    with pytest.raises(ValueError):
        intrinsic_share_price(2133.76, -100.0)
    with pytest.raises(ValueError):
        margin_of_safety(21.33, 0.0)
    with pytest.raises(ValueError):
        margin_of_safety(21.33, -28.0)


def test_discounting_validation_booleans():
    """Verify boolean parameters are rejected across discounting functions."""
    with pytest.raises((TypeError, ValueError)):
        present_value(True, 0.10, 5)
    with pytest.raises((TypeError, ValueError)):
        present_value(100.0, 0.10, True)
    with pytest.raises((TypeError, ValueError)):
        equity_value(2483.76, True, 150.0)
    with pytest.raises((TypeError, ValueError)):
        intrinsic_share_price(2133.76, True)
    with pytest.raises((TypeError, ValueError)):
        margin_of_safety(True, 28.0)
