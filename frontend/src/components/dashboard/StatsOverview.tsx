'use client';

import React from 'react';

interface StatProps {
  label: string;
  value: number | string;
  sub: string;
  accent?: string;
}

function StatCard({ label, value, sub, accent }: StatProps) {
  return (
    <div className="bg-white rounded-xl border border-border p-4 transition-shadow hover:shadow-sm">
      <p className="text-xs font-medium text-muted-foreground mb-0.5">{label}</p>
      <div className="flex items-baseline gap-1.5">
        <span className={`text-2xl font-semibold tracking-tight ${accent || 'text-foreground'}`}>{value}</span>
        <span className="text-xs text-muted-foreground font-medium">Unités</span>
      </div>
      <p className="text-[10px] text-muted-foreground mt-1 font-medium italic leading-tight">
        {sub}
      </p>
    </div>
  );
}

interface StatsOverviewProps {
  stats: {
    total: number;
    urgent: number;
    warning: number;
    healthy: number;
  };
}

export function StatsOverview({ stats }: StatsOverviewProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
      <StatCard 
        label="Total produits" 
        value={stats.total} 
        sub="Inventaire complet" 
      />
      <StatCard 
        label="Ruptures critiques" 
        value={stats.urgent} 
        sub="Rupture immédiate" 
        accent="text-red-500" 
      />
      <StatCard 
        label="À surveiller" 
        value={stats.warning} 
        sub="Stock < 20u." 
        accent="text-amber-500" 
      />
      <StatCard 
        label="Sains" 
        value={stats.healthy} 
        sub="Stock optimisé" 
        accent="text-emerald-500" 
      />
    </div>
  );
}
