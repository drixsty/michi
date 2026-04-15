'use client';

import React from 'react';
import { ShieldCheck, Clock, TrendingUp, AlertCircle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SupplierProps {
  name: string;
  reliability: number;
  avgDelay: number;
  ltSigma: number;
  className?: string;
}

export function SupplierCard({ name, reliability, avgDelay, ltSigma, className }: SupplierProps) {
  // Score de fiabilité : 0-1 (converti en %)
  const relPct = Math.round(reliability * 100);
  
  // Couleurs sémantiques basées sur la fiabilité
  const status = relPct >= 90 ? 'stable' : relPct >= 60 ? 'warning' : 'critical';
  
  const colors = {
    stable: 'text-emerald-600 bg-emerald-50 border-emerald-100',
    warning: 'text-amber-600 bg-amber-50 border-amber-100',
    critical: 'text-destructive bg-destructive/10 border-destructive/20'
  }[status];

  return (
    <div className={cn("bg-white rounded-xl border p-4 transition-shadow hover:shadow-md", className)}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-800 tracking-tight">{name}</h3>
          <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">Performance Logistique</p>
        </div>
        <div className={cn("px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-tighter border", colors)}>
          {status === 'stable' ? 'Fiable' : status === 'warning' ? 'À surveiller' : 'Critique'}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {/* Fiabilité */}
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <ShieldCheck className="h-3 w-3" />
            <span className="text-[9px] font-bold uppercase tracking-widest">Fiabilité</span>
          </div>
          <p className={cn("text-base font-black", colors.split(' ')[0])}>{relPct}%</p>
        </div>

        {/* Retard Moyen */}
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span className="text-[9px] font-bold uppercase tracking-widest">Retard</span>
          </div>
          <p className="text-base font-black text-slate-700">+{avgDelay.toFixed(1)}j</p>
        </div>

        {/* Stabilité (Sigma) */}
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <TrendingUp className="h-3 w-3" />
            <span className="text-[9px] font-bold uppercase tracking-widest">Stabilité</span>
          </div>
          <p className="text-base font-black text-slate-700">±{ltSigma.toFixed(1)}j</p>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t flex items-center justify-between">
        <div className="flex items-center gap-1.5 group cursor-help">
          <Info className="h-3 w-3 text-slate-300 group-hover:text-primary transition-colors" />
          <span className="text-[8px] font-medium text-slate-400 group-hover:text-slate-600 transition-colors">
            Impact stock sécu : {Math.round(ltSigma * 1.645 * 10) / 10}j
          </span>
        </div>
        {ltSigma > 5 && (
          <div className="flex items-center gap-1 animate-pulse">
            <AlertCircle className="h-3 w-3 text-destructive" />
            <span className="text-[8px] font-black text-destructive uppercase">Instabilité critique</span>
          </div>
        )}
      </div>
    </div>
  );
}
