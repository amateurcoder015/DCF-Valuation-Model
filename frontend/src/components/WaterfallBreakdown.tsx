import type { ValuationResponse } from '../types/valuation';
import { formatCurrency, getCurrencySymbol } from '../utils/formatters';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { PieChart, Cpu } from 'lucide-react';

interface WaterfallBreakdownProps {
  result: ValuationResponse;
}

export const WaterfallBreakdown = ({ result }: WaterfallBreakdownProps) => {
  const sym = getCurrencySymbol(result.currency);

  const fcffChartData = result.projected_fcffs.map((val, idx) => ({
    year: `Year ${idx + 1}`,
    fcff: val,
    displayFcff: formatCurrency(val, result.currency),
  }));

  const waterfallRows = [
    { label: 'Base Year FCFF (Year 0)', val: formatCurrency(result.base_year_fcff, result.currency), highlight: false },
    { label: 'Sum of Discounted Forecast FCFFs', val: formatCurrency(result.sum_of_discounted_fcffs, result.currency), highlight: false },
    { label: `Nominal Terminal Value (Year ${result.projection_years})`, val: formatCurrency(result.terminal_value, result.currency), highlight: false },
    { label: 'PV of Terminal Value', val: formatCurrency(result.discounted_terminal_value, result.currency), highlight: false },
    { label: 'Enterprise Value (EV)', val: formatCurrency(result.enterprise_value, result.currency), highlight: true },
    { label: 'Less: Total Debt', val: `- ${formatCurrency(result.equity_value + (result.enterprise_value - result.equity_value) - result.enterprise_value, result.currency)}`, highlight: false },
    { label: 'Implied Equity Value', val: formatCurrency(result.equity_value, result.currency), highlight: true },
    { label: 'Diluted Shares Outstanding', val: `${(result.equity_value / result.implied_share_price).toLocaleString(undefined, { maximumFractionDigits: 0 })}`, highlight: false },
    { label: 'Implied Intrinsic Share Price', val: `${sym}${result.implied_share_price.toFixed(2)}`, highlight: true },
  ];

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 shadow-lg mb-6">
      <div className="flex items-center space-x-2 pb-3 mb-6 border-b border-slate-800">
        <PieChart className="w-5 h-5 text-blue-400" />
        <h3 className="text-base font-semibold text-slate-100">📑 Financial Breakdown & Valuation Waterfall</h3>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Recharts Bar Chart of Projected FCFFs */}
        <div className="bg-slate-950/60 p-5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div className="mb-4">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
              Projected Free Cash Flow to Firm (FCFF)
            </h4>
            <span className="text-[11px] text-slate-500 block">
              {result.projection_years}-Year Forecast at {(result.projection_growth_rate * 100).toFixed(2)}% Annual Growth
            </span>
          </div>

          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={fcffChartData} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
                <XAxis dataKey="year" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => formatCurrency(v, result.currency)} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc', fontSize: '12px' }}
                  formatter={(value: number) => [formatCurrency(value, result.currency), 'FCFF']}
                />
                <Bar dataKey="fcff" radius={[4, 4, 0, 0]}>
                  {fcffChartData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={index === fcffChartData.length - 1 ? '#0284c7' : '#3b82f6'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Labeled Waterfall Bridge Table */}
        <div className="bg-slate-950/60 p-5 rounded-xl border border-slate-800">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
            Valuation Capital Bridge
          </h4>
          <div className="divide-y divide-slate-800/60">
            {waterfallRows.map((row, idx) => (
              <div
                key={idx}
                className={`flex justify-between items-center py-2 px-1 text-xs ${
                  row.highlight ? 'bg-blue-950/40 font-bold text-blue-300 rounded px-2' : 'text-slate-300'
                }`}
              >
                <span>{row.label}</span>
                <span className="font-mono">{row.val}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Capital Structure & WACC Breakdown */}
      <div className="bg-slate-950/60 p-5 rounded-xl border border-slate-800">
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <Cpu className="w-4 h-4 text-blue-400" /> Capital Structure & WACC Components
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400 block mb-1">Cost of Equity (CAPM)</span>
            <span className="text-lg font-bold text-slate-100 font-mono">{(result.cost_of_equity * 100).toFixed(2)}%</span>
            <span className="text-[10px] text-slate-500 block mt-1">Ke = Rf + Beta × ERP</span>
          </div>

          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400 block mb-1">After-Tax Cost of Debt</span>
            <span className="text-lg font-bold text-slate-100 font-mono">{(result.cost_of_debt_after_tax * 100).toFixed(2)}%</span>
            <span className="text-[10px] text-slate-500 block mt-1">Kd = (Interest / Debt) × (1 - t)</span>
          </div>

          <div className="bg-slate-900/80 p-3 rounded-lg border border-blue-900/50">
            <span className="text-slate-400 block mb-1">Weighted Average Cost of Capital (WACC)</span>
            <span className="text-lg font-bold text-blue-400 font-mono">{(result.wacc * 100).toFixed(2)}%</span>
            <span className="text-[10px] text-slate-500 block mt-1">WACC = (E/V)Ke + (D/V)Kd</span>
          </div>
        </div>
      </div>
    </div>
  );
};
