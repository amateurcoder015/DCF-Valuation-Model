"""End-to-End integration test for Step 1 core math functions (TV1 -> TV2 -> TV3 -> TV5 -> TV6 -> TV7 -> TV8)."""

import pytest
from src.wacc import cost_of_equity, cost_of_debt_after_tax, wacc
from src.fcff import calculate_fcff, project_fcff
from src.terminal_value import gordon_growth_terminal_value
from src.discounting import (
    enterprise_value,
    equity_value,
    intrinsic_share_price,
    margin_of_safety,
)


def test_step1_full_pipeline_composition():
    """Chains TV1 -> TV2 -> TV3 -> TV5 -> TV6 -> TV7 -> TV8 end-to-end to verify module composition."""
    # TV1: Cost of Equity
    rf = 0.07
    beta = 1.2
    erp = 0.05
    ke = cost_of_equity(rf, beta, erp)
    assert pytest.approx(ke, abs=1e-6) == 0.13

    # TV2: Cost of Debt (after-tax)
    interest_exp = 50.0
    total_debt = 500.0
    tax_rate = 0.25
    kd = cost_of_debt_after_tax(interest_exp, total_debt, tax_rate)
    assert pytest.approx(kd, abs=1e-6) == 0.075

    # TV3: WACC
    mve = 2000.0
    wacc_val = wacc(mve, total_debt, ke, kd)
    assert pytest.approx(wacc_val, abs=1e-6) == 0.11900000000000001

    # TV5: Base FCFF
    ebit = 300.0
    da = 50.0
    capex = 80.0
    change_nwc = 20.0
    base_fcff = calculate_fcff(ebit, tax_rate, da, capex, change_nwc)
    assert pytest.approx(base_fcff, abs=1e-6) == 175.0

    # TV6: 5-Year FCFF Projection
    growth_rate = 0.08
    projection_years = 5
    fcff_proj = project_fcff(base_fcff, growth_rate, projection_years)
    expected_proj = [
        189.0,
        204.12,
        220.44960000000003,
        238.08556800000005,
        257.1324134400001,
    ]
    for p, e in zip(fcff_proj, expected_proj):
        assert pytest.approx(p, abs=1e-6) == e

    # TV7: Terminal Value
    terminal_g = 0.03
    final_fcff = fcff_proj[-1]
    tv = gordon_growth_terminal_value(final_fcff, terminal_g, wacc_val)
    assert pytest.approx(tv, abs=1e-6) == 2975.8020881258435

    # TV8: Discounting Bridge
    ev = enterprise_value(fcff_proj, tv, wacc_val)
    assert pytest.approx(ev, abs=1e-6) == 2483.7623498246357

    cash = 150.0
    eq_val = equity_value(ev, total_debt, cash)
    assert pytest.approx(eq_val, abs=1e-6) == 2133.7623498246357

    shares = 100.0
    price = intrinsic_share_price(eq_val, shares)
    assert pytest.approx(price, abs=1e-6) == 21.33762349824636

    mkt_price = 28.0
    mos = margin_of_safety(price, mkt_price)
    assert pytest.approx(mos, abs=1e-6) == -0.2379420179197729
