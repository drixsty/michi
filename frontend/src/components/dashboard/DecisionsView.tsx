'use client';

import React, { useState, useMemo } from 'react';
import { useQuery, gql } from '@apollo/client';
import { 
  Wallet, 
  Euro, 
  AlertTriangle, 
  Clock, 
  ArrowRight,
  LayoutDashboard,
  Calendar,
  Activity
} from 'lucide-react';
import { 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  Cell,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Line,
  ComposedChart
} from 'recharts';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { LoadingState } from '@/components/ui/LoadingState';
import { ProductQuickView } from '@/components/dashboard/ProductQuickView';
import { RisksReportPanel } from '@/components/dashboard/RisksReportPanel';
import { CustomSelect } from '@/components/ui/CustomSelect';

const GET_FINANCIAL_OVERVIEW = gql`
  query GetFinancialOverview {
    financialOverview {
      kpis {
        inventoryValueCost
        inventoryValueSale
        revenueAtRisk
        stockCoverageAvgDays
        currency
        isMutualized
      }
      topRisks {
        productId
        sku
        title
        riskValue
        stockoutDate
        reorderQuantity
        daysOfStock
        runRate
        supplierId
        sourcePlatform
        costPrice
        salePrice
      }
      totalRunRate
      totalStock
      healthScore
      message
    }
  }
`;

// ── Stat Card (aligned with StatsOverview design system) ────
function StatCard({ label, value, sub, accent, icon: Icon }: {
  label: string; value: string; sub?: string; accent?: string; icon: React.ElementType;
}) {
  return (
    <div className="bg-white rounded-xl border border-border p-3.5 transition-shadow hover:shadow-sm">
      <div className="flex items-center gap-2.5 mb-2">
        <div className={cn("p-1.5 rounded-lg", accent === 'destructive' ? 'bg-destructive/10 text-destructive' : accent === 'emerald' ? 'bg-emerald-50 text-emerald-600' : accent === 'amber' ? 'bg-amber-50 text-amber-600' : 'bg-primary/10 text-primary')}>
          <Icon className="h-3.5 w-3.5" />
        </div>
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
      </div>
      <p className={cn("text-xl font-semibold tracking-tight", accent === 'destructive' ? 'text-destructive' : 'text-foreground')}>{value}</p>
      {sub && <p className="text-[10px] text-muted-foreground mt-1 font-medium italic leading-tight">{sub}</p>}
    </div>
  );
}

// ── Health Score Gauge ───────────────────────────────────────
function HealthGauge({ score }: { score: number }) {
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  
  const config = score >= 80 ? { color: 'hsl(var(--primary))', label: 'Optimal', className: 'text-primary bg-primary/10' }
    : score >= 60 ? { color: '#3b82f6', label: 'Sain', className: 'text-blue-600 bg-blue-50' }
    : score >= 40 ? { color: 'hsl(var(--ring))', label: 'Tendu', className: 'text-amber-600 bg-amber-50' }
    : { color: 'hsl(var(--destructive))', label: 'Critique', className: 'text-destructive bg-destructive/10' };

  return (
    <div className="flex items-center gap-3">
      <div className="relative w-[76px] h-[76px] shrink-0">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r={radius} fill="none" stroke="hsl(var(--border))" strokeWidth="5" />
          <motion.circle cx="40" cy="40" r={radius} fill="none" stroke={config.color}
            strokeWidth="5" strokeLinecap="round" strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }} animate={{ strokeDashoffset: circumference - progress }}
            transition={{ duration: 1.2, ease: "easeOut" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-lg font-bold text-foreground">{score}</span>
        </div>
      </div>
      <div>
        <p className="text-xs font-medium text-muted-foreground">Santé inventaire</p>
        <span className={cn("text-[10px] font-semibold px-2 py-0.5 rounded-full mt-1 inline-block", config.className)}>{config.label}</span>
      </div>
    </div>
  );
}

