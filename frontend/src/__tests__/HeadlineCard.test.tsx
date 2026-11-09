import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HeadlineCard } from '../components/HeadlineCard';
import type { ValuationResponse } from '../types/valuation';

describe('HeadlineCard component', () => {
  const mockResult: ValuationResponse = {
    ticker: 'TEST',
    company_name: 'Test Company',
    currency: 'USD',
    data_retrieved_at: '2026-08-29T00:00:00Z',
    base_year_fcff: 10000.0,
    cost_of_equity: 0.10,
    cost_of_debt_after_tax: 0.04,
    wacc: 0.0481,
    projected_fcffs: [10500.0, 11025.0],
    terminal_value: 200000.0,
    discounted_terminal_value: 136116.64,
    sum_of_discounted_fcffs: 44300.0,
    enterprise_value: 180416.64,
    equity_value: 165416.64,
    implied_share_price: 165.42,
    current_price: 150.0,
    implied_upside_pct: 10.28,
    primary_fiscal_year: '2025-12-31',
    interest_expense_fiscal_year: '2025-12-31',
    interest_expense_vintage_gap_years: 0,
    cost_of_debt_flagged: false,
    tax_rate_fallback_used: false,
    fx_rate_applied: 1.0,
    manual_cost_of_debt_used: false,
    growth_rate_source: 'explicit',
    projection_growth_rate: 0.05,
    terminal_growth_rate: 0.03,
    projection_years: 5,
    warnings: [],
    wacc_spread_pct: 1.81,
    is_sensitivity_caution: true,
    sensitivity_caution_message: 'High sensitivity caution alert: WACC spread is thin.',
    discounted_tv_share_pct: 75.4,
    growth_summary: 'Projection Growth Rate: 5.00% (Source: Explicit Input).',
    cost_of_debt_summary: 'Cost of Debt derived from current FY 2025-12-31 interest expense.',
  };

  it('renders implied share price, market price, WACC, terminal growth rate, and spread co-located in the same block', () => {
    render(<HeadlineCard result={mockResult} />);

    // Assert Implied Price and Market Price render
    expect(screen.getByText('Implied Intrinsic Price')).toBeInTheDocument();
    expect(screen.getByText('$165.42')).toBeInTheDocument();
    expect(screen.getByText('Current Market Price')).toBeInTheDocument();
    expect(screen.getByText('$150.00')).toBeInTheDocument();

    // Assert Co-located Sensitivity Block renders WACC, Terminal Growth, and Spread together
    expect(screen.getByText('Sensitivity & Spread Context')).toBeInTheDocument();
    expect(screen.getByText('4.81%')).toBeInTheDocument(); // WACC
    expect(screen.getByText('3.00%')).toBeInTheDocument(); // Terminal Growth
    expect(screen.getByText('1.81%')).toBeInTheDocument(); // Spread
  });

  it('renders High Sensitivity Caution Alert Banner when spread < 2.0%', () => {
    render(<HeadlineCard result={mockResult} />);

    expect(screen.getByText(/High sensitivity caution alert: WACC spread is thin/i)).toBeInTheDocument();
  });
});
