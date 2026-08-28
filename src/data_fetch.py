"""Data fetch engine — implemented in Step 2. Fetches and normalizes historical financials and market data via yfinance."""

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Any, Dict, Optional
import pandas as pd
import yfinance as yf


class UnsupportedSectorError(ValueError):
    """Raised when valuation is attempted on a financial sector company (Bank/Insurer/Financial Services)."""
    pass


# Empirically verified financial sector string from real yfinance API responses
# Confirmed against: JPM, BAC, GS, C, MS, WFC, BLK, HDFCBANK.NS, ICICIBANK.NS, SBIN.NS, AXISBANK.NS
FINANCIAL_SECTORS = {
    "financial services",
}


def is_financial_sector(sector: Optional[str]) -> bool:
    """Checks whether the company belongs to the financial sector.

    Standard FCFF-based DCF models do not apply to financial sector companies (banks, insurers,
    investment firms) because their balance sheets treat debt and interest as operational inventory.

    Args:
        sector: Sector name string returned by market data provider (e.g. 'Financial Services').

    Returns:
        bool: True if company is in financial sector, False otherwise.
    """
    if not sector or not isinstance(sector, str):
        return False
    return sector.strip().lower() in FINANCIAL_SECTORS


@dataclass
class CompanyFinancials:
    """Normalized company financials and market data container for DCF valuation inputs.

    Net Working Capital (NWC) Definition:
        NWC = Total Current Assets - Total Current Liabilities
        Change in NWC = NWC_t - NWC_{t-1}
        (Simplification of operational working capital using balance sheet current totals).

    CapEx Convention:
        Always normalized to a positive float quantity representing cash outflow.

    Currency Normalization:
        All monetary figures are converted to the market trading currency (info['currency'])
        if financial statement currency (info['financialCurrency']) differs (e.g. INFY.NS statement in USD, traded in INR).

    Column Alignment:
        ebit, depreciation_amortization, capex, and change_in_nwc are strictly drawn from the primary
        most recent fiscal year column (col 0). If interest_expense is NaN in col 0 (e.g. AAPL), it falls back
        to the most recent non-NaN prior column with interest_expense_fallback_used = True.

    Attributes:
        ticker: Ticker symbol string (e.g. 'AAPL').
        company_name: Full company or short name.
        sector: Sector classification.
        industry: Industry classification.
        currency: Statement currency code (e.g. 'USD', 'INR').
        ebit: Earnings Before Interest and Taxes (most recent fiscal year, in market currency).
        effective_tax_rate: Derived tax rate (tax_provision / pretax_income), or 0.25 fallback.
        depreciation_amortization: D&A non-cash add-back (most recent fiscal year, in market currency).
        capex: Capital expenditures as a positive outflow number (most recent fiscal year, in market currency).
        change_in_nwc: NWC_t - NWC_{t-1} across most recent two fiscal years (in market currency).
        total_debt: Total interest-bearing debt (in market currency).
        cash_and_equivalents: Cash and cash equivalents balance (in market currency).
        beta: Equity beta measuring systemic market risk.
        market_cap: Total market equity value (Market Capitalization, in market currency).
        diluted_shares_outstanding: Total diluted common shares outstanding.
        current_price: Current market share price (in market currency).
        interest_expense: Annual interest expense on debt obligations (in market currency).
        data_retrieved_at: ISO 8601 UTC timestamp of data retrieval.
        tax_rate_fallback_used: True if effective tax rate defaulted due to negative/zero pretax income.
        fx_rate_applied: Exchange rate multiplier used to convert financialCurrency to currency (1.0 if identical).
        interest_expense_fallback_used: True if interest_expense was drawn from a prior fiscal year due to NaN in col 0.
    """
    ticker: str
    company_name: str
    sector: str
    industry: str
    currency: str
    ebit: float
    effective_tax_rate: float
    depreciation_amortization: float
    capex: float
    change_in_nwc: float
    total_debt: float
    cash_and_equivalents: float
    beta: float
    market_cap: float
    diluted_shares_outstanding: float
    current_price: float
    interest_expense: float
    data_retrieved_at: str
    tax_rate_fallback_used: bool = False
    fx_rate_applied: float = 1.0
    interest_expense_fallback_used: bool = False


