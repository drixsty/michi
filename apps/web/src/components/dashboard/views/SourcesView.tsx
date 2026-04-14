'use client';

import React from 'react';
import { ConnectorsGrid } from '@/components/dashboard/ConnectorsGrid';
import { CheckCircle2, Database } from 'lucide-react';

interface SourcesViewProps {
  onImport: (e: React.ChangeEvent<HTMLInputElement>) => void;
  isAdmin: boolean;
}

export const SourcesView: React.FC<SourcesViewProps> = ({ onImport, isAdmin }) => {
  return (
    <div className="space-y-5 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div className="bg-white rounded-2xl border border-slate-100 p-6">
        <ConnectorsGrid onImport={onImport} isAdmin={isAdmin} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-6 bg-slate-50/50 rounded-2xl border border-slate-100 flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold text-slate-400 tracking-widest mb-1 text-balance">État Global</p>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-bold text-slate-900">Systèmes opérationnels</span>
            </div>
          </div>
          <CheckCircle2 className="h-5 w-5 text-emerald-500/20" />
        </div>
        <div className="p-6 bg-slate-50/50 rounded-2xl border border-slate-100 flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold text-slate-400 tracking-widest mb-1">Flux Automatiques</p>
            <p className="text-xs font-bold text-slate-900">Activés (Temps réel)</p>
          </div>
          <Database className="h-5 w-5 text-primary/20" />
        </div>
      </div>
    </div>
  );
};
