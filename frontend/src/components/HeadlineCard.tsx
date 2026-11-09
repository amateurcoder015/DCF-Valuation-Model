import type { ValuationResponse } from '../types/valuation';
import { getCurrencySymbol } from '../utils/formatters';
import { AlertTriangle, TrendingUp, TrendingDown, Scale } from 'lucide-react';

interface HeadlineCardProps {
  result: ValuationResponse;
}

export const HeadlineCard = ({ result }: HeadlineCardProps) => {
  const sym = getCurrencySymbol(result.currency);
  const isUndervalued = result.implied_upside_pct >= 0;

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 shadow-lg mb-6">
      {/* Header Info */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center pb-4 mb-4 border-b border-slate-800 gap-2">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            {result.company_name} <span className="text-sm font-mono px-2.5 py-0.5 rounded bg-slate-800 text-blue-400 border border-slate-700">{result.ticker}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Trading Currency: <span className="text-slate-200 font-semibold">{result.currency}</span> | Statement Primary FY: <span className="text-slate-200 font-semibold">{result.primary_fiscal_year}</span>
          </p>
        </div>

        <div className="text-xs text-slate-400 bg-slate-850 px-3 py-1.5 rounded-lg border border-slate-800">
          Retrieved: <span className="font-mono text-slate-300">{new Date(result.data_retrieved_at).toLocaleString()}</span>
        </div>
      </div>

      {/* Main Headline Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Left Column: Intrinsic Price vs Market Price & Upside Status (7 cols) */}
        <div className="lg:col-span-7 bg-slate-950/60 rounded-xl p-5 border border-slate-800 flex flex-col justify-between space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-xs font-medium text-slate-400 block mb-1">Implied Intrinsic Price</span>
              <div className="text-3xl font-extrabold text-slate-100 font-mono">
                {sym}{result.implied_share_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <span className="text-[11px] text-slate-500 block mt-1">Single-Stage FCFF DCF Value</span>
            </div>

            <div>
              <span className="text-xs font-medium text-slate-400 block mb-1">Current Market Price</span>
              <div className="text-3xl font-extrabold text-slate-300 font-mono">
                {sym}{result.current_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <span className="text-[11px] text-slate-500 block mt-1">Live Market Share Price</span>
            </div>
          </div>

          <div className={`p-4 rounded-lg border flex items-center justify-between ${
            isUndervalued
              ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
              : 'bg-rose-950/40 border-rose-800/60 text-rose-300'
          }`}>
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-lg ${isUndervalued ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                {isUndervalued ? <TrendingUp className="w-6 h-6" /> : <TrendingDown className="w-6 h-6" />}
              </div>
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider block">
                  {isUndervalued ? '🟢 UNDERVALUED (Implied Upside)' : '🔴 OVERVALUED (Implied Downside)'}
                </span>
                <span className="text-2xl font-black font-mono">
                  {result.implied_upside_pct >= 0 ? '+' : ''}{result.implied_upside_pct.toFixed(2)}%
                </span>
              </div>
            </div>
            <span className="text-xs opacity-80 hidden sm:block">Margin of Safety relative to Market</span>
          </div>
        </div>

        {/* Right Column: IMMEDIATELY ADJACENT WACC, Terminal Growth, & Spread Context (5 cols) */}
        <div className="lg:col-span-5 bg-slate-950/60 rounded-xl p-5 border border-slate-800 flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Scale className="w-4 h-4 text-blue-400" /> Sensitivity & Spread Context
            </span>
            <span className="text-[11px] font-mono text-slate-400">Co-located Context</span>
          </div>

          <div className="grid grid-cols-3 gap-2 py-1">
            <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 text-center">
              <span className="text-[11px] text-slate-400 block mb-0.5">WACC</span>
              <span className="text-base font-bold text-slate-200 font-mono">{(result.wacc * 100).toFixed(2)}%</span>
            </div>

            <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 text-center">
              <span className="text-[11px] text-slate-400 block mb-0.5">Term Growth (g)</span>
              <span className="text-base font-bold text-slate-200 font-mono">{(result.terminal_growth_rate * 100).toFixed(2)}%</span>
            </div>

            <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 text-center">
              <span className="text-[11px] text-slate-400 block mb-0.5">Spread (WACC−g)</span>
              <span className={`text-base font-bold font-mono ${result.is_sensitivity_caution ? 'text-amber-400' : 'text-emerald-400'}`}>
                {result.wacc_spread_pct.toFixed(2)}%
              </span>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 flex items-center justify-between">
            <span>Discounted TV Share of EV:</span>
            <span className="font-mono font-semibold text-slate-200">{result.discounted_tv_share_pct.toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {/* HIGH SENSITIVITY CAUTION BANNER (When spread < 2.0%) */}
      {result.is_sensitivity_caution && (
        <div className="mt-4 p-4 rounded-xl bg-amber-950/40 border border-amber-800/60 text-amber-200 flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed">
            <span className="font-bold text-amber-300 block mb-0.5">⚠️ HIGH SENSITIVITY CAUTION ALERT (Spread &lt; 2.00%):</span>
            {result.sensitivity_caution_message || (
              `The WACC to Terminal Growth spread is thin (${result.wacc_spread_pct.toFixed(2)}% < 2.00%). ` +
              `Discounted Terminal Value accounts for ${result.discounted_tv_share_pct.toFixed(1)}% of total Enterprise Value. ` +
              `The implied share price and upside/downside percentage are mathematically hyper-sensitive to small 25-50 bps shifts in WACC (${(result.wacc * 100).toFixed(2)}%) or terminal growth (${(result.terminal_growth_rate * 100).toFixed(2)}%).`
            )}
          </div>
        </div>
      )}
    </div>
  );
};