def _get_fx_rate(from_curr: str, to_curr: str) -> float:
    """Fetches real-time exchange rate to convert amounts from statement currency to trading currency."""
    if not from_curr or not to_curr or from_curr.strip().upper() == to_curr.strip().upper():
        return 1.0

    fc = from_curr.strip().upper()
    tc = to_curr.strip().upper()
    pair = f"{fc}{tc}=X"

    try:
        fx_t = yf.Ticker(pair)
        info = fx_t.info if hasattr(fx_t, "info") and fx_t.info else {}
        rate = info.get("regularMarketPrice") or info.get("currentPrice")
        if rate and isinstance(rate, (int, float)) and float(rate) > 0:
            return float(rate)
    except Exception:
        pass

    inv_pair = f"{tc}{fc}=X"
    try:
        fx_t = yf.Ticker(inv_pair)
        info = fx_t.info if hasattr(fx_t, "info") and fx_t.info else {}
        rate = info.get("regularMarketPrice") or info.get("currentPrice")
        if rate and isinstance(rate, (int, float)) and float(rate) > 0:
            return 1.0 / float(rate)
    except Exception:
        pass

    return 1.0


def _get_row_value(
    df: pd.DataFrame,
    row_names: list[str],
    col_idx: int = 0,
    search_all_cols: bool = False
) -> Optional[float]:
    """Retrieves numeric value from a DataFrame by candidate row names.

    If primary col_idx value is NaN and search_all_cols is True, iterates across remaining columns.
    """
    if df is None or df.empty:
        return None

    # Attempt at specified col_idx
    for name in row_names:
        if name in df.index:
            try:
                if col_idx < len(df.columns):
                    val = df.loc[name].iloc[col_idx]
                    if pd.notna(val):
                        val_float = float(val)
                        if not math.isnan(val_float) and not math.isinf(val_float):
                            return val_float
            except (IndexError, ValueError, TypeError):
                continue

    # Fallback to search remaining columns if enabled
    if search_all_cols and len(df.columns) > 1:
        for col in range(len(df.columns)):
            if col == col_idx:
                continue
            for name in row_names:
                if name in df.index:
                    try:
                        val = df.loc[name].iloc[col]
                        if pd.notna(val):
                            val_float = float(val)
                            if not math.isnan(val_float) and not math.isinf(val_float):
                                return val_float
                    except (IndexError, ValueError, TypeError):
                        continue

    return None


