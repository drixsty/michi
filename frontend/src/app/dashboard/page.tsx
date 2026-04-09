'use client';

import { useQuery, useMutation } from '@apollo/client';
import { useRouter, useSearchParams } from 'next/navigation';
import React, { useEffect, useState, useMemo, Suspense } from 'react';
import { GET_ME } from '@/graphql/queries/getMe';
import { GET_PRODUCTS } from '@/graphql/queries/getProducts';
import { TRIGGER_MOCK_DATA_SYNC } from '@/graphql/mutations/syncShopify';
import { GET_DASHBOARD_STATS } from '@/graphql/queries/getDashboardStats';
import { GET_UNREAD_ALERTS } from '@/graphql/queries/getUnreadAlerts';
import { INGEST_CSV_DATA } from '@/graphql/mutations/ingestCSV';
import { AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { LayoutDashboard, Package, Layers, Bell, AlertCircle, Trash2, ExternalLink, Eye, CheckCircle2, Database } from 'lucide-react';
import Link from 'next/link';
import { gql } from '@apollo/client';
import { cn } from '@/lib/utils';
import { ProductQuickView } from '@/components/dashboard/ProductQuickView';
import { LoadingState } from '@/components/ui/LoadingState';

import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { StatsOverview } from '@/components/dashboard/StatsOverview';
import { ProductTable } from '@/components/dashboard/ProductTable';
import { ConnectorsGrid } from '@/components/dashboard/ConnectorsGrid';

import OnboardingWizard from '@/components/dashboard/OnboardingWizard';

import { GET_OMNICHANNEL_INVENTORY } from '@/graphql/queries/getOmnichannelInventory';
import type { Product, OmnichannelProduct } from '@/types/product';

const DELETE_ALERT = gql`
  mutation DeleteAlert($id: ID!) {
    deleteAlert(alertId: $id)
  }
`;

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);

  // Sync active view with URL 'tab' param
  const activeTab = searchParams.get('tab') || 'overview';
  const searchQuery = searchParams.get('q') || '';

  useEffect(() => {
    const onboarded = localStorage.getItem('michi_onboarded');
    if (!onboarded) setShowOnboarding(true);
  }, []);

  // -- Queries --
  const { data: meData, loading: meLoading, error: meError } = useQuery(GET_ME);
  const { data: omnichannelData, loading: productsLoading, refetch: refetchProducts } = useQuery(GET_OMNICHANNEL_INVENTORY);
  const { data: statsData, refetch: refetchStats } = useQuery(GET_DASHBOARD_STATS);
  const { data: alertsData, refetch: refetchAlerts } = useQuery(GET_UNREAD_ALERTS, { pollInterval: 30000 });

  // -- Mutations --
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

  const [ingestCSV] = useMutation(INGEST_CSV_DATA, {
    onCompleted: () => {
      setToast({ message: 'Import réussi', type: 'success' });
      refetchProducts();
      refetchStats();
      setTimeout(() => setToast(null), 5000);
    },
  });

  const [deleteAlert] = useMutation(DELETE_ALERT, {
    onCompleted: () => refetchAlerts(),
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
            skuCol: 'sku', dateCol: 'date', salesCol: 'sales', stockCol: 'stock', titleCol: 'title'
          }
        });
      }
    };
    reader.readAsText(file);
  };

  const handleExport = () => {
    try {
      const products = (omnichannelData?.omnichannelInventory || []) as OmnichannelProduct[];
      const headers = ['Produit', 'SKU', 'Stock Total', 'Commande Suggérée'];
      const rows = products.map(p => [p.title, p.sku, p.totalStock, Math.round(p.totalReorderQuantity || 0)]);
      const csvContent = [headers, ...rows].map(e => e.join(',')).join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `michi_export_${format(new Date(), 'yyyy-MM-dd')}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setToast({ message: 'Export réussi', type: 'success' });
      setTimeout(() => setToast(null), 5000);
    } catch (err) {
      setToast({ message: "Erreur export", type: 'error' });
    }
  };

  const kpis = useMemo(() => {
    if (statsData?.dashboardKpis) {
      const s = statsData.dashboardKpis;
      return { 
        total: s.totalProducts || 0, 
        urgent: s.actualStockouts || 0, 
        warning: s.urgentAlerts || 0, 
        healthy: (s.totalProducts || 0) - (s.urgentAlerts || 0) - (s.actualStockouts || 0) 
      };
    }
    return { total: 0, urgent: 0, warning: 0, healthy: 0 };
  }, [statsData]);

  // Relaxed Auth check for preview stability
  useEffect(() => {
    if (meError) {
      console.warn("Auth error, redirecting to login...");
      router.replace('/login');
    }
  }, [meError, router]);

  // Loading state with beautiful skeleton
  // Loading state with beautiful spinner
  if (meLoading && !meData) return (
    <LoadingState fullScreen message="initialisation michi..." />
  );

  const tabConfigs: Record<string, { title: string; subtitle: string }> = {
    overview: { 
      title: "Tableau de bord", 
      subtitle: "Pilotez votre inventaire avec précision" 
    },
    inventory: { 
      title: "Inventaire", 
      subtitle: "Gérez vos catalogues produits et niveaux de stock" 
    },
    sources: { 
      title: "Navigation des sources", 
      subtitle: "Gérez vos connexions de données et flux api" 
    },
    profile: { 
      title: "Mon Profil", 
      subtitle: "Gérez vos préférences de notification et sécurité" 
    }
  };

  const { title, subtitle } = tabConfigs[activeTab] || tabConfigs.overview;

  return (
    <div className="space-y-6">
      {/* Onboarding Wizard */}
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
        <div className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-md shadow-lg text-sm bg-primary text-white border border-white/20 animate-in slide-in-from-right-2`}>
          {toast.message}
        </div>
      )}
 
      {/* Header */}
      <DashboardHeader 
        title={title}
        subtitle={subtitle}
        syncing={syncing}
        onSync={() => triggerSync()}
        onExport={handleExport}
        showActions={activeTab === 'inventory'}
      />

      {/* View Content (Routed by tab search param) */}
      <div className="mt-2">
        {activeTab === 'overview' && (
          <div className="space-y-5 animate-in fade-in duration-500">
            <StatsOverview stats={kpis} />
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* Recent Alerts */}
              <div className="bg-white rounded-xl border p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold">Alertes récentes</h3>
                  <div className="p-1.5 bg-primary/5 rounded-full">
                    <Bell className="h-4 w-4 text-primary" />
                  </div>
                </div>
                <div className="space-y-1">
                  {alertsData?.unreadAlerts?.length === 0 ? (
                    <p className="text-xs text-muted-foreground italic px-2">Aucune alerte pour le moment.</p>
                  ) : (
                    <div className="divide-y divide-slate-50">
                      {alertsData?.unreadAlerts?.slice(0, 5).map((a: any) => (
                        <div 
                          key={a.id} 
                          className={cn(
                            "flex gap-3 items-center px-2 py-3 transition-all group relative cursor-pointer hover:bg-slate-50 rounded-lg",
                            a.type === 'CRITICAL_STOCK' ? "bg-red-50/30" :
                            a.type === 'STOCKOUT_RISK' ? "bg-amber-50/30" :
                            "bg-white"
                          )}
                        >
                          <div className={cn(
                             "h-8 w-8 rounded-full flex items-center justify-center shrink-0",
                             a.type === 'CRITICAL_STOCK' ? "bg-white text-red-500" :
                             a.type === 'STOCKOUT_RISK' ? "bg-white text-amber-500" :
                             "bg-slate-50 text-slate-400"
                          )}>
                             <AlertCircle className="h-4 w-4" />
                          </div>
                          
                          <div className="flex-1 min-w-0 pr-16">
                            <p className="text-[10px] text-slate-400 mb-0.5">
                               {format(new Date(a.createdAt), 'dd MMM HH:mm', { locale: fr })}
                            </p>
                            <p className="text-xs font-medium text-slate-700 leading-snug truncate">
                               {a.message.replace(/^(alerte|danger)\s*:\s*/i, '')}
                            </p>
                          </div>

                          {/* Quick Actions (Hover) */}
                          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                             <Link 
                                href={`/dashboard/product/${a.productId}`}
                                className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-400 hover:text-primary transition-all shadow-sm"
                                title="ouvrir"
                             >
                                <ExternalLink className="h-3.5 w-3.5" />
                             </Link>
                             <button
                                onClick={() => deleteAlert({ variables: { id: a.id } })}
                                className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-400 hover:text-red-500 transition-all shadow-sm"
                                title="Supprimer"
                             >
                                <Trash2 className="h-3.5 w-3.5" />
                             </button>
                          </div>
                        </div>
                      ))}
                      
                      <div className="pt-2 px-2">
                        <button 
                          onClick={() => window.dispatchEvent(new CustomEvent('michi:open-notifications'))}
                          className="w-full py-2 text-[10px] font-bold text-primary tracking-widest bg-primary/5 hover:bg-primary/10 rounded-lg transition-all"
                        >
                          Voir toutes les alertes
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Optimized Stock / Real Products */}
              <div className="bg-white rounded-xl border p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold">Stock optimisé</h3>
                  <div className="p-1.5 bg-emerald-50 rounded-full">
                    <Package className="h-4 w-4 text-emerald-600" />
                  </div>
                </div>
                
                <div className="space-y-1">
                   {omnichannelData?.omnichannelInventory?.length === 0 ? (
                     <p className="text-xs text-muted-foreground italic px-2">Aucun produit synchronisé.</p>
                   ) : (
                     <div className="divide-y divide-slate-50">
                         {omnichannelData?.omnichannelInventory?.slice(0, 5).map((p: any) => (
                          <div 
                            key={p.id} 
                            onClick={() => setSelectedProductId(p.id || p.sku)}
                            className="group relative flex items-center justify-between px-2 py-3 hover:bg-slate-50 transition-all cursor-pointer rounded-lg"
                          >
                            <div className="min-w-0 flex-1 pr-4">
                              <p className="text-xs font-medium text-foreground truncate">{p.title}</p>
                              <p className="text-[10px] text-muted-foreground">SKU: {p.sku}</p>
                            </div>
                            
                            <div className="flex items-center gap-3">
                              <div className="text-right group-hover:opacity-0 transition-opacity">
                                <p className="text-xs font-bold text-foreground">{p.totalStock}</p>
                                <p className="text-[9px] text-muted-foreground">Unités</p>
                              </div>
                              
                              {/* Quick Actions (Hover) */}
                              <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-all">
                                <button 
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedProductId(p.id || p.sku);
                                  }}
                                  className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-400 hover:text-primary transition-all shadow-none flex items-center gap-1.5"
                                >
                                  <Eye className="h-3.5 w-3.5" />
                                  <span className="text-[10px] font-bold tracking-widest">Ouvrir</span>
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                        
                        <div className="pt-2 px-2">
                          <button 
                            onClick={() => router.push('/dashboard?tab=inventory')}
                            className="w-full py-2 text-[10px] font-bold text-emerald-600 tracking-widest bg-emerald-50 hover:bg-emerald-100 rounded-lg transition-all"
                          >
                            Gérer l'inventaire
                          </button>
                        </div>
                     </div>
                   )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'inventory' && (
          <div className="space-y-5 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="space-y-4">
              {productsLoading && !omnichannelData ? (
                <LoadingState message="chargement du catalogue..." />
              ) : (
                <ProductTable 
                  products={(omnichannelData?.omnichannelInventory || []) as OmnichannelProduct[]} 
                  query={searchQuery}
                  onRowClick={(id) => setSelectedProductId(id)}
                />
              )}
            </div>
          </div>
        )}

        {activeTab === 'sources' && (
          <div className="space-y-5 animate-in fade-in slide-in-from-bottom-2 duration-500">
             <div className="bg-white rounded-2xl border border-slate-100 p-6">
                <div className="flex items-center gap-3 mb-5">
                   <div className="p-3 bg-primary/5 rounded-2xl text-primary">
                      <Database className="h-5 w-5" />
                   </div>
                   <div>
                      <h2 className="text-sm font-extrabold text-slate-900 tracking-widest">Connecteurs de données</h2>
                      <p className="text-[10px] text-slate-500 font-medium italic">Connectez vos plateformes pour synchroniser votre inventaire Michi en temps réel.</p>
                   </div>
                </div>

                <ConnectorsGrid onImport={handleCSVUpload} />
             </div>

             <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-6 bg-slate-50/50 rounded-2xl border border-slate-100">
                   <p className="text-[10px] font-bold text-slate-400 tracking-widest mb-2">État de santé API</p>
                   <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                      <span className="text-xs font-bold text-slate-900">Systèmes opérationnels</span>
                   </div>
                </div>
                <div className="p-8 bg-slate-50/50 rounded-2xl border border-slate-100">
                   <p className="text-[10px] font-bold text-slate-400 tracking-widest mb-2">Dernière synchronisation</p>
                   <p className="text-xs font-bold text-slate-900">Il y a 5 minutes (automatique)</p>
                </div>
             </div>
          </div>
        )}
      </div>

      <ProductQuickView 
        productId={selectedProductId}
        onClose={() => setSelectedProductId(null)}
      />
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="h-6 w-6 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
