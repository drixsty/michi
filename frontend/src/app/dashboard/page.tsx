'use client';

import { useQuery, useMutation, useLazyQuery } from '@apollo/client';
import { useRouter } from 'next/navigation';
import React, { useEffect, useState, useMemo } from 'react';
import { GET_ME } from '@/graphql/queries/getMe';
import { GET_PRODUCTS } from '@/graphql/queries/getProducts';
import { TRIGGER_MOCK_DATA_SYNC } from '@/graphql/mutations/syncShopify';
import { GET_DASHBOARD_STATS } from '@/graphql/queries/getDashboardStats';
import { UPDATE_PRODUCT_SETTINGS } from '@/graphql/mutations/updateProduct';
import { GET_PRODUCT_DETAIL } from '@/graphql/queries/getProductDetail';
import { GET_UNREAD_ALERTS, MARK_ALERT_AS_READ } from '@/graphql/queries/getUnreadAlerts';
import { INGEST_CSV_DATA } from '@/graphql/mutations/ingestCSV';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import SalesChart from '@/components/dashboard/SalesChart';
import OmnichannelView from '@/components/dashboard/OmnichannelView';
import OnboardingWizard from '@/components/dashboard/OnboardingWizard';
import type { Product, SyncResult, CleanedDemand } from '@/types/product';
import { ChevronDown, ChevronUp, BarChart2, Download, Upload, Bell, CheckCircle2, AlertCircle, Layers, Zap } from 'lucide-react';

type FilterTab = 'all' | 'urgent' | 'warning' | 'healthy';
type DashboardTab = 'products' | 'channels';

function getStockStatus(product: Product): 'urgent' | 'warning' | 'healthy' {
  if (product.currentStock === 0) return 'urgent';
  
  if (product.currentStock <= product.warningThreshold) return 'warning';
  
  return 'healthy';
}

const STATUS_CONFIG = {
  urgent: {
    label: 'Rupture',
    dot: 'bg-red-500',
    badge: 'bg-red-50 text-red-700 ring-1 ring-red-200',
  },
  warning: {
    label: 'Faible',
    dot: 'bg-amber-400',
    badge: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
  },
  healthy: {
    label: '',
    dot: 'bg-emerald-400',
    badge: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
  },
};

// ── Sub-components ────────────────────────────────────────────────────────────

function KpiCard({ label, value, sub, accent }: { label: string; value: number | string; sub: string; accent: string }) {
  return (
    <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-sm transition-all hover:shadow-md">
      <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 block mb-1">{label}</span>
      <div className="flex items-baseline gap-2">
        <span className={`text-4xl font-bold ${accent}`}>{value}</span>
        <span className="text-sm text-gray-400 font-medium">produits</span>
      </div>
      <p className="text-[11px] text-gray-400 mt-2 flex items-center gap-1.5 font-medium italic">
        {sub}
      </p>
    </div>
  );
}

function StockBadge({ product } : { product: Product }) {
  const status = getStockStatus(product);
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold tracking-tight shadow-sm ${STATUS_CONFIG[status].badge}`}>
      {product.currentStock} u.
    </span>
  );
}

function SupplierBadge({ supplier }: { supplier?: any }) {
  if (!supplier) return <span className="text-gray-300 text-[10px] italic">Non assigné</span>;
  
  const isReliable = supplier.reliabilityScore >= 0.9;
  const hasDelay = supplier.averageDelayDays > 0;

  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${isReliable ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200' : 'bg-amber-50 text-amber-700 ring-1 ring-amber-200'}`}>
        {supplier.name}
      </span>
      {hasDelay && (
        <span className="text-[9px] font-bold text-amber-600 flex items-center gap-0.5">
          <AlertCircle className="h-2 w-2" />
          +{supplier.averageDelayDays.toFixed(1)}j retard
        </span>
      )}
    </div>
  );
}

