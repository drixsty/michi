'use client';

import React from 'react';
import { Bell, BellOff, AlertCircle, AlertTriangle, Package, ExternalLink, Trash2, Eye } from 'lucide-react';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { StatsOverview } from '@/components/dashboard/StatsOverview';
import type { OmnichannelProduct } from '@michi/types';
import { useTranslations } from 'next-intl';

interface OverviewViewProps {
  stats: {
    total: number;
    urgent: number;
    warning: number;
    healthy: number;
  };
  alerts: any[];
  onDeleteAlert: (id: string) => void;
  omnichannelInventory: OmnichannelProduct[];
  financialData?: {
    inventoryValueCost: number;
    revenueAtRisk: number;
    currency: string;
  };
  onProductClick: (id: string) => void;
  onOpenInventory: () => void;
  onOpenNotifications: () => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  stats,
  alerts,
  onDeleteAlert,
  omnichannelInventory,
  financialData,
  onProductClick,
  onOpenInventory,
  onOpenNotifications
}) => {
  const t = useTranslations('overview');

  return (
    <div className="space-y-5 animate-in fade-in duration-500">
      <StatsOverview stats={stats} financial={financialData} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Recent Alerts */}
        <div className="bg-white rounded-xl border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold">{t('recentAlerts')}</h3>
            <div className="p-1.5 bg-primary/5 rounded-full">
              <Bell className="h-4 w-4 text-primary" />
            </div>
          </div>
          <div className="space-y-1">
            {(!alerts || alerts.length === 0) ? (
              <div className="flex flex-col items-center justify-center py-10 text-center min-h-[160px]">
                <div className="p-3 bg-slate-50 rounded-full mb-3">
                  <BellOff className="h-6 w-6 text-slate-300" />
                </div>
                <p className="text-[10px] font-bold text-slate-400 tracking-widest mb-1 text-balance">{t('emptyTitle')}</p>
                <p className="text-[10px] text-slate-300 italic">{t('noAlerts')}</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-50">
                {alerts.slice(0, 5).map((a: any) => (
                  <div
                    key={`alert-${a.id}`}
                    className="flex gap-3 items-center px-2 py-3 transition-all group relative cursor-pointer hover:bg-slate-50 rounded-lg"
                  >
                    <div className={cn(
                      "h-8 w-8 rounded-full flex items-center justify-center shrink-0",
                      (a.type === 'CRITICAL_STOCK' || a.type === 'STOCKOUT_CRITICAL') ? "bg-white text-red-500 shadow-sm" :
                        (a.type === 'STOCKOUT_RISK' || a.type === 'STOCKOUT_RISK_HIGH') ? "bg-white text-orange-500 shadow-sm" :
                          a.type === 'STOCKOUT_WARNING' ? "bg-white text-amber-500 shadow-sm" :
                            "bg-slate-50 text-slate-400"
                    )}>
                      {(a.type === 'CRITICAL_STOCK' || a.type === 'STOCKOUT_CRITICAL') ? <AlertTriangle className="h-4 w-4" /> :
                        (a.type === 'STOCKOUT_RISK' || a.type === 'STOCKOUT_RISK_HIGH') ? <AlertCircle className="h-4 w-4" /> :
                          a.type === 'STOCKOUT_WARNING' ? <Bell className="h-4 w-4" /> :
                            <AlertCircle className="h-4 w-4" />}
                    </div>

                    <div className="flex-1 min-w-0 pr-16">
                      <p className="text-[10px] text-slate-400 mb-0.5">
                        {format(new Date(a.createdAt), 'dd MMM HH:mm', { locale: fr })}
                      </p>
                      <p className="text-xs font-medium text-slate-700 leading-snug truncate">
                        {a.message.replace(/^(alerte|danger|attention)\s*:\s*/i, '')}
                      </p>
                    </div>

                    <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                      <Link
                        href={`/dashboard/product/${a.productId}`}
                        className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-400 hover:text-primary transition-all shadow-sm"
                        title={t('open')}
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </Link>
                      <button
                        onClick={() => onDeleteAlert(a.id)}
                        className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-400 hover:text-red-500 transition-all shadow-sm"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}

                <div className="pt-2 px-2">
                  <button
                    onClick={onOpenNotifications}
                    className="w-full py-2 text-[10px] font-bold text-primary tracking-widest bg-primary/5 hover:bg-primary/10 rounded-lg transition-all"
                  >
                    {t('seeAllAlerts')}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Optimized Stock */}
        <div className="bg-white rounded-xl border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold">{t('optimizedStock')}</h3>
            <div className="p-1.5 bg-emerald-50 rounded-full">
              <Package className="h-4 w-4 text-emerald-600" />
            </div>
          </div>

          <div className="space-y-1">
            {(!omnichannelInventory || omnichannelInventory.length === 0) ? (
              <div className="flex flex-col items-center justify-center py-10 text-center min-h-[160px]">
                <div className="p-3 bg-slate-50 rounded-full mb-3">
                  <Package className="h-6 w-6 text-slate-300" />
                </div>
                <p className="text-[10px] font-bold text-slate-400 tracking-widest mb-1">{t('emptyTitle')}</p>
                <p className="text-[10px] text-slate-300 italic">{t('noProducts')}</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-50">
                {omnichannelInventory.slice(0, 5).map((p: any) => (
                  <div
                    key={`prod-${p.id || p.sku}`}
                    onClick={() => onProductClick(p.id || p.sku)}
                    className="group relative flex items-center justify-between px-2 py-3 hover:bg-slate-50 transition-all cursor-pointer rounded-lg"
                  >
                    <div className="min-w-0 flex-1 pr-4">
                      <p className="text-xs font-medium text-foreground truncate">{p.title}</p>
                      <p className="text-[10px] text-muted-foreground">Sku: {p.sku}</p>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="text-right group-hover:opacity-0 transition-opacity">
                        <p className="text-xs font-bold text-foreground">{p.totalStock}</p>
                        <p className="text-[9px] text-muted-foreground">{t('units')}</p>
                      </div>

                      <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-all">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onProductClick(p.id || p.sku);
                          }}
                          className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-400 hover:text-primary transition-all shadow-none flex items-center gap-1.5"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          <span className="text-[10px] font-bold tracking-widest">{t('open')}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}

                <div className="pt-2 px-2">
                  <button
                    onClick={onOpenInventory}
                    className="w-full py-2 text-[10px] font-bold text-emerald-600 tracking-widest bg-emerald-50 hover:bg-emerald-100 rounded-lg transition-all"
                  >
                    {t('manageInventory')}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
