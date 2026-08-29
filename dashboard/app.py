"""Single-Page Streamlit Dashboard for Discounted Cash Flow (DCF) Valuation Model."""

import os
import sys
import streamlit as st

# Ensure repository root is on sys.path for clean imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.app_helpers import (
    compute_wacc_spread,
    format_currency,
    get_cost_of_debt_summary,
    get_currency_symbol,
    get_growth_summary,
    get_sensitivity_caution_message,
)
from src.data_fetch import UnsupportedSectorError
from src.dcf_engine import DCFValuationResult, run_dcf_valuation


def main():
    st.set_page_config(
        page_title="DCF Valuation Model",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom Header
    st.title("📈 Discounted Cash Flow (DCF) Valuation Model")
    st.caption("Institutional Single-Stage FCFF Valuation Engine with Real yFinance Fundamentals & Transparent Assumption Tracking")

    # 1. INPUT PANEL (Sidebar)
    st.sidebar.header("🎯 Valuation Inputs")

    ticker_input = st.sidebar.text_input(
        "Ticker Symbol",
        value="AAPL",
        help="Enter company ticker symbol (e.g. AAPL, INFY.NS, MSFT, GOOGL)",
    )

    projection_years = st.sidebar.number_input(
        "Forecast Horizon (Years)",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        help="Explicit FCFF projection period in years",
    )

    terminal_growth_pct = st.sidebar.number_input(
        "Perpetual Terminal Growth Rate (%)",
        min_value=-5.0,
        max_value=10.0,
        value=2.5,
        step=0.1,
        help="Perpetual growth rate after forecast horizon (must be < WACC)",
    )

    proj_growth_str = st.sidebar.text_input(
        "Projection Growth Rate (%) (Optional)",
        value="",
        help="Explicit annual growth rate e.g. 6.0. Leave blank to rely on historical CAGR suggestion.",
    )

    use_cagr_suggestion = st.sidebar.checkbox(
        "Use 3-Year Historical Revenue CAGR as growth suggestion",
        value=False,
        help="If checked and explicit growth rate is blank, uses historical revenue CAGR.",
    )

    manual_kd_str = st.sidebar.text_input(
        "Manual Pre-Tax Cost of Debt (%) (Optional)",
        value="",
        help="Optional override for pre-tax cost of debt e.g. 4.5. Leave blank to derive from financials.",
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Hurdle Rate Assumptions")

    rf_pct = st.sidebar.number_input(
        "Risk-Free Rate (%)",
        min_value=0.0,
        max_value=20.0,
        value=4.25,
        step=0.05,
        help="Benchmark risk-free rate (e.g. 10-Year US Treasury yield)",
    )

    erp_pct = st.sidebar.number_input(
        "Equity Risk Premium (%)",
        min_value=0.0,
        max_value=20.0,
        value=5.50,
        step=0.05,
        help="Expected excess market return over risk-free rate",
    )

    run_button = st.sidebar.button("🚀 Run DCF Valuation", type="primary", use_container_width=True)

    if not run_button:
        st.info("👈 Enter a ticker symbol and valuation assumptions in the sidebar, then click **Run DCF Valuation** to generate valuation outputs.")
        return

    # Parse numerical inputs
    terminal_growth_rate = terminal_growth_pct / 100.0
    risk_free_rate = rf_pct / 100.0
    equity_risk_premium = erp_pct / 100.0

    projection_growth_rate = None
    if proj_growth_str.strip():
        try:
            projection_growth_rate = float(proj_growth_str.strip()) / 100.0
        except ValueError:
            st.error("Invalid input for Projection Growth Rate (%). Please enter a valid number e.g. 6.0.")
            return

    manual_cost_of_debt = None
    if manual_kd_str.strip():
        try:
            manual_cost_of_debt = float(manual_kd_str.strip()) / 100.0
        except ValueError:
            st.error("Invalid input for Manual Cost of Debt (%). Please enter a valid number e.g. 4.5.")
            return

    # 2. EXECUTION & ERROR HANDLING
    with st.spinner(f"Fetching real financial data and building DCF model for {ticker_input.upper()}..."):
        try:
            res: DCFValuationResult = run_dcf_valuation(
                ticker=ticker_input,
                projection_years=projection_years,
                terminal_growth_rate=terminal_growth_rate,
                projection_growth_rate=projection_growth_rate,
                use_historical_cagr_suggestion=use_cagr_suggestion,
                manual_cost_of_debt=manual_cost_of_debt,
                risk_free_rate=risk_free_rate,
                equity_risk_premium=equity_risk_premium,
            )
        except UnsupportedSectorError as err:
            st.warning(
                f"🏦 **UNSUPPORTED FINANCIAL SECTOR COMPANY**\n\n{err}\n\n"
                "**Explanation**: Banks, insurers, and financial institutions cannot be valued using "
                "standard FCFF DCF models because interest income and debt obligations represent raw operating inventory rather than capital structure."
            )
            return
        except ValueError as err:
            st.error(f"❌ **VALUATION / DATA INPUT ERROR**: {err}")
            return
        except Exception as err:
            st.error(f"⚠️ **VALUATION EXECUTION FAILED**: {err}")
            with st.expander("Technical Exception Details"):
                st.exception(err)
            return

    # 3. HEADLINE RESULT SECTION
    st.markdown("---")
    curr_sym = get_currency_symbol(res.currency)

    st.subheader(f"📊 Valuation Summary: {res.company_name} ({res.ticker})")

    col_h1, col_h2, col_h3 = st.columns([1.2, 1.2, 1.6])

    with col_h1:
        st.metric(
            label="Implied Intrinsic Share Price",
            value=f"{curr_sym}{res.implied_share_price:,.2f}",
        )
        st.caption(f"Trading Currency: {res.currency}")

    with col_h2:
        st.metric(
            label="Current Market Share Price",
            value=f"{curr_sym}{res.current_price:,.2f}",
        )
        st.caption(f"Statement FY: {res.primary_fiscal_year}")

    with col_h3:
        if res.implied_upside_pct >= 0:
            status_label = "🟢 UNDERVALUED (Implied Upside)"
            delta_str = f"+{res.implied_upside_pct:.2f}%"
        else:
            status_label = "🔴 OVERVALUED (Implied Downside)"
            delta_str = f"{res.implied_upside_pct:.2f}%"

        st.metric(
            label=status_label,
            value=delta_str,
            delta=f"{res.implied_upside_pct:.2f}% relative to market",
        )

    # IMMEDIATELY ADJACENT SENSITIVITY & WACC SPREAD PANEL
    st.markdown("##### ⚡ Sensitivity Context & Hurdle Rate Spread")

    spread_pct, is_caution = compute_wacc_spread(res.wacc, res.terminal_growth_rate)
    tv_share_pct = (res.discounted_terminal_value / res.enterprise_value) * 100.0 if res.enterprise_value > 0 else 0.0

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Discount Rate (WACC)", f"{res.wacc * 100:.2f}%")
    with col_s2:
        st.metric("Terminal Growth Rate (g)", f"{res.terminal_growth_rate * 100:.2f}%")
    with col_s3:
        st.metric("WACC − Terminal Growth Spread", f"{spread_pct:.2f}%")

    if is_caution:
        st.warning(get_sensitivity_caution_message(res.wacc, res.terminal_growth_rate, spread_pct, tv_share_pct))

    # 4. ASSUMPTION & FLAG TRANSPARENCY PANEL
    st.markdown("---")
    st.subheader("🔍 Assumption & Data Flag Transparency Panel")

    t_col1, t_col2 = st.columns(2)

    with t_col1:
        st.markdown("**Growth Rate Model & Precedence**")
        st.info(get_growth_summary(res))

        st.markdown("**Effective Tax Rate Status**")
        if res.tax_rate_fallback_used:
            st.warning("⚠️ Tax Rate: Defaulted to 0.25 (25%) statutory fallback rate due to negative or zero pretax income.")
        else:
            st.success("✅ Tax Rate: Derived directly from historical tax provision and pretax income.")

    with t_col2:
        st.markdown("**Cost of Debt & Fiscal Year Vintage Status**")
        if res.cost_of_debt_flagged:
            st.warning(f"⚠️ {get_cost_of_debt_summary(res)}")
        else:
            st.success(f"✅ {get_cost_of_debt_summary(res)}")

        st.markdown("**Currency Normalization**")
        if res.fx_rate_applied != 1.0:
            st.info(f"🌐 FX Adjustment Applied: Financial statements converted to {res.currency} using rate {res.fx_rate_applied}.")
        else:
            st.success(f"✅ Financial statement currency matches trading currency ({res.currency}).")

    if res.warnings:
        st.markdown("##### ⚠️ Active Model Warnings & Transparency Callouts")
        for w in res.warnings:
            st.warning(f"• {w}")

    # 5. DETAIL & FINANCIAL BREAKDOWN SECTION
    st.markdown("---")
    st.subheader("📑 Financial Breakdown & Valuation Waterfall")

    tab1, tab2 = st.columns(2)

    with tab1:
        st.markdown("#### Projected Annual Free Cash Flows (FCFF)")
        fcff_data = []
        for i, val in enumerate(res.projected_fcffs, 1):
            fcff_data.append({"Forecast Year": f"Year {i}", "FCFF": val})
        st.dataframe(fcff_data, use_container_width=True)

    with tab2:
        st.markdown("#### Valuation Waterfall & Equity Bridge")
        waterfall_data = [
            {"Metric": "Base Year FCFF (Year 0)", "Amount": format_currency(res.base_year_fcff, res.currency)},
            {"Metric": "Sum of PV of Projected FCFFs", "Amount": format_currency(res.sum_of_discounted_fcffs, res.currency)},
            {"Metric": f"Nominal Terminal Value (Year {res.projection_years})", "Amount": format_currency(res.terminal_value, res.currency)},
            {"Metric": "PV of Terminal Value", "Amount": format_currency(res.discounted_terminal_value, res.currency)},
            {"Metric": "Enterprise Value (EV)", "Amount": format_currency(res.enterprise_value, res.currency)},
            {"Metric": "Less: Total Debt", "Amount": format_currency(res.equity_value + (res.enterprise_value - res.equity_value) - res.enterprise_value, res.currency)},
            {"Metric": "Implied Equity Value", "Amount": format_currency(res.equity_value, res.currency)},
            {"Metric": "Diluted Shares Outstanding", "Amount": f"{res.equity_value / res.implied_share_price:,.0f}"},
            {"Metric": "Implied Intrinsic Share Price", "Amount": f"{curr_sym}{res.implied_share_price:,.2f}"},
        ]
        st.table(waterfall_data)

    st.markdown("#### ⚡ Capital Structure & WACC Component Breakdown")
    w_col1, w_col2, w_col3 = st.columns(3)
    with w_col1:
        st.write(f"**Cost of Equity (CAPM)**: {res.cost_of_equity * 100:.2f}%")
        st.write(f"*(Risk-Free: {rf_pct:.2f}%, Beta: {res.cost_of_equity}, ERP: {erp_pct:.2f}%)*")
    with w_col2:
        st.write(f"**After-Tax Cost of Debt**: {res.cost_of_debt_after_tax * 100:.2f}%")
        st.write(f"*(Manual Override: {res.manual_cost_of_debt_used})*")
    with w_col3:
        st.write(f"**Weighted Average Cost of Capital (WACC)**: {res.wacc * 100:.2f}%")

    # 6. DATA FRESHNESS & METADATA
    st.markdown("---")
    st.caption(f"🕒 **Data Freshness Timestamp**: Underlying financial data retrieved at `{res.data_retrieved_at}` via yFinance.")


if __name__ == "__main__":
    main()
