'use client';

import React from 'react';
import { useQuery, useMutation, gql } from '@apollo/client';
import { 
  ShoppingCart, 
  Globe, 
  Anchor, 
  CheckCircle2, 
  PowerOff,
  Plus,
  Layers,
  Upload,
  X,
  ArrowRight,
  ShieldCheck,
  Search,
  Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { LoadingState } from '../ui/LoadingState';
import { motion, AnimatePresence } from 'framer-motion';
import { useSearchParams, useRouter } from 'next/navigation';
import { TRIGGER_MOCK_DATA_SYNC } from '@/graphql/mutations/syncInventory';
import { GET_OMNICHANNEL_INVENTORY } from '@/graphql/queries/getOmnichannelInventory';
import { GET_DASHBOARD_STATS } from '@/graphql/queries/getDashboardStats';
import { GET_UNREAD_ALERTS } from '@/graphql/queries/getUnreadAlerts';

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
}

export function ConnectorsGrid({ onImport }: ConnectorsGridProps) {
  const [wizardPlatform, setWizardPlatform] = React.useState<string | null>(null);
  const [shopUrl, setShopUrl] = React.useState('');
  const [amazonSellerId, setAmazonSellerId] = React.useState('');
  const [amazonToken, setAmazonToken] = React.useState('');
  const [wooUrl, setWooUrl] = React.useState('');
  const [wooKey, setWooKey] = React.useState('');
  const [wooSecret, setWooSecret] = React.useState('');
  
  const [showSuccess, setShowSuccess] = React.useState(false);
  const [confirmDelete, setConfirmDelete] = React.useState<string | null>(null);
  const [syncedPlatform, setSyncedPlatform] = React.useState<string>('');
  const [isSyncing, setIsSyncing] = React.useState(false);
  
  const searchParams = useSearchParams();
  const router = useRouter();
  const status = searchParams.get('status');

  const { data, loading, refetch } = useQuery(GET_SOURCES);
  const [toggleSource, { loading: toggling }] = useMutation(TOGGLE_SOURCE, {
    refetchQueries: [
      { query: GET_SOURCES },
      { query: GET_OMNICHANNEL_INVENTORY },
      { query: GET_DASHBOARD_STATS },
      { query: GET_UNREAD_ALERTS }
    ]
  });

  const [triggerMockSync] = useMutation(TRIGGER_MOCK_DATA_SYNC, {
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
      // Nettoyer l'URL et masquer l'overlay après 3 secondes
      const timer = setTimeout(() => {
        setShowSuccess(false);
        router.replace('/dashboard?tab=sources');
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [status, router]);

  const handleConnect = (platform: string) => {
    setWizardPlatform(platform);
  };

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

  const handlePlatformAuth = async (platform: string) => {
    setIsSyncing(true);
    if (platform === 'shopify') {
      if (!shopUrl) {
        setIsSyncing(false);
        return;
      }
      const cleanShop = shopUrl.replace('https://', '').replace('.myshopify.com', '');
      window.location.href = `http://localhost:8000/api/shopify/auth?shop=${cleanShop}`;
    } else {
      // Simulation pour Amazon/WooCommerce
      try {
        // 1. Connecter dans la base
        await handleToggle(platform, false);
        
        // 2. Déclencher la synchronisation des données (Mock)
        // On attend la fin effective de la génération des produits
        await triggerMockSync();
        
        setWizardPlatform(null);
        setSyncedPlatform(platform);
        setShowSuccess(true);
        
        // Nettoyer l'URL et masquer l'overlay après 3 secondes
        setTimeout(() => {
          setShowSuccess(false);
          router.replace('/dashboard?tab=sources');
        }, 3000);

      } catch (err) {
        console.error("Simulation error:", err);
      } finally {
        setIsSyncing(false);
      }
    }
  };

  if (loading) return (
    <LoadingState size="sm" />
  );

  return (
    <section className="space-y-4 relative">
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {/* CSV Import Card */}
        <div className="group relative bg-white border rounded-xl p-4 transition-all hover:border-primary/30">
           <div className="flex items-center justify-between mb-2">
              <div className="p-2.5 rounded-xl bg-slate-50 text-slate-400 group-hover:bg-primary/5 group-hover:text-primary transition-colors">
                 <Layers className="h-4 w-4" />
              </div>
              <div className="flex items-center gap-1.5 text-[9px] font-bold tracking-widest text-slate-400">
                 <div className="h-1.5 w-1.5 rounded-full bg-slate-300" />
                 Manuel
              </div>
           </div>
           
           <div className="space-y-1 mb-4">
              <h3 className="text-sm font-bold text-slate-900">Fichier CSV</h3>
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] text-slate-400 font-bold tracking-wider">Santé</span>
                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-md bg-emerald-50 text-emerald-600">
                    Disponible
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[9px] text-slate-400 font-bold tracking-wider">Dernier import</span>
                  <span className="text-[9px] text-slate-600 font-bold italic">Manuel</span>
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
             htmlFor="csv-connector-upload"
             className="w-full py-2.5 rounded-lg text-[10px] font-bold tracking-widest transition-all bg-primary text-white hover:opacity-90 shadow-none flex items-center justify-center gap-2 cursor-pointer"
           >
              <Upload className="h-3.5 w-3.5" />
              Importer
           </label>
        </div>

        {data?.sources?.map((source: any) => {
          const Icon = ICON_MAP[source.platform] || Globe;
          return (
            <div 
              key={source.id} 
              className={cn(
                "group relative bg-white border rounded-xl p-4 transition-all hover:border-primary/30",
                source.connected && "border-primary/10 bg-primary/[0.02]"
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <div className={cn("p-2.5 rounded-xl", BG_MAP[source.platform] || "bg-slate-50")}>
                  <Icon className={cn("h-4 w-4", COLOR_MAP[source.platform] || "text-slate-400")} />
                </div>
                
                <div className={cn(
                  "flex items-center gap-1.5 text-[9px] font-bold tracking-widest",
                  source.connected ? "text-emerald-600" : "text-slate-400"
                )}>
                  <div className={cn("h-1.5 w-1.5 rounded-full", source.connected ? "bg-emerald-500" : "bg-slate-300")} />
                  {source.connected ? "Actif" : "Inactif"}
                </div>
              </div>

              <div className="space-y-1 mb-4">
                <h3 className="text-sm font-bold text-slate-900">{source.name}</h3>
                <div className="flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] text-slate-400 font-bold tracking-wider">Santé API</span>
                    <span className={cn(
                      "text-[9px] font-bold px-1.5 py-0.5 rounded-md",
                      source.healthStatus === 'HEALTHY' ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-600"
                    )}>
                      {source.healthStatus === 'HEALTHY' ? 'Healthy' : source.healthStatus || 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] text-slate-400 font-bold tracking-wider">Dernière sync</span>
                    <span className="text-[9px] text-slate-600 font-bold">
                      {source.lastSyncAt ? new Date(source.lastSyncAt).toLocaleDateString() : 'Jamais'}
                    </span>
                  </div>
                </div>
              </div>
              
              <button 
                onClick={() => source.connected ? setConfirmDelete(source.platform) : handleConnect(source.platform)}
                disabled={toggling}
                className={cn(
                  "w-full py-2.5 rounded-lg text-[10px] font-bold tracking-widest transition-all flex items-center justify-center gap-2",
                  source.connected 
                    ? "bg-slate-100 text-slate-600 hover:bg-red-50 hover:text-red-600 border border-transparent shadow-sm" 
                    : "bg-primary text-white hover:opacity-90 shadow-[0_4px_12px_rgba(0,0,0,0.1)]"
                )}
              >
                {source.connected ? (
                   <>
                     <PowerOff className="h-3.5 w-3.5" />
                     Déconnecter
                   </>
                ) : (
                   <>
                     <Plus className="h-3.5 w-3.5" />
                     Connecter
                   </>
                )}
              </button>
            </div>
          );
        })}
      </div>

      {/* Onboarding Wizard Modal */}
      <AnimatePresence>
        {wizardPlatform && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setWizardPlatform(null)}
              className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-100"
            >
              {/* Header */}
              <div className="p-6 border-b border-slate-50 flex items-center justify-between bg-slate-50/50">
                <div className="flex items-center gap-3">
                  <div className={cn("p-2.5 rounded-xl", BG_MAP[wizardPlatform])}>
                    {wizardPlatform === 'shopify' && <ShoppingCart className="h-5 w-5 text-emerald-600" />}
                  </div>
                  <div>
                    <h2 className="text-sm font-extrabold text-slate-900 tracking-widest">
                      Connexion {wizardPlatform}
                    </h2>
                    <p className="text-[9px] text-slate-500 font-bold tracking-tighter">Étape 1 sur 2 : Identification</p>
                  </div>
                </div>
                <button 
                  onClick={() => setWizardPlatform(null)}
                  className="p-2 hover:bg-white rounded-full transition-colors border border-transparent hover:border-slate-100"
                >
                  <X className="h-4 w-4 text-slate-400" />
                </button>
              </div>

              {/* Body */}
              <div className="p-8 space-y-8">
                {/* --- Section 1: Instructions & Platform info --- */}
                <div className="space-y-2">
                  <h3 className="text-lg font-bold text-slate-900 tracking-tight">
                    {wizardPlatform === 'shopify' && "Recherchez votre boutique"}
                    {wizardPlatform === 'amazon' && "Connectez votre compte Vendeur"}
                    {wizardPlatform === 'woocommerce' && "Liez votre boutique WooCommerce"}
                  </h3>
                  <p className="text-[11px] text-slate-500 leading-relaxed font-medium">
                    {wizardPlatform === 'shopify' && "Saisissez l'URL de votre boutique Shopify. Nous vous redirigerons vers leur interface sécurisée pour autoriser Michi."}
                    {wizardPlatform === 'amazon' && "Connectez-vous à Seller Central pour récupérer votre Seller ID et votre Token MWS Michigan v2."}
                    {wizardPlatform === 'woocommerce' && "Générez vos clés API Consumer dans WooCommerce > Réglages > Avancé > API REST."}
                  </p>
                </div>

                {/* --- Section 2: Form Fields --- */}
                <div className="space-y-6">
                  {/* SHOPIFY FORM */}
                  {wizardPlatform === 'shopify' && (
                    <div className="group space-y-2">
                       <label className="text-[10px] font-bold text-slate-400 tracking-widest ml-1">URL de la boutique</label>
                       <div className="relative">
                         <div className="absolute left-4 top-1/2 -translate-y-1/2 p-1.5 bg-slate-50 rounded-lg group-focus-within:bg-emerald-50 transition-colors">
                           <Search className="h-3.5 w-3.5 text-slate-400 group-focus-within:text-emerald-600" />
                         </div>
                         <input 
                           type="text"
                           placeholder="ma-boutique-elite"
                           value={shopUrl}
                           onChange={(e) => setShopUrl(e.target.value)}
                           className="w-full h-12 pl-14 pr-32 bg-slate-50 border-2 border-transparent rounded-2xl text-xs font-bold text-slate-900 focus:bg-white focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/5 outline-none transition-all"
                         />
                         <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                           <span className="text-[10px] font-bold text-slate-400 tracking-tight">.myshopify.com</span>
                         </div>
                       </div>
                    </div>
                  )}

                  {/* AMAZON FORM */}
                  {wizardPlatform === 'amazon' && (
                    <div className="space-y-4">
                      <div className="group space-y-2">
                        <label className="text-[10px] font-bold text-slate-400 tracking-widest ml-1">Seller ID</label>
                        <input 
                          type="text"
                          placeholder="A123456789BCDE"
                          value={amazonSellerId}
                          onChange={(e) => setAmazonSellerId(e.target.value)}
                          className="w-full h-12 px-6 bg-slate-50 border-2 border-transparent rounded-2xl text-xs font-bold text-slate-900 focus:bg-white focus:border-orange-500 focus:ring-4 focus:ring-orange-500/5 outline-none transition-all placeholder:text-slate-300"
                        />
                      </div>
                      <div className="group space-y-2">
                        <label className="text-[10px] font-bold text-slate-400 tracking-widest ml-1">MWS Auth Token</label>
                        <input 
                          type="password"
                          placeholder="amzn.mws.xxxx-xxxx-xxxx"
                          value={amazonToken}
                          onChange={(e) => setAmazonToken(e.target.value)}
                          className="w-full h-12 px-6 bg-slate-50 border-2 border-transparent rounded-2xl text-xs font-bold text-slate-900 focus:bg-white focus:border-orange-500 focus:ring-4 focus:ring-orange-500/5 outline-none transition-all placeholder:text-slate-300"
                        />
                      </div>
                    </div>
                  )}

                  {/* WOOCOMMERCE FORM */}
                  {wizardPlatform === 'woocommerce' && (
                    <div className="space-y-4">
                      <div className="group space-y-2">
                        <label className="text-[10px] font-bold text-slate-400 tracking-widest ml-1">URL du site</label>
                        <input 
                          type="text"
                          placeholder="https://ma-boutique.com"
                          value={wooUrl}
                          onChange={(e) => setWooUrl(e.target.value)}
                          className="w-full h-12 px-6 bg-slate-50 border-2 border-transparent rounded-2xl text-xs font-bold text-slate-900 focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/5 outline-none transition-all placeholder:text-slate-300"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="group space-y-2">
                          <label className="text-[10px] font-bold text-slate-400 tracking-widest ml-1">Consumer Key</label>
                          <input 
                            type="text"
                            placeholder="ck_xxxx"
                            value={wooKey}
                            onChange={(e) => setWooKey(e.target.value)}
                            className="w-full h-12 px-6 bg-slate-50 border-2 border-transparent rounded-2xl text-xs font-bold text-slate-900 focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/5 outline-none transition-all placeholder:text-slate-300"
                          />
                        </div>
                        <div className="group space-y-2">
                          <label className="text-[10px] font-bold text-slate-400 tracking-widest ml-1">Secret Key</label>
                          <input 
                            type="password"
                            placeholder="cs_xxxx"
                            value={wooSecret}
                            onChange={(e) => setWooSecret(e.target.value)}
                            className="w-full h-12 px-6 bg-slate-50 border-2 border-transparent rounded-2xl text-xs font-bold text-slate-900 focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/5 outline-none transition-all placeholder:text-slate-300"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  <div className={cn(
                    "flex items-center gap-3 p-4 rounded-2xl border",
                    wizardPlatform === 'shopify' ? "bg-emerald-50 border-emerald-100/50" :
                    wizardPlatform === 'amazon' ? "bg-orange-50 border-orange-100/50" :
                    "bg-indigo-50 border-indigo-100/50"
                  )}>
                    <ShieldCheck className={cn(
                      "h-5 w-5 shrink-0",
                      wizardPlatform === 'shopify' ? "text-emerald-600" :
                      wizardPlatform === 'amazon' ? "text-orange-600" :
                      "text-indigo-600"
                    )} />
                    <p className={cn(
                      "text-[10px] font-medium leading-relaxed",
                      wizardPlatform === 'shopify' ? "text-emerald-800" :
                      wizardPlatform === 'amazon' ? "text-orange-800" :
                      "text-indigo-800"
                    )}>
                      {wizardPlatform === 'shopify' && "L'authentification est gérée par Shopify. Michi n'aura jamais accès à votre mot de passe."}
                      {wizardPlatform === 'amazon' && "Vos identifiants sont cryptés selon les standards AES-256 avant transmission aux APIs Seller Central."}
                      {wizardPlatform === 'woocommerce' && "Utilisez des clés en lecture seule pour une sécurité maximale. Michi n'a pas besoin de droit d'écriture."}
                    </p>
                  </div>
                </div>

                {/* --- Section 3: Action Buttons --- */}
                <div className="pt-4 space-y-3">
                  <button 
                    onClick={() => handlePlatformAuth(wizardPlatform)}
                    disabled={
                      (wizardPlatform === 'shopify' && !shopUrl) || 
                      (wizardPlatform === 'amazon' && (!amazonSellerId || !amazonToken)) ||
                      (wizardPlatform === 'woocommerce' && (!wooUrl || !wooKey || !wooSecret)) ||
                      toggling || isSyncing
                    }
                    className="w-full h-14 bg-slate-900 text-white rounded-2xl text-xs font-bold tracking-widest hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-3 group"
                  >
                    {isSyncing ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Synchronisation...
                      </>
                    ) : (
                      <>
                        Continuer vers {wizardPlatform === 'shopify' ? 'Shopify' : wizardPlatform === 'amazon' ? 'Amazon Seller' : 'WooCommerce'}
                        <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                      </>
                    )}
                  </button>
                  
                  {/* Simulation Button for Dev */}
                  <button 
                    onClick={() => {
                       handlePlatformAuth(wizardPlatform);
                    }}
                    disabled={isSyncing}
                    className="w-full h-10 border border-slate-200 text-slate-500 rounded-xl text-[10px] font-bold tracking-widest hover:bg-slate-50 transition-all flex items-center justify-center gap-2"
                  >
                    {isSyncing ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : null}
                    Simulation Michi (Mock Data)
                  </button>

                  <p className="text-center text-[9px] text-slate-400 font-bold mt-4 tracking-widest">
                    Secured by Michi Auth Gateway
                  </p>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Success Celebration Overlay */}
      <AnimatePresence>
        {showSuccess && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[200] flex items-center justify-center bg-slate-900/90 backdrop-blur-xl"
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
                  className="w-24 h-24 bg-emerald-500 rounded-full flex items-center justify-center shadow-[0_0_50px_rgba(16,185,129,0.5)]"
                >
                  <CheckCircle2 className="h-12 w-12 text-white" />
                </motion.div>
                <div className="absolute -top-4 -right-4 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-lg animate-bounce">
                  {syncedPlatform === 'amazon' ? <Anchor className="h-4 w-4 text-orange-600" /> :
                   syncedPlatform === 'woocommerce' ? <Globe className="h-4 w-4 text-indigo-600" /> :
                   <ShoppingCart className="h-4 w-4 text-emerald-600" />}
                </div>
              </div>
              
              <div className="space-y-2">
                <h2 className="text-3xl font-extrabold text-white tracking-tight">
                  {syncedPlatform.charAt(0).toUpperCase() + syncedPlatform.slice(1) || 'Michi'} Connecté !
                </h2>
                <p className="text-slate-400 text-sm font-medium tracking-wide">Votre boutique {syncedPlatform} est synchronisée</p>
              </div>

              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: "100%" }}
                transition={{ duration: 2.5 }}
                className="h-1 bg-emerald-500 rounded-full mx-auto max-w-[200px]"
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Confirmation Modale Déconnexion Destructive */}
      <AnimatePresence>
        {confirmDelete && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setConfirmDelete(null)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }} className="relative w-full max-w-sm bg-white rounded-3xl p-8 shadow-2xl border border-red-100">
               <div className="w-14 h-14 bg-red-50 rounded-2xl flex items-center justify-center mb-6">
                 <PowerOff className="h-6 w-6 text-red-600" />
               </div>
               <h3 className="text-lg font-bold text-slate-900 mb-2 tracking-tight">Supprimer les données ?</h3>
               <p className="text-[11px] text-slate-500 font-medium leading-relaxed mb-8">
                 En déconnectant <span className="text-slate-900 font-extrabold">{confirmDelete}</span>, vous perdrez instantanément tous les produits et l'historique de ventes associés à ce canal. Cette action est irréversible.
               </p>
               <div className="flex gap-3">
                 <button onClick={() => setConfirmDelete(null)} className="flex-1 py-3.5 text-[10px] font-extrabold tracking-widest text-slate-400 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors">Annuler</button>
                 <button 
                   onClick={() => {
                     handleToggle(confirmDelete!, true);
                     setConfirmDelete(null);
                   }} 
                   className="flex-1 py-3.5 text-[10px] font-extrabold tracking-widest text-white bg-red-600 rounded-xl hover:bg-red-700 transition-shadow shadow-lg shadow-red-200"
                 >
                   Confirmer
                 </button>
               </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {toggling && (
         <div className="fixed inset-0 z-[110] flex items-center justify-center bg-white/40 backdrop-blur-sm animate-in fade-in duration-300">
            <LoadingState size="lg" message="mise à jour du canal..." />
         </div>
      )}
    </section>
  );
}
