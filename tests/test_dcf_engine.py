"""Unit and integration tests for DCF Orchestration Engine (src/dcf_engine.py)."""

from unittest.mock import MagicMock, patch
import pytest

from src.data_fetch import CompanyFinancials, UnsupportedSectorError
from src.dcf_engine import DCFValuationResult, run_dcf_valuation


@pytest.fixture
def clean_company_financials():
    """Constructs a clean CompanyFinancials object with no fallbacks, no FX mismatch, and aligned vintages."""
    return CompanyFinancials(
        ticker="CLEAN",
        company_name="Clean Corp Inc.",
        sector="Technology",
        industry="Software",
        currency="USD",
        primary_fiscal_year="2025-12-31",
        interest_expense_fiscal_year="2025-12-31",
        ebit=10000.0,
        effective_tax_rate=0.20,
        depreciation_amortization=1000.0,
        capex=1500.0,
        change_in_nwc=500.0,
        total_debt=20000.0,
        cash_and_equivalents=5000.0,
        beta=1.0,
        market_cap=100000.0,
        diluted_shares_outstanding=1000.0,
        current_price=100.0,
        interest_expense=1000.0,
        data_retrieved_at="2026-08-29T00:00:00Z",
        tax_rate_fallback_used=False,
        fx_rate_applied=1.0,
        interest_expense_fallback_used=False,
    )


@pytest.fixture
def mock_aapl_ticker():
    """Constructs a mocked yfinance Ticker object populated with frozen AAPL fixtures."""
    from tests.test_data_fetch import load_fixture_df, load_fixture_info
    mock_t = MagicMock()
    mock_t.info = load_fixture_info("yfinance_info.json")
    mock_t.income_stmt = load_fixture_df("yfinance_income_stmt.json")
    mock_t.balance_sheet = load_fixture_df("yfinance_balance_sheet.json")
    mock_t.cashflow = load_fixture_df("yfinance_cashflow.json")
    return mock_t


@pytest.fixture
def mock_infy_ticker():
    """Constructs a mocked yfinance Ticker object populated with frozen INFY.NS fixtures."""
    from tests.test_data_fetch import load_fixture_df, load_fixture_info
    mock_t = MagicMock()
    mock_t.info = load_fixture_info("infy_info.json")
    mock_t.income_stmt = load_fixture_df("infy_income_stmt.json")
    mock_t.balance_sheet = load_fixture_df("infy_balance_sheet.json")
    mock_t.cashflow = load_fixture_df("infy_cashflow.json")
    return mock_t


@patch("src.dcf_engine.fetch_company_financials")
def test_dcf_valuation_clean_run(mock_fetch, clean_company_financials):
    """Verify end-to-end valuation pipeline on a clean CompanyFinancials object with spot-checked arithmetic."""
    mock_fetch.return_value = clean_company_financials

    res = run_dcf_valuation(
        ticker="CLEAN",
        projection_years=5,
        terminal_growth_rate=0.02,
        projection_growth_rate=0.05,
        risk_free_rate=0.0425,
        equity_risk_premium=0.055,
    )

    assert isinstance(res, DCFValuationResult)
    assert res.ticker == "CLEAN"
    assert res.company_name == "Clean Corp Inc."
    assert res.currency == "USD"

    # Base FCFF: 10000 * (1 - 0.20) + 1000 - 1500 - 500 = 7000.0
    assert pytest.approx(res.base_year_fcff, abs=1e-2) == 7000.0

    # ke = 0.0425 + 1.0 * 0.055 = 0.0975 (9.75%)
    assert pytest.approx(res.cost_of_equity, abs=1e-4) == 0.0975

    # kd_after_tax = (1000 / 20000) * (1 - 0.20) = 0.04 (4.0%)
    assert pytest.approx(res.cost_of_debt_after_tax, abs=1e-4) == 0.040

    # WACC = (100000 / 120000) * 0.0975 + (20000 / 120000) * 0.040 = 0.0879166667
    expected_wacc = (100000.0 / 120000.0) * 0.0975 + (20000.0 / 120000.0) * 0.040
    assert pytest.approx(res.wacc, abs=1e-5) == expected_wacc

    # Projected FCFFs (5 years at 5% growth)
    expected_fcffs = [7000.0 * (1.05 ** t) for t in range(1, 6)]
    for p_fcff, e_fcff in zip(res.projected_fcffs, expected_fcffs):
        assert pytest.approx(p_fcff, abs=1e-2) == e_fcff

    # Terminal Value: 7000 * (1.05^5) * 1.02 / (wacc - 0.02)
    expected_tv = expected_fcffs[-1] * 1.02 / (expected_wacc - 0.02)
    assert pytest.approx(res.terminal_value, abs=1e-2) == expected_tv

    # Discounted Terminal Value
    expected_pv_tv = expected_tv / ((1.0 + expected_wacc) ** 5)
    assert pytest.approx(res.discounted_terminal_value, abs=1e-2) == expected_pv_tv

    # Enterprise Value & Equity Value
    expected_pv_series = [fcff / ((1.0 + expected_wacc) ** (i + 1)) for i, fcff in enumerate(expected_fcffs)]
    expected_ev = sum(expected_pv_series) + expected_pv_tv
    expected_eq_val = expected_ev - 20000.0 + 5000.0
    expected_price = expected_eq_val / 1000.0

    assert pytest.approx(res.enterprise_value, abs=1e-2) == expected_ev
    assert pytest.approx(res.equity_value, abs=1e-2) == expected_eq_val
    assert pytest.approx(res.implied_share_price, abs=1e-2) == expected_price
    assert pytest.approx(res.current_price, abs=1e-2) == 100.0

    # Assumption flags
    assert res.interest_expense_vintage_gap_years == 0
    assert res.cost_of_debt_flagged is False
    assert res.tax_rate_fallback_used is False
    assert res.fx_rate_applied == 1.0
    assert res.manual_cost_of_debt_used is False
    assert res.growth_rate_source == "explicit"
    assert len(res.warnings) == 0


