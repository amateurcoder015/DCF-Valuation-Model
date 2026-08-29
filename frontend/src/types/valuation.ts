export interface ValuationRequest {
  ticker: string;
  projection_years: number;
  terminal_growth_rate: number;
  projection_growth_rate?: number | null;
  use_historical_cagr_suggestion?: boolean;
  manual_cost_of_debt?: number | null;
  risk_free_rate?: number;
  equity_risk_premium?: number;
}

export interface ValuationResponse {
  ticker: string;
  company_name: string;
  currency: string;
  data_retrieved_at: string;
  base_year_fcff: number;
  cost_of_equity: number;
  cost_of_debt_after_tax: number;
  wacc: number;
  projected_fcffs: number[];
  terminal_value: number;
  discounted_terminal_value: number;
  sum_of_discounted_fcffs: number;
  enterprise_value: number;
  equity_value: number;
  implied_share_price: number;
  current_price: number;
  implied_upside_pct: number;
  primary_fiscal_year: string;
  interest_expense_fiscal_year: string;
  interest_expense_vintage_gap_years: number;
  cost_of_debt_flagged: boolean;
  tax_rate_fallback_used: boolean;
  fx_rate_applied: number;
  manual_cost_of_debt_used: boolean;
  growth_rate_source: string;
  historical_cagr_suggestion?: number | null;
  projection_growth_rate: number;
  terminal_growth_rate: number;
  projection_years: number;
  warnings: string[];
  wacc_spread_pct: number;
  is_sensitivity_caution: boolean;
  sensitivity_caution_message?: string | null;
  discounted_tv_share_pct: number;
  growth_summary: string;
  cost_of_debt_summary: string;
}

export interface ApiErrorResponse {
  detail: string;
  error_type?: string;
}
