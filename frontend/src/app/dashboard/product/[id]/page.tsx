'use client';

import React, { useState } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { useParams, useRouter } from 'next/navigation';
import { GET_PRODUCT_DETAIL } from '@/graphql/queries/getProductDetail';
import { UPDATE_PRODUCT_SETTINGS } from '@/graphql/mutations/updateProduct';
import { 
  ChevronLeft, 
  Package, 
  TrendingUp, 
  AlertCircle, 
  Zap,
  Calendar,
  Box
} from 'lucide-react';
import SalesChart from '@/components/dashboard/SalesChart';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { cn } from '@/lib/utils';

export default function ProductDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [leadTimeDelta, setLeadTimeDelta] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

  // Form states
  const [leadTime, setLeadTime] = useState<number>(0);
  const [moq, setMoq] = useState<number>(0);

  const { data, loading, error, refetch } = useQuery(GET_PRODUCT_DETAIL, {
    variables: { id: id as string },
  });

  const [updateSettings] = useMutation(UPDATE_PRODUCT_SETTINGS, {
    onCompleted: () => {
      setIsSaving(false);
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
      refetch();
    },
    onError: () => {
      setIsSaving(false);
      setSaveStatus('error');
    }
  });

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await updateSettings({
        variables: {
          id: id as string,
          leadTime,
          moq
        }
      });
    } catch (err) {
      setIsSaving(false);
    }
  };

  // Initialize form states when data is loaded
  React.useEffect(() => {
    if (data?.productDetail?.[0]) {
      setLeadTime(data.productDetail[0].leadTime);
      setMoq(data.productDetail[0].moq || 0);
    }
  }, [data]);

  if (loading) return <div className="p-8 text-sm animate-pulse">Chargement analyse...</div>;
  if (error || !data?.productDetail?.[0]) return <div className="p-8 text-sm text-red-500">Erreur lors de la récupération du produit.</div>;

  const product = data.productDetail[0];
  const prediction = product.prediction;

  // Simulate impact
  const adjustedLeadTime = product.leadTime + leadTimeDelta;
  const impactOnStockout = leadTimeDelta > 0 ? "Risque accru" : "Sécurité améliorée";

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Header Navigation */}
      <div className="flex items-center gap-4">
        <button 
          onClick={() => router.back()}
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border bg-white hover:bg-accent transition-colors"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold tracking-tight text-sentence">{product.title}</h1>
            <span className="text-xs font-mono text-muted-foreground bg-accent px-2 py-0.5 rounded">{product.sku}</span>
          </div>
          <p className="text-xs text-muted-foreground text-sentence">Analyse prédictive et simulation d'inventaire</p>
        </div>
        {product.supplier && (
          <div className="ml-auto flex items-center gap-4 px-4 py-2 bg-accent/50 rounded-lg border">
            <div className="text-right">
              <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Fournisseur</p>
              <p className="text-sm font-semibold text-sentence">{product.supplier.name}</p>
            </div>
            <div className={`h-8 w-8 rounded-full border-2 flex items-center justify-center text-[10px] font-bold ${product.supplier.reliabilityScore > 0.8 ? 'border-green-500 text-green-600' : 'border-amber-500 text-amber-600'}`}>
              {(product.supplier.reliabilityScore * 100).toFixed(0)}%
            </div>
          </div>
        )}
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center gap-2 mb-4 text-muted-foreground">
            <Box className="h-4 w-4" />
            <span className="text-xs font-medium text-sentence">Stock actuel</span>
          </div>
          <div className="text-3xl font-bold tracking-tight">{product.currentStock} u.</div>
          <p className="text-[11px] text-muted-foreground mt-2 text-sentence">Seuil d'alerte : {product.warningThreshold} u.</p>
        </div>

        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center gap-2 mb-4 text-muted-foreground">
            <Calendar className="h-4 w-4" />
            <span className="text-xs font-medium text-sentence">Rupture prévue</span>
          </div>
          <div className={`text-3xl font-bold tracking-tight ${prediction?.predictedStockoutDate && new Date(prediction.predictedStockoutDate) < new Date() ? 'text-red-500' : ''}`}>
            {prediction?.predictedStockoutDate ? format(new Date(prediction.predictedStockoutDate), 'dd MMM yyyy', { locale: fr }) : 'N/A'}
          </div>
          <p className="text-[11px] text-muted-foreground mt-2 text-sentence">Basé sur un run rate de {prediction?.runRate.toFixed(1)}/j</p>
        </div>

        <div className="bg-primary text-primary-foreground rounded-lg border p-6 shadow-md">
          <div className="flex items-center gap-2 mb-4 opacity-80">
            <Zap className="h-4 w-4" />
            <span className="text-xs font-medium text-sentence">Commande suggérée</span>
          </div>
          <div className="text-3xl font-bold tracking-tight">+{Math.round(prediction?.reorderQuantity || 0)} u.</div>
          <p className="text-[11px] opacity-80 mt-2 text-sentence">Délai fournisseur : {product.leadTime} jours</p>
        </div>
      </div>

      {/* Analytics Chart */}
      <div className="bg-white rounded-lg border p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h3 className="text-sm font-semibold text-sentence italic">Demande Historique & Prévisions IA</h3>
            <p className="text-xs text-muted-foreground text-sentence">Cycle de 365 jours analysé</p>
          </div>
          <div className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest">
            <div className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-indigo-500" /> Historique</div>
            <div className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-indigo-200" /> Prédiction</div>
          </div>
        </div>
        <div className="h-[400px]">
          <SalesChart 
            data={product.cleanedDemand || []} 
            title="" 
          />
        </div>
      </div>

      {/* Simulator (US 11.4) */}
      <div className="bg-accent/30 rounded-lg border border-indigo-100 p-8">
        <div className="flex items-center gap-3 mb-8">
          <div className="p-2 bg-indigo-100 rounded-lg">
            <Zap className="h-5 w-5 text-indigo-600" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-sentence">Simulateur What-If</h4>
            <p className="text-xs text-muted-foreground text-sentence italic">Évaluez l'impact d'un retard de livraison sur vos stocks</p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <div className="flex justify-between items-end">
              <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Retard fournisseur estimé</label>
              <span className="text-lg font-bold bg-white px-3 py-1 rounded-md border shadow-sm">
                {leadTimeDelta > 0 ? `+${leadTimeDelta}` : leadTimeDelta} jours
              </span>
            </div>
            <input 
              type="range" 
              min="-7" 
              max="30" 
              value={leadTimeDelta} 
              onChange={(e) => setLeadTimeDelta(parseInt(e.target.value))}
              className="w-full"
            />
          </div>

          <div className="bg-white p-6 rounded-lg border shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle className={`h-4 w-4 ${leadTimeDelta > 5 ? 'text-red-500' : 'text-indigo-500'}`} />
              <span className="text-xs font-bold text-sentence">Analyse d'impact</span>
            </div>
            <p className="text-sm font-medium text-sentence mb-1">{impactOnStockout}</p>
            <p className="text-xs text-muted-foreground text-sentence">
              {leadTimeDelta > 0 
                ? `Une livraison retardée de ${leadTimeDelta} jours augmente la probabilité de rupture de ${(leadTimeDelta * 3.5).toFixed(0)}%.`
                : "Optimiser le délai fournisseur réduit drastiquement vos besoins en stock de sécurité."
              }
            </p>
          </div>
        </div>
      </div>

      {/* Persistent Settings (US 11.4) */}
      <div className="bg-white rounded-lg border p-8">
        <div className="flex items-center justify-between mb-8">
           <div className="flex items-center gap-3">
              <div className="p-2 bg-slate-100 rounded-lg">
                <Box className="h-5 w-5 text-slate-600" />
              </div>
              <h4 className="text-sm font-bold text-sentence">Paramètres d'Inventaire (Réels)</h4>
           </div>
           {saveStatus === 'success' && <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full animate-in fade-in zoom-in">✓ Enregistré</span>}
           {saveStatus === 'error' && <span className="text-[10px] font-bold text-red-600 bg-red-50 px-3 py-1 rounded-full animate-in fade-in zoom-in">⚠️ Erreur</span>}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-4">
            <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Délai fournisseur (jours)</label>
            <input 
              type="number" 
              value={leadTime} 
              onChange={(e) => setLeadTime(Math.max(1, parseInt(e.target.value) || 0))}
              className="w-full h-11 px-4 rounded-md border text-sm focus:ring-2 focus:ring-primary/10 transition-all"
            />
            <p className="text-[10px] text-muted-foreground italic">Délai de livraison annoncé par le fournisseur (Lead Time).</p>
          </div>
          <div className="space-y-4">
            <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Quantité minimale (MOQ)</label>
            <input 
              type="number" 
              value={moq} 
              onChange={(e) => setMoq(Math.max(1, parseInt(e.target.value) || 0))}
              className="w-full h-11 px-4 rounded-md border text-sm focus:ring-2 focus:ring-primary/10 transition-all"
            />
            <p className="text-[10px] text-muted-foreground italic">Commande par multiples de cette valeur.</p>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t flex justify-end">
           <button
             onClick={handleSave}
             disabled={isSaving}
             className={cn(
               "px-6 py-2.5 bg-slate-900 text-white rounded-md text-xs font-bold tracking-widest hover:bg-slate-800 transition-all shadow-sm",
               isSaving && "opacity-70 cursor-not-allowed"
             )}
           >
             {isSaving ? "Enregistrement..." : "Sauvegarder les paramètres"}
           </button>
        </div>
      </div>
    </div>
  );
}
