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
  Settings,
  Save,
  Check,
  Activity,
  Copy,
  ShieldCheck,
  Zap,
  Info
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
  Line
} from 'recharts';
import { GET_PRODUCT_DETAIL } from '@/graphql/queries/getProductDetail';
import { UPDATE_PRODUCT_SETTINGS } from '@/graphql/mutations/updateProduct';
import { cn } from '@/lib/utils';
import { useRouter } from 'next/navigation';
import { LoadingState } from '../ui/LoadingState';
interface ProductQuickViewProps {
  productId: string | null;
  onClose: () => void;
}

// ── What-If Simulator Component (US 14.4) ───────────────────
function WhatIfSimulator({
  currentStock, runRate, leadTime, boostFactor, salePrice, costPrice, demandSigma,
  supplierAvgDelay = 0, supplierSigma = 0
}: {
  currentStock: number; 
  runRate: number; 
  leadTime: number; 
  boostFactor: number; 
  costPrice: number; 
  salePrice: number;
  demandSigma: number;
  supplierAvgDelay?: number;
  supplierSigma?: number;
}) {
  const [extraDelay, setExtraDelay] = React.useState(0);
  const [salesMultiplier, setSalesMultiplier] = React.useState(1.0);
  const isSimulating = extraDelay > 0 || salesMultiplier !== 1.0;

  // Approximation de la distribution normale (ERF) pour le calcul du RoS
  const normalCDF = (x: number) => {
    const t = 1 / (1 + 0.2316419 * Math.abs(x));
    const d = 0.3989423 * Math.exp(-x * x / 2);
    const p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
    return x > 0 ? 1 - p : p;
  };

  const simRunRate = runRate * boostFactor * salesMultiplier;
  const simLeadTime = leadTime + extraDelay;
  
  // Calcul statistique du Risque de Rupture (Risk of Stockout)
  // Dual-Sigma logic: Combining Quantity variance (demandSigma) and Time variance (supplierSigma)
  // sigmaCombined = sqrt( (LT * sigma_demand^2) + (RunRate^2 * sigma_LT^2) )
  const meanOverLT = simRunRate * simLeadTime;
  const sigmaOverLT = Math.sqrt(
    (simLeadTime * Math.pow(demandSigma, 2)) + 
    (Math.pow(simRunRate, 2) * Math.pow(supplierSigma, 2))
  );
  
  const ros = sigmaOverLT > 0 
    ? (1 - normalCDF((currentStock - meanOverLT) / sigmaOverLT)) * 100
    : (currentStock < meanOverLT ? 100 : 0);

  const simDaysOfStock = simRunRate > 0 ? currentStock / simRunRate : 999;
  const simStockoutDate = new Date(Date.now() + simDaysOfStock * 86400000);
  
  // Coût de détention (Holding Cost) estimé à 20% par an si on sur-stocke
  const safetyStockLevel = Math.max(0, currentStock - meanOverLT);
  const annualHoldingCost = safety_stock_value => safety_stock_value * 0.20;
  const dailyHoldingCost = annualHoldingCost(safetyStockLevel * costPrice) / 365;

  const simRevenueAtRisk = Math.max(0, (simRunRate * Math.max(0, simLeadTime - simDaysOfStock)) * (salePrice || 0));

  const projectionData = React.useMemo(() => {
    const pts = [];
    const maxDays = Math.min(90, Math.ceil(simDaysOfStock) + 20);
    const sigma = demandSigma;
    
    for (let d = 0; d <= maxDays; d += 2) {
      const mean = Math.max(0, currentStock - (simRunRate * d));
      const stdDev = sigma * Math.sqrt(d);
      pts.push({
        day: `J+${d}`,
        base: Math.max(0, Math.round(currentStock - runRate * boostFactor * d)),
        sim: Math.round(mean),
        // Intervalle de confiance 95% (+/- 1.96 sigma)
        low: Math.max(0, Math.round(mean - 1.96 * stdDev)),
        high: Math.round(mean + 1.96 * stdDev),
      });
    }
    return pts;
  }, [currentStock, runRate, boostFactor, simRunRate, simDaysOfStock, demandSigma]);

  return (
    <div className={cn(
      "p-3 rounded-xl border space-y-3 transition-all",
      isSimulating ? "bg-indigo-50/30 border-indigo-200" : "bg-slate-50 border-slate-100"
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-3 w-3 text-primary" />
          <h3 className="text-[10px] font-bold text-slate-700 tracking-widest uppercase">Simulateur What-if</h3>
          {isSimulating && (
            <span className="text-[7px] font-black text-primary bg-primary/10 px-1.5 py-0.5 rounded-full border border-primary/20 animate-pulse">
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

      {!isSimulating && supplierAvgDelay > 0 && (
         <button 
           onClick={() => setExtraDelay(Math.ceil(supplierAvgDelay))}
           className="w-full py-1.5 bg-amber-50 border border-amber-100 rounded-lg text-[9px] font-bold text-amber-700 hover:bg-amber-100 transition-all flex items-center justify-center gap-1.5"
         >
           <Clock className="h-3 w-3" />
           Simuler avec retard historique (+{supplierAvgDelay.toFixed(1)}j)
         </button>
      )}

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
              <>
                {/* Confidence Ribbon */}
                <Area 
                  type="monotone" 
                  dataKey="high" 
                  stroke="none" 
                  fill="#f59e0b" 
                  fillOpacity={0.08} 
                  name="Confiance Sup" 
                />
                <Area 
                  type="monotone" 
                  dataKey="low" 
                  stroke="none" 
                  fill="#f59e0b" 
                  fillOpacity={0.08} 
                  name="Confiance Inf" 
                />
                <Area type="monotone" dataKey="sim" stroke="#f59e0b" strokeWidth={2} strokeDasharray="4 3" fillOpacity={1} fill="url(#colorSim)" name="Simulé" />
              </>
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Results */}
      <div className="grid grid-cols-3 gap-2">
        <div className="text-center p-2 bg-white rounded-lg border border-slate-100">
          <p className="text-[7px] font-bold text-slate-400 mb-0.5">Risque Rupture</p>
          <p className={cn("text-sm font-black transition-colors", ros > 5 ? "text-red-600" : "text-emerald-600")}>
            {ros.toFixed(1)}%
          </p>
        </div>
        <div className="text-center p-2 bg-white rounded-lg border border-slate-100">
          <p className="text-[7px] font-bold text-slate-400 mb-0.5">Rupture (Date)</p>
          <p className={cn("text-[9px] font-black", simDaysOfStock < simLeadTime ? "text-red-600" : "text-slate-900")}>
            {simStockoutDate.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
          </p>
        </div>
        <div className="text-center p-2 bg-white rounded-lg border border-slate-100">
          <p className="text-[7px] font-bold text-slate-400 mb-0.5">Coût Surstock</p>
          <p className={cn("text-[9px] font-black", dailyHoldingCost > 1 ? "text-amber-600" : "text-slate-500")}>
            {dailyHoldingCost > 0.01 ? `${dailyHoldingCost.toFixed(2)}€/j` : "—"}
          </p>
        </div>
      </div>
    </div>
  );
}

export function ProductQuickView({ productId, onClose }: ProductQuickViewProps) {
  const router = useRouter();
  const { data, loading } = useQuery(GET_PRODUCT_DETAIL, {
    variables: {
      id: productId!
    },
    skip: !productId,
    fetchPolicy: 'cache-and-network'
  });

  const product = data?.productDetail?.[0];

  // Prepare chart data
  const chartData = React.useMemo(() => {
    if (!product?.cleanedDemands) return [];
    return product.cleanedDemands
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
  const [copied, setCopied] = React.useState(false);

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
              data-testid="product-quickview"
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
                    <div className="flex items-center gap-2">
                      <p className="text-[10px] font-bold text-slate-400 tracking-widest uppercase">SKU: {product.sku}</p>
                      <button 
                        onClick={() => {
                          navigator.clipboard.writeText(product.sku);
                          setCopied(true);
                          setTimeout(() => setCopied(false), 2000);
                        }}
                        className={cn(
                          "p-1 rounded transition-all",
                          copied ? "bg-emerald-50 text-emerald-600" : "hover:bg-slate-100 text-slate-300 hover:text-primary"
                        )}
                        title="Copier le SKU"
                      >
                        {copied ? <Check className="h-2.5 w-2.5" /> : <Copy className="h-2.5 w-2.5" />}
                      </button>
                    </div>
                  </div>
                  <button 
                    onClick={onClose}
                    data-testid="close-quickview"
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
                  {(product.prediction?.runRate ?? 0) > 0 && (
                    <WhatIfSimulator
                      currentStock={product.currentStock}
                      runRate={product.prediction!.runRate}
                      leadTime={leadTime}
                      boostFactor={boostFactor}
                      costPrice={costPrice}
                      salePrice={salePrice}
                      demandSigma={product.prediction!.demandSigma || 0}
                      supplierAvgDelay={product.supplier?.averageDelayDays}
                      supplierSigma={product.supplier?.leadTimeSigma}
                    />
                  )}

                  {/* Supplier Reliability Section (Dual-Sigma) */}
                  {product.supplier && (
                    <div className="p-3 bg-emerald-50/50 border border-emerald-100 rounded-xl space-y-3">
                      <div className="flex items-center gap-2">
                        <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                        <h3 className="text-[10px] font-bold text-emerald-700 tracking-widest uppercase">Performance Fournisseur</h3>
                      </div>
                      
                      <div className="grid grid-cols-3 gap-2">
                        <div className="text-center p-2 bg-white rounded-lg border border-emerald-100 shadow-sm">
                          <p className="text-[7px] font-bold text-slate-400 mb-0.5 uppercase tracking-tighter">Fiabilité</p>
                          <p className={cn(
                            "text-sm font-black",
                            product.supplier.reliabilityScore < 0.8 ? "text-amber-600" : "text-emerald-600"
                          )}>
                            {(product.supplier.reliabilityScore * 100).toFixed(0)}%
                          </p>
                        </div>
                        <div className="text-center p-2 bg-white rounded-lg border border-emerald-100 shadow-sm">
                          <p className="text-[7px] font-bold text-slate-400 mb-0.5 uppercase tracking-tighter">Retard Moyen</p>
                          <p className="text-sm font-black text-slate-900">
                            +{product.supplier.averageDelayDays.toFixed(1)}j.
                          </p>
                        </div>
                        <div className="text-center p-2 bg-white rounded-lg border border-emerald-100 shadow-sm">
                          <p className="text-[7px] font-bold text-slate-400 mb-0.5 uppercase tracking-tighter">Variabilité</p>
                          <p className="text-sm font-black text-slate-900">
                            σ {product.supplier.leadTimeSigma.toFixed(1)}j.
                          </p>
                        </div>
                      </div>
                      
                      {product.supplier.leadTimeSigma > 2 && (
                        <div className="flex items-start gap-2 px-1">
                          <AlertCircle className="h-3 w-3 text-amber-500 shrink-0 mt-0.5" />
                          <p className="text-[8px] text-amber-700 font-medium leading-tight italic">
                            Attention : La variabilité de livraison est élevée. Nous recommandons un stock de sécurité majoré de 15%.
                          </p>
                        </div>
                      )}
                    </div>
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
                    data-testid="open-full-detail"
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
