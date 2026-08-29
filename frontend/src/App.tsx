import React, { useState } from 'react';
import { ValuationRequest, ValuationResponse } from './types/valuation';
import { fetchValuation } from './api/valuation';
import { Navbar } from './components/Navbar';
import { InputPanel } from './components/InputPanel';
import { HeadlineCard } from './components/HeadlineCard';
import { TransparencyPanel } from './components/TransparencyPanel';
import { WaterfallBreakdown } from './components/WaterfallBreakdown';
import { DataFreshnessFooter } from './components/DataFreshnessFooter';
import { AlertCircle, AlertTriangle, Loader2, Sparkles } from 'lucide-react';

export function App() {
  const [result, setResult] = useState<ValuationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSectorError, setIsSectorError] = useState<boolean>(false);

  const handleRunValuation = async (request: ValuationRequest) => {
    setIsLoading(true);
    setErrorMsg(null);
    setIsSectorError(false);

    try {
      const data = await fetchValuation(request);
      setResult(data);
    } catch (err: any) {
      const msg = err.message || 'An unexpected valuation failure occurred.';
      setErrorMsg(msg);
      if (msg.includes('financial sector') || msg.includes('UnsupportedSectorError')) {
        setIsSectorError(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 flex-1 w-full">
        {/* Input Controls Panel */}
        <InputPanel onRunValuation={handleRunValuation} isLoading={isLoading} />

        {/* Loading Indicator */}
        {isLoading && (
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-12 text-center my-6 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
            <h3 className="text-base font-semibold text-slate-200">Executing DCF Valuation Engine</h3>
            <p className="text-xs text-slate-400 max-w-md">
              Fetching real historical statement fundamentals and market prices via yFinance, calculating un-levered cash flows, WACC, and perpetual terminal value...
            </p>
          </div>
        )}

        {/* Error Handling Callouts */}
        {errorMsg && !isLoading && (
          <div className="my-6">
            {isSectorError ? (
              <div className="bg-amber-950/40 border border-amber-800/80 rounded-xl p-6 text-amber-200 flex items-start space-x-4">
                <AlertTriangle className="w-6 h-6 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-base font-bold text-amber-300 mb-1">🏦 Unsupported Financial Sector Issuer</h4>
                  <p className="text-xs leading-relaxed text-amber-200/90">{errorMsg}</p>
                  <p className="text-[11px] text-amber-400/80 mt-2">
                    Standard FCFF DCF models are not appropriate for banks or insurers because interest income and debt obligations represent core operational inventory.
                  </p>
                </div>
              </div>
            ) : (
              <div className="bg-rose-950/40 border border-rose-800/80 rounded-xl p-6 text-rose-200 flex items-start space-x-4">
                <AlertCircle className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-base font-bold text-rose-300 mb-1">❌ Valuation Execution / Data Input Error</h4>
                  <p className="text-xs font-mono leading-relaxed bg-slate-950/60 p-3 rounded border border-rose-900/40 text-rose-300 mt-2">
                    {errorMsg}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty Initial State Prompt */}
        {!result && !isLoading && !errorMsg && (
          <div className="bg-slate-900/40 border border-dashed border-slate-800 rounded-xl p-12 text-center my-6">
            <div className="w-12 h-12 rounded-full bg-blue-600/10 text-blue-400 flex items-center justify-center mx-auto mb-3 border border-blue-500/20">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-200 mb-1">Ready for Valuation Execution</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Configure ticker symbol and macro assumptions above, then click <strong>Run DCF Valuation</strong> to generate intrinsic value metrics and complete assumption transparency.
            </p>
          </div>
        )}

        {/* Successful Valuation Results */}
        {result && !isLoading && (
          <div>
            {/* 3. Headline Result Card */}
            <HeadlineCard result={result} />

            {/* 4. Assumption & Flag Transparency Panel */}
            <TransparencyPanel result={result} />

            {/* 5. Detail & Valuation Waterfall */}
            <WaterfallBreakdown result={result} />

            {/* 6. Data Freshness */}
            <DataFreshnessFooter timestamp={result.data_retrieved_at} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
