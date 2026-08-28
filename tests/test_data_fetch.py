"""Unit and integration tests for data fetch engine (src/data_fetch.py)."""

import json
import os
from unittest.mock import MagicMock
import pandas as pd
import pytest

from src.data_fetch import (
    CompanyFinancials,
    UnsupportedSectorError,
    fetch_company_financials,
    historical_revenue_cagr,
    is_financial_sector,
)

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture_df(filename: str) -> pd.DataFrame:
    """Loads DataFrame from fixture JSON file."""
    filepath = os.path.join(FIXTURE_DIR, filename)
    with open(filepath, "r") as f:
        data = json.load(f)
    if not data:
        return pd.DataFrame()

    return pd.DataFrame(data)


def load_fixture_info(filename: str) -> dict:
    """Loads info dict from fixture JSON file."""
    filepath = os.path.join(FIXTURE_DIR, filename)
    with open(filepath, "r") as f:
        return json.load(f)


@pytest.fixture
def mock_aapl_ticker():
    """Constructs a mocked yfinance Ticker object populated with frozen AAPL fixtures."""
    mock_t = MagicMock()
    mock_t.info = load_fixture_info("yfinance_info.json")
    mock_t.income_stmt = load_fixture_df("yfinance_income_stmt.json")
    mock_t.balance_sheet = load_fixture_df("yfinance_balance_sheet.json")
    mock_t.cashflow = load_fixture_df("yfinance_cashflow.json")
    return mock_t


@pytest.fixture
def mock_infy_ticker():
    """Constructs a mocked yfinance Ticker object populated with frozen INFY.NS fixtures."""
    mock_t = MagicMock()
    mock_t.info = load_fixture_info("infy_info.json")
    mock_t.income_stmt = load_fixture_df("infy_income_stmt.json")
    mock_t.balance_sheet = load_fixture_df("infy_balance_sheet.json")
    mock_t.cashflow = load_fixture_df("infy_cashflow.json")
    return mock_t


def test_is_financial_sector_empirical_only():
    """Verify sector detection uses ONLY empirically confirmed sector string ('Financial Services')."""
    assert is_financial_sector("Financial Services") is True
    assert is_financial_sector("FINANCIAL SERVICES ") is True
    # Unconfirmed / removed guessed strings return False
    assert is_financial_sector("Financials") is False
    assert is_financial_sector("Finance") is False
    assert is_financial_sector("Banking") is False
    assert is_financial_sector("Insurance") is False
    assert is_financial_sector("Technology") is False
    assert is_financial_sector(None) is False


def test_fetch_company_financials_aapl_fixture(mock_aapl_ticker):
    """Verify parsing and normalization of frozen AAPL fixture data into CompanyFinancials."""
    res = fetch_company_financials("AAPL", ticker_obj=mock_aapl_ticker)

    assert isinstance(res, CompanyFinancials)
    assert res.ticker == "AAPL"
    assert res.company_name == "Apple Inc."
    assert res.sector == "Technology"
    assert res.currency == "USD"
    assert pytest.approx(res.ebit, abs=1e-2) == 1.33050e11
    assert pytest.approx(res.depreciation_amortization, abs=1e-2) == 1.1698e10
    assert res.capex == 1.2715e10  # Positive outflow normalized from -1.2715e10
    assert pytest.approx(res.effective_tax_rate, abs=1e-4) == 20719000000 / 132729000000
    assert res.tax_rate_fallback_used is False

    # AAPL Interest Expense searched across available columns (found $3.933B in col 2, triggering fallback flag)
    assert pytest.approx(res.interest_expense, abs=1e-2) == 3.933e9
    assert res.interest_expense_fallback_used is True

    # NWC: (147957000000 - 165631000000) - (152987000000 - 176392000000) = 5731000000
    assert pytest.approx(res.change_in_nwc, abs=1e-2) == 5731000000.0
    assert res.current_price == 314.58
    assert res.market_cap == 4591036923904
    assert res.diluted_shares_outstanding == 14594180000
    assert res.beta == 1.086


def test_fetch_company_financials_infy_fixture_scaling(mock_infy_ticker):
    """Regression test verifying INFY.NS FX conversion correctly scales USD statement to INR market currency."""
    fx_rate = 95.368  # USD to INR conversion rate
    res = fetch_company_financials("INFY.NS", ticker_obj=mock_infy_ticker, fx_rate_override=fx_rate)

    assert res.ticker == "INFY.NS"
    assert res.currency == "INR"

    # Raw USD EBIT ($4.553B) * 95.368 = ₹434.2095B INR (~₹43,421 Crore INR)
    expected_ebit_inr = 4.553e9 * fx_rate
    assert pytest.approx(res.ebit, abs=1e-2) == expected_ebit_inr

    # Raw USD CapEx ($3.06e8) * 95.368 = ₹29.18B INR
    expected_capex_inr = 3.06e8 * fx_rate
    assert pytest.approx(res.capex, abs=1e-2) == expected_capex_inr

    # Raw USD D&A ($5.52e8) * 95.368 = ₹52.64B INR
    expected_da_inr = 5.52e8 * fx_rate
    assert pytest.approx(res.depreciation_amortization, abs=1e-2) == expected_da_inr

    # INFY.NS has interest expense in col 0
    assert res.interest_expense_fallback_used is False

    # Implied Operating Margin check (EBIT / Revenue = 4.553B / 20.158B = 22.58%)
    raw_rev_usd = float(mock_infy_ticker.income_stmt.loc["Total Revenue"].iloc[0])
    implied_op_margin = (res.ebit / (raw_rev_usd * fx_rate))
    assert pytest.approx(implied_op_margin, abs=1e-4) == 0.22586566


