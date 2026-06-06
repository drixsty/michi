'use client';

import React from 'react';
import { ConnectorsGrid } from '@/components/dashboard/ConnectorsGrid';
import { useTranslations } from 'next-intl';
import { useStore } from '@/context/StoreContext';
import { usePermissions, Permission } from '@/hooks/usePermissions';
import { PermissionGuard } from '@/components/auth/PermissionGuard';
import { motion, AnimatePresence } from 'framer-motion';

export default function ConnectionsPage() {
  const t = useTranslations('connections');
  const { currentOrganization } = useStore();
  const { isAdmin } = usePermissions();
  const [copiedDiag, setCopiedDiag] = React.useState<string | null>(null);
  const [activePlatformLog, setActivePlatformLog] = React.useState<string | null>(null);

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    console.log("Import CSV triggered from Settings");
  };

  const platformsDiagnostics = [
    {
      id: 'shopify',
      name: 'Shopify',
      status: 'Connected',
      apiHealth: '100% (0.2s latency)',
      webhooks: 'Healthy (4 active)',
      lastSync: 'Il y a 14 minutes',
      logs: [
        '[2026-06-05 23:10:15] INFO: Starting webhook product_update synchronization.',
        '[2026-06-05 23:10:16] SUCCESS: Updated SKU MICHI-PROD-981 in database.',
        '[2026-06-05 23:24:00] INFO: Scheduled daily full sync triggered.',
        '[2026-06-05 23:24:02] SUCCESS: Ingested 124 variants from Shopify API (Shop ID: shop_91a0).'
      ]
    },
    {
      id: 'woocommerce',
      name: 'WooCommerce',
      status: 'Not Connected',
      apiHealth: 'N/A',
      webhooks: 'N/A',
      lastSync: 'Jamais',
      logs: [
        '[2026-06-05 18:00:00] WARN: WooCommerce connector is inactive.',
        '[2026-06-05 18:00:00] INFO: Setup your API keys in WooCommerce > Settings to activate.'
      ]
    },
    {
      id: 'amazon',
      name: 'Amazon Seller Central',
      status: 'Not Connected',
      apiHealth: 'N/A',
      webhooks: 'N/A',
      lastSync: 'Jamais',
      logs: [
        '[2026-06-05 18:00:00] WARN: Amazon connector is inactive.'
      ]
    },
    {
      id: 'csv',
      name: 'CSV / Excel Import',
      status: 'Operational',
      apiHealth: 'N/A (Local Ingestion)',
      webhooks: 'N/A',
      lastSync: 'Il y a 2 heures',
      logs: [
        '[2026-06-05 22:15:30] INFO: Parsing CSV payload (Size: 4.2MB).',
        '[2026-06-05 22:15:31] SUCCESS: Smart import validation completed. 98% confidence score.',
        '[2026-06-05 22:15:33] SUCCESS: Ingested 2,410 sales logs and 45 unified products.'
      ]
    }
  ];

  const handleCopyPlatformReport = (platform: typeof platformsDiagnostics[0]) => {
    if (typeof window === 'undefined') return;

    const report = {
      organizationId: currentOrganization?.id || 'N/A',
      platform: platform.name,
      status: platform.status,
      apiHealth: platform.apiHealth,
      webhooks: platform.webhooks,
      lastSync: platform.lastSync,
      flowId: sessionStorage.getItem('michi_last_error_flow_id') || 'N/A',
      userAgent: navigator.userAgent,
      time: new Date().toISOString(),
      logs: platform.logs
    };

    navigator.clipboard.writeText(JSON.stringify(report, null, 2));
    setCopiedDiag(platform.id);
    setTimeout(() => setCopiedDiag(null), 3000);
  };

  return (
    <PermissionGuard permission={Permission.SETTINGS_VIEW}>
      <div className="p-6 max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">{t('title')}</h1>
          <p className="text-sm text-slate-500">
            {t('description')}
          </p>
        </div>

        <div className="bg-white rounded-xl border border-slate-100 p-4 shadow-sm">
          <ConnectorsGrid isAdmin={isAdmin} onImport={handleImport} />
        </div>

        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 space-y-6 text-slate-100">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <h3 className="text-base font-bold text-white tracking-tight">Diagnostics & logs d'ingestion</h3>
              </div>
              <p className="text-xs text-slate-400">
                Vérifiez la latence de vos API, l'état de santé des Webhooks et exportez les rapports de diagnostic pour notre support.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {platformsDiagnostics.map((platform) => {
              const isActiveLog = activePlatformLog === platform.id;
              return (
                <div key={platform.id} className="bg-slate-950/60 border border-slate-800 rounded-lg p-4 space-y-4">
                  <div className="flex justify-between items-start">
                    <div className="space-y-0.5">
                      <h4 className="text-sm font-bold text-white">{platform.name}</h4>
                      <span className={`inline-flex items-center text-[9px] font-bold px-1.5 py-0.5 rounded ${
                        platform.status === 'Connected' || platform.status === 'Operational'
                          ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-500/20'
                          : 'bg-slate-900 text-slate-400'
                      }`}>
                        {platform.status}
                      </span>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => setActivePlatformLog(isActiveLog ? null : platform.id)}
                        className="px-2.5 py-1 text-[10px] font-bold text-slate-400 hover:text-white bg-slate-900 border border-slate-800 rounded transition-colors focus:ring-0 focus:outline-none"
                      >
                        {isActiveLog ? 'Masquer logs' : 'Voir logs'}
                      </button>
                      <button
                        onClick={() => handleCopyPlatformReport(platform)}
                        className="px-2.5 py-1 text-[10px] font-bold text-slate-300 hover:text-white bg-primary/20 border border-primary/30 rounded flex items-center gap-1 transition-colors focus:ring-0 focus:outline-none"
                      >
                        {copiedDiag === platform.id ? (
                          <>
                            <span className="text-emerald-400">Copié !</span>
                          </>
                        ) : (
                          <>
                            Copier diagnostic
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-[10px] bg-slate-950/80 p-2.5 rounded border border-slate-800/40">
                    <div className="space-y-0.5">
                      <span className="text-slate-500 block font-semibold">Santé API</span>
                      <span className="text-slate-300 font-bold">{platform.apiHealth}</span>
                    </div>
                    <div className="space-y-0.5">
                      <span className="text-slate-500 block font-semibold">Webhooks</span>
                      <span className="text-slate-300 font-bold">{platform.webhooks}</span>
                    </div>
                    <div className="space-y-0.5">
                      <span className="text-slate-500 block font-semibold">Dernière synchro</span>
                      <span className="text-slate-300 font-bold">{platform.lastSync}</span>
                    </div>
                  </div>

                  <AnimatePresence>
                    {isActiveLog && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden bg-slate-950 rounded border border-slate-800 font-mono text-[9px] text-slate-400 leading-relaxed"
                      >
                        <div className="p-3 space-y-1.5 overflow-x-auto max-h-40">
                          {platform.logs.map((log, idx) => (
                            <div key={idx} className={
                              log.includes('SUCCESS') ? 'text-emerald-400' :
                              log.includes('WARN') ? 'text-amber-400' : 'text-slate-400'
                            }>
                              {log}
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 opacity-70">
           <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <h4 className="text-[10px] font-bold text-slate-400 tracking-widest mb-1">{t('security.title')}</h4>
              <p className="text-xs text-slate-600">
                {t('security.description')}
              </p>
           </div>
           <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <h4 className="text-[10px] font-bold text-slate-400 tracking-widest mb-1">{t('quotas.title')}</h4>
              <p className="text-xs text-slate-600">
                {t('quotas.description')}
              </p>
           </div>
        </div>
      </div>
    </PermissionGuard>
  );
}
