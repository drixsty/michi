'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, gql, useApolloClient } from '@apollo/client';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { 
  Building2, 
  History, 
  Terminal, 
  ShieldAlert, 
  Search, 
  UserSquare2, 
  LogOut, 
  Play, 
  StopCircle, 
  Package, 
  TrendingDown, 
  Copy, 
  Check, 
  Activity,
  UserCheck
} from 'lucide-react';

// ── QUERIES GRAPHQL ──────────────────────────────────────────────────────────

const SUPPORT_ORGANIZATIONS_QUERY = gql`
  query SupportOrganizations {
    supportOrganizations {
      id
      name
      slug
      plan
      subscriptionStatus
      createdAt
    }
  }
`;

const SUPPORT_AUDIT_LOGS_QUERY = gql`
  query SupportAuditLogs {
    supportAuditLogs {
      id
      supportUserEmail
      impersonatedOrgName
      action
      flowId
      createdAt
    }
  }
`;

// Queries client (exécutées sous impersonation)
const GET_CLIENT_PRODUCTS = gql`
  query GetClientProducts {
    products {
      id
      title
      sku
      currentStock
      leadTime
      moq
    }
  }
`;

const GET_CLIENT_KPIS = gql`
  query GetClientKpis {
    dashboardKpis {
      totalProducts
      actualStockouts
      urgentAlerts
      predictedStockouts30d
      message
    }
  }
`;

// ── COMPOSANT PRINCIPAL ──────────────────────────────────────────────────────