def test_missing_interest_expense_with_debt_raises_error(mock_aapl_ticker):
    """Verify missing interest expense on a company with debt raises ValueError (no silent zero)."""
    # Delete Interest Expense rows completely across all columns
    inc_df = mock_aapl_ticker.income_stmt.drop(
        index=["Interest Expense", "Interest Expense Non Operating", "Net Non Operating Interest Income Expense"],
        errors="ignore"
    )
    mock_aapl_ticker.income_stmt = inc_df

    with pytest.raises(ValueError, match="interest_expense"):
        fetch_company_financials("AAPL", ticker_obj=mock_aapl_ticker)


def test_financial_sector_rejection_raises_error():
    """Verify mocked financial sector company raises UnsupportedSectorError."""
    mock_t = MagicMock()
    mock_t.info = {"sector": "Financial Services", "longName": "JPMorgan Chase & Co."}

    with pytest.raises(UnsupportedSectorError, match="belongs to the financial sector"):
        fetch_company_financials("JPM", ticker_obj=mock_t)


def test_invalid_ticker_or_empty_response_raises_error():
    """Verify empty/missing data raises ValueError."""
    mock_t = MagicMock()
    mock_t.info = {}
    mock_t.income_stmt = pd.DataFrame()

    with pytest.raises(ValueError, match="not found or lacks sufficient"):
        fetch_company_financials("INVALID123", ticker_obj=mock_t)


def test_missing_required_field_raises_error(mock_aapl_ticker):
    """Verify missing required row (e.g. D&A) raises ValueError naming that field."""
    cf_df = mock_aapl_ticker.cashflow.drop(index=["Depreciation And Amortization", "Depreciation Amortization Depletion"], errors="ignore")
    mock_aapl_ticker.cashflow = cf_df

    with pytest.raises(ValueError, match="depreciation_amortization"):
        fetch_company_financials("AAPL", ticker_obj=mock_aapl_ticker)


def test_tax_rate_fallback_when_pretax_income_negative(mock_aapl_ticker):
    """Verify pretax income <= 0 triggers 0.25 statutory tax rate fallback."""
    inc_df = mock_aapl_ticker.income_stmt.copy()
    inc_df.loc["Pretax Income"] = -100.0
    mock_aapl_ticker.income_stmt = inc_df

    res = fetch_company_financials("AAPL", ticker_obj=mock_aapl_ticker)
    assert res.effective_tax_rate == 0.25
    assert res.tax_rate_fallback_used is True


def test_historical_revenue_cagr_fixture(mock_aapl_ticker):
    """Verify calculation of historical revenue CAGR from fixture."""
    cagr = historical_revenue_cagr("AAPL", years=1, ticker_obj=mock_aapl_ticker)
    expected_cagr = (4.16161e11 / 3.91035e11) - 1.0
    assert pytest.approx(cagr, abs=1e-4) == expected_cagr


@pytest.mark.integration
def test_live_yfinance_integration():
    """Live integration test making REAL network calls to yfinance for AAPL, JPM, and INFY.NS."""
    # 1. US Tech (AAPL)
    aapl_res = fetch_company_financials("AAPL")
    assert aapl_res.ticker == "AAPL"
    assert aapl_res.ebit > 0
    assert aapl_res.capex > 0
    assert aapl_res.interest_expense > 0  # Resolved: interest_expense is non-zero
    assert aapl_res.interest_expense_fallback_used is True  # Resolved: explicitly flagged prior column fallback for AAPL
    assert aapl_res.current_price > 0
    assert aapl_res.market_cap > 0

    # 2. Bank / Financial Sector (JPM)
    with pytest.raises(UnsupportedSectorError, match="financial sector"):
        fetch_company_financials("JPM")

    # 3. Non-US Indian Ticker (INFY.NS)
    infy_res = fetch_company_financials("INFY.NS")
    assert infy_res.ticker == "INFY.NS"
    assert infy_res.currency == "INR"
    assert infy_res.ebit > 3.0e11
    assert infy_res.interest_expense_fallback_used is False  # INFY.NS has interest expense in col 0
    assert infy_res.market_cap > 1.0e12

    # Test historical revenue CAGR live
    aapl_cagr = historical_revenue_cagr("AAPL", years=1)
    assert isinstance(aapl_cagr, float)
