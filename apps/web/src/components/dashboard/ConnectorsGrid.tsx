'use client';

import React from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { createPortal } from 'react-dom';
import { useQuery, useMutation, gql } from '@apollo/client';
import { 
  ShoppingCart, 
  Globe, 
  Anchor, 
  Layers, 
  Upload, 
  Plus, 
  Loader2, 
  PowerOff, 
  CheckCircle2 
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { LoadingState } from '../ui/LoadingState';
import { GET_OMNICHANNEL_INVENTORY } from '@/graphql/queries/getOmnichannelInventory';
import { GET_DASHBOARD_STATS } from '@/graphql/queries/getDashboardStats';
import { GET_UNREAD_ALERTS } from '@/graphql/queries/getUnreadAlerts';
import { AddSourcePanel } from './AddSourcePanel';

export const GET_SOURCES = gql`
  query GetSources {
    sources {
      id
      name
      platform
      connected
      lastSyncAt
      healthStatus
    }
  }
`;

export const TOGGLE_SOURCE = gql`
  mutation ToggleSource($platform: String!, $connected: Boolean!) {
    toggleSource(platform: $platform, connected: $connected) {
      id
      connected
    }
  }
`;

const ICON_MAP: Record<string, any> = {
  shopify: ShoppingCart,
  woocommerce: Globe,
  amazon: Anchor,
};

const COLOR_MAP: Record<string, string> = {
  shopify: 'text-emerald-600',
  woocommerce: 'text-indigo-600',
  amazon: 'text-orange-600',
};

const BG_MAP: Record<string, string> = {
  shopify: 'bg-emerald-50',
  woocommerce: 'bg-indigo-50',
  amazon: 'bg-orange-50',
};

interface ConnectorsGridProps {
  onImport?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  isAdmin?: boolean;
}

import { useTranslations, useFormatter } from 'next-intl';
import { useStore } from '@/context/StoreContext';

export function ConnectorsGrid({ onImport, isAdmin = false }: ConnectorsGridProps) {
  const t = useTranslations('dashboard.connectors');
  const format = useFormatter();
  const [showAddSourcePanel, setShowAddSourcePanel] = React.useState(false);
  const [showSuccess, setShowSuccess] = React.useState(false);
  const [confirmDelete, setConfirmDelete] = React.useState<string | null>(null);
  const searchParams = useSearchParams();
  const router = useRouter();
  const status = searchParams.get('status');

  const { currentOrganization } = useStore();
  const { data, loading, refetch } = useQuery(GET_SOURCES, {
    fetchPolicy: 'cache-and-network',
    skip: !currentOrganization
  });
  const [toggleSource, { loading: toggling }] = useMutation(TOGGLE_SOURCE, {
    refetchQueries: [
      { query: GET_SOURCES },
      { query: GET_OMNICHANNEL_INVENTORY },
      { query: GET_DASHBOARD_STATS },
      { query: GET_UNREAD_ALERTS }
    ]
  });

  React.useEffect(() => {
    if (status === 'connected') {
      setShowSuccess(true);
      const timer = setTimeout(() => {
        setShowSuccess(false);
        router.replace('/dashboard?tab=sources');
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [status, router]);

  const handleToggle = async (platform: string, currentStatus: boolean) => {
    try {
      await toggleSource({
        variables: {
          platform,
          connected: !currentStatus
        }
      });
    } catch (err) {
      console.error("error toggling source:", err);
    }
  };

  if (loading && !data) return (
    <LoadingState size="sm" />
  );

  // Filter sources to only show connected ones
  const activeSources = data?.sources?.filter((s: any) => s.connected) || [];
  const connectedPlatforms = activeSources.map((s: any) => s.platform);

  return (
    <section className="space-y-4 relative animate-in fade-in duration-500">
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {/* CSV Import Card */}
        <div className="group relative bg-white border border-slate-100 rounded-lg p-4 transition-all hover:border-primary/30">
           <div className="flex items-center justify-between mb-2">
              <div className="p-2.5 rounded-lg bg-slate-50 text-slate-400 group-hover:bg-primary/5 group-hover:text-primary transition-colors">
                 <Layers className="h-4 w-4" />
              </div>
              <div className="flex items-center gap-1.5 text-[9px] font-bold text-slate-400">
                 <div className="h-1.5 w-1.5 rounded-full bg-slate-300" />
                 {t('manual')}
              </div>
           </div>
           
           <div className="space-y-1 mb-4">
              <h3 className="text-sm font-bold text-slate-900">{t('manual')} (CSV)</h3>
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] text-slate-400 font-bold tracking-wider">{t('apiHealth')}</span>
                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-lg bg-emerald-50 text-emerald-600">
                    {t('available')}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[9px] text-slate-400 font-bold">{t('lastImport')}</span>
                  <span className="text-[9px] text-slate-600 font-bold italic">{t('manual')}</span>
                </div>
              </div>
           </div>
           
           <input 
             type="file" 
             id="csv-connector-upload" 
             className="hidden" 
             accept=".csv" 
             onChange={onImport} 
           />
           <label 
             htmlFor={isAdmin ? "csv-connector-upload" : ""}
             className={cn(
               "w-full py-2.5 rounded-lg text-[10px] font-bold transition-all flex items-center justify-center gap-2",
               isAdmin 
                ? "bg-primary text-white hover:opacity-90 cursor-pointer" 
                : "bg-slate-100 text-slate-400 cursor-not-allowed opacity-60"
             )}
           >
              <Upload className="h-3.5 w-3.5" />
              {isAdmin ? t('header.export') : t('restricted')}
           </label>
        </div>

        {/* Add Source Button Card */}
        <button 
          onClick={() => isAdmin && setShowAddSourcePanel(true)}
          disabled={!isAdmin}
          className={cn(
            "group relative bg-slate-50 border border-dashed border-slate-200 rounded-lg p-4 transition-all flex flex-col items-center justify-center text-center gap-3 min-h-[160px] focus:ring-0 focus:outline-none",
            isAdmin ? "hover:bg-white hover:border-primary/50" : "opacity-50 cursor-not-allowed"
          )}
        >
          <div className={cn(
            "p-3 rounded-lg bg-white text-slate-400 shadow-sm",
            isAdmin && "group-hover:text-primary transition-colors"
          )}>
            <Plus className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <p className="text-[11px] font-extrabold text-slate-900">{t('newSource')}</p>
            <p className="text-[9px] text-slate-400 font-bold">{isAdmin ? t('adminOnly') : t('restricted')}</p>
          </div>
        </button>

        {activeSources.map((source: any) => {
          const platformKey = source.platform?.toLowerCase() || '';
          const Icon = ICON_MAP[platformKey] || Globe;
          return (
            <div 
              key={source.id} 
              className="group relative bg-white border border-primary/10 bg-primary/[0.02] rounded-lg p-4 transition-all hover:border-primary/30"
            >
              <div className="flex items-center justify-between mb-2">
                <div className={cn("p-2.5 rounded-lg", BG_MAP[platformKey] || "bg-slate-50")}>
                  <Icon className={cn("h-4 w-4", COLOR_MAP[platformKey] || "text-slate-400")} />
                </div>
                
                <div className="flex items-center gap-1.5 text-[9px] font-bold text-emerald-600">
                  <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  {t('active')}
                </div>
              </div>

              <div className="space-y-1 mb-4">
                <h3 className="text-sm font-bold text-slate-900">{source.platform}</h3>
                <div className="flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] text-slate-400 font-bold">{t('apiHealth')} API</span>
                    <span className={cn(
                      "text-[9px] font-bold px-1.5 py-0.5 rounded-lg",
                      source.healthStatus === 'HEALTHY' ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-600"
                    )}>
                      {source.healthStatus === 'HEALTHY' ? 'Healthy' : source.healthStatus || 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] text-slate-400 font-bold">{t('lastSyncAt')}</span>
                    <span className="text-[9px] text-slate-600 font-bold">
                      {source.lastSyncAt ? format.dateTime(new Date(source.lastSyncAt)) : 'Jamais'}
                    </span>
                  </div>
                </div>
              </div>

              <button 
                onClick={() => isAdmin && setConfirmDelete(source.platform)}
                disabled={toggling || !isAdmin}
                className={cn(
                  "w-full py-2.5 rounded-lg text-[10px] font-bold transition-all flex items-center justify-center gap-2 border border-transparent shadow-sm",
                  isAdmin 
                    ? "bg-slate-100 text-slate-600 hover:bg-red-50 hover:text-red-600" 
                    : "bg-slate-50 text-slate-300 cursor-not-allowed",
                  toggling && "opacity-50"
                )}
              >
                {toggling ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                   <>
                     <PowerOff className="h-3.5 w-3.5" />
                     {isAdmin ? t('disconnect') : t('readonly')}
                   </>
                )}
              </button>
            </div>
          );
        })}
      </div>

      {/* Add Source Side Panel */}
      <AddSourcePanel 
        isOpen={showAddSourcePanel}
        onClose={() => setShowAddSourcePanel(false)}
        onSuccess={() => {
          refetch();
          setShowSuccess(true);
        }}
        connectedPlatforms={connectedPlatforms}
      />

      {/* Legacy Success Celebration Overlay (kept for visual feedback) */}
      {typeof document !== 'undefined' && createPortal(
        <AnimatePresence>
          {showSuccess && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-[200] flex items-center justify-center bg-slate-900/90 backdrop-blur-xl"
              onClick={() => setShowSuccess(false)}
            >
              <motion.div 
                initial={{ scale: 0.5, y: 50 }}
                animate={{ scale: 1, y: 0 }}
                className="text-center space-y-6 p-8"
              >
                <div className="relative inline-block">
                  <motion.div 
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                    className="w-24 h-24 bg-emerald-500 rounded-lg flex items-center justify-center shadow-[0_0_50px_rgba(16,185,129,0.5)]"
                  >
                    <CheckCircle2 className="h-12 w-12 text-white" />
                  </motion.div>
                </div>
                
                <div className="space-y-2">
                  <h2 className="text-3xl font-extrabold text-white tracking-tight">
                    {t('success.title')}
                  </h2>
                  <p className="text-slate-400 text-sm font-medium tracking-wide">{t('success.subtitle')}</p>
                </div>
                <p className="text-[10px] text-slate-500 font-bold  tracking-[0.2em] animate-pulse">Chargement intelligent...</p>
                
                <button 
                  onClick={() => setShowSuccess(false)}
                  className="mt-8 px-8 py-3 bg-white text-slate-900 rounded-lg font-bold text-xs hover:bg-slate-50 transition-colors focus:ring-0 focus:outline-none"
                >
                  {t('success.button')}
                </button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>,
        document.body
      )}
      
      {/* Confirmation Modale Déconnexion Destructive */}
      <AnimatePresence>
        {confirmDelete && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setConfirmDelete(null)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }} className="relative w-full max-w-sm bg-white rounded-lg p-8 shadow-2xl border border-red-100">
               <div className="w-14 h-14 bg-red-50 rounded-lg flex items-center justify-center mb-6">
                 <PowerOff className="h-6 w-6 text-red-600" />
               </div>
               <h3 className="text-lg font-bold text-slate-900 mb-2 tracking-tight">{t('confirmDelete.title')}</h3>
               <p className="text-[11px] text-slate-500 font-medium leading-relaxed mb-8">
                 {t('confirmDelete.description', { platform: confirmDelete })}
               </p>
               <div className="flex gap-3">
                 <button onClick={() => setConfirmDelete(null)} className="flex-1 py-3.5 text-[10px] font-extrabold  text-slate-400 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors focus:ring-0 focus:outline-none">{t('cancel')}</button>
                 <button 
                   onClick={() => {
                     handleToggle(confirmDelete!, true);
                     setConfirmDelete(null);
                   }} 
                   className="flex-1 py-3.5 text-[10px] font-extrabold  text-white bg-red-600 rounded-lg hover:bg-red-700 transition-shadow shadow-lg shadow-red-200 focus:ring-0 focus:outline-none"
                 >
                   {t('confirm')}
                 </button>
               </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {toggling && (
         <div className="fixed inset-0 z-[110] flex items-center justify-center bg-white/40 backdrop-blur-sm animate-in fade-in duration-300">
            <LoadingState size="lg" message="{t('updating')}" />
         </div>
      )}
    </section>
  );
}