@patch("src.dcf_engine.fetch_company_financials")
def test_interest_expense_vintage_gap_flagging(mock_fetch, clean_company_financials):
    """Verify interest expense vintage gap creates warnings and sets cost_of_debt_flagged = True."""
    clean_company_financials.primary_fiscal_year = "2025-09-30"
    clean_company_financials.interest_expense_fiscal_year = "2023-09-30"
    clean_company_financials.interest_expense_fallback_used = True
    mock_fetch.return_value = clean_company_financials

    res = run_dcf_valuation(
        ticker="AAPL_MOCK",
        projection_years=5,
        terminal_growth_rate=0.02,
        projection_growth_rate=0.05,
    )

    assert res.interest_expense_vintage_gap_years == 2
    assert res.cost_of_debt_flagged is True
    assert res.manual_cost_of_debt_used is False
    assert any("2-year vintage gap" in w for w in res.warnings)


@patch("src.dcf_engine.fetch_company_financials")
def test_manual_cost_of_debt_override(mock_fetch, clean_company_financials):
    """Verify supplying manual_cost_of_debt overrides derived cost of debt and clears cost_of_debt_flagged."""
    clean_company_financials.interest_expense_fiscal_year = "2023-09-30"
    clean_company_financials.interest_expense_fallback_used = True
    mock_fetch.return_value = clean_company_financials

    # Supply 4.5% pre-tax manual cost of debt (0.045)
    res = run_dcf_valuation(
        ticker="AAPL_MOCK",
        projection_years=5,
        terminal_growth_rate=0.02,
        projection_growth_rate=0.05,
        manual_cost_of_debt=0.045,
    )

    # kd_after_tax = 0.045 * (1 - 0.20) = 0.036 (3.6%)
    assert pytest.approx(res.cost_of_debt_after_tax, abs=1e-4) == 0.036
    assert res.manual_cost_of_debt_used is True
    assert res.cost_of_debt_flagged is False


@patch("src.dcf_engine.fetch_company_financials")
def test_tax_rate_and_fx_fallback_propagation(mock_fetch, clean_company_financials):
    """Verify tax_rate_fallback_used and fx_rate_applied propagate into valuation result and warnings."""
    clean_company_financials.tax_rate_fallback_used = True
    clean_company_financials.fx_rate_applied = 95.368
    clean_company_financials.currency = "INR"
    mock_fetch.return_value = clean_company_financials

    res = run_dcf_valuation(
        ticker="INFY_MOCK",
        projection_years=5,
        terminal_growth_rate=0.02,
        projection_growth_rate=0.05,
    )

    assert res.tax_rate_fallback_used is True
    assert res.fx_rate_applied == 95.368
    assert any("tax rate defaulted" in w.lower() for w in res.warnings)
    assert any("converted to trading currency" in w.lower() for w in res.warnings)


@patch("src.dcf_engine.historical_revenue_cagr")
@patch("src.dcf_engine.fetch_company_financials")
def test_growth_rate_historical_cagr_suggestion_used(mock_fetch, mock_cagr, clean_company_financials):
    """Verify use_historical_cagr_suggestion=True uses historical CAGR when no explicit rate is provided."""
    mock_fetch.return_value = clean_company_financials
    mock_cagr.return_value = 0.075  # 7.5% CAGR

    res = run_dcf_valuation(
        ticker="CLEAN",
        projection_years=5,
        terminal_growth_rate=0.02,
        use_historical_cagr_suggestion=True,
    )

    assert pytest.approx(res.projection_growth_rate, abs=1e-4) == 0.075
    assert res.growth_rate_source == "historical_cagr_suggestion"
    assert pytest.approx(res.historical_cagr_suggestion, abs=1e-4) == 0.075


