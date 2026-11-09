import React, { useState } from 'react';
import type { ValuationRequest } from '../types/valuation';
import { Play, Settings } from 'lucide-react';

interface InputPanelProps {
  onRunValuation: (request: ValuationRequest) => void;
  isLoading: boolean;
}

export const InputPanel = ({ onRunValuation, isLoading }: InputPanelProps) => {
  const [ticker, setTicker] = useState('AAPL');
  const [projectionYears, setProjectionYears] = useState(5);
  const [terminalGrowthPct, setTerminalGrowthPct] = useState(2.5);
  const [projGrowthPctStr, setProjGrowthPctStr] = useState('');
  const [useCagrSuggestion, setUseCagrSuggestion] = useState(false);
  const [manualKdStr, setManualKdStr] = useState('');
  const [rfPct, setRfPct] = useState(4.25);
  const [erpPct, setErpPct] = useState(5.50);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticker.trim()) return;

    const request: ValuationRequest = {
      ticker: ticker.trim().toUpperCase(),
      projection_years: projectionYears,
      terminal_growth_rate: terminalGrowthPct / 100.0,
      projection_growth_rate: projGrowthPctStr.trim() ? parseFloat(projGrowthPctStr.trim()) / 100.0 : null,
      use_historical_cagr_suggestion: useCagrSuggestion,
      manual_cost_of_debt: manualKdStr.trim() ? parseFloat(manualKdStr.trim()) / 100.0 : null,
      risk_free_rate: rfPct / 100.0,
      equity_risk_premium: erpPct / 100.0,
    };

    onRunValuation(request);
  };

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 shadow-lg mb-6">
      <div className="flex items-center space-x-2 mb-4 pb-3 border-b border-slate-800">
        <Settings className="w-5 h-5 text-blue-400" />
        <h2 className="text-base font-semibold text-slate-100">Valuation Inputs & Macro Parameters</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Ticker Input */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Ticker Symbol <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder="e.g. AAPL, INFY.NS, MSFT"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500 font-mono uppercase"
              required
            />
            <span className="text-[10px] text-slate-500 mt-1 block">Free text e.g. AAPL, INFY.NS</span>
          </div>

          {/* Projection Horizon */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Forecast Horizon (Years) <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              min={1}
              max={20}
              value={projectionYears}
              onChange={(e) => setProjectionYears(parseInt(e.target.value) || 5)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500 font-mono"
              required
            />
            <span className="text-[10px] text-slate-500 mt-1 block">Explicit FCFF period (1-20 yrs)</span>
          </div>

          {/* Terminal Growth Rate */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Terminal Growth Rate (%) <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              step="0.1"
              value={terminalGrowthPct}
              onChange={(e) => setTerminalGrowthPct(parseFloat(e.target.value) || 0.0)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500 font-mono"
              required
            />
            <span className="text-[10px] text-slate-500 mt-1 block">Perpetual growth (must be &lt; WACC)</span>
          </div>

          {/* Explicit Projection Growth Rate */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Forecast Growth Rate (%) <span className="text-slate-500">(Optional)</span>
            </label>
            <input
              type="number"
              step="0.1"
              placeholder="e.g. 6.0"
              value={projGrowthPctStr}
              onChange={(e) => setProjGrowthPctStr(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500 font-mono"
            />
            <span className="text-[10px] text-slate-500 mt-1 block">Leave blank to use CAGR toggle</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          {/* CAGR Toggle */}
          <div className="flex items-center space-x-2 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2">
            <input
              type="checkbox"
              id="cagr-toggle"
              checked={useCagrSuggestion}
              onChange={(e) => setUseCagrSuggestion(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded bg-slate-900 border-slate-700 focus:ring-blue-500"
            />
            <label htmlFor="cagr-toggle" className="text-xs text-slate-300 cursor-pointer select-none">
              Use 3-Yr Historical Revenue CAGR as growth suggestion
            </label>
          </div>

          {/* Manual Cost of Debt */}
          <div>
            <input
              type="number"
              step="0.1"
              placeholder="Manual Pre-Tax Cost of Debt (%) e.g. 4.5"
              value={manualKdStr}
              onChange={(e) => setManualKdStr(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-blue-500 font-mono"
            />
            <span className="text-[10px] text-slate-500 mt-1 block">Optional pre-tax debt yield override</span>
          </div>

          {/* Macro Rates */}
          <div className="flex items-center space-x-2">
            <div className="flex-1">
              <input
                type="number"
                step="0.05"
                value={rfPct}
                onChange={(e) => setRfPct(parseFloat(e.target.value) || 0.0)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-2 text-xs text-slate-100 font-mono"
                placeholder="Rf %"
              />
              <span className="text-[10px] text-slate-500 block">Risk-Free Rate %</span>
            </div>
            <div className="flex-1">
              <input
                type="number"
                step="0.05"
                value={erpPct}
                onChange={(e) => setErpPct(parseFloat(e.target.value) || 0.0)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-2 text-xs text-slate-100 font-mono"
                placeholder="ERP %"
              />
              <span className="text-[10px] text-slate-500 block">Equity ERP %</span>
            </div>
          </div>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            disabled={isLoading}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm px-6 py-2.5 rounded-lg shadow-md transition-colors disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>{isLoading ? 'Running Valuation Engine...' : 'Run DCF Valuation'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
