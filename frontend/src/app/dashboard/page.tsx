'use client';

import { useQuery, useMutation } from '@apollo/client';
import { useRouter } from 'next/navigation';
import { useEffect, useState, useMemo } from 'react';
import { GET_ME } from '@/graphql/queries/getMe';
import { GET_PRODUCTS } from '@/graphql/queries/getProducts';
import { TRIGGER_MOCK_DATA_SYNC } from '@/graphql/mutations/syncShopify';
import type { Product, SyncResult } from '@/types/product';

type FilterTab = 'all' | 'urgent' | 'warning' | 'healthy';

function getStockStatus(stock: number): 'urgent' | 'warning' | 'healthy' {
  if (stock === 0) return 'urgent';
  if (stock < 20) return 'warning';
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

function KpiCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: number | string;
  sub?: string;
  accent: string;
}) {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-widest mb-3">{label}</p>
      <p className={`text-3xl font-bold ${accent}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

function StockBadge({ stock }: { stock: number }) {
  const status = getStockStatus(stock);
  const cfg = STATUS_CONFIG[status];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.badge}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
      {status === 'healthy' ? `${stock} u.` : status === 'urgent' ? 'Rupture' : `${stock} u.`}
    </span>
  );
}

function SyncButton({ syncing, onClick }: { syncing: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      disabled={syncing}
      className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm font-medium transition-colors shadow-sm"
    >
      {syncing ? (
        <>
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
          Synchronisation…
        </>
      ) : (
        <>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Synchroniser
        </>
      )}
    </button>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const router = useRouter();
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<FilterTab>('all');

  const { data: meData, loading: meLoading, error: meError } = useQuery(GET_ME);
  const { data: productsData, loading: productsLoading, refetch: refetchProducts } = useQuery(GET_PRODUCTS);

  const [triggerSync, { loading: syncing }] = useMutation(TRIGGER_MOCK_DATA_SYNC, {
    onCompleted: (data) => {
      const result: SyncResult = data.triggerMockDataSync;
      setToast({ message: result.message, type: 'success' });
      refetchProducts();
      setTimeout(() => setToast(null), 5000);
    },
    onError: (err) => {
      setToast({ message: err.message, type: 'error' });
      setTimeout(() => setToast(null), 5000);
    },
  });

  useEffect(() => {
    if (typeof window !== 'undefined' && !localStorage.getItem('michi_token')) {
      router.push('/login');
    }
  }, [router]);

  const allProducts: Product[] = productsData?.products ?? [];

  const kpis = useMemo(() => {
    const urgent = allProducts.filter((p) => p.currentStock === 0).length;
    const warning = allProducts.filter((p) => p.currentStock > 0 && p.currentStock < 20).length;
    const healthy = allProducts.filter((p) => p.currentStock >= 20).length;
    return { total: allProducts.length, urgent, warning, healthy };
  }, [allProducts]);

  const filtered = useMemo(() => {
    let list = allProducts;
    if (filter === 'urgent') list = list.filter((p) => p.currentStock === 0);
    else if (filter === 'warning') list = list.filter((p) => p.currentStock > 0 && p.currentStock < 20);
    else if (filter === 'healthy') list = list.filter((p) => p.currentStock >= 20);

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
            <div className="flex items-center gap-3">
              <span className="hidden sm:block text-xs text-gray-400">{user?.email}</span>
              <button
                onClick={() => { localStorage.removeItem('michi_token'); router.push('/login'); }}
                className="px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
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
          <SyncButton syncing={syncing} onClick={() => triggerSync()} />
        </div>

        {/* KPI cards */}
        {allProducts.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <KpiCard label="Total produits" value={kpis.total} sub="dans le catalogue" accent="text-gray-900" />
            <KpiCard label="Ruptures" value={kpis.urgent} sub="stock = 0" accent="text-red-600" />
            <KpiCard label="À surveiller" value={kpis.warning} sub="stock < 20 u." accent="text-amber-500" />
            <KpiCard label="Sains" value={kpis.healthy} sub="stock ≥ 20 u." accent="text-emerald-600" />
          </div>
        )}

        {/* Filters + Search */}
        {allProducts.length > 0 && (
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

        {/* Table / Empty states */}
        {productsLoading ? (
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
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider">Stock</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider hidden md:table-cell">Lead Time</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider hidden md:table-cell">MOQ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filtered.map((product) => {
                  const status = getStockStatus(product.currentStock);
                  return (
                    <tr
                      key={product.id}
                      className={`transition-colors hover:bg-gray-50/70 ${
                        status === 'urgent' ? 'bg-red-50/30' : ''
                      }`}
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className={`h-2 w-2 rounded-full flex-shrink-0 ${STATUS_CONFIG[status].dot}`} />
                          <span className="text-sm font-medium text-gray-900 leading-tight">{product.title}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 hidden sm:table-cell">
                        <span className="text-xs font-mono text-gray-400 bg-gray-100 px-2 py-0.5 rounded">{product.sku}</span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <StockBadge stock={product.currentStock} />
                      </td>
                      <td className="px-6 py-4 text-center hidden md:table-cell">
                        <span className="text-sm text-gray-500">{product.leadTime} j</span>
                      </td>
                      <td className="px-6 py-4 text-center hidden md:table-cell">
                        <span className="text-sm text-gray-500">{product.moq} u.</span>
                      </td>
                    </tr>
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
