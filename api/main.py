"""FastAPI Backend API — exposes Step 3 run_dcf_valuation() for the React frontend dashboard."""

import os
import sys
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure root directory is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.app_helpers import (
    compute_wacc_spread,
    get_cost_of_debt_summary,
    get_growth_summary,
    get_sensitivity_caution_message,
)
from src.data_fetch import UnsupportedSectorError
from src.dcf_engine import DCFValuationResult, run_dcf_valuation

app = FastAPI(
    title="DCF Valuation Model API",
    description="Thin FastAPI wrapper exposing Step 3 DCF valuation engine and transparent assumptions.",
    version="1.0.0",
)

# CORS setup for local development (React dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ValuationRequest(BaseModel):
    ticker: str = Field(..., description="Company ticker symbol (e.g. AAPL, INFY.NS)")
    projection_years: int = Field(..., ge=1, le=20, description="Forecast period in years")
    terminal_growth_rate: float = Field(..., description="Perpetual growth rate as decimal (e.g. 0.025)")
    projection_growth_rate: Optional[float] = Field(None, description="Optional explicit growth rate as decimal (e.g. 0.06)")
    use_historical_cagr_suggestion: bool = Field(False, description="If True and no explicit rate, uses historical CAGR")
    manual_cost_of_debt: Optional[float] = Field(None, description="Optional pre-tax cost of debt override as decimal (e.g. 0.045)")
    risk_free_rate: float = Field(0.0425, description="Risk-free rate as decimal (default 0.0425)")
    equity_risk_premium: float = Field(0.055, description="Equity risk premium as decimal (default 0.055)")


class ValuationResponse(BaseModel):
    ticker: str
    company_name: str
    currency: str
    data_retrieved_at: str
    base_year_fcff: float
    cost_of_equity: float
    cost_of_debt_after_tax: float
    wacc: float
    projected_fcffs: List[float]
    terminal_value: float
    discounted_terminal_value: float
    sum_of_discounted_fcffs: float
    enterprise_value: float
    equity_value: float
    implied_share_price: float
    current_price: float
    implied_upside_pct: float
    primary_fiscal_year: str
    interest_expense_fiscal_year: str
    interest_expense_vintage_gap_years: int
    cost_of_debt_flagged: bool
    tax_rate_fallback_used: bool
    fx_rate_applied: float
    manual_cost_of_debt_used: bool
    growth_rate_source: str
    historical_cagr_suggestion: Optional[float]
    projection_growth_rate: float
    terminal_growth_rate: float
    projection_years: int
    warnings: List[str]

    # Derived presentation fields
    wacc_spread_pct: float
    is_sensitivity_caution: bool
    sensitivity_caution_message: Optional[str]
    discounted_tv_share_pct: float
    growth_summary: str
    cost_of_debt_summary: str


@app.post("/api/valuation", response_model=ValuationResponse)
def compute_valuation(req: ValuationRequest) -> Dict[str, Any]:
    try:
        res: DCFValuationResult = run_dcf_valuation(
            ticker=req.ticker,
            projection_years=req.projection_years,
            terminal_growth_rate=req.terminal_growth_rate,
            projection_growth_rate=req.projection_growth_rate,
            use_historical_cagr_suggestion=req.use_historical_cagr_suggestion,
            manual_cost_of_debt=req.manual_cost_of_debt,
            risk_free_rate=req.risk_free_rate,
            equity_risk_premium=req.equity_risk_premium,
        )

        spread_pct, is_caution = compute_wacc_spread(res.wacc, res.terminal_growth_rate, caution_threshold_pct=2.0)
        tv_share_pct = (res.discounted_terminal_value / res.enterprise_value * 100.0) if res.enterprise_value > 0 else 0.0
        caution_msg = get_sensitivity_caution_message(res.wacc, res.terminal_growth_rate, spread_pct, tv_share_pct) if is_caution else None

        res_dict = res.__dict__.copy()
        res_dict.update({
            "wacc_spread_pct": spread_pct,
            "is_sensitivity_caution": is_caution,
            "sensitivity_caution_message": caution_msg,
            "discounted_tv_share_pct": tv_share_pct,
            "growth_summary": get_growth_summary(res),
            "cost_of_debt_summary": get_cost_of_debt_summary(res),
        })
        return res_dict

    except UnsupportedSectorError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{type(err).__name__}: {str(err)}",
        )
