"""Unit tests for FastAPI backend API endpoints (api/main.py)."""

from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest

from api.main import app
from src.data_fetch import UnsupportedSectorError
from src.dcf_engine import DCFValuationResult

client = TestClient(app)


@pytest.fixture
def mock_dcf_result():
    """Constructs a mock DCFValuationResult object for API endpoint testing."""
    return DCFValuationResult(
        ticker="API_MOCK",
        company_name="API Mock Corp",
        currency="USD",
        data_retrieved_at="2026-08-29T00:00:00Z",
        base_year_fcff=10000.0,
        cost_of_equity=0.10,
        cost_of_debt_after_tax=0.04,
        wacc=0.08,
        projected_fcffs=[10500.0, 11025.0, 11576.25, 12155.06, 12762.82],
        terminal_value=200000.0,
        discounted_terminal_value=136116.64,
        sum_of_discounted_fcffs=44300.0,
        enterprise_value=180416.64,
        equity_value=165416.64,
        implied_share_price=165.42,
        current_price=150.0,
        implied_upside_pct=10.28,
        primary_fiscal_year="2025-12-31",
        interest_expense_fiscal_year="2025-12-31",
        interest_expense_vintage_gap_years=0,
        cost_of_debt_flagged=False,
        tax_rate_fallback_used=False,
        fx_rate_applied=1.0,
        manual_cost_of_debt_used=False,
        growth_rate_source="explicit",
        historical_cagr_suggestion=0.07,
        projection_growth_rate=0.05,
        terminal_growth_rate=0.02,
        projection_years=5,
        warnings=["Test warning callout"],
    )


@patch("api.main.run_dcf_valuation")
def test_api_valuation_success(mock_run, mock_dcf_result):
    """Verify HTTP 200 OK response with full serialized valuation JSON payload."""
    mock_run.return_value = mock_dcf_result

    payload = {
        "ticker": "API_MOCK",
        "projection_years": 5,
        "terminal_growth_rate": 0.02,
        "projection_growth_rate": 0.05,
        "use_historical_cagr_suggestion": False,
        "risk_free_rate": 0.0425,
        "equity_risk_premium": 0.055,
    }

    response = client.post("/api/valuation", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["ticker"] == "API_MOCK"
    assert data["company_name"] == "API Mock Corp"
    assert data["currency"] == "USD"
    assert data["base_year_fcff"] == 10000.0
    assert data["implied_share_price"] == 165.42
    assert data["cost_of_debt_flagged"] is False

    # Presentation derived fields
    assert "wacc_spread_pct" in data
    assert pytest.approx(data["wacc_spread_pct"], abs=1e-2) == 6.0  # 8% - 2% = 6%
    assert data["is_sensitivity_caution"] is False
    assert "growth_summary" in data
    assert "cost_of_debt_summary" in data


@patch("api.main.run_dcf_valuation")
def test_api_valuation_unsupported_sector_error(mock_run):
    """Verify HTTP 422 Unprocessable Entity on UnsupportedSectorError."""
    mock_run.side_effect = UnsupportedSectorError("Ticker 'JPM' belongs to the financial sector.")

    payload = {
        "ticker": "JPM",
        "projection_years": 5,
        "terminal_growth_rate": 0.02,
    }

    response = client.post("/api/valuation", json=payload)
    assert response.status_code == 422

    data = response.json()
    assert "belongs to the financial sector" in data["detail"]


@patch("api.main.run_dcf_valuation")
def test_api_valuation_value_error(mock_run):
    """Verify HTTP 400 Bad Request on ValueError."""
    mock_run.side_effect = ValueError("terminal_growth_rate (0.15) must be strictly less than WACC (0.08).")

    payload = {
        "ticker": "AAPL",
        "projection_years": 5,
        "terminal_growth_rate": 0.15,
    }

    response = client.post("/api/valuation", json=payload)
    assert response.status_code == 400

    data = response.json()
    assert "strictly less than WACC" in data["detail"]


@patch("api.main.run_dcf_valuation")
def test_api_valuation_unexpected_exception(mock_run):
    """Verify HTTP 500 Internal Server Error on unexpected runtime exception."""
    mock_run.side_effect = RuntimeError("Unexpected upstream API failure.")

    payload = {
        "ticker": "FAIL",
        "projection_years": 5,
        "terminal_growth_rate": 0.02,
    }

    response = client.post("/api/valuation", json=payload)
    assert response.status_code == 500

    data = response.json()
    assert "RuntimeError" in data["detail"]