export default function SupportDashboard() {
  const router = useRouter();
  const apolloClient = useApolloClient();
  const [activeTab, setActiveTab] = useState<'orgs' | 'audit' | 'diagnostics'>('orgs');
  const [copiedFlowId, setCopiedFlowId] = useState<string | null>(null);
  
  // États impersonation
  const [impersonatedOrgId, setImpersonatedOrgId] = useState<string | null>(null);
  const [impersonatedOrgName, setImpersonatedOrgName] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchAuditQuery, setSearchAuditQuery] = useState('');

  // Vérification de l'authentification au démarrage
  useEffect(() => {
    const token = localStorage.getItem('michi_token');
    if (!token) {
      router.push('/login');
      return;
    }
    const savedImpersonation = localStorage.getItem('michi_support_impersonated_org');
    if (savedImpersonation) {
      setImpersonatedOrgId(savedImpersonation);
    }
  }, [router]);

  // Requêtes globales
  const { 
    data: orgsData, 
    loading: orgsLoading, 
    error: orgsError,
    refetch: refetchOrgs
  } = useQuery(SUPPORT_ORGANIZATIONS_QUERY, {
    onError: (err) => {
      // Si l'utilisateur n'est pas autorisé (ex: pas de rôle support), redirection vers login
      if (err.message.includes('permission') || err.message.includes('refus')) {
        toast.error('Accès interdit : cette console est réservée au support.');
        handleLogout();
      }
    }
  });

  const { 
    data: logsData, 
    loading: logsLoading, 
    refetch: refetchLogs 
  } = useQuery(SUPPORT_AUDIT_LOGS_QUERY, {
    skip: !localStorage.getItem('michi_token'),
  });

  // Mettre à jour le nom de l'organisation impersonnée pour affichage
  useEffect(() => {
    if (impersonatedOrgId && orgsData?.supportOrganizations) {
      const org = orgsData.supportOrganizations.find(
        (o: any) => o.id === impersonatedOrgId
      );
      if (org) {
        setImpersonatedOrgName(org.name);
      }
    } else {
      setImpersonatedOrgName(null);
    }
  }, [impersonatedOrgId, orgsData]);

  // Requêtes client impersonné
  const { 
    data: clientProductsData, 
    loading: clientProductsLoading, 
    error: clientProductsError 
  } = useQuery(GET_CLIENT_PRODUCTS, {
    skip: !impersonatedOrgId,
    fetchPolicy: 'no-cache' // Forcer à bypasser le cache pour voir les vraies données client
  });

  const { 
    data: clientKpisData, 
    loading: clientKpisLoading 
  } = useQuery(GET_CLIENT_KPIS, {
    skip: !impersonatedOrgId,
    fetchPolicy: 'no-cache'
  });

  // Actions
  const handleLogout = () => {
    localStorage.removeItem('michi_token');
    localStorage.removeItem('michi_support_impersonated_org');
    apolloClient.clearStore();
    router.push('/login');
  };

  const startImpersonation = (orgId: string) => {
    localStorage.setItem('michi_support_impersonated_org', orgId);
    setImpersonatedOrgId(orgId);
    toast.success("Mode Impersonation Activé");
    
    // Réinitialiser le store Apollo pour nettoyer le cache et forcer le rechargement
    apolloClient.resetStore().then(() => {
      refetchLogs();
    });
  };

  const stopImpersonation = () => {
    localStorage.removeItem('michi_support_impersonated_org');
    setImpersonatedOrgId(null);
    setImpersonatedOrgName(null);
    toast.info("Mode Impersonation Désactivé");
    
    apolloClient.resetStore().then(() => {
      refetchLogs();
    });
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedFlowId(id);
    toast.success('Flow ID copié avec succès !');
    setTimeout(() => setCopiedFlowId(null), 2000);
  };

  // Filtres
  const filteredOrgs = orgsData?.supportOrganizations?.filter((org: any) => 
    org.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    org.slug.toLowerCase().includes(searchQuery.toLowerCase()) || 
    org.id.includes(searchQuery)
  ) || [];

  const filteredLogs = logsData?.supportAuditLogs?.filter((log: any) => 
    log.supportUserEmail.toLowerCase().includes(searchAuditQuery.toLowerCase()) || 
    (log.impersonatedOrgName && log.impersonatedOrgName.toLowerCase().includes(searchAuditQuery.toLowerCase())) || 
    log.action.toLowerCase().includes(searchAuditQuery.toLowerCase()) || 
    (log.flowId && log.flowId.includes(searchAuditQuery))
  ) || [];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Glow ambient background decoration */}
      <div className="absolute top-0 left-1/3 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl -z-10 animate-glow"></div>
      <div className="absolute bottom-10 right-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl -z-10 animate-glow" style={{ animationDelay: '1s' }}></div>

      {/* TOP GLOWING BANNER WHEN IMPERSONATING */}
      {impersonatedOrgId && (
        <div className="bg-gradient-to-r from-red-950/80 to-purple-950/80 border-b border-red-500/30 px-6 py-3 text-sm flex items-center justify-between shadow-lg backdrop-blur-md sticky top-0 z-50">
          <div className="flex items-center space-x-3 text-red-200">
            <span className="w-2.5 h-2.5 bg-red-500 rounded-full animate-ping"></span>
            <span className="font-semibold uppercase tracking-wider text-xs bg-red-500/20 border border-red-500/30 px-2 py-0.5 rounded text-red-400">
              IMPERSONATION ACTIVE
            </span>
            <span>
              Consultation des données de : <strong className="text-slate-100">{impersonatedOrgName || 'Chargement...'}</strong> <code className="text-slate-400 bg-black/30 px-1.5 py-0.5 rounded text-xs">({impersonatedOrgId})</code>
            </span>
          </div>
          <button 
            onClick={stopImpersonation}
            className="bg-red-600 hover:bg-red-500 text-white font-medium px-4 py-1.5 rounded-lg flex items-center space-x-2 transition-all hover:scale-105 active:scale-95 text-xs shadow-md shadow-red-900/20"
          >
            <StopCircle className="w-3.5 h-3.5" />
            <span>Quitter le mode Impersonation</span>
          </button>
        </div>
      )}

      {/* HEADER MAIN */}
      <header className="border-b border-slate-800 bg-slate-950/60 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center font-bold text-white text-xl shadow-lg shadow-indigo-600/20">
            M
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-slate-100 to-slate-300 bg-clip-text text-transparent">
              Michi 道
            </h1>
            <p className="text-xs text-slate-400 tracking-wide">
              CONSOLE OPÉRATIONS SUPPORT
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1.5 rounded-xl text-indigo-300 text-xs font-semibold">
            <UserCheck className="w-3.5 h-3.5" />
            <span>Rôle Agent Support</span>
          </div>

          <button 
            onClick={handleLogout}
            className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-100 rounded-xl transition-all active:scale-95"
            title="Se Déconnecter"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* TABS SELECTOR */}
      <div className="border-b border-slate-900 bg-slate-950/20 px-6 py-3 flex items-center justify-between">
        <div className="flex space-x-2">
          <button 
            onClick={() => setActiveTab('orgs')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              activeTab === 'orgs' 
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/15' 
                : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/50'
            }`}
          >
            <Building2 className="w-4 h-4" />
            <span>Organisations Clients</span>
          </button>
          
          <button 
            onClick={() => setActiveTab('audit')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              activeTab === 'audit' 
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/15' 
                : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/50'
            }`}
          >
            <History className="w-4 h-4" />
            <span>Journal d'Audit Global</span>
          </button>

          <button 
            onClick={() => setActiveTab('diagnostics')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              activeTab === 'diagnostics' 
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/15' 
                : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/50'
            }`}
          >
            <Terminal className="w-4 h-4" />
            <span>Diagnostics Système</span>
          </button>
        </div>

        {/* Dynamic State Info */}
        <div className="text-xs text-slate-500">
          Base : SQLite (In-Memory Testing env) | API : FastAPI
        </div>
      </div>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
        {activeTab === 'orgs' && (
          <div className="space-y-6">
            {/* Search Orgs and Impersonation Guide */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                <input 
                  type="text" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Rechercher une organisation par nom, slug, ID..."
                  className="w-full bg-slate-950/60 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all placeholder-slate-500"
                />
              </div>

              {!impersonatedOrgId && (
                <div className="text-slate-400 text-xs bg-indigo-500/5 border border-indigo-500/10 px-4 py-3 rounded-xl max-w-md">
                  <strong>💡 Guide :</strong> Sélectionnez une organisation ci-dessous pour activer le mode Impersonation. Vous pourrez alors visualiser ses produits en stock et ses indicateurs de vente comme si vous y étiez connecté.
                </div>
              )}
            </div>

            {/* Organizations Grid */}
            {orgsLoading ? (
              <div className="flex items-center justify-center h-64 text-slate-400">
                <span className="w-6 h-6 border-2 border-slate-700 border-t-indigo-500 rounded-full animate-spin mr-3"></span>
                <span>Chargement de l'annuaire client...</span>
              </div>
            ) : orgsError ? (
              <div className="p-6 bg-red-950/20 border border-red-500/30 rounded-2xl text-center text-red-200">
                Une erreur est survenue lors de la récupération des organisations : {orgsError.message}
              </div>
            ) : filteredOrgs.length === 0 ? (
              <div className="text-center py-20 bg-slate-950/20 border border-slate-900 rounded-2xl text-slate-500 text-sm">
                Aucune organisation trouvée correspondant à votre recherche.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredOrgs.map((org: any) => {
                  const isActiveImpersonation = impersonatedOrgId === org.id;
                  
                  return (
                    <div 
                      key={org.id} 
                      className={`glass-card p-6 rounded-2xl flex flex-col justify-between ${
                        isActiveImpersonation ? 'border-indigo-500/40 ring-1 ring-indigo-500/20 bg-indigo-950/5' : ''
                      }`}
                    >
                      <div>
                        <div className="flex items-start justify-between mb-3">
                          <h3 className="text-lg font-bold text-slate-100 tracking-tight leading-snug">
                            {org.name}
                          </h3>
                          <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                            org.plan === 'ENTERPRISE' 
                              ? 'bg-purple-500/10 border-purple-500/30 text-purple-400' 
                              : org.plan === 'PRO'
                              ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400'
                              : 'bg-slate-500/10 border-slate-500/30 text-slate-400'
                          }`}>
                            {org.plan}
                          </span>
                        </div>
                        <div className="space-y-1.5 text-xs text-slate-400 mb-6">
                          <div className="flex justify-between">
                            <span>Slug :</span>
                            <span className="text-slate-300 font-mono">{org.slug}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Statut Abonnement :</span>
                            <span className={`font-semibold ${org.subscriptionStatus === 'ACTIVE' ? 'text-emerald-400' : 'text-amber-400'}`}>
                              {org.subscriptionStatus}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Date de création :</span>
                            <span>{new Date(org.createdAt).toLocaleDateString('fr-FR')}</span>
                          </div>
                          <div className="flex flex-col pt-1.5 border-t border-slate-900 mt-2">
                            <span className="text-[10px] text-slate-500">ID Unique :</span>
                            <span className="text-slate-300 font-mono tracking-tight select-all text-[11px] bg-black/20 px-1 py-0.5 rounded mt-0.5 truncate">
                              {org.id}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="pt-2">
                        {isActiveImpersonation ? (
                          <button 
                            onClick={stopImpersonation}
                            className="w-full bg-red-600/20 hover:bg-red-600/30 border border-red-500/40 text-red-200 font-semibold py-2.5 rounded-xl transition-all text-xs flex items-center justify-center space-x-2"
                          >
                            <StopCircle className="w-4 h-4" />
                            <span>Arrêter l'Impersonation</span>
                          </button>
                        ) : (
                          <button 
                            onClick={() => startImpersonation(org.id)}
                            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 rounded-xl transition-all text-xs flex items-center justify-center space-x-2 shadow-md hover:shadow-indigo-500/10"
                          >
                            <Play className="w-3.5 h-3.5 fill-white" />
                            <span>Impersonner cette Organisation</span>
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* IMPERSONATION DATA DASHBOARD (Si actif) */}
            {impersonatedOrgId && (
              <div className="border-t border-slate-900 pt-8 mt-12 space-y-6 animate-fade-in">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
                    <UserSquare2 className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-100 tracking-tight">
                      Console d'Impersonation Client : {impersonatedOrgName}
                    </h2>
                    <p className="text-xs text-slate-400">
                      Visualisation temps réel de l'état des prévisions et des produits de ce tenant.
                    </p>
                  </div>
                </div>

                {/* KPIS CLIENT CARD GRID */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  {clientKpisLoading ? (
                    Array(4).fill(0).map((_, i) => (
                      <div key={i} className="bg-slate-950/20 border border-slate-900 rounded-2xl p-6 h-28 animate-pulse flex items-center justify-center">
                        <span className="w-5 h-5 border border-slate-800 rounded-full border-t-indigo-500 animate-spin"></span>
                      </div>
                    ))
                  ) : (
                    <>
                      <div className="bg-slate-950/40 border border-slate-900 rounded-2xl p-6 relative overflow-hidden flex flex-col justify-between">
                        <Package className="absolute right-4 top-4 w-12 h-12 text-slate-800 -z-10" />
                        <span className="text-xs text-slate-400 font-medium">Total Produits</span>
                        <span className="text-3xl font-extrabold text-slate-100 tracking-tight mt-2">
                          {clientKpisData?.dashboardKpis?.totalProducts ?? 0}
                        </span>
                      </div>
                      <div className="bg-slate-950/40 border border-slate-900 rounded-2xl p-6 relative overflow-hidden flex flex-col justify-between">
                        <ShieldAlert className="absolute right-4 top-4 w-12 h-12 text-slate-800 -z-10" />
                        <span className="text-xs text-slate-400 font-medium">Ruptures Actuelles</span>
                        <span className={`text-3xl font-extrabold tracking-tight mt-2 ${
                          (clientKpisData?.dashboardKpis?.actualStockouts ?? 0) > 0 ? 'text-amber-500' : 'text-slate-100'
                        }`}>
                          {clientKpisData?.dashboardKpis?.actualStockouts ?? 0}
                        </span>
                      </div>
                      <div className="bg-slate-950/40 border border-slate-900 rounded-2xl p-6 relative overflow-hidden flex flex-col justify-between">
                        <ShieldAlert className="absolute right-4 top-4 w-12 h-12 text-slate-800 -z-10" />
                        <span className="text-xs text-slate-400 font-medium">Alertes Urgentes</span>
                        <span className={`text-3xl font-extrabold tracking-tight mt-2 ${
                          (clientKpisData?.dashboardKpis?.urgentAlerts ?? 0) > 0 ? 'text-red-500 animate-pulse' : 'text-slate-100'
                        }`}>
                          {clientKpisData?.dashboardKpis?.urgentAlerts ?? 0}
                        </span>
                      </div>
                      <div className="bg-slate-950/40 border border-slate-900 rounded-2xl p-6 relative overflow-hidden flex flex-col justify-between">
                        <TrendingDown className="absolute right-4 top-4 w-12 h-12 text-slate-800 -z-10" />
                        <span className="text-xs text-slate-400 font-medium">Stockouts Prévis. (30j)</span>
                        <span className="text-3xl font-extrabold text-slate-100 tracking-tight mt-2">
                          {clientKpisData?.dashboardKpis?.predictedStockouts30d ?? 0}
                        </span>
                      </div>
                    </>
                  )}
                </div>

                {/* CLIENT PRODUCTS TABLE */}
                <div className="bg-slate-950/40 border border-slate-900 rounded-2xl overflow-hidden shadow-inner">
                  <div className="px-6 py-4 border-b border-slate-900 bg-slate-950/40 flex items-center justify-between">
                    <h3 className="font-semibold text-slate-200 text-sm">
                      Catalogue des Produits du Client
                    </h3>
                    <span className="text-[10px] text-slate-500 uppercase tracking-widest font-mono">
                      Query: products
                    </span>
                  </div>

                  {clientProductsLoading ? (
                    <div className="py-20 flex items-center justify-center text-slate-400">
                      <span className="w-5 h-5 border-2 border-slate-700 border-t-indigo-500 rounded-full animate-spin mr-3"></span>
                      <span>Chargement du catalogue...</span>
                    </div>
                  ) : clientProductsError ? (
                    <div className="p-8 text-center text-xs text-red-400">
                      Erreur de chargement : {clientProductsError.message}
                    </div>
                  ) : !clientProductsData?.products || clientProductsData.products.length === 0 ? (
                    <div className="py-12 text-center text-slate-500 text-sm">
                      Aucun produit trouvé dans cette boutique.
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="bg-slate-950/30 text-slate-400 border-b border-slate-900 uppercase tracking-wider font-mono">
                            <th className="px-6 py-3.5">Designation</th>
                            <th className="px-6 py-3.5">SKU</th>
                            <th className="px-6 py-3.5 text-right">Stock Actuel</th>
                            <th className="px-6 py-3.5 text-right">Lead Time (Jours)</th>
                            <th className="px-6 py-3.5 text-right">MOQ</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-900/40">
                          {clientProductsData.products.map((p: any) => (
                            <tr key={p.id} className="hover:bg-slate-900/10 text-slate-300">
                              <td className="px-6 py-4 font-semibold text-slate-100">{p.title}</td>
                              <td className="px-6 py-4 font-mono text-slate-400">{p.sku}</td>
                              <td className="px-6 py-4 text-right font-semibold">
                                <span className={p.currentStock <= p.moq ? 'text-amber-500' : 'text-slate-100'}>
                                  {p.currentStock}
                                </span>
                              </td>
                              <td className="px-6 py-4 text-right">{p.leadTime}</td>
                              <td className="px-6 py-4 text-right font-mono text-slate-400">{p.moq}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="space-y-6">
            {/* Search Audit Logs */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                <input 
                  type="text" 
                  value={searchAuditQuery}
                  onChange={(e) => setSearchAuditQuery(e.target.value)}
                  placeholder="Filtrer par email agent, organisation cible, action, flowId..."
                  className="w-full bg-slate-950/60 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all placeholder-slate-500"
                />
              </div>

              <div className="text-[11px] text-slate-500 bg-slate-950/40 border border-slate-900 px-4 py-2 rounded-xl flex items-center space-x-2">
                <Activity className="w-3.5 h-3.5 text-emerald-400" />
                <span>Tous les accès et requêtes de support sont persistés dans la table de base de données <code>support_audit_logs</code>.</span>
              </div>
            </div>

            {/* Audit Logs Table */}
            {logsLoading ? (
              <div className="flex items-center justify-center h-64 text-slate-400">
                <span className="w-6 h-6 border-2 border-slate-700 border-t-indigo-500 rounded-full animate-spin mr-3"></span>
                <span>Chargement de la piste d'audit globale...</span>
              </div>
            ) : filteredLogs.length === 0 ? (
              <div className="text-center py-20 bg-slate-950/20 border border-slate-900 rounded-2xl text-slate-500 text-sm">
                Aucun log d'audit trouvé.
              </div>
            ) : (
              <div className="bg-slate-950/40 border border-slate-900 rounded-2xl overflow-hidden shadow-lg">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-950/60 text-slate-400 border-b border-slate-900 uppercase tracking-wider font-mono">
                        <th className="px-6 py-4">Horodatage (UTC)</th>
                        <th className="px-6 py-4">Agent Support (Email)</th>
                        <th className="px-6 py-4">Org. Impersonnée (Cible)</th>
                        <th className="px-6 py-4">Action GraphQL</th>
                        <th className="px-6 py-4">Flow ID de Session</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-900/40 text-slate-300">
                      {filteredLogs.map((log: any) => {
                        const date = new Date(log.createdAt);
                        return (
                          <tr key={log.id} className="hover:bg-slate-900/10">
                            <td className="px-6 py-4 font-mono text-slate-400">
                              {date.toLocaleDateString('fr-FR')} {date.toLocaleTimeString('fr-FR')}
                            </td>
                            <td className="px-6 py-4 font-semibold text-slate-200">
                              {log.supportUserEmail}
                            </td>
                            <td className="px-6 py-4 font-semibold text-indigo-400">
                              {log.impersonatedOrgName || 'N/A'}
                            </td>
                            <td className="px-6 py-4">
                              <span className="bg-slate-900 border border-slate-800 px-2 py-0.5 rounded font-mono text-[11px] text-slate-400">
                                {log.action}
                              </span>
                            </td>
                            <td className="px-6 py-4 font-mono text-slate-400">
                              {log.flowId ? (
                                <button
                                  onClick={() => copyToClipboard(log.flowId, log.id)}
                                  className="flex items-center space-x-1.5 hover:text-indigo-400 transition-all select-all"
                                  title="Copier le Flow ID dans le presse-papiers"
                                >
                                  <span>{log.flowId.substring(0, 8)}...</span>
                                  {copiedFlowId === log.id ? (
                                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                                  ) : (
                                    <Copy className="w-3 h-3" />
                                  )}
                                </button>
                              ) : (
                                <span className="text-slate-600">N/A</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'diagnostics' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 animate-fade-in">
            {/* API Health panel */}
            <div className="bg-slate-950/40 border border-slate-900 rounded-2xl p-6 space-y-6">
              <h2 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
                <Activity className="w-5 h-5 text-indigo-400" />
                <span>Rapport de Santé API</span>
              </h2>

              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-slate-900/30 border border-slate-900 rounded-xl">
                  <span className="text-xs text-slate-400">Backend Server (Port 8000)</span>
                  <span className="text-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-2 py-0.5 rounded-full font-bold">
                    ONLINE
                  </span>
                </div>
                <div className="flex items-center justify-between p-4 bg-slate-900/30 border border-slate-900 rounded-xl">
                  <span className="text-xs text-slate-400">GraphQL Route (/graphql)</span>
                  <span className="text-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-2 py-0.5 rounded-full font-bold">
                    HEALTHY
                  </span>
                </div>
                <div className="flex items-center justify-between p-4 bg-slate-900/30 border border-slate-900 rounded-xl">
                  <span className="text-xs text-slate-400">Relational DB Engine (SQLite)</span>
                  <span className="text-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-2 py-0.5 rounded-full font-bold">
                    CONNECTED
                  </span>
                </div>
                <div className="flex items-center justify-between p-4 bg-slate-900/30 border border-slate-900 rounded-xl">
                  <span className="text-xs text-slate-400">Cache & Queue Engine (Redis)</span>
                  <span className="text-xs bg-amber-500/10 border border-amber-500/30 text-amber-400 px-2 py-0.5 rounded-full font-bold">
                    DEGRADED (FALLBACK IN-MEMORY)
                  </span>
                </div>
              </div>
            </div>

            {/* Error Diagnostics Helper */}
            <div className="bg-slate-950/40 border border-slate-900 rounded-2xl p-6 space-y-6">
              <h2 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
                <Terminal className="w-5 h-5 text-indigo-400" />
                <span>Diagnostic des Erreurs</span>
              </h2>

              <p className="text-xs text-slate-400 leading-relaxed">
                Utilisez le Flow ID transmis par le client lors d'un incident de production. Le Flow ID identifie de manière unique la requête et permet de retrouver sa trace dans les logs sans exposer de données sensibles.
              </p>

              <div className="p-4 bg-indigo-500/5 border border-indigo-500/10 rounded-xl space-y-3">
                <span className="text-[11px] font-bold text-indigo-300 uppercase tracking-wider block">
                  Rechercher un Flow ID client
                </span>
                <div className="flex space-x-2">
                  <input 
                    type="text" 
                    placeholder="Entrez le Flow ID (ex: 214aec6d...)"
                    className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <button 
                    onClick={() => toast.info("Recherche de traces non disponible en environnement d'intégration.")}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all"
                  >
                    Tracer
                  </button>
                </div>
              </div>

              <div className="text-[10px] text-slate-500 flex flex-col space-y-1">
                <span>Variables d'Environnement de Production :</span>
                <span className="font-mono">NODE_ENV = production</span>
                <span className="font-mono">API_GATEWAY_URL = http://localhost:8000</span>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