// ── ABC Pareto Chart ────────────────────────────────────────
function ABCParetoChart({ risks }: { risks: any[] }) {
  const abcData = useMemo(() => {
    const sorted = [...risks]
      .map(r => ({ ...r, annualValue: (r.salePrice || 0) * (r.runRate || 0) * 365 }))
      .sort((a, b) => b.annualValue - a.annualValue);
    const total = sorted.reduce((acc, r) => acc + r.annualValue, 0) || 1;
    let cumulative = 0;
    return sorted.slice(0, 12).map((r) => {
      cumulative += r.annualValue;
      const pct = (cumulative / total) * 100;
      return {
        name: r.sku.length > 6 ? r.sku.substring(0, 6) + '…' : r.sku,
        value: Math.round(r.annualValue),
        cumulative: Math.round(pct),
        category: pct <= 80 ? 'A' : pct <= 95 ? 'B' : 'C',
      };
    });
  }, [risks]);
  const colors = { A: 'hsl(262, 83%, 58%)', B: '#f59e0b', C: '#cbd5e1' };

  return (
    <div className="h-44 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={abcData} margin={{ top: 0, right: 4, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
          <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 7, fill: 'hsl(var(--muted-foreground))' }} interval={0} angle={-35} textAnchor="end" height={35} />
          <YAxis yAxisId="left" hide />
          <YAxis yAxisId="right" orientation="right" axisLine={false} tickLine={false} tick={{ fontSize: 7, fill: 'hsl(var(--muted-foreground))' }} domain={[0, 100]} unit="%" />
          <RechartsTooltip contentStyle={{ borderRadius: 'var(--radius)', border: '1px solid hsl(var(--border))', boxShadow: 'none', fontSize: '10px' }} />
          <Bar yAxisId="left" dataKey="value" radius={[3, 3, 0, 0]}>
            {abcData.map((entry, i) => (<Cell key={i} fill={colors[entry.category as keyof typeof colors]} fillOpacity={0.85} />))}
          </Bar>
          <Line yAxisId="right" type="monotone" dataKey="cumulative" stroke="hsl(var(--destructive))" strokeWidth={1.5} dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Capital by Channel Donut ────────────────────────────────
