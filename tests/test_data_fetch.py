"""Unit and integration tests for data fetch engine (src/data_fetch.py)."""

import json
import math
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

    df = pd.DataFrame(data)
    return df


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


def test_is_financial_sector():
    """Verify sector detection for financial vs non-financial corporate issuers."""
    assert is_financial_sector("Financial Services") is True
    assert is_financial_sector("Financials") is True
    assert is_financial_sector("Finance") is True
    assert is_financial_sector("Banking") is True
    assert is_financial_sector("Insurance") is True
    assert is_financial_sector("FINANCIAL SERVICES ") is True
    assert is_financial_sector("Technology") is False
    assert is_financial_sector("Healthcare") is False
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

    # NWC: (147957000000 - 165631000000) - (152987000000 - 176392000000) = -17674000000 - (-23405000000) = 5731000000
    assert pytest.approx(res.change_in_nwc, abs=1e-2) == 5731000000.0
    assert res.current_price == 314.58
    assert res.market_cap == 4591036923904
    assert res.diluted_shares_outstanding == 14594180000
    assert res.beta == 1.086


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
    # Delete Depreciation And Amortization row from cashflow
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
    # 4.16161e11 in recent col, 3.91035e11 in col 1 (1 year lookback)
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
    assert aapl_res.current_price > 0
    assert aapl_res.market_cap > 0

    # 2. Bank / Financial Sector (JPM)
    with pytest.raises(UnsupportedSectorError, match="financial sector"):
        fetch_company_financials("JPM")

    # 3. Non-US Indian Ticker (INFY.NS)
    infy_res = fetch_company_financials("INFY.NS")
    assert infy_res.ticker == "INFY.NS"
    assert infy_res.currency == "INR"
    assert infy_res.ebit > 0
    assert infy_res.market_cap > 0

    # Test historical revenue CAGR live
    aapl_cagr = historical_revenue_cagr("AAPL", years=1)
    assert isinstance(aapl_cagr, float)
