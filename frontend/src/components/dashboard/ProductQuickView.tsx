'use client';

import React from 'react';
import { useQuery } from '@apollo/client';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  ArrowRight, 
  TrendingUp, 
  AlertCircle, 
  Box, 
  Calendar,
  ExternalLink,
  ChevronRight
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
import { cn } from '@/lib/utils';
import { useRouter } from 'next/navigation';
import { LoadingState } from '../ui/LoadingState';

interface ProductQuickViewProps {
  productId: string | null;
  onClose: () => void;
}

export function ProductQuickView({ productId, onClose }: ProductQuickViewProps) {
  const router = useRouter();
  const { data, loading } = useQuery(GET_PRODUCTS, {
    variables: { id: productId },
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
            className="fixed inset-y-0 right-0 z-[70] w-full max-w-md bg-white border-l border-slate-100 flex flex-col shadow-none rounded-tl-xl"
          >
            {loading ? (
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

                  {/* Graph Section */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-[10px] font-bold text-slate-400 tracking-widest">Historique & tendances</h3>
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
                    
                    <div className="h-40 w-full">
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
                             Votre rythme de vente actuel est de <span className="text-slate-900 font-bold">{(product.prediction?.runRate || 0).toFixed(1)} Unit./jour</span>.
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
                    className="w-full py-3 bg-slate-900 text-white rounded-lg text-[10px] font-bold tracking-widest hover:bg-slate-800 transition-all flex items-center justify-center gap-2"
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
