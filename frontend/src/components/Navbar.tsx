import React from 'react';
import { TrendingUp, ShieldCheck } from 'lucide-react';

export const Navbar: React.FC = () => {
  return (
    <header className="bg-slate-900 border-b border-slate-800 py-4 px-6 mb-6">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-600/20 text-blue-400 rounded-lg border border-blue-500/30">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              DCF Valuation Engine <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">v1.0 Institutional</span>
            </h1>
            <p className="text-xs text-slate-400">
              Single-Stage Unlevered Free Cash Flow (FCFF) Model with Real-Time yFinance Integration
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-850 px-3 py-1.5 rounded-full border border-slate-800">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Full Assumption & Vintage Transparency Layer</span>
        </div>
      </div>
    </header>
  );
};