def fetch_company_financials(
    ticker: str,
    ticker_obj: Optional[Any] = None,
    fx_rate_override: Optional[float] = None
) -> CompanyFinancials:
    """Fetches real historical financials and market data for a given ticker via yfinance and normalizes structure.

    Args:
        ticker: Ticker symbol string (e.g. 'AAPL', 'MSFT', 'INFY.NS').
        ticker_obj: Optional pre-constructed yfinance Ticker object (useful for testing/mocking).
        fx_rate_override: Optional manual exchange rate override for testing/mocking currency conversion.

    Returns:
        CompanyFinancials: Normalized dataclass instance containing all inputs required for Step 1 math functions.

    Raises:
        ValueError: If ticker symbol is invalid, ticker is not found, or required financial statement fields are missing.
        UnsupportedSectorError: If company belongs to the financial sector (Banks/Insurers).
    """
    if not ticker or not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("Ticker symbol must be a non-empty string.")

    clean_ticker = ticker.strip().upper()
    t = ticker_obj if ticker_obj is not None else yf.Ticker(clean_ticker)

    try:
        info: Dict[str, Any] = t.info if hasattr(t, "info") and t.info else {}
    except Exception as err:
        raise ValueError(f"Ticker '{clean_ticker}' not found or network error: {err}")

    # Sector check first if sector is present
    sector = str(info.get("sector", ""))
    if is_financial_sector(sector):
        raise UnsupportedSectorError(
            f"Ticker '{clean_ticker}' belongs to the financial sector ('{sector}'). "
            "Standard FCFF DCF models are not appropriate for financial institutions."
        )

    inc: pd.DataFrame = getattr(t, "income_stmt", None)
    if inc is None or (isinstance(inc, pd.DataFrame) and inc.empty):
        inc = getattr(t, "financials", None)

    bs: pd.DataFrame = getattr(t, "balance_sheet", None)
    cf: pd.DataFrame = getattr(t, "cashflow", None)

    # Validate ticker data availability
    if not info or not isinstance(info, dict) or len(info) < 5:
        if (inc is None or inc.empty) and (bs is None or bs.empty):
            raise ValueError(f"Ticker '{clean_ticker}' not found or lacks sufficient financial statement data.")

    # Company metadata & Currency Check
    company_name = str(info.get("longName") or info.get("shortName") or clean_ticker)
    industry = str(info.get("industry", "Unknown"))
    currency = str(info.get("currency", "USD")).upper()
    financial_currency = str(info.get("financialCurrency") or currency).upper()

    if fx_rate_override is not None:
        fx_rate = float(fx_rate_override)
    else:
        fx_rate = _get_fx_rate(financial_currency, currency)

    # Market metadata (already in trading currency)
    current_price = info.get("currentPrice") or info.get("regularMarketPrice")
    if current_price is None or pd.isna(current_price) or float(current_price) <= 0:
        raise ValueError(f"Required market field 'current_price' is missing or invalid for ticker '{clean_ticker}'.")
    current_price_val = float(current_price)

    market_cap = info.get("marketCap")
    if market_cap is None or pd.isna(market_cap) or float(market_cap) <= 0:
        raise ValueError(f"Required market field 'market_cap' is missing or invalid for ticker '{clean_ticker}'.")
    market_cap_val = float(market_cap)

    shares = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
    if shares is None or pd.isna(shares) or float(shares) <= 0:
        shares_row = _get_row_value(inc, ["Diluted Average Shares", "Basic Average Shares"], col_idx=0, search_all_cols=False)
        if shares_row is not None and shares_row > 0:
            shares_val = shares_row
        else:
            shares_val = market_cap_val / current_price_val
    else:
        shares_val = float(shares)

    beta_raw = info.get("beta")
    if beta_raw is None or pd.isna(beta_raw):
        beta_val = 1.0
    else:
        beta_val = float(beta_raw)

    # Primary Income Statement extraction (col_idx=0 strictly)
    if inc is None or inc.empty:
        raise ValueError(f"Income statement missing or empty for ticker '{clean_ticker}'.")

    ebit_raw = _get_row_value(inc, ["EBIT", "Operating Income", "Total Operating Income As Reported"], col_idx=0, search_all_cols=False)
    if ebit_raw is None:
        raise ValueError(f"Required field 'ebit' is missing or NaN for ticker '{clean_ticker}'.")
    ebit_val = ebit_raw * fx_rate

    tax_provision = _get_row_value(inc, ["Tax Provision", "Income Tax Expense"], col_idx=0, search_all_cols=False)
    pretax_income = _get_row_value(inc, ["Pretax Income", "Income Before Tax"], col_idx=0, search_all_cols=False)

    tax_rate_fallback_used = False
    if pretax_income is not None and pretax_income > 0 and tax_provision is not None and tax_provision >= 0:
        derived_tax_rate = tax_provision / pretax_income
        if 0.0 <= derived_tax_rate <= 1.0:
            effective_tax_rate = derived_tax_rate
        else:
            effective_tax_rate = 0.25
            tax_rate_fallback_used = True
    else:
        effective_tax_rate = 0.25
        tax_rate_fallback_used = True

    # Balance sheet extraction for Debt and Cash
    if bs is None or bs.empty:
        raise ValueError(f"Balance sheet missing or empty for ticker '{clean_ticker}'.")

    total_debt_row = _get_row_value(bs, ["Total Debt", "Long Term Debt And Capital Lease Obligation"], col_idx=0, search_all_cols=True)
    if total_debt_row is not None:
        total_debt_val = total_debt_row * fx_rate
    else:
        info_debt = info.get("totalDebt")
        total_debt_val = float(info_debt) if info_debt is not None and not pd.isna(info_debt) else 0.0

    # Interest Expense extraction: check primary col_idx=0 first
    interest_expense_fallback_used = False
    interest_exp_col0 = _get_row_value(
        inc,
        ["Interest Expense", "Interest Expense Non Operating", "Net Non Operating Interest Income Expense"],
        col_idx=0,
        search_all_cols=False
    )

    if interest_exp_col0 is not None:
        interest_expense_val = abs(interest_exp_col0) * fx_rate
    else:
        # Fallback to search remaining columns if col 0 is NaN (e.g. AAPL)
        interest_exp_prior = _get_row_value(
            inc,
            ["Interest Expense", "Interest Expense Non Operating", "Net Non Operating Interest Income Expense"],
            col_idx=0,
            search_all_cols=True
        )
        if interest_exp_prior is not None:
            interest_expense_val = abs(interest_exp_prior) * fx_rate
            interest_expense_fallback_used = True
        elif info.get("interestExpense") is not None and not pd.isna(info.get("interestExpense")):
            interest_expense_val = abs(float(info.get("interestExpense"))) * fx_rate
            interest_expense_fallback_used = True
        else:
            if total_debt_val > 0.0:
                raise ValueError(f"Required field 'interest_expense' is missing or NaN for ticker '{clean_ticker}'.")
            else:
                interest_expense_val = 0.0  # Valid debt-free case

    # Primary Cashflow extraction (col_idx=0 strictly)
    if cf is None or cf.empty:
        raise ValueError(f"Cash flow statement missing or empty for ticker '{clean_ticker}'.")

    da_raw = _get_row_value(cf, ["Depreciation And Amortization", "Depreciation Amortization Depletion", "Reconciled Depreciation"], col_idx=0, search_all_cols=False)
    if da_raw is None:
        raise ValueError(f"Required field 'depreciation_amortization' is missing or NaN for ticker '{clean_ticker}'.")
    da_val = da_raw * fx_rate

    capex_raw = _get_row_value(cf, ["Capital Expenditure", "Capital Expenditure Reported"], col_idx=0, search_all_cols=False)
    if capex_raw is None:
        raise ValueError(f"Required field 'capex' is missing or NaN for ticker '{clean_ticker}'.")
    capex_val = abs(capex_raw) * fx_rate  # Normalize outflow to positive float

    # Balance sheet NWC extraction (most recent two fiscal years: col_idx 0 vs col_idx 1)
    cols = bs.columns
    if len(cols) < 2:
        raise ValueError(f"Insufficient balance sheet history (found {len(cols)} years, need 2) to calculate change in NWC for ticker '{clean_ticker}'.")

    ca_0 = _get_row_value(bs, ["Current Assets"], col_idx=0, search_all_cols=False)
    cl_0 = _get_row_value(bs, ["Current Liabilities"], col_idx=0, search_all_cols=False)
    ca_1 = _get_row_value(bs, ["Current Assets"], col_idx=1, search_all_cols=False)
    cl_1 = _get_row_value(bs, ["Current Liabilities"], col_idx=1, search_all_cols=False)

    if ca_0 is None or cl_0 is None or ca_1 is None or cl_1 is None:
        raise ValueError(f"Required balance sheet fields ('Current Assets' / 'Current Liabilities') missing or NaN for ticker '{clean_ticker}'.")

    nwc_0 = (ca_0 - cl_0) * fx_rate
    nwc_1 = (ca_1 - cl_1) * fx_rate
    change_in_nwc = nwc_0 - nwc_1

    cash_row = _get_row_value(bs, ["Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"], col_idx=0, search_all_cols=True)
    if cash_row is not None:
        cash_val = cash_row * fx_rate
    else:
        info_cash = info.get("totalCash")
        cash_val = float(info_cash) if info_cash is not None and not pd.isna(info_cash) else 0.0

    now_iso = datetime.now(timezone.utc).isoformat()

    return CompanyFinancials(
        ticker=clean_ticker,
        company_name=company_name,
        sector=sector,
        industry=industry,
        currency=currency,
        ebit=ebit_val,
        effective_tax_rate=effective_tax_rate,
        depreciation_amortization=da_val,
        capex=capex_val,
        change_in_nwc=change_in_nwc,
        total_debt=total_debt_val,
        cash_and_equivalents=cash_val,
        beta=beta_val,
        market_cap=market_cap_val,
        diluted_shares_outstanding=shares_val,
        current_price=current_price_val,
        interest_expense=interest_expense_val,
        data_retrieved_at=now_iso,
        tax_rate_fallback_used=tax_rate_fallback_used,
        fx_rate_applied=fx_rate,
        interest_expense_fallback_used=interest_expense_fallback_used,
    )