@patch("src.dcf_engine.historical_revenue_cagr")
@patch("src.dcf_engine.fetch_company_financials")
def test_explicit_growth_rate_takes_precedence_over_cagr_suggestion(mock_fetch, mock_cagr, clean_company_financials):
    """Verify explicit projection_growth_rate wins over suggestion and records a comparative warning."""
    mock_fetch.return_value = clean_company_financials
    mock_cagr.return_value = 0.075

    res = run_dcf_valuation(
        ticker="CLEAN",
        projection_years=5,
        terminal_growth_rate=0.02,
        projection_growth_rate=0.06,
        use_historical_cagr_suggestion=True,
    )

    assert pytest.approx(res.projection_growth_rate, abs=1e-4) == 0.06
    assert res.growth_rate_source == "explicit"
    assert pytest.approx(res.historical_cagr_suggestion, abs=1e-4) == 0.075
    assert any("historical cagr suggestion computed" in w.lower() for w in res.warnings)


@patch("src.dcf_engine.fetch_company_financials")
def test_terminal_growth_greater_or_equal_wacc_raises_error(mock_fetch, clean_company_financials):
    """Verify terminal_growth_rate >= WACC raises ValueError from Step 1's terminal_value module."""
    mock_fetch.return_value = clean_company_financials

    with pytest.raises(ValueError, match="terminal_growth_rate .* must be strictly less than WACC"):
        run_dcf_valuation(
            ticker="CLEAN",
            projection_years=5,
            terminal_growth_rate=0.15,  # 15% > WACC (~8.79%)
            projection_growth_rate=0.05,
        )


@patch("src.dcf_engine.fetch_company_financials")
def test_unsupported_sector_error_propagates_unmodified(mock_fetch):
    """Verify UnsupportedSectorError from Step 2 propagates through run_dcf_valuation unmodified."""
    mock_fetch.side_effect = UnsupportedSectorError("Ticker 'JPM' belongs to the financial sector.")

    with pytest.raises(UnsupportedSectorError, match="belongs to the financial sector"):
        run_dcf_valuation(
            ticker="JPM",
            projection_years=5,
            terminal_growth_rate=0.02,
            projection_growth_rate=0.05,
        )


@patch("src.dcf_engine.fetch_company_financials")
def test_value_error_from_step2_propagates_unmodified(mock_fetch):
    """Verify ValueError from Step 2 propagates through run_dcf_valuation unmodified."""
    mock_fetch.side_effect = ValueError("Ticker 'INVALID' not found or lacks sufficient financial statement data.")

    with pytest.raises(ValueError, match="not found or lacks sufficient"):
        run_dcf_valuation(
            ticker="INVALID",
            projection_years=5,
            terminal_growth_rate=0.02,
            projection_growth_rate=0.05,
        )


@pytest.mark.integration
def test_dcf_valuation_aapl_fixture_and_live(mock_aapl_ticker):
    """Integration test executing run_dcf_valuation for AAPL using frozen fixture ticker object."""
    res = run_dcf_valuation(
        ticker="AAPL",
        projection_years=5,
        terminal_growth_rate=0.025,
        projection_growth_rate=0.06,
        ticker_obj=mock_aapl_ticker,
    )

    assert res.ticker == "AAPL"
    assert res.currency == "USD"
    assert res.base_year_fcff > 0
    assert res.wacc > 0.05
    assert res.enterprise_value > 1.0e12
    assert res.equity_value > 1.0e12
    assert res.implied_share_price > 0
    assert res.interest_expense_vintage_gap_years == 2
    assert res.cost_of_debt_flagged is True


@pytest.mark.integration
def test_dcf_valuation_infy_fixture_and_live(mock_infy_ticker):
    """Integration test executing run_dcf_valuation for INFY.NS using frozen fixture ticker object."""
    res = run_dcf_valuation(
        ticker="INFY.NS",
        projection_years=5,
        terminal_growth_rate=0.03,
        use_historical_cagr_suggestion=True,
        ticker_obj=mock_infy_ticker,
        fx_rate_override=95.368,
    )

    assert res.ticker == "INFY.NS"
    assert res.currency == "INR"
    assert res.fx_rate_applied == 95.368
    assert res.base_year_fcff > 1.0e11
    assert res.growth_rate_source == "historical_cagr_suggestion"
    assert res.historical_cagr_suggestion is not None
    assert res.interest_expense_vintage_gap_years == 0
    assert res.cost_of_debt_flagged is False
