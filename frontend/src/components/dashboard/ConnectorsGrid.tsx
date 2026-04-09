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
  Upload
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { LoadingState } from '../ui/LoadingState';

export const GET_SOURCES = gql`
  query GetSources {
    sources {
      id
      name
      platform
      connected
    }
  }
`;

export const TOGGLE_SOURCE = gql`
  mutation ToggleSource($platform: String!, $connected: Boolean!) {
    toggle_source(platform: $platform, connected: $connected) {
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
  const { data, loading, refetch } = useQuery(GET_SOURCES);
  const [toggleSource, { loading: toggling }] = useMutation(TOGGLE_SOURCE, {
    onCompleted: () => refetch()
  });

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

  if (loading) return (
    <LoadingState size="sm" />
  );

  return (
    <section className="space-y-4">
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
           
           <div className="space-y-0.5 mb-4">
              <h3 className="text-sm font-bold text-slate-900">Fichier CSV</h3>
              <p className="text-[10px] text-slate-500 font-medium italic">Importation manuelle</p>
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

              <div className="space-y-1 mb-6">
                <h3 className="text-sm font-bold text-slate-900">{source.name}</h3>
                <p className="text-[10px] text-slate-500 font-medium">Plateforme e-commerce</p>
              </div>
              
              <button 
                onClick={() => handleToggle(source.platform, source.connected)}
                disabled={toggling}
                className={cn(
                  "w-full py-2.5 rounded-lg text-[10px] font-bold tracking-widest transition-all flex items-center justify-center gap-2",
                  source.connected 
                    ? "bg-slate-100 text-slate-600 hover:bg-red-50 hover:text-red-600 border border-transparent" 
                    : "bg-primary text-white hover:opacity-90 shadow-none"
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
      
      {toggling && (
         <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/20 backdrop-blur-sm animate-in fade-in duration-300">
            <LoadingState size="lg" message="mise à jour..." />
         </div>
      )}
    </section>
  );
}