function ChannelDonut({ risks }: { risks: any[] }) {
  const channelData = useMemo(() => {
    const map: Record<string, number> = {};
    risks.forEach(r => {
      const p = r.sourcePlatform || 'custom';
      map[p] = (map[p] || 0) + (r.costPrice || 0) * Math.max(1, Math.round(r.runRate || 0));
    });
    return Object.entries(map).map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1), value: Math.round(value)
    })).sort((a, b) => b.value - a.value);
  }, [risks]);
  const total = channelData.reduce((acc, d) => acc + d.value, 0) || 1;
  const COLORS = ['hsl(262, 83%, 58%)', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6'];

  return (
    <div className="flex items-center gap-4 w-full">
      <div className="w-[140px] h-[140px] shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={channelData} cx="50%" cy="50%" innerRadius={34} outerRadius={56}
              paddingAngle={3} dataKey="value" stroke="none">
              {channelData.map((_, i) => (<Cell key={i} fill={COLORS[i % COLORS.length]} />))}
            </Pie>
            <RechartsTooltip contentStyle={{ borderRadius: 'var(--radius)', border: '1px solid hsl(var(--border))', boxShadow: 'none', fontSize: '10px' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="flex-1 space-y-3">
        {channelData.map((entry, i) => {
          const pct = Math.round((entry.value / total) * 100);
          return (
            <div key={i} className="space-y-1">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                  <span className="text-xs font-medium text-foreground">{entry.name}</span>
                </div>
                <span className="text-xs font-semibold text-foreground">{entry.value.toLocaleString('fr-FR')}€</span>
              </div>
              <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: COLORS[i % COLORS.length] }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function DecisionsView() {
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [showReport, setShowReport] = useState(false);
  const [period, setPeriod] = useState('all');
  const [channel, setChannel] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const { data, loading } = useQuery(GET_FINANCIAL_OVERVIEW, { pollInterval: 30000 });

  const overview = data?.financialOverview;
  const kpis = overview?.kpis;
  const allRisks = overview?.topRisks || [];
  const totalRunRate = overview?.totalRunRate || 0;
  const totalStock = overview?.totalStock || 0;
  const healthScore = overview?.healthScore || 0;
  const currency = kpis?.currency || '€';
  const platforms = [...new Set(allRisks.map((r: any) => r.sourcePlatform).filter(Boolean))] as string[];

  const risks = useMemo(() => allRisks.filter((r: any) => {
    if (channel !== 'all' && r.sourcePlatform !== channel) return false;
    if (statusFilter === 'critical' && r.daysOfStock >= 14) return false;
    if (statusFilter === 'tense' && (r.daysOfStock < 14 || r.daysOfStock >= 30)) return false;
    if (statusFilter === 'healthy' && r.daysOfStock < 30) return false;
    if (period !== 'all') {
      const days = parseInt(period);
      if (r.stockoutDate) {
        const stockoutMs = new Date(r.stockoutDate).getTime() - Date.now();
        if (stockoutMs > days * 86400000) return false;
      } else if (r.riskValue === 0) return false;
    }
    return true;
  }), [allRisks, channel, statusFilter, period]);

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(val).replace('€', currency);

  const projectionData = useMemo(() => {
    if (totalStock <= 0 || totalRunRate <= 0) return [];
    const costPerUnit = kpis?.inventoryValueCost / totalStock || 0;
    const pts = [];
    for (let d = 0; d <= 90; d += 5) {
      pts.push({ day: `J+${d}`, value: Math.round(Math.max(0, totalStock - totalRunRate * d) * costPerUnit) });
    }
    return pts;
  }, [totalStock, totalRunRate, kpis]);

  const reorderThreshold = useMemo(() => {
    const avgLead = 14;
    return totalRunRate * avgLead * (kpis?.inventoryValueCost / Math.max(1, totalStock) || 0);
  }, [totalRunRate, totalStock, kpis]);

  if (loading) return <LoadingState fullScreen message="Génération des indicateurs stratégiques..." />;

  const periods = [
    { value: 'all', label: 'Tout' },
    { value: '7', label: '7j' },
    { value: '30', label: '30j' },
    { value: '90', label: '90j' },
  ];
  const statuses = [
    { value: 'all', label: 'Tous' },
    { value: 'critical', label: 'Critique' },
    { value: 'tense', label: 'Tendu' },
    { value: 'healthy', label: 'Sain' },
  ];

  const risksWithValue = risks.filter((r: any) => r.riskValue > 0);

  return (
    <div className="space-y-5 animate-in fade-in duration-500">
      {/* Filters — using standard michi-select and michi-card styles */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="inline-flex items-center rounded-lg border border-input bg-background p-0.5">
          {periods.map(p => (
            <button key={p.value} onClick={() => setPeriod(p.value)}
              className={cn("px-3 py-1.5 text-xs font-medium rounded-md transition-colors",
                period === p.value ? "bg-accent text-accent-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              )}>{p.label}</button>
          ))}
        </div>

        <CustomSelect 
          options={[
            { value: 'all', label: 'Tous les canaux' },
            ...platforms.map(p => ({ value: p, label: p.charAt(0).toUpperCase() + p.slice(1) }))
          ]}
          value={channel}
          onChange={setChannel}
          className="h-8"
        />

        <div className="inline-flex items-center rounded-lg border border-input bg-background p-0.5">
          {statuses.map(s => (
            <button key={s.value} onClick={() => setStatusFilter(s.value)}
              className={cn("px-3 py-1.5 text-xs font-medium rounded-md transition-colors",
                statusFilter === s.value
                  ? s.value === 'critical' ? "bg-destructive/10 text-destructive shadow-sm"
                  : s.value === 'tense' ? "bg-amber-50 text-amber-600 shadow-sm"
                  : s.value === 'healthy' ? "bg-emerald-50 text-emerald-600 shadow-sm"
                  : "bg-accent text-accent-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
              )}>{s.label}</button>
          ))}
        </div>
      </div>

      {/* KPIs Row — compact 2-column layout + health gauge */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <StatCard icon={Wallet} label="Capital immobilisé" value={formatCurrency(kpis?.inventoryValueCost || 0)} accent="primary" />
        <StatCard icon={Euro} label="Valeur marchande" value={formatCurrency(kpis?.inventoryValueSale || 0)} accent="emerald" />
        <StatCard icon={AlertTriangle} label="Revenue at risk" value={formatCurrency(kpis?.revenueAtRisk || 0)} sub="Perte estimée (30j)" accent="destructive" />
        <StatCard icon={Clock} label="Couverture moyenne" value={`${kpis?.stockCoverageAvgDays || 0} jours`} accent="amber" />
        <div className="bg-white rounded-xl border border-border p-3.5 flex items-center justify-center transition-shadow hover:shadow-sm">
          <HealthGauge score={healthScore} />
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left Column — Charts */}
        <div className="lg:col-span-2 space-y-5">
          {/* Projection Chart */}
          <section className="bg-white rounded-xl border border-border p-4 transition-shadow hover:shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-sm font-semibold text-foreground">Projection du stock</h2>
                <p className="text-[10px] text-muted-foreground font-medium">Run rate IA : {totalRunRate.toFixed(1)} unités/jour.</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5"><div className="w-2 h-0.5 bg-primary rounded-full" /><span className="text-[9px] font-medium text-muted-foreground">Stock</span></div>
                <div className="flex items-center gap-1.5"><div className="w-4 h-0 border-t border-dashed border-destructive" /><span className="text-[9px] font-medium text-muted-foreground">Seuil</span></div>
              </div>
            </div>
            <div className="h-48 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={projectionData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorProjection" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(262, 83%, 58%)" stopOpacity={0.12}/>
                      <stop offset="95%" stopColor="hsl(262, 83%, 58%)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fontSize: 9, fill: 'hsl(var(--muted-foreground))'}} />
                  <YAxis hide />
                  <RechartsTooltip contentStyle={{ borderRadius: 'var(--radius)', border: '1px solid hsl(var(--border))', boxShadow: 'none', fontSize: '10px' }} />
                  <Area type="monotone" dataKey="value" stroke="hsl(var(--primary))" strokeWidth={2} fillOpacity={1} fill="url(#colorProjection)" />
                  <Area type="monotone" dataKey={() => Math.round(reorderThreshold)} stroke="hsl(var(--destructive))" strokeWidth={1} strokeDasharray="6 4" fillOpacity={0} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* ABC + Channel — side by side, compact */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <section className="bg-white rounded-xl border border-border p-4 transition-shadow hover:shadow-sm">
              <h2 className="text-sm font-semibold text-foreground mb-1">Analyse ABC</h2>
              <p className="text-[10px] text-muted-foreground font-medium mb-3">Classement par valeur annualisée.</p>
              <ABCParetoChart risks={risks} />
              <div className="flex items-center gap-3 mt-2 justify-center">
                {[{l:'A (80%)', c:'hsl(262, 83%, 58%)'}, {l:'B (15%)', c:'#f59e0b'}, {l:'C (5%)', c:'#cbd5e1'}].map(x => (
                  <div key={x.l} className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-sm" style={{backgroundColor: x.c}} />
                    <span className="text-[9px] font-medium text-muted-foreground">{x.l}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="bg-white rounded-xl border border-border p-4 flex flex-col transition-shadow hover:shadow-sm">
              <h2 className="text-sm font-semibold text-foreground mb-1">Capital par canal</h2>
              <p className="text-[10px] text-muted-foreground font-medium mb-3">Répartition par plateforme.</p>
              <div className="flex-1 flex items-center">
                <ChannelDonut risks={risks} />
              </div>
            </section>
          </div>
        </div>

        {/* Right Column — Risks */}
        <div>
          <section className="bg-white rounded-xl border border-border p-4 flex flex-col h-full transition-shadow hover:shadow-sm">
            <h2 className="text-xs font-medium text-muted-foreground mb-3 flex items-center gap-2">
              <AlertTriangle className="h-3 w-3 text-destructive" />
              Risques financiers ({risksWithValue.length})
            </h2>

            <div className="space-y-2.5 flex-1 max-h-[520px] overflow-y-auto no-scrollbar">
              {risksWithValue.length > 0 ? risksWithValue.slice(0, 10).map((risk: any, i: number) => (
                <div key={i} onClick={() => setSelectedProductId(risk.productId)}
                  className="group p-3 bg-background rounded-lg border border-transparent hover:border-border transition-all cursor-pointer"
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wide">{risk.sku}</span>
                    <span className="text-[10px] font-bold text-destructive">{formatCurrency(risk.riskValue)}</span>
                  </div>
                  <h4 className="text-xs font-semibold text-foreground mb-1.5 group-hover:text-primary transition-colors truncate">{risk.title}</h4>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1 text-[9px] font-medium text-muted-foreground">
                      <Calendar className="h-2.5 w-2.5" />
                      {risk.stockoutDate ? new Date(risk.stockoutDate).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }) : '—'}
                    </div>
                    {risk.reorderQuantity > 0 && (
                      <span className="text-[8px] font-semibold text-primary bg-primary/10 px-1.5 py-0.5 rounded">
                        Cmd: {risk.reorderQuantity} u.
                      </span>
                    )}
                  </div>
                </div>
              )) : (
                <div className="flex flex-col items-center justify-center text-center py-12 opacity-30">
                  <LayoutDashboard className="h-10 w-10 mb-3" />
                  <p className="text-xs font-medium">Aucun risque identifié</p>
                </div>
              )}
            </div>

            <button onClick={() => setShowReport(true)}
              className="mt-3 w-full inline-flex h-9 items-center justify-center rounded-lg border border-input bg-background text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground gap-2"
            >
              Rapport complet <ArrowRight className="h-3 w-3" />
            </button>
          </section>
        </div>
      </div>

      {/* Side Panels */}
      <ProductQuickView productId={selectedProductId} onClose={() => setSelectedProductId(null)} />
      <RisksReportPanel isOpen={showReport} onClose={() => setShowReport(false)}
        risks={risksWithValue} formatCurrency={formatCurrency}
        onSelectProduct={(id) => { setShowReport(false); setSelectedProductId(id); }}
      />
    </div>
  );
}
