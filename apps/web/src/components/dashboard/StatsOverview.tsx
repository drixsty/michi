'use client';

import React from 'react';
import { useTranslations } from 'next-intl';

interface StatProps {
  label: string;
  value: number | string;
  sub: string;
  units: string;
  accent?: string;
}

function StatCard({ label, value, sub, units, accent }: StatProps) {
  return (
    <div className="bg-white rounded-xl border border-border p-4 transition-shadow hover:shadow-sm">
      <p className="text-xs font-medium text-muted-foreground mb-0.5">{label}</p>
      <div className="flex items-baseline gap-1.5">
        <span className={`text-2xl font-semibold tracking-tight ${accent || 'text-foreground'}`}>{value}</span>
        <span className="text-xs text-muted-foreground font-medium">{units}</span>
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
  financial?: {
    inventoryValueCost: number;
    revenueAtRisk: number;
    currency: string;
  };
}

export function StatsOverview({ stats, financial }: StatsOverviewProps) {
  const t = useTranslations('stats');

  const formatValue = (val: number) => {
    if (!financial) return val;
    return new Intl.NumberFormat(undefined, { 
      style: 'currency', 
      currency: 'EUR',
      maximumFractionDigits: 0
    }).format(val).replace('€', financial.currency);
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
      <StatCard
        label={t('totalProducts')}
        value={stats.total}
        sub={t('totalProductsSub')}
        units={t('units')}
      />
      {financial ? (
        <StatCard
          label={t('inventoryValue')}
          value={formatValue(financial.inventoryValueCost)}
          sub={t('inventoryValueSub')}
          units=""
          accent="text-primary"
        />
      ) : (
        <StatCard
          label={t('criticalStockouts')}
          value={stats.urgent}
          sub={t('criticalStockoutsSub')}
          units={t('units')}
          accent="text-red-500"
        />
      )}
      {financial ? (
        <StatCard
          label={t('revenueAtRisk')}
          value={formatValue(financial.revenueAtRisk)}
          sub={t('revenueAtRiskSub')}
          units=""
          accent="text-red-500"
        />
      ) : (
        <StatCard
          label={t('toWatch')}
          value={stats.warning}
          sub={t('toWatchSub')}
          units={t('units')}
          accent="text-amber-500"
        />
      )}
      <StatCard
        label={t('healthy')}
        value={stats.healthy}
        sub={t('healthySub')}
        units={t('units')}
        accent="text-emerald-500"
      />
    </div>
  );
}
