'use client';

import React, { useEffect, useState } from 'react';
import { ShieldAlert, RefreshCw, ClipboardCopy, CheckCircle, ChevronDown, ChevronUp, Mail } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorBoundary({ error, reset }: ErrorProps) {
  const [copied, setCopied] = useState(false);
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  const [flowId, setFlowId] = useState<string | null>(null);

  useEffect(() => {
    // Read the last error flowId stored by the Apollo client
    if (typeof window !== 'undefined') {
      const stored = sessionStorage.getItem('michi_last_error_flow_id');
      if (stored) {
        setFlowId(stored);
      }
    }
    console.error('[ErrorBoundary] Captured:', error);
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
      flowId: flowId || 'N/A'
    };

    navigator.clipboard.writeText(JSON.stringify(diagInfo, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6 font-sans relative overflow-hidden">
      {/* Background ambient light */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-xl bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-8 shadow-2xl relative z-10 space-y-6"
      >
        <div className="flex flex-col items-center text-center space-y-4">
          <div className="w-16 h-16 bg-red-950/40 border border-red-500/20 rounded-2xl flex items-center justify-center text-red-500 shadow-[0_0_30px_rgba(239,68,68,0.1)]">
            <ShieldAlert className="h-8 w-8" />
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl font-extrabold tracking-tight text-white sm:text-3xl">
              Une erreur est survenue
            </h1>
            <p className="text-sm text-slate-400 max-w-sm mx-auto">
              L'application a rencontré une anomalie inattendue. Nos équipes sont alertées.
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={() => reset()}
            className="flex-1 py-3.5 px-4 bg-primary text-white font-bold text-xs rounded-xl flex items-center justify-center gap-2 hover:bg-primary/95 transition-all shadow-lg shadow-primary/20 active:scale-95 focus:ring-0 focus:outline-none"
          >
            <RefreshCw className="h-4 w-4 animate-spin-slow" />
            Réessayer la page
          </button>
          
          <button
            onClick={handleCopyDiagnostics}
            className="flex-1 py-3.5 px-4 bg-slate-800 hover:bg-slate-700/80 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-2 transition-all active:scale-95 focus:ring-0 focus:outline-none"
          >
            {copied ? (
              <>
                <CheckCircle className="h-4 w-4 text-emerald-400" />
                <span className="text-emerald-400">Diagnostic copié !</span>
              </>
            ) : (
              <>
                <ClipboardCopy className="h-4 w-4 text-slate-400" />
                Copier le diagnostic
              </>
            )}
          </button>
        </div>

        {/* Collapsible Diagnostics Accordion */}
        <div className="border border-slate-800/80 rounded-xl bg-slate-950/50 overflow-hidden">
          <button
            onClick={() => setShowDiagnostics(!showDiagnostics)}
            className="w-full p-4 flex items-center justify-between text-xs font-semibold text-slate-400 hover:text-white transition-colors"
          >
            <span>Informations de diagnostic pour le support</span>
            {showDiagnostics ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>

          <AnimatePresence>
            {showDiagnostics && (
              <motion.div
                initial={{ height: 0 }}
                animate={{ height: 'auto' }}
                exit={{ height: 0 }}
                className="overflow-hidden border-t border-slate-800/80"
              >
                <div className="p-4 space-y-3 font-mono text-[10px] text-slate-400 select-all leading-normal bg-slate-950/80">
                  <div className="grid grid-cols-3 gap-1">
                    <span className="text-slate-500 font-bold">Corrélation ID :</span>
                    <span className="col-span-2 text-slate-300 font-semibold break-all">{flowId || 'N/A'}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-1">
                    <span className="text-slate-500 font-bold">Erreur :</span>
                    <span className="col-span-2 text-red-400 break-all">{error.message || 'Unknown error'}</span>
                  </div>
                  {error.digest && (
                    <div className="grid grid-cols-3 gap-1">
                      <span className="text-slate-500 font-bold">Digest Next.js :</span>
                      <span className="col-span-2 text-slate-300 break-all">{error.digest}</span>
                    </div>
                  )}
                  <div className="grid grid-cols-3 gap-1">
                    <span className="text-slate-500 font-bold">URL :</span>
                    <span className="col-span-2 text-slate-300 break-all">{typeof window !== 'undefined' ? window.location.href : ''}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-1">
                    <span className="text-slate-500 font-bold">Horodatage :</span>
                    <span className="col-span-2 text-slate-300">{new Date().toISOString()}</span>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Contact Support Direct link */}
        <div className="text-center pt-2">
          <a
            href={`mailto:support@michi-app.com?subject=Rapport%20d%27erreur%20Michi&body=Bonjour%20l%27equipe%20Support%2C%0A%0AMon%20application%20a%20rencontre%20un%20dysfonctionnement.%20Voici%20les%20details%20de%20diagnostic%20copie%20depuis%20mon%20ecran%20%3A%0A%0A%5BColler%20le%20diagnostic%20ici%5D`}
            className="inline-flex items-center gap-2 text-xs font-semibold text-primary hover:text-primary/80 transition-colors"
          >
            <Mail className="h-3.5 w-3.5" />
            Contacter le support par email
          </a>
        </div>
      </motion.div>
    </div>
  );
}
