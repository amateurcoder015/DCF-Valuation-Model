import React from 'react';
import { Clock } from 'lucide-react';

interface DataFreshnessFooterProps {
  timestamp: string;
}

export const DataFreshnessFooter: React.FC<DataFreshnessFooterProps> = ({ timestamp }) => {
  return (
    <footer className="mt-8 pt-4 pb-8 border-t border-slate-800 text-center text-xs text-slate-500">
      <div className="flex items-center justify-center space-x-1.5 mb-1">
        <Clock className="w-3.5 h-3.5 text-slate-400" />
        <span>Data Freshness Timestamp: <span className="font-mono text-slate-400">{new Date(timestamp).toUTCString()}</span></span>
      </div>
      <p className="text-[11px] opacity-70">
        DCF Valuation Model Engine • FastAPI + React TypeScript + Tailwind CSS
      </p>
    </footer>
  );
};
