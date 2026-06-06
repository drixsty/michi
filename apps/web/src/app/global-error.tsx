'use client';

import React, { useEffect, useState } from 'react';
import { ShieldAlert, RefreshCw, ClipboardCopy, CheckCircle } from 'lucide-react';

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  const [copied, setCopied] = useState(false);
  const [flowId, setFlowId] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = sessionStorage.getItem('michi_last_error_flow_id');
      if (stored) {
        setFlowId(stored);
      }
    }
    console.error('[GlobalError] System crash captured:', error);
  }, [error]);

  const handleCopyDiagnostics = () => {
    if (typeof window === 'undefined') return;

    const diagInfo = {
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      errorMessage: error.message,
      errorStack: error.stack || 'N/A',
      digest: error.digest || 'N/A',
      flowId: flowId || 'N/A',
      level: 'GLOBAL_CRITICAL'
    };

    navigator.clipboard.writeText(JSON.stringify(diagInfo, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  return (
    <html lang="fr" className="h-full">
      <body className="h-full bg-slate-950 text-slate-100 flex items-center justify-center p-6 font-sans antialiased">
        <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl space-y-6 text-center">
          <div className="mx-auto w-16 h-16 bg-red-950/40 border border-red-500/20 rounded-2xl flex items-center justify-center text-red-500 shadow-[0_0_30px_rgba(239,68,68,0.1)]">
            <ShieldAlert className="h-8 w-8" />
          </div>

          <div className="space-y-2">
            <h1 className="text-xl font-extrabold tracking-tight text-white">
              Incident système critique
            </h1>
            <p className="text-xs text-slate-400">
              L'application a rencontré une panne majeure au niveau du chargeur principal.
            </p>
          </div>

          <div className="space-y-2">
            <button
              onClick={() => reset()}
              className="w-full py-3.5 px-4 bg-primary hover:bg-primary/90 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-2 transition-all active:scale-95 focus:ring-0 focus:outline-none"
            >
              <RefreshCw className="h-4 w-4" />
              Redémarrer l'application
            </button>
            
            <button
              onClick={handleCopyDiagnostics}
              className="w-full py-3.5 px-4 bg-slate-800 hover:bg-slate-700/80 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-2 transition-all active:scale-95 focus:ring-0 focus:outline-none"
            >
              {copied ? (
                <>
                  <CheckCircle className="h-4 w-4 text-emerald-400" />
                  <span className="text-emerald-400">Rapport copié !</span>
                </>
              ) : (
                <>
                  <ClipboardCopy className="h-4 w-4 text-slate-400" />
                  Copier le rapport système
                </>
              )}
            </button>
          </div>

          {flowId && (
            <p className="text-[9px] font-mono text-slate-500 tracking-wider">
              CORRELATION ID: {flowId}
            </p>
          )}
        </div>
      </body>
    </html>
  );
}