def historical_revenue_cagr(ticker: str, years: int = 3, ticker_obj: Optional[Any] = None) -> float:
    """Computes historical revenue Compound Annual Growth Rate (CAGR) over requested number of years.

    Args:
        ticker: Ticker symbol string (e.g. 'AAPL').
        years: Historical lookback horizon in years (default 3).
        ticker_obj: Optional pre-constructed yfinance Ticker object (useful for testing/mocking).

    Returns:
        float: Historical revenue CAGR as a decimal (e.g. 0.08 for 8%).

    Raises:
        ValueError: If ticker is invalid, revenue history is missing/insufficient, or calculation results in non-positive base.
    """
    if not ticker or not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("Ticker symbol must be a non-empty string.")

    if years <= 0:
        raise ValueError("Historical CAGR horizon 'years' must be a positive integer > 0.")

    clean_ticker = ticker.strip().upper()
    t = ticker_obj if ticker_obj is not None else yf.Ticker(clean_ticker)

    inc: pd.DataFrame = getattr(t, "income_stmt", None)
    if inc is None or (isinstance(inc, pd.DataFrame) and inc.empty):
        inc = getattr(t, "financials", None)

    if inc is None or inc.empty:
        raise ValueError(f"Income statement missing or empty for ticker '{clean_ticker}'.")

    rev_series = None
    for row_name in ["Total Revenue", "Operating Revenue"]:
        if row_name in inc.index:
            rev_series = inc.loc[row_name].dropna()
            break

    if rev_series is None or len(rev_series) < years + 1:
        found_years = len(rev_series) if rev_series is not None else 0
        raise ValueError(
            f"Insufficient revenue history available for ticker '{clean_ticker}' "
            f"(found {found_years} years, needed {years + 1})."
        )

    rev_latest = float(rev_series.iloc[0])
    rev_past = float(rev_series.iloc[years])

    if rev_past <= 0.0 or rev_latest <= 0.0:
        raise ValueError(f"Non-positive revenue history values encountered for ticker '{clean_ticker}'.")

    return (rev_latest / rev_past) ** (1.0 / years) - 1.0