function SyncButton({ syncing, onClick }: { syncing: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      disabled={syncing}
      className={`
        flex items-center gap-2.5 px-6 py-2.5 rounded-2xl text-sm font-bold transition-all
        ${syncing 
          ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
          : 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg shadow-purple-200 hover:shadow-xl hover:scale-105 active:scale-95'}
      `}
    >
      <BarChart2 className={`h-4 w-4 ${syncing ? 'animate-pulse' : ''}`} />
      {syncing ? 'Synchronisation…' : 'Lancer Synchronisation'}
    </button>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const router = useRouter();
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<FilterTab>('all');
  const [dashTab, setDashTab] = useState<DashboardTab>('products');

  const [editing, setEditing] = useState<{ id: string; field: 'leadTime' | 'moq' } | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [leadTimeDelta, setLeadTimeDelta] = useState(0);
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    const onboarded = localStorage.getItem('michi_onboarded');
    if (!onboarded) setShowOnboarding(true);
  }, []);

  const { data: meData, loading: meLoading, error: meError } = useQuery(GET_ME);
  const { data: productsData, loading: productsLoading, refetch: refetchProducts } = useQuery(GET_PRODUCTS);
  const { data: statsData, refetch: refetchStats } = useQuery(GET_DASHBOARD_STATS);
  const { data: alertsData, refetch: refetchAlerts } = useQuery(GET_UNREAD_ALERTS, { pollInterval: 30000 });

  const [fetchDetail, { data: detailData, loading: detailLoading }] = useLazyQuery(GET_PRODUCT_DETAIL);

  const [triggerSync, { loading: syncing }] = useMutation(TRIGGER_MOCK_DATA_SYNC, {
    onCompleted: (data) => {
      setToast({ message: data.triggerMockDataSync.message, type: 'success' });
      refetchProducts();
      refetchStats();
      refetchAlerts();
      setTimeout(() => setToast(null), 5000);
    },
    onError: (err) => {
      setToast({ message: err.message, type: 'error' });
      setTimeout(() => setToast(null), 5000);
    },
  });

  const [ingestCSV, { loading: importing }] = useMutation(INGEST_CSV_DATA, {
    onCompleted: (data) => {
      setToast({ 
        message: `Import réussi : ${data.ingestCsvData.productsCount} produits synchronisés.`, 
        type: 'success' 
      });
      refetchProducts();
      refetchStats();
      refetchAlerts();
      setTimeout(() => setToast(null), 5000);
    },
    onError: (err) => {
      setToast({ message: err.message, type: 'error' });
      setTimeout(() => setToast(null), 5000);
    }
  });

  const [markAsRead] = useMutation(MARK_ALERT_AS_READ, {
    onCompleted: () => refetchAlerts()
  });

  const handleCSVUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      const content = event.target?.result as string;
      if (content) {
        await ingestCSV({
          variables: {
            csvContent: content,
            skuCol: 'sku',
            dateCol: 'date',
            salesCol: 'sales',
            stockCol: 'stock',
            titleCol: 'title'
          }
        });
      }
    };
    reader.readAsText(file);
  };

  const [updateSettings] = useMutation(UPDATE_PRODUCT_SETTINGS, {
    onCompleted: () => {
      setToast({ message: 'Produit mis à jour', type: 'success' });
      setEditing(null);
      refetchProducts();
      refetchStats();
      setTimeout(() => setToast(null), 3000);
    },
    onError: (err) => {
      setToast({ message: err.message, type: 'error' });
      setEditing(null);
    }
  });

  const handleExport = () => {
    try {
      const urgentProducts = allProducts.filter(p => getStockStatus(p) === 'urgent' || getStockStatus(p) === 'warning');
      
      const headers = ['Produit', 'SKU', 'Stock Actuel', 'Prévision Rupture', 'Run Rate', 'Lead Time', 'MOQ', 'Commande Suggérée'];
      const rows = urgentProducts.map(p => [
        p.title,
        p.sku,
        p.currentStock,
        p.prediction?.predictedStockoutDate || 'N/A',
        p.prediction?.runRate.toFixed(2) || '0',
        p.leadTime,
        p.moq,
        Math.round(p.prediction?.reorderQuantity || 0)
      ]);

      const csvContent = [headers, ...rows].map(e => e.join(',')).join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `alertes_reappro_michi_${format(new Date(), 'yyyy-MM-dd')}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setToast({ message: 'Export CSV réussi', type: 'success' });
      setTimeout(() => setToast(null), 3000);
    } catch (err) {
      setToast({ message: "Erreur lors de l'export", type: 'error' });
    }
  };

  useEffect(() => {
    if (meError) {
      console.error('[Auth] Error detected, redirecting to login...', meError);
      router.replace('/login');
    }
  }, [meError, router]);

  const allProducts = useMemo(() => {
    return (productsData?.products || []) as Product[];
  }, [productsData]);

  const kpis = useMemo(() => {
    if (statsData?.dashboardKpis) {
      const s = statsData.dashboardKpis;
      return { 
        total: s.totalProducts, 
        urgent: s.actualStockouts, // Ruptures réelles
        warning: s.urgentAlerts,   // Alertes prédictives (Urgent dans le backend)
        healthy: s.totalProducts - s.urgentAlerts - s.actualStockouts 
      };
    }
    
    // Fallback local
    let urgent = 0;
    let warning = 0;
    let healthy = 0;
    
    allProducts.forEach(p => {
      const status = getStockStatus(p);
      if (status === 'urgent') urgent++;
      else if (status === 'warning') warning++;
      else healthy++;
    });
    
    return { total: allProducts.length, urgent, warning, healthy };
  }, [allProducts, statsData]);

  const filtered = useMemo(() => {
    let list = allProducts;
    if (filter === 'urgent') list = list.filter((p) => getStockStatus(p) === 'urgent');
    else if (filter === 'warning') list = list.filter((p) => getStockStatus(p) === 'warning');
    else if (filter === 'healthy') list = list.filter((p) => getStockStatus(p) === 'healthy');

    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (p) => p.title.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q),
      );
    }
    return list;
  }, [allProducts, filter, search]);

  if (meLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-2 border-purple-200 border-t-purple-600 mx-auto" />
          <p className="mt-4 text-sm text-gray-400">Chargement…</p>
        </div>
      </div>
    );
  }

  if (meError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-red-500 text-sm">{meError.message}</p>
          <button
            onClick={() => router.push('/login')}
            className="mt-4 px-4 py-2 bg-purple-600 text-white text-sm rounded-xl"
          >
            Retour au login
          </button>
        </div>
      </div>
    );
  }

  const user = meData?.me;

  const TABS: { key: FilterTab; label: string; count: number }[] = [
    { key: 'all', label: 'Tous', count: kpis.total },
    { key: 'urgent', label: 'Rupture', count: kpis.urgent },
    { key: 'warning', label: 'À surveiller', count: kpis.warning },
    { key: 'healthy', label: 'Sains', count: kpis.healthy },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Onboarding Wizard (Sprint 10) */}
      <AnimatePresence>
        {showOnboarding && (
          <OnboardingWizard 
            onSync={() => triggerSync() as any} 
            onComplete={() => setShowOnboarding(false)} 
          />
        )}
      </AnimatePresence>

      {/* Toast */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 flex items-start gap-3 px-4 py-3 rounded-xl shadow-lg text-sm max-w-sm ${
            toast.type === 'success'
              ? 'bg-emerald-600 text-white'
              : 'bg-red-600 text-white'
          }`}
        >
          <span className="mt-0.5 text-base">{toast.type === 'success' ? '✓' : '✕'}</span>
          <span>{toast.message}</span>
        </div>
      )}

      {/* Header */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-3">
              <span className="text-xl font-serif text-purple-600">道</span>
              <span className="text-sm font-semibold text-gray-900 tracking-wide">MICHI</span>
            </div>
            <div className="flex items-center gap-5">
              <div className="relative cursor-pointer group">
                <Bell className="h-5 w-5 text-gray-400 group-hover:text-purple-600 transition-colors" />
                {alertsData?.unreadAlerts?.length > 0 && (
                  <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 text-white text-[9px] font-bold flex items-center justify-center rounded-full border-2 border-white ring-red-200 group-hover:ring-4 transition-all">
                    {alertsData.unreadAlerts.length}
                  </span>
                )}
                
                {/* Alert Dropdown (Simple) */}
                <div className="absolute right-0 mt-2 w-72 bg-white rounded-xl shadow-xl border border-gray-100 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all py-2 z-50">
                  <p className="px-4 py-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest border-b border-gray-50">Alertes Récentes</p>
                  <div className="max-h-64 overflow-y-auto">
                    {alertsData?.unreadAlerts?.length === 0 ? (
                      <p className="px-4 py-4 text-xs text-center text-gray-400">Aucune alerte</p>
                    ) : (
                      alertsData?.unreadAlerts?.map((a: any) => (
                        <div key={a.id} className="px-4 py-3 hover:bg-gray-50 border-b border-gray-50 last:border-0 transition-colors">
                          <div className="flex gap-3">
                            <AlertCircle className={`h-4 w-4 mt-0.5 ${a.severity === 3 ? 'text-red-500' : 'text-amber-500'}`} />
                            <div>
                              <p className="text-xs font-semibold text-gray-800 leading-tight">{a.message}</p>
                              <p className="text-[10px] text-gray-400 mt-1">{format(new Date(a.createdAt), 'dd MMMM HH:mm', { locale: undefined })}</p>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
              <span className="hidden sm:block text-xs text-gray-400 font-medium">{user?.email}</span>
              <button
                onClick={() => { localStorage.removeItem('michi_token'); router.push('/login'); }}
                className="px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
              >
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

        {/* Page title + Sync */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Catalogue produits</h1>
            <p className="text-sm text-gray-400 mt-0.5">Vue d&apos;ensemble de votre inventaire</p>
          </div>
            <div className="flex items-center gap-3">
            <input 
                type="file" 
                id="csv-upload" 
                className="hidden" 
                accept=".csv" 
                onChange={handleCSVUpload} 
              />
              <label
                htmlFor="csv-upload"
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-gray-200 hover:bg-gray-50 text-gray-600 text-sm font-medium transition-all shadow-sm cursor-pointer
                  ${importing ? 'opacity-50 cursor-not-allowed' : ''}
                `}
                title="Importer des données via CSV"
              >
                <Upload className={`h-4 w-4 ${importing ? 'animate-bounce' : ''}`} />
                <span className="hidden sm:inline">{importing ? 'Import…' : 'Importer CSV'}</span>
              </label>
              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-gray-200 hover:bg-gray-50 text-gray-600 text-sm font-medium transition-colors shadow-sm"
                title="Exporter les alertes en CSV"
              >
                <Download className="h-4 w-4" />
                <span className="hidden sm:inline">Exporter</span>
              </button>
              <SyncButton syncing={syncing} onClick={() => triggerSync()} />
            </div>
        </div>

        {/* Dashboard tab switcher — Sprint 9 */}
        <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit">
          <button
            onClick={() => setDashTab('products')}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
              dashTab === 'products' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <BarChart2 size={13} />
            Produits
          </button>
          <button
            onClick={() => setDashTab('channels')}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
              dashTab === 'channels' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Layers size={13} />
            Canaux
          </button>
        </div>

        {/* KPI cards */}
        {dashTab === 'products' && allProducts.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <KpiCard label="Total produits" value={kpis.total} sub="dans le catalogue" accent="text-gray-900" />
            <KpiCard label="Ruptures" value={kpis.urgent} sub="stock = 0" accent="text-red-600" />
            <KpiCard label="À surveiller" value={kpis.warning} sub="stock < 20 u." accent="text-amber-500" />
            <KpiCard label="Sains" value={kpis.healthy} sub="stock ≥ 20 u." accent="text-emerald-600" />
          </div>
        )}

        {/* ── Vue Canaux (Sprint 9) ─────────────────────────────────────── */}
        {dashTab === 'channels' && <OmnichannelView />}

        {/* Filters + Search — only shown on Products tab */}
        {dashTab === 'products' && allProducts.length > 0 && (
          <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
            {/* Tabs */}
            <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setFilter(tab.key)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    filter === tab.key
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab.label}
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded-full font-semibold ${
                      filter === tab.key ? 'bg-purple-100 text-purple-700' : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {tab.count}
                  </span>
                </button>
              ))}
            </div>

            {/* Search */}
            <div className="relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Rechercher par nom ou SKU…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 pr-4 py-2 text-sm bg-white border border-gray-200 rounded-xl w-full sm:w-64 focus:outline-none focus:ring-2 focus:ring-purple-300 focus:border-transparent placeholder-gray-400"
              />
            </div>
          </div>
        )}

        {/* Table / Empty states — Products tab only */}
        {dashTab === 'products' && productsLoading && allProducts.length === 0 ? (
          <div className="bg-white rounded-2xl p-16 text-center shadow-sm border border-gray-100">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-purple-200 border-t-purple-600 mx-auto" />
          </div>
        ) : allProducts.length === 0 ? (
          /* Empty — no sync yet */
          <div className="bg-white rounded-2xl p-16 text-center shadow-sm border border-gray-100">
            <div className="text-5xl mb-4">📦</div>
            <h3 className="text-base font-semibold text-gray-800 mb-1">Aucun produit</h3>
            <p className="text-sm text-gray-400 max-w-xs mx-auto">
              Cliquez sur <strong className="text-gray-600">Synchroniser</strong> pour générer 50 produits de démonstration avec 365 jours d&apos;historique.
            </p>
          </div>
        ) : filtered.length === 0 ? (
          /* Empty — no match */
          <div className="bg-white rounded-2xl p-12 text-center shadow-sm border border-gray-100">
            <div className="text-4xl mb-3">🔍</div>
            <p className="text-sm text-gray-500">Aucun résultat pour <strong>&quot;{search}&quot;</strong></p>
            <button onClick={() => { setSearch(''); setFilter('all'); }} className="mt-3 text-xs text-purple-600 hover:underline">
              Réinitialiser les filtres
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            {/* Table header */}
            <div className="px-6 py-3 bg-gray-50 border-b border-gray-100 flex items-center justify-between">
              <span className="text-xs font-medium text-gray-400">
                {filtered.length} produit{filtered.length > 1 ? 's' : ''}
                {filtered.length !== allProducts.length && ` sur ${allProducts.length}`}
              </span>
            </div>

            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Produit</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider hidden sm:table-cell">SKU</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider">Fournisseur</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider">Stock</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider">Prévision Rupture</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider">Commande Suggérée</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider hidden md:table-cell">Lead Time</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider hidden md:table-cell">MOQ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filtered.map((product) => {
                  const status = getStockStatus(product);
                  return (
                    <React.Fragment key={product.id}>
                      <tr
                        className={`transition-colors hover:bg-gray-50/70 border-b border-gray-50 cursor-pointer ${
                          status === 'urgent' ? 'bg-red-50/10' : ''
                        } ${expandedId === product.id ? 'bg-purple-50/30' : ''}`}
                        onClick={() => {
                          if (expandedId === product.id) {
                            setExpandedId(null);
                          } else {
                            setExpandedId(product.id);
                            fetchDetail({ variables: { id: product.id } });
                          }
                        }}
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <motion.div 
                              animate={{ rotate: expandedId === product.id ? 180 : 0 }}
                              className="text-gray-300"
                            >
                              <ChevronDown className="h-4 w-4" />
                            </motion.div>
                            <div className={`h-2 w-2 rounded-full flex-shrink-0 ${STATUS_CONFIG[status].dot}`} />
                            <span className="text-sm font-medium text-gray-900 leading-tight">{product.title}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 hidden sm:table-cell">
                          <span className="text-xs font-mono text-gray-400 bg-gray-100 px-2 py-0.5 rounded">{product.sku}</span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <SupplierBadge supplier={product.supplier} />
                        </td>
                        <td className="px-6 py-4 text-center">
                          <StockBadge product={product} />
                        </td>
                        <td className="px-6 py-4 text-center whitespace-nowrap">
                          {product.prediction?.predictedStockoutDate ? (
                            <div className="flex flex-col items-center">
                              <span className={`text-sm font-medium ${
                                new Date(product.prediction.predictedStockoutDate) < new Date() ? 'text-red-600' : 'text-gray-900'
                              }`}>
                                {new Date(product.prediction.predictedStockoutDate).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
                              </span>
                              <span className="text-[10px] text-gray-400 uppercase tracking-tight">
                                Run rate: {product.prediction.runRate.toFixed(1)}/j
                              </span>
                            </div>
                          ) : (
                            <span className="text-xs text-gray-300 italic">En calcul…</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-center">
                          {product.prediction ? (
                            <div className={`px-2 py-1 rounded-lg inline-block ${
                              product.prediction.reorderQuantity > 0 
                                ? 'bg-purple-50 text-purple-700 font-bold border border-purple-100' 
                                : 'text-gray-400 italic text-xs'
                            }`}>
                              {product.prediction.reorderQuantity > 0 
                                ? `${Math.round(product.prediction.reorderQuantity)} u.`
                                : '0 u.'
                              }
                            </div>
                          ) : (
                            <span className="h-1 w-4 bg-gray-100 rounded animate-pulse inline-block" />
                          )}
                        </td>
                        <td className="px-6 py-4 text-center hidden md:table-cell" onClick={(e) => e.stopPropagation()}>
                          {editing?.id === product.id && editing?.field === 'leadTime' ? (
                            <input
                              type="number"
                              className="w-16 px-1 py-0.5 text-xs border-2 border-purple-300 rounded text-center focus:outline-none"
                              defaultValue={product.leadTime}
                              autoFocus
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') e.currentTarget.blur();
                                if (e.key === 'Escape') setEditing(null);
                              }}
                              onBlur={(e) => {
                                const val = parseInt(e.target.value);
                                if (!isNaN(val) && val !== product.leadTime) updateSettings({ variables: { id: product.id, leadTime: val } });
                                else setEditing(null);
                              }}
                            />
                          ) : (
                            <button 
                              onClick={() => setEditing({ id: product.id, field: 'leadTime' })}
                              className="text-sm text-gray-500 hover:text-purple-600 hover:bg-purple-50 px-2 py-1 rounded transition-colors"
                            >
                              {product.leadTime} j
                            </button>
                          )}
                        </td>
                        <td className="px-6 py-4 text-center hidden md:table-cell" onClick={(e) => e.stopPropagation()}>
                          {editing?.id === product.id && editing?.field === 'moq' ? (
                            <input
                              type="number"
                              className="w-16 px-1 py-0.5 text-xs border-2 border-purple-300 rounded text-center focus:outline-none"
                              defaultValue={product.moq}
                              autoFocus
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') e.currentTarget.blur();
                                if (e.key === 'Escape') setEditing(null);
                              }}
                              onBlur={(e) => {
                                const val = parseInt(e.target.value);
                                if (!isNaN(val) && val !== product.moq) updateSettings({ variables: { id: product.id, moq: val } });
                                else setEditing(null);
                              }}
                            />
                          ) : (
                            <button 
                              onClick={() => setEditing({ id: product.id, field: 'moq' })}
                              className="text-sm text-gray-500 hover:text-purple-600 hover:bg-purple-50 px-2 py-1 rounded transition-colors"
                            >
                              {product.moq} u.
                            </button>
                          )}
                        </td>
                      </tr>
                      
                      {/* Expanded View */}
                      <AnimatePresence>
                        {expandedId === product.id && (
                          <tr>
                            <td colSpan={7} className="px-0 py-0 overflow-hidden bg-gray-50/30">
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.3, ease: 'easeInOut' }}
                                className="px-8 py-6"
                              >
                                {detailLoading ? (
                                  <div className="flex items-center justify-center py-12">
                                    <div className="animate-spin h-6 w-6 border-2 border-purple-200 border-t-purple-600 rounded-full" />
                                  </div>
                                ) : (
                                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                                    {/* Chart Slot */}
                                    <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden group">
                                      <div className="absolute top-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <BarChart2 className="h-4 w-4 text-purple-200" />
                                      </div>
                                      <SalesChart 
                                        data={detailData?.productDetail?.[0]?.cleanedDemand || []} 
                                        title="Historique de Demande (IA)" 
                                      />
                                    </div>
                                    
                                    {/* Summary Slot */}
                                    <div className="space-y-4">
                                      <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                                        <h4 className="text-sm font-semibold text-gray-900 mb-4">Focus IA</h4>
                                        <div className="space-y-3">
                                          <div className="flex justify-between items-center text-xs">
                                            <span className="text-gray-400">Run Rate (Moyenne 30j)</span>
                                            <span className="font-bold text-gray-900">{product.prediction?.runRate.toFixed(2)} u./jour</span>
                                          </div>
                                          <div className="flex justify-between items-center text-xs">
                                            <span className="text-gray-400">Couverture Stock</span>
                                            <span className="font-bold text-gray-900">{Math.round(product.prediction?.daysOfStock || 0)} jours</span>
                                          </div>
                                          <div className="flex justify-between items-center text-xs">
                                            <span className="text-gray-400">Statut IA</span>
                                            <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-600 font-semibold uppercase tracking-widest text-[9px]">Optimisé</span>
                                          </div>
                                        </div>
                                      </div>
                                      
                                      <div className="bg-purple-600 p-6 rounded-2xl text-white shadow-xl shadow-purple-200 relative overflow-hidden">
                                        <div className="absolute -right-4 -bottom-4 h-24 w-24 bg-purple-500 rounded-full opacity-20" />
                                        <h4 className="text-xs font-medium uppercase tracking-widest opacity-80 mb-1">Recommandation</h4>
                                        <div className="text-2xl font-black mb-2">{product.prediction?.reorderQuantity.toFixed(0)} u.</div>
                                        <p className="text-[10px] leading-relaxed opacity-90">
                                          Commandez dès aujourd'hui pour couvrir un délai de {product.leadTime} jours avec un stock de sécurité de 50%.
                                        </p>
                                      </div>
                                    </div>
                                    
                                    {/* What-if Simulator (US 10.7) */}
                                    <div className="lg:col-span-3 mt-6 p-8 bg-gradient-to-br from-indigo-50/50 to-purple-50/50 rounded-[2.5rem] border border-indigo-100/50 backdrop-blur-sm shadow-inner relative overflow-hidden group">
                                      <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity">
                                        <Zap size={120} className="text-indigo-900" />
                                      </div>
                                      
                                      <div className="flex items-center justify-between mb-8 relative z-10">
                                        <div className="flex items-center gap-3">
                                          <div className="p-2.5 bg-white rounded-2xl shadow-sm border border-indigo-50">
                                            <Zap size={20} className="text-indigo-600 animate-pulse" />
                                          </div>
                                          <div>
                                            <h4 className="text-base font-black text-gray-900 tracking-tight">Simulateur de Rupture What-if</h4>
                                            <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Ajustez les délais fournisseur pour voir l'impact</p>
                                          </div>
                                        </div>
                                        <button 
                                          onClick={() => setLeadTimeDelta(0)}
                                          className="text-[10px] font-black text-indigo-600 hover:text-indigo-800 bg-white px-4 py-2 rounded-xl shadow-sm border border-indigo-50 transition-all uppercase tracking-widest active:scale-95"
                                        >
                                          Réinitialiser
                                        </button>
                                      </div>
                                      
                                      <div className="grid md:grid-cols-5 gap-12 items-center relative z-10">
                                        <div className="md:col-span-3 space-y-6">
                                          <div className="flex justify-between items-end">
                                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Variation de Lead Time (jours)</label>
                                            <div className="flex items-center gap-2">
                                              <span className={`${leadTimeDelta >= 0 ? 'text-amber-600' : 'text-emerald-600'} text-lg font-black bg-white px-4 py-1.5 rounded-2xl shadow-sm border border-indigo-50 min-w-[70px] text-center`}>
                                                {leadTimeDelta > 0 ? `+${leadTimeDelta}` : leadTimeDelta}j
                                              </span>
                                            </div>
                                          </div>
                                          <div className="relative pt-2">
                                            <input 
                                              type="range" 
                                              min="-7" 
                                              max="30" 
                                              value={leadTimeDelta} 
                                              onChange={(e) => setLeadTimeDelta(parseInt(e.target.value))}
                                              className="w-full h-3 bg-gray-200 rounded-full appearance-none cursor-pointer accent-indigo-600 focus:outline-none focus:ring-4 focus:ring-indigo-100"
                                            />
                                            <div className="flex justify-between mt-3 text-[9px] font-black text-gray-400 uppercase tracking-tighter">
                                              <span className="flex flex-col"><span>Optimiste</span><span className="text-emerald-500">-7j</span></span>
                                              <span className="flex flex-col text-center italic"><span>Standard</span><span>{product.leadTime}j</span></span>
                                              <span className="flex flex-col text-right"><span>Retard Critique</span><span className="text-red-500">+30j</span></span>
                                            </div>
                                          </div>
                                        </div>

                                        <div className="md:col-span-2 grid grid-cols-1 gap-4">
                                          <div className="bg-white/80 backdrop-blur-md rounded-3xl p-6 border border-white shadow-xl shadow-indigo-100/50 relative overflow-hidden">
                                            <p className="text-[9px] font-black text-gray-400 uppercase tracking-widest mb-2">Nouvel objectif de stock</p>
                                            <div className="flex items-baseline gap-2">
                                              <span className="text-4xl font-black text-gray-900 tracking-tighter">
                                                {Math.ceil(
                                                  (product.prediction?.runRate || 0) * 
                                                  (product.leadTime + leadTimeDelta + (product.supplier?.averageDelayDays || 0)) * 
                                                  1.5
                                                )}
                                              </span>
                                              <span className="text-xs font-bold text-gray-400 uppercase">unités</span>
                                            </div>
                                          </div>

                                          <div className="bg-indigo-600 rounded-3xl p-6 border border-indigo-500 shadow-xl shadow-indigo-200 relative overflow-hidden">
                                            <div className="absolute right-0 top-0 p-3 opacity-20">
                                              <Download size={16} className="text-white" />
                                            </div>
                                            <p className="text-[9px] font-black text-indigo-100 uppercase tracking-widest mb-2">Réapprovisionnement Simulée</p>
                                            <div className="flex items-baseline gap-2 text-white">
                                              <span className="text-4xl font-black tracking-tighter">
                                                {Math.max(0, Math.ceil(
                                                  (Math.ceil(
                                                    (product.prediction?.runRate || 0) * 
                                                    (product.leadTime + leadTimeDelta + (product.supplier?.averageDelayDays || 0)) * 
                                                    1.5
                                                  ) - product.currentStock) / (product.moq || 1)
                                                ) * (product.moq || 1))}
                                              </span>
                                              <span className="text-xs font-bold opacity-80 uppercase">unités</span>
                                            </div>
                                            {leadTimeDelta > 5 && (
                                              <div className="mt-4 flex items-center gap-2 bg-red-400/20 px-3 py-1.5 rounded-xl border border-red-400/30">
                                                <AlertCircle size={12} className="text-red-100" />
                                                <span className="text-[9px] font-black text-red-50 uppercase tracking-widest">Risque Rupture Accentué</span>
                                              </div>
                                            )}
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </motion.div>
                            </td>
                          </tr>
                        )}
                      </AnimatePresence>
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
