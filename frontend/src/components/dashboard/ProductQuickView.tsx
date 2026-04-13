'use client';

import React from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  ArrowRight, 
  TrendingUp, 
  AlertCircle, 
  Box, 
  Calendar,
  ExternalLink,
  ChevronRight,
  Settings,
  Save,
  Check,
  Activity
} from 'lucide-react';
import { createPortal } from 'react-dom';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ComposedChart,
  Line,
  Legend
} from 'recharts';
import { GET_PRODUCTS } from '@/graphql/queries/getProducts';
import { UPDATE_PRODUCT_SETTINGS } from '@/graphql/mutations/updateProduct';
import { cn } from '@/lib/utils';
import { useRouter } from 'next/navigation';
import { LoadingState } from '../ui/LoadingState';
import { useStore } from '@/context/StoreContext';

interface ProductQuickViewProps {
  productId: string | null;
  onClose: () => void;
}

// ── What-If Simulator Component (US 14.4) ───────────────────
function WhatIfSimulator({ 
  currentStock, runRate, leadTime, boostFactor, costPrice, salePrice 
}: { 
  currentStock: number; runRate: number; leadTime: number; boostFactor: number; costPrice: number; salePrice: number;
}) {
  const [extraDelay, setExtraDelay] = React.useState(0);
  const [salesMultiplier, setSalesMultiplier] = React.useState(1.0);
  const isSimulating = extraDelay > 0 || salesMultiplier !== 1.0;

  const simRunRate = runRate * boostFactor * salesMultiplier;
  const simLeadTime = leadTime + extraDelay;
  const simDaysOfStock = simRunRate > 0 ? currentStock / simRunRate : 999;
  const simStockoutDate = new Date(Date.now() + simDaysOfStock * 86400000);
  const simRevenueAtRisk = Math.max(0, (simRunRate * Math.max(0, simLeadTime - simDaysOfStock)) * (salePrice || 0));

  const projectionData = React.useMemo(() => {
    const pts = [];
    const maxDays = Math.min(90, Math.ceil(simDaysOfStock) + 15);
    for (let d = 0; d <= maxDays; d += 2) {
      pts.push({
        day: `J+${d}`,
        base: Math.max(0, Math.round(currentStock - runRate * boostFactor * d)),
        sim: Math.max(0, Math.round(currentStock - simRunRate * d)),
      });
    }
    return pts;
  }, [currentStock, runRate, boostFactor, simRunRate, simDaysOfStock]);

  return (
    <div className={cn(
      "p-3 rounded-xl border space-y-3 transition-all",
      isSimulating ? "bg-amber-50/50 border-amber-200" : "bg-slate-50 border-slate-100"
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-3 w-3 text-amber-500" />
          <h3 className="text-[10px] font-bold text-slate-700 tracking-widest">Simulateur What-if</h3>
          {isSimulating && (
            <span className="text-[7px] font-black text-amber-600 bg-amber-100 px-1.5 py-0.5 rounded-full border border-amber-200 animate-pulse">
              Simulation active
            </span>
          )}
        </div>
        {isSimulating && (
          <button 
            onClick={() => { setExtraDelay(0); setSalesMultiplier(1.0); }}
            className="text-[8px] font-bold text-slate-400 hover:text-slate-600 transition-colors"
          >
            Réinitialiser
          </button>
        )}
      </div>

      {/* Slider: Extra delay */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-[9px] font-bold text-slate-500">Retard fournisseur</span>
          <span className={cn("text-[9px] font-black", extraDelay > 0 ? "text-amber-600" : "text-slate-400")}>
            +{extraDelay} jours
          </span>
        </div>
        <input 
          type="range" min="0" max="30" step="1" value={extraDelay}
          onChange={(e) => setExtraDelay(parseInt(e.target.value))}
          className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-amber-500 [&::-webkit-slider-thumb]:shadow"
          style={{ background: `linear-gradient(to right, #f59e0b 0%, #f59e0b ${(extraDelay/30)*100}%, #e2e8f0 ${(extraDelay/30)*100}%, #e2e8f0 100%)` }}
        />
      </div>

      {/* Slider: Sales multiplier */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-[9px] font-bold text-slate-500">Pic de ventes</span>
          <span className={cn("text-[9px] font-black", salesMultiplier !== 1.0 ? "text-amber-600" : "text-slate-400")}>
            ×{salesMultiplier.toFixed(1)}
          </span>
        </div>
        <input 
          type="range" min="0.5" max="3.0" step="0.1" value={salesMultiplier}
          onChange={(e) => setSalesMultiplier(parseFloat(e.target.value))}
          className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-amber-500 [&::-webkit-slider-thumb]:shadow"
          style={{ background: `linear-gradient(to right, #f59e0b 0%, #f59e0b ${((salesMultiplier-0.5)/2.5)*100}%, #e2e8f0 ${((salesMultiplier-0.5)/2.5)*100}%, #e2e8f0 100%)` }}
        />
      </div>

      {/* Projection Chart */}
      <div className="h-28 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={projectionData}>
            <defs>
              <linearGradient id="colorBase" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.1}/>
                <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorSim" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.15}/>
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 7, fill: '#94a3b8' }} interval={4} />
            <YAxis hide />
            <Tooltip contentStyle={{ borderRadius: '10px', border: '1px solid #f1f5f9', boxShadow: 'none', fontSize: '9px' }} />
            <Area type="monotone" dataKey="base" stroke="#4f46e5" strokeWidth={1.5} fillOpacity={1} fill="url(#colorBase)" name="Actuel" />
            {isSimulating && (
              <Area type="monotone" dataKey="sim" stroke="#f59e0b" strokeWidth={2} strokeDasharray="4 3" fillOpacity={1} fill="url(#colorSim)" name="Simulé" />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Results */}
      <div className="grid grid-cols-3 gap-2">
        <div className="text-center p-2 bg-white rounded-lg border border-slate-100">
          <p className="text-[7px] font-bold text-slate-400 mb-0.5">Couverture</p>
          <p className={cn("text-sm font-black", simDaysOfStock < simLeadTime ? "text-red-600" : "text-slate-900")}>
            {Math.round(simDaysOfStock)}j
          </p>
        </div>
        <div className="text-center p-2 bg-white rounded-lg border border-slate-100">
          <p className="text-[7px] font-bold text-slate-400 mb-0.5">Rupture</p>
          <p className={cn("text-[10px] font-black", simDaysOfStock < simLeadTime ? "text-red-600" : "text-slate-900")}>
            {simStockoutDate.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
          </p>
        </div>
        <div className="text-center p-2 bg-white rounded-lg border border-slate-100">
          <p className="text-[7px] font-bold text-slate-400 mb-0.5">Risque €</p>
          <p className="text-[10px] font-black text-red-600">
            {simRevenueAtRisk > 0 ? `${Math.round(simRevenueAtRisk).toLocaleString('fr-FR')}€` : '0€'}
          </p>
        </div>
      </div>
    </div>
  );
}

export function ProductQuickView({ productId, onClose }: ProductQuickViewProps) {
  const router = useRouter();
  const { user } = useStore();
  const { data, loading } = useQuery(GET_PRODUCTS, {
    variables: { 
      id: productId 
    },
    skip: !productId
  });

  const product = data?.products?.[0];

  // Prepare chart data
  const chartData = React.useMemo(() => {
    if (!product?.cleanedDemand) return [];
    return product.cleanedDemand
      .slice(-30) // Last 30 days
      .map((d: any) => ({
        date: new Date(d.date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }),
        sales: d.correctedUnitsSold,
        stock: d.inventoryLevel ?? 0
      }));
  }, [product]);

  // Client-side portal target check
  const [mounted, setMounted] = React.useState(false);
  const [leadTime, setLeadTime] = React.useState<number>(0);
  const [moq, setMoq] = React.useState<number>(0);
  const [boostFactor, setBoostFactor] = React.useState<number>(1.0);
  const [stockWeight, setStockWeight] = React.useState<number>(1.0);
  const [costPrice, setCostPrice] = React.useState<number>(0);
  const [salePrice, setSalePrice] = React.useState<number>(0);
  const [saveStatus, setSaveStatus] = React.useState<'idle' | 'saving' | 'success'>('idle');

  const [updateSettings] = useMutation(UPDATE_PRODUCT_SETTINGS, {
    onCompleted: () => {
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 2000);
    },
    onError: () => setSaveStatus('idle')
  });

  const handleQuickSave = async () => {
    if (!productId) return;
    setSaveStatus('saving');
    try {
      await updateSettings({
        variables: { 
          id: productId, 
          leadTime, 
          moq, 
          boostFactor, 
          stockWeight,
          costPrice,
          salePrice
        }
      });
    } catch (e) {
      setSaveStatus('idle');
    }
  };

  React.useEffect(() => {
    if (product) {
      setLeadTime(product.leadTime || 14);
      setMoq(product.moq || 0);
      setBoostFactor(product.boostFactor || 1.0);
      setStockWeight(product.stockWeight || 1.0);
      setCostPrice(product.costPrice || 0);
      setSalePrice(product.salePrice || 0);
    }
  }, [product]);

  React.useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  return createPortal(
    <AnimatePresence>
      {productId && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-[60] bg-slate-900/20 backdrop-blur-md"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed inset-y-0 right-0 z-[70] w-full max-w-md bg-white border-l border-slate-100 flex flex-col shadow-none"
          >
            {loading && !product ? (
              <LoadingState className="flex-1" message="Chargement du produit..." />
            ) : product ? (
              <>
                <div className="p-4 border-b border-slate-50 flex items-start justify-between sticky top-0 bg-white z-10">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                       <h2 className="text-sm font-extrabold text-slate-900 tracking-widest">{product.title}</h2>
                    </div>
                    <p className="text-[10px] font-bold text-slate-400 tracking-widest">SKU: {product.sku}</p>
                  </div>
                  <button 
                    onClick={onClose}
                    className="p-2 hover:bg-slate-50 rounded-full transition-colors"
                  >
                    <X className="h-4 w-4 text-slate-400" />
                  </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto no-scrollbar p-4 space-y-4">
                  {/* Key Stats */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-slate-50/50 rounded-xl border border-slate-100">
                      <div className="flex items-center gap-2 mb-2">
                        <Box className="h-3.5 w-3.5 text-slate-400" />
                        <span className="text-[9px] font-bold text-slate-400 tracking-widest">Stock actuel</span>
                      </div>
                      <p className="text-xl font-bold text-slate-900">{product.currentStock} <span className="text-xs font-medium text-slate-400">Unités</span></p>
                    </div>
                    <div className="p-4 bg-slate-50/50 rounded-xl border border-slate-100">
                      <div className="flex items-center gap-2 mb-2">
                        <Calendar className="h-3.5 w-3.5 text-slate-400" />
                        <span className="text-[9px] font-bold text-slate-400 tracking-widest">Rupture prévue</span>
                      </div>
                      <p className="text-xl font-bold text-emerald-600">
                        {product.prediction?.predictedStockoutDate 
                          ? new Date(product.prediction.predictedStockoutDate).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
                          : "N/A"}
                      </p>
                    </div>
                  </div>
                  
                  {/* Seasonality Boost (US 12.1) */}
                  <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-xl space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="h-3 w-3 text-indigo-500" />
                        <h3 className="text-[10px] font-bold text-indigo-500 tracking-widest">Boost de saisonnalité</h3>
                      </div>
                      <span className="text-[10px] font-bold text-indigo-600 bg-white px-2 py-0.5 rounded-md border border-indigo-100 shadow-sm">
                        × {boostFactor.toFixed(2)}
                      </span>
                    </div>
                    
                    <div className="space-y-4">
                      <div className="flex items-center gap-4">
                        <div className="relative pt-2 flex-1">
                          <input 
                            type="range"
                            min="0.5"
                            max="3.0"
                            step="0.1"
                            value={boostFactor}
                            onChange={(e) => setBoostFactor(parseFloat(e.target.value))}
                            className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-500 transition-colors [&::-webkit-slider-runnable-track]:h-2 [&::-webkit-slider-runnable-track]:rounded-lg [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-indigo-600 [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:-mt-1"
                            style={{
                              background: `linear-gradient(to right, #4f46e5 0%, #4f46e5 ${((boostFactor - 0.5) / 2.5) * 100}%, #f1f5f9 ${((boostFactor - 0.5) / 2.5) * 100}%, #f1f5f9 100%)`
                            }}
                          />
                          
                   {/* Scale markers with absolute positioning */}
                   <div className="relative h-6 mt-3">
                     {[0.5, 1.0, 2.0, 3.0].map((val) => {
                       const isActive = Math.abs(boostFactor - val) < 0.05;
                       const percent = ((val - 0.5) / 2.5) * 100;
                       return (
                         <div 
                           key={val} 
                           className="absolute flex flex-col items-center gap-1 transition-all duration-300"
                           style={{ left: `${percent}%`, transform: 'translateX(-50%)' }}
                         >
                           <div className={cn(
                             "h-1 w-0.5 rounded-full",
                             isActive ? "bg-indigo-600 h-2" : "bg-slate-300"
                           )} />
                           <span className={cn(
                             "text-[7px] font-bold tracking-tighter whitespace-nowrap",
                             isActive ? "text-indigo-600 scale-110" : "text-slate-400"
                           )}>
                             {val === 1.0 ? "NORM" : `x${val}`}
                           </span>
                         </div>
                       );
                     })}
                   </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 bg-indigo-50/50 p-2.5 rounded-xl border border-indigo-100/30">
                         <div className="flex-1">
                            <p className="text-[8px] font-bold text-indigo-900 uppercase tracking-wider mb-0.5">Ratio de boost</p>
                            <p className="text-[8px] text-indigo-600/70 italic leading-tight">Accélère la demande de {((boostFactor - 1) * 100).toFixed(0)}%</p>
                         </div>
                         <input 
                           type="number"
                           step="0.01"
                           min="0.1"
                           value={boostFactor.toFixed(2)}
                           onChange={(e) => setBoostFactor(parseFloat(e.target.value) || 1.0)}
                           className="w-14 h-8 border-2 border-indigo-200 rounded-lg text-[10px] font-black text-indigo-700 text-center focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 bg-white transition-all duration-300"
                         />
                      </div>
                      <p className="text-[8px] text-slate-400 font-medium italic px-1">
                        * Ce coefficient multiplie directement la demande statistique moyenne pour anticiper les pics.
                      </p>
                    </div>
                  </div>

                  {/* Settings Grid (Inventory + Weighting) */}
                  <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Settings className="h-3 w-3 text-slate-400" />
                        <h3 className="text-[10px] font-bold text-slate-400 tracking-widest">Paramètres d'inventaire</h3>
                      </div>
                      <button 
                        onClick={handleQuickSave}
                        disabled={saveStatus === 'saving'}
                        className={cn(
                          "flex items-center gap-1.5 px-2 py-1 rounded-md text-[9px] font-bold transition-colors",
                          saveStatus === 'success' ? "bg-emerald-500 text-white shadow-sm" : 
                          saveStatus === 'saving' ? "bg-slate-100 text-slate-400" :
                          "bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 shadow-sm"
                        )}
                      >
                        {saveStatus === 'saving' ? "..." : saveStatus === 'success' ? (
                          <><Check className="h-2.5 w-2.5" /> Enregistré</>
                        ) : (
                          <><Save className="h-2.5 w-2.5" /> Sauver</>
                        )}
                      </button>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1.5">
                        <p className="text-[9px] font-bold text-slate-400 ml-0.5">Délai (jours)</p>
                        <input 
                          type="number"
                          value={leadTime}
                          onChange={(e) => setLeadTime(parseInt(e.target.value) || 0)}
                          className="w-full h-8 px-2 bg-white border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 transition-all font-medium text-slate-900"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <p className="text-[9px] font-bold text-slate-400 ml-0.5">MOQ (unités)</p>
                        <input 
                          type="number"
                          value={moq}
                          onChange={(e) => setMoq(parseInt(e.target.value) || 0)}
                          className="w-full h-8 px-2 bg-white border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 transition-all font-medium text-slate-900"
                        />
                      </div>
                      <div className="col-span-1 space-y-1.5">
                        <p className="text-[9px] font-bold text-slate-400 ml-0.5">Coût d'achat (€)</p>
                        <input 
                          type="number"
                          step="0.01"
                          value={costPrice}
                          onChange={(e) => setCostPrice(parseFloat(e.target.value) || 0)}
                          className="w-full h-8 px-2 bg-white border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 transition-all font-medium text-slate-900"
                        />
                      </div>
                      <div className="col-span-1 space-y-1.5">
                        <p className="text-[9px] font-bold text-slate-400 ml-0.5">Prix de vente (€)</p>
                        <input 
                          type="number"
                          step="0.01"
                          value={salePrice}
                          onChange={(e) => setSalePrice(parseFloat(e.target.value) || 0)}
                          className="w-full h-8 px-2 bg-white border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 transition-all font-medium text-slate-900"
                        />
                      </div>
                      <div className="col-span-2 space-y-1.5">
                        <p className="text-[9px] font-bold text-slate-400 ml-0.5">Pondération du canal (Priorité)</p>
                        <div className="flex items-center gap-3">
                           <input 
                            type="number"
                            step="0.1"
                            min="0.1"
                            value={stockWeight.toFixed(2)}
                            onChange={(e) => setStockWeight(parseFloat(e.target.value) || 1.0)}
                            className="flex-1 h-8 px-2 bg-white border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 transition-all font-medium text-slate-900"
                          />
                          <p className="text-[8px] text-slate-400 leading-tight italic">Allocation stock en cas de rupture.</p>
                        </div>
                      </div>
                    </div>
                  </div>
        
                  {/* ── What-If Simulator (US 14.4) ── */}
                  {product.prediction?.runRate > 0 && (
                    <WhatIfSimulator 
                      currentStock={product.currentStock}
                      runRate={product.prediction.runRate}
                      leadTime={leadTime}
                      boostFactor={boostFactor}
                      costPrice={costPrice}
                      salePrice={salePrice}
                    />
                  )}

                  {/* Graph Section — Historical */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-[10px] font-bold text-slate-400 tracking-widest">Historique &amp; tendances</h3>
                      <div className="flex items-center gap-3">
                          <div className="flex items-center gap-1.5">
                             <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                             <span className="text-[9px] font-bold text-slate-500">Ventes</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                             <div className="h-1.5 w-1.5 rounded-full bg-slate-300" />
                             <span className="text-[9px] font-bold text-slate-500">Stock</span>
                          </div>
                      </div>
                    </div>
                    
                    <div className="h-36 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData}>
                          <defs>
                            <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1}/>
                              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                          <XAxis 
                            dataKey="date" 
                            axisLine={false} 
                            tickLine={false} 
                            tick={{ fontSize: 8, fill: '#94a3b8' }}
                            interval={5}
                          />
                          <YAxis 
                            axisLine={false} 
                            tickLine={false} 
                            tick={{ fontSize: 8, fill: '#94a3b8' }}
                          />
                          <Tooltip 
                            contentStyle={{ 
                              backgroundColor: '#fff', 
                              borderRadius: '12px', 
                              border: '1px solid #f1f5f9',
                              boxShadow: 'none',
                              fontSize: '10px'
                            }}
                          />
                          <Area 
                            type="monotone" 
                            dataKey="sales" 
                            stroke="#3b82f6" 
                            fillOpacity={1} 
                            fill="url(#colorSales)" 
                            strokeWidth={2}
                          />
                          <Line 
                            type="stepAfter" 
                            dataKey="stock" 
                            stroke="#94a3b8" 
                            strokeWidth={1.5} 
                            dot={false}
                            strokeDasharray="4 4"
                          />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>
                    <p className="text-[10px] text-slate-400 italic text-center">Évolution du stock (pointillés) et ventes quotidiennes corrigées sur 30j.</p>
                  </div>

                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-primary/10 rounded-lg">
                        <TrendingUp className="h-3.5 w-3.5 text-primary" />
                      </div>
                      <span className="text-[10px] font-black text-slate-900 tracking-widest">Analyse prédictive</span>
                    </div>
                    
                    <div className="space-y-3">
                       <div className="flex items-start gap-3">
                          <div className="h-5 w-5 rounded-full bg-white border border-slate-200 flex items-center justify-center shrink-0 mt-0.5">
                             <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                          </div>
                           <p className="text-xs text-slate-600 font-medium leading-relaxed">
                             Votre rythme de vente actuel est de <span className="text-slate-900 font-bold">{(product.prediction?.runRate || 0).toFixed(2)} Unit./jour</span>.
                           </p>
                       </div>

                       <div className="flex items-start gap-3">
                          <div className={cn(
                             "h-5 w-5 rounded-full bg-white border flex items-center justify-center shrink-0 mt-0.5",
                             (product.prediction?.daysOfStock || 0) < product.leadTime ? "border-red-200" : "border-slate-200"
                          )}>
                             <div className={cn(
                                "h-1.5 w-1.5 rounded-full",
                                (product.prediction?.daysOfStock || 0) < product.leadTime ? "bg-red-500" : "bg-emerald-500"
                             )} />
                          </div>
                           <p className="text-xs text-slate-600 font-medium leading-relaxed">
                             Le stock actuel couvre environ <span className={cn(
                                "font-bold",
                                (product.prediction?.daysOfStock || 0) < product.leadTime ? "text-red-600" : "text-slate-900"
                             )}>{Math.round(product.prediction?.daysOfStock || 0)} jours</span> d'activité.
                           </p>
                       </div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="p-4 border-t border-slate-50 bg-slate-50/30">
                  <button 
                    onClick={() => {
                      router.push(`/dashboard/product/${product.id}`);
                      onClose();
                    }}
                    className="w-full py-3 bg-slate-900 text-white rounded-lg text-[10px] font-bold tracking-widest hover:bg-slate-800 transition-colors flex items-center justify-center gap-2"
                  >
                    Voir les détails complets
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-4">
                <AlertCircle className="h-8 w-8 text-slate-200" />
                <p className="text-xs text-slate-500">Impossible de charger les détails du produit.</p>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>,
    document.body
  );
}
