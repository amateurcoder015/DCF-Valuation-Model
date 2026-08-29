import React from 'react';
import { ValuationResponse } from '../types/valuation';
import { ShieldAlert, CheckCircle2, Info, AlertOctagon, Globe } from 'lucide-react';

interface TransparencyPanelProps {
  result: ValuationResponse;
}

export const TransparencyPanel: React.FC<TransparencyPanelProps> = ({ result }) => {
  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 shadow-lg mb-6">
      <div className="flex items-center space-x-2 pb-3 mb-4 border-b border-slate-800">
        <ShieldAlert className="w-5 h-5 text-blue-400" />
        <h3 className="text-base font-semibold text-slate-100">🔍 Assumption & Data Flag Transparency Panel</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Growth Rate Source */}
        <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
          <span className="text-xs font-semibold text-slate-300 block mb-1.5 flex items-center gap-1.5">
            <Info className="w-4 h-4 text-blue-400" /> Growth Rate Model & Precedence
          </span>
          <p className="text-xs text-slate-300 leading-relaxed">
            {result.growth_summary}
          </p>
        </div>

        {/* Tax Rate Status */}
        <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
          <span className="text-xs font-semibold text-slate-300 block mb-1.5 flex items-center gap-1.5">
            {result.tax_rate_fallback_used ? (
              <AlertOctagon className="w-4 h-4 text-amber-400" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            )}
            Effective Tax Rate Status
          </span>
          <p className="text-xs text-slate-300 leading-relaxed">
            {result.tax_rate_fallback_used
              ? '⚠️ Tax Rate: Defaulted to 0.25 (25%) statutory fallback rate due to negative or zero pretax income.'
              : '✅ Tax Rate: Derived directly from historical tax provision and pretax income.'}
          </p>
        </div>

        {/* Cost of Debt & Vintage Mismatch Status */}
        <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
          <span className="text-xs font-semibold text-slate-300 block mb-1.5 flex items-center gap-1.5">
            {result.cost_of_debt_flagged ? (
              <AlertOctagon className="w-4 h-4 text-amber-400" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            )}
            Cost of Debt & Fiscal Year Vintage Alignment
          </span>
          <p className="text-xs text-slate-300 leading-relaxed">
            {result.cost_of_debt_summary}
          </p>
        </div>

        {/* FX Currency Normalization */}
        <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
          <span className="text-xs font-semibold text-slate-300 block mb-1.5 flex items-center gap-1.5">
            <Globe className="w-4 h-4 text-blue-400" /> Foreign Exchange Currency Normalization
          </span>
          <p className="text-xs text-slate-300 leading-relaxed">
            {result.fx_rate_applied !== 1.0
              ? `🌐 FX Adjustment Applied: Financial statements converted to trading currency '${result.currency}' using multiplier ${result.fx_rate_applied}.`
              : `✅ Financial statement currency matches trading currency (${result.currency}).`}
          </p>
        </div>
      </div>

      {/* Active Model Warnings List */}
      {result.warnings && result.warnings.length > 0 && (
        <div className="mt-4 p-4 rounded-lg bg-amber-950/30 border border-amber-800/40">
          <span className="text-xs font-semibold text-amber-300 block mb-2 flex items-center gap-1.5">
            <AlertOctagon className="w-4 h-4 text-amber-400" /> Active Model Warnings ({result.warnings.length})
          </span>
          <ul className="space-y-1.5 text-xs text-amber-200/90 list-disc list-inside">
            {result.warnings.map((w, idx) => (
              <li key={idx} className="leading-relaxed">{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
