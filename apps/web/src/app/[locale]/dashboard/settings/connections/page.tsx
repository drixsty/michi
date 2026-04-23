'use client';

import React from 'react';
import { ConnectorsGrid } from '@/components/dashboard/ConnectorsGrid';
import { useTranslations } from 'next-intl';
import { useStore } from '@/context/StoreContext';
import { useQuery } from '@apollo/client';
import { GET_ME } from '@/graphql/queries/getMe';
import { motion } from 'framer-motion';

export default function ConnectionsPage() {
  const t = useTranslations('connections');
  const { currentOrganization } = useStore();
  const { data: meData } = useQuery(GET_ME);

  const isAdmin = React.useMemo(() => {
    const orgs = meData?.me?.organizations || [];
    const currentOrgId = meData?.me?.currentOrganizationId;
    const currentOrg = orgs.find((o: any) => o.organizationId === currentOrgId);
    return currentOrg?.role?.toLowerCase() === 'admin';
  }, [meData]);

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Logique d'import CSV (si nécessaire ici)
    console.log("Import CSV triggered from Settings");
  };

  return (
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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 opacity-70">
         <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
            <h4 className="text-[10px] font-bold text-slate-400 tracking-widest mb-1">Sécurité des données</h4>
            <p className="text-xs text-slate-600">
              Toutes vos clés API sont chiffrées au repos avec l'algorithme AES-256. Michi ne stocke jamais vos mots de passe en clair.
            </p>
         </div>
         <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
            <h4 className="text-[10px] font-bold text-slate-400 tracking-widest mb-1">Quotas & limites</h4>
            <p className="text-xs text-slate-600">
              Votre plan actuel permet de connecter jusqu'à 3 sources de données simultanément.
            </p>
         </div>
      </div>
    </div>
  );
}
