'use client';

import React, { useState } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { useParams, useRouter } from 'next/navigation';
import { GET_PRODUCT_DETAIL } from '@/graphql/queries/getProductDetail';
import { UPDATE_PRODUCT_SETTINGS } from '@/graphql/mutations/updateProduct';
import { 
  ChevronLeft,
  TrendingUp,
  AlertCircle, 
  Zap,
  Calendar,
  Box,
  Settings
} from 'lucide-react';
import SalesChart from '@/components/dashboard/SalesChart';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import { LoadingState } from '@/components/ui/LoadingState';
import { ProductQuickView } from '@/components/dashboard/ProductQuickView';
import { useTranslations } from 'next-intl';

export default function ProductDetailPage() {
  const t = useTranslations('inventory.details');
  const { id } = useParams();
  const router = useRouter();
  const [leadTimeDelta, setLeadTimeDelta] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

  // Form states
  const [leadTime, setLeadTime] = useState<number>(0);
  const [moq, setMoq] = useState<number>(0);
  const [boostFactor, setBoostFactor] = useState<number>(1.0);
  const [stockWeight, setStockWeight] = useState<number>(1.0);
  const [selectedChannelId, setSelectedChannelId] = useState<string | null>(null);

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
          moq,
          boostFactor,
          stockWeight
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
      setBoostFactor(data.productDetail[0].boostFactor || 1.0);
      setStockWeight(data.productDetail[0].stockWeight || 1.0);
    }
  }, [data]);

  if (loading) return <LoadingState />;
  if (error || !data?.productDetail?.[0]) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center animate-in fade-in zoom-in duration-500">
        <div className="bg-red-50 p-6 rounded-full mb-6 ring-8 ring-red-50/50">
          <AlertCircle className="h-12 w-12 text-red-500" />
        </div>
        <h2 className="text-xl font-black text-sentence mb-2 italic tracking-tight">{t('notFound')}</h2>
        <p className="text-sm text-muted-foreground text-sentence max-w-sm mb-8 leading-relaxed">
          {t('notFoundDesc')}
        </p>
        <div className="flex items-center gap-4">
          <button 
            onClick={() => refetch()}
            className="px-6 py-2.5 bg-slate-900 text-white rounded-lg text-xs font-bold tracking-widest hover:bg-slate-800 transition-all shadow-lg hover:shadow-slate-200 active:scale-95"
          >
            {t('retry')}
          </button>
          <button 
            onClick={() => router.push('/dashboard?tab=inventory')}
            className="px-6 py-2.5 bg-white border-2 border-slate-200 text-slate-600 rounded-lg text-xs font-bold tracking-widest hover:bg-slate-50 transition-all active:scale-95"
          >
            {t('backToInventory')}
          </button>
        </div>
      </div>
    );
  }

  const product = data.productDetail[0];
  const prediction = product.prediction;

  // Simulate impact
  const impactOnStockout = leadTimeDelta > 0 ? t('increasedRisk') : t('improvedSecurity');

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
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
          <p className="text-xs text-muted-foreground text-sentence">{t('subtitle')}</p>
        </div>
        {product.supplier && (
          <div className="ml-auto flex items-center gap-3 px-3 py-1.5 bg-slate-50/50 rounded-lg border border-slate-100">
            <div className="flex flex-col items-end">
              <span className="text-[9px] font-bold text-slate-400 leading-none">{t('supplier')}</span>
              <span className="text-[11px] font-bold text-slate-900 mt-0.5">{product.supplier.name}</span>
            </div>
            <div className={cn(
              "flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-black",
              product.supplier.reliabilityScore > 0.8 
                ? "bg-emerald-50 text-emerald-600" 
                : "bg-amber-50 text-amber-600"
            )}>
              <div className={cn(
                "h-1.5 w-1.5 rounded-full animate-pulse",
                product.supplier.reliabilityScore > 0.8 ? "bg-emerald-500" : "bg-amber-500"
              )} />
              {(product.supplier.reliabilityScore * 100).toFixed(0)}%
            </div>
          </div>
        )}
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center gap-2 mb-4 text-muted-foreground">
            <Box className="h-4 w-4" />
            <span className="text-xs font-medium text-sentence">{t('currentStock')}</span>
          </div>
          <div className="text-3xl font-bold tracking-tight">{product.currentStock} u.</div>
          <p className="text-[11px] text-muted-foreground mt-2 text-sentence">{t('warningThreshold')} : {product.warningThreshold} u.</p>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center gap-2 mb-4 text-muted-foreground">
            <Calendar className="h-4 w-4" />
            <span className="text-xs font-medium text-sentence">{t('predictedStockout')}</span>
          </div>
          <div className={`text-3xl font-bold tracking-tight ${prediction?.predictedStockoutDate && new Date(prediction.predictedStockoutDate) < new Date() ? 'text-red-500' : ''}`}>
            {prediction?.predictedStockoutDate ? format(new Date(prediction.predictedStockoutDate), 'dd MMM yyyy', { locale: fr }) : 'N/A'}
          </div>
          <p className="text-[11px] text-muted-foreground mt-2 text-sentence">{t('runRateInfo', { rate: prediction?.runRate.toFixed(2) || '0' })}</p>
        </div>

        <div className="bg-primary text-primary-foreground rounded-lg border p-6 shadow-md relative overflow-hidden">
          <div className="flex items-center gap-2 mb-4 opacity-80">
            <Zap className="h-4 w-4" />
            <span className="text-xs font-medium text-sentence">{t('suggestedOrder')}</span>
          </div>
          <div className="text-3xl font-bold tracking-tight">+{Math.round(prediction?.reorderQuantity || 0)} u.</div>
          <p className="text-[11px] opacity-80 mt-2 text-sentence">
            {t('leadTimeInfo', { days: product.leadTime })} 
            {boostFactor !== 1 && ` ${t('boostNote', { factor: boostFactor.toFixed(2) })}`}
          </p>
          {boostFactor > 1.2 && (
             <div className="absolute top-2 right-2 bg-white/20 px-1.5 py-0.5 rounded text-[8px] font-bold tracking-wider animate-pulse">{t('highDemand')}</div>
          )}
        </div>
      </div>

      {/* Analytics Chart */}
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-sentence italic">{t('analyticsTitle')}</h3>
            <p className="text-xs text-muted-foreground text-sentence">{t('analyticsSubtitle')}</p>
          </div>
          <div className="flex items-center gap-4 text-[10px] font-bold">
            <div className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-indigo-500" /> {t('history')}</div>
            <div className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-indigo-200" /> {t('prediction')}</div>
          </div>
        </div>
        <div className="h-[320px] bg-slate-50/50 rounded-xl border border-dashed relative overflow-hidden">
          {product.cleanedDemands && product.cleanedDemands.length > 0 ? (
            <SalesChart 
              data={product.cleanedDemands || []} 
              title="" 
            />
          ) : (
            <div className="text-center py-20">
               <p className="text-[10px] font-bold text-slate-400 tracking-widest mb-1">{t('emptyHistory')}</p>
            </div>
          )}
        </div>
      </div>


      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Seasonality Boost (US 12.1) */}
        <div className="bg-white rounded-lg border p-6 space-y-6">
           <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-50 rounded-lg">
                  <TrendingUp className="h-5 w-5 text-indigo-600" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-sentence">{t('boostTitle')}</h4>
                  <p className="text-xs text-muted-foreground text-sentence">{t('boostSubtitle')}</p>
                </div>
              </div>
              <div className="text-lg font-bold text-indigo-600 bg-indigo-50 px-3 py-1 rounded-lg border border-indigo-100">
                × {boostFactor.toFixed(2)}
              </div>
           </div>

           <div className="space-y-6">
              <div className="flex flex-col gap-6">
                <input 
                  type="range"
                  min="0.5"
                  max="3.0"
                  step="0.1"
                  value={boostFactor}
                  onChange={(e) => setBoostFactor(parseFloat(e.target.value))}
                  className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer transition-all [&::-webkit-slider-runnable-track]:h-2 [&::-webkit-slider-runnable-track]:rounded-lg [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-indigo-600 [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:-mt-1.5"
                  style={{
                    background: `linear-gradient(to right, #4f46e5 0%, #4f46e5 ${((boostFactor - 0.5) / 2.5) * 100}%, #f1f5f9 ${((boostFactor - 0.5) / 2.5) * 100}%, #f1f5f9 100%)`
                  }}
                />
                
                {/* Visual scale indicators with fixed positioning */}
                <div className="relative h-8 mt-3 mx-1">
                  {[0.5, 1.0, 2.0, 3.0].map((val) => {
                    const isActive = Math.abs(boostFactor - val) < 0.05;
                    const percent = ((val - 0.5) / 2.5) * 100;
                    return (
                      <div 
                        key={val} 
                        className="absolute flex flex-col items-center gap-1.5 transition-all duration-300"
                        style={{ left: `${percent}%`, transform: 'translateX(-50%)' }}
                      >
                        <div className={cn(
                          "h-1.5 w-0.5 rounded-full",
                          isActive ? "bg-indigo-600 h-2.5" : "bg-slate-300"
                        )} />
                        <span className={cn(
                          "text-[9px] font-bold tracking-tighter transition-all whitespace-nowrap",
                          isActive ? "text-indigo-600 scale-125" : "text-slate-400",
                          val === 1.0 && !isActive && "text-slate-900 border-b border-slate-200"
                        )}>
                          {val === 1.0 ? t('normal') : `x${val}`}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
              
              <div className="flex items-center gap-4 bg-indigo-50/50 p-4 rounded-xl border border-indigo-100/50">
                 <div className="flex-1">
                    <p className="text-[10px] font-bold text-indigo-900 tracking-wider mb-0.5">{t('multiplicationFactor')}</p>
                    <p className="text-[10px] text-indigo-600/70 italic leading-tight">{t('optimizedForecasting', { percent: ((boostFactor - 1) * 100).toFixed(0) })}</p>
                 </div>
                 <input 
                   type="number"
                   step="0.01"
                   min="0.1"
                   value={boostFactor.toFixed(2)}
                   onChange={(e) => setBoostFactor(parseFloat(e.target.value) || 1.0)}
                   className="w-20 h-10 border-2 border-indigo-200 rounded-lg text-sm font-black text-indigo-700 text-center focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 bg-white transition-all duration-300"
                 />
              </div>
              
              <div className="p-4 bg-slate-50 rounded-xl border border-dashed text-[11px] text-muted-foreground text-sentence leading-relaxed">
                {t('boostExplanation')} 
                <br />• <strong>{boostFactor > 1 ? `+${((boostFactor-1)*100).toFixed(0)}%` : `${((boostFactor-1)*100).toFixed(0)}%`}</strong> {t('boostImpact')}
                <br />• {t('boostOrderImpact')} <strong>+{Math.round((prediction?.reorderQuantity || 0) * (boostFactor - 1))} u.</strong>
              </div>
           </div>
        </div>

        {/* Omnichannel Allocation (US 12.3) */}
        <div className="bg-white rounded-lg border p-6 space-y-6">
           <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-50 rounded-lg">
                <Settings className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-sentence">{t('omnichannelTitle')}</h4>
                <p className="text-xs text-muted-foreground text-sentence">{t('omnichannelSubtitle')}</p>
              </div>
           </div>

           <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-[10px] font-bold text-muted-foreground tracking-wider">{t('globalWeight')}</label>
                <input 
                  type="number" 
                  step="0.1"
                  value={stockWeight.toFixed(2)}
                  onChange={(e) => setStockWeight(parseFloat(e.target.value) || 1.0)}
                  className="w-20 h-10 border rounded-lg text-sm font-bold text-center focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20"
                />
              </div>
              <p className="text-[11px] text-muted-foreground text-sentence leading-relaxed">
                {t('weightExplanation')}
              </p>
              <div className="flex gap-2">
                {[0.5, 1.0, 1.5, 2.0].map(val => (
                  <button 
                    key={val}
                    onClick={() => setStockWeight(val)}
                    className={cn(
                      "flex-1 py-2 text-[10px] font-bold rounded-md border transition-colors",
                      stockWeight === val ? "bg-amber-100 border-amber-200 text-amber-700" : "bg-white hover:bg-slate-50 text-slate-500"
                    )}
                  >
                    {val === 1.0 ? t('normal') : val > 1.0 ? `High (${val}x)` : `Low (${val}x)`}
                  </button>
                ))}
              </div>
           </div>
        </div>
      </div>

      {/* Sources Breakdown (US 12.2) */}
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-slate-100 rounded-lg">
              <Box className="h-5 w-5 text-slate-600" />
            </div>
            <h4 className="text-sm font-bold text-sentence">{t('channelBreakdown')}</h4>
        </div>

        <div className="overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="text-left border-b text-muted-foreground">
                  <th className="pb-3 font-bold tracking-wider">{t('platform')}</th>
                  <th className="pb-3 font-bold tracking-wider text-center">{t('stock')}</th>
                  <th className="pb-3 font-bold tracking-wider text-center">{t('runRate')}</th>
                  <th className="pb-3 font-bold tracking-wider text-center">{t('delay')}</th>
                  <th className="pb-3 font-bold tracking-wider text-center">{t('moq')}</th>
                  <th className="pb-3 font-bold tracking-wider text-right">{t('weight')}</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {product.channels && product.channels.length > 0 ? (
                  product.channels.map((ch: any) => (
                    <tr 
                      key={ch.productId} 
                      onClick={() => setSelectedChannelId(ch.productId)}
                      className="hover:bg-slate-50/50 transition-colors cursor-pointer group"
                    >
                      <td className="py-4">
                        <div className="flex items-center gap-2">
                          <span className="capitalize font-semibold text-sentence group-hover:text-primary transition-colors">{ch.platform}</span>
                        </div>
                      </td>
                      <td className="py-4 text-center font-bold">{ch.currentStock} u.</td>
                      <td className="py-4 text-center text-indigo-600 font-bold">{ch.runRate.toFixed(2)} /j</td>
                      <td className="py-4 text-center text-slate-500">{ch.leadTime} j.</td>
                      <td className="py-4 text-center text-slate-500">{ch.moq} u.</td>
                      <td className="py-4 text-right">
                         <span className={cn(
                            "px-2 py-0.5 rounded text-[10px] font-bold",
                            ch.stockWeight > 1 ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-600"
                         )}>
                            {ch.stockWeight.toFixed(2)}x
                         </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="py-20 text-center">
                       <p className="text-[10px] font-bold text-slate-400 tracking-widest mb-1">{t('emptySources')}</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
        </div>
      </div>

      {/* Simulator (US 11.4) */}
      <div className="bg-accent/30 rounded-lg border border-indigo-100 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-indigo-100 rounded-lg">
            <Zap className="h-5 w-5 text-indigo-600" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-sentence">{t('whatIfTitle')}</h4>
            <p className="text-xs text-muted-foreground text-sentence italic">{t('whatIfSubtitle')}</p>
          </div>
        </div>

        {prediction ? (
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div className="space-y-4">
              <div className="flex justify-between items-end">
                <label className="text-[10px] font-bold text-muted-foreground">{t('estimatedDelay')}</label>
                <span className="text-lg font-bold bg-white px-3 py-1 rounded-md border shadow-sm">
                  {leadTimeDelta > 0 ? `+${leadTimeDelta}` : leadTimeDelta} {t('delay')}
                </span>
              </div>
              <div className="relative pt-2">
                <input 
                  type="range" 
                  min="-7" 
                  max="30" 
                  value={leadTimeDelta} 
                  onChange={(e) => setLeadTimeDelta(parseInt(e.target.value))}
                  className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-600 transition-all [&::-webkit-slider-runnable-track]:h-2 [&::-webkit-slider-runnable-track]:rounded-lg [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-indigo-600 [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:-mt-1.5"
                  style={{
                    background: `linear-gradient(to right, #4f46e5 0%, #4f46e5 ${((leadTimeDelta + 7) / 37) * 100}%, #f1f5f9 ${((leadTimeDelta + 7) / 37) * 100}%, #f1f5f9 100%)`
                  }}
                />
                
                {/* Visual scale markers with absolute positioning */}
                <div className="relative h-8 mt-4 mx-1">
                  {[-7, 0, 7, 14, 21, 30].map((val) => {
                    const isActive = Math.abs(leadTimeDelta - val) < 1;
                    const percent = ((val + 7) / 37) * 100;
                    return (
                      <div 
                        key={val} 
                        className="absolute flex flex-col items-center gap-1.5 transition-all duration-300"
                        style={{ left: `${percent}%`, transform: 'translateX(-50%)' }}
                      >
                        <div className={cn(
                          "h-1.5 w-0.5 rounded-full",
                          isActive ? "bg-indigo-600 h-2.5" : "bg-slate-300"
                        )} />
                        <span className={cn(
                          "text-[8px] font-bold tracking-tighter whitespace-nowrap transition-all",
                          isActive ? "text-indigo-600 scale-110" : "text-slate-400",
                          val === 0 && !isActive && "text-slate-900 border-b border-slate-200"
                        )}>
                          {val === 0 ? t('normal') : `${val > 0 ? '+' : ''}${val}j`}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg border shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <AlertCircle className={`h-4 w-4 ${leadTimeDelta > 5 ? 'text-red-500' : 'text-indigo-500'}`} />
                <span className="text-xs font-bold text-sentence">{t('impactAnalysis')}</span>
              </div>
              <p className="text-sm font-medium text-sentence mb-1">{impactOnStockout}</p>
              <p className="text-xs text-muted-foreground text-sentence">
                {leadTimeDelta > 0 
                  ? t('impactNote', { days: leadTimeDelta, percent: (leadTimeDelta * 3.5).toFixed(0) })
                  : t('optimizedDelayNote')
                }
              </p>
            </div>
          </div>
        ) : (
          <div className="py-12 text-center bg-white/50 rounded-xl border border-dashed flex flex-col items-center justify-center min-h-[140px]">
             <p className="text-[10px] font-bold text-slate-400 tracking-widest mb-1">{t('simUnavailable')}</p>
             <p className="text-[10px] text-slate-300 italic">{t('simUnavailableDesc')}</p>
          </div>
        )}
      </div>

      {/* Persistent Settings (US 11.4) */}
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
           <div className="flex items-center gap-3">
              <div className="p-2 bg-slate-100 rounded-lg">
                <Box className="h-5 w-5 text-slate-600" />
              </div>
              <h4 className="text-sm font-bold text-sentence">{t('inventorySettings')}</h4>
           </div>
           {saveStatus === 'success' && <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full animate-in fade-in zoom-in">✓ {t('saveSuccess')}</span>}
           {saveStatus === 'error' && <span className="text-[10px] font-bold text-red-600 bg-red-50 px-3 py-1 rounded-full animate-in fade-in zoom-in">⚠️ {t('saveError')}</span>}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <label className="text-[10px] font-bold text-muted-foreground">{t('leadTimeLabel')}</label>
            <input 
              type="number" 
              value={leadTime} 
              onChange={(e) => setLeadTime(Math.max(1, parseInt(e.target.value) || 0))}
              className="w-full h-11 px-4 rounded-md border text-sm focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 transition-all"
            />
            <p className="text-[10px] text-muted-foreground italic">{t('leadTimeDesc')}</p>
          </div>
          <div className="space-y-4">
            <label className="text-[10px] font-bold text-muted-foreground">{t('moqLabel')}</label>
            <input 
              type="number" 
              value={moq} 
              onChange={(e) => setMoq(Math.max(1, parseInt(e.target.value) || 0))}
              className="w-full h-11 px-4 rounded-md border text-sm focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 transition-all"
            />
            <p className="text-[10px] text-muted-foreground italic">{t('moqDesc')}</p>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t flex justify-end">
           <button
             onClick={handleSave}
             disabled={isSaving}
             className={cn(
               "px-6 py-2.5 bg-slate-900 text-white rounded-md text-xs font-bold hover:bg-slate-800 transition-colors shadow-sm",
               isSaving && "opacity-70 cursor-not-allowed"
             )}
           >
             {isSaving ? t('saving') : t('saveButton')}
           </button>
        </div>
      </div>

      <ProductQuickView 
        productId={selectedChannelId}
        onClose={() => setSelectedChannelId(null)}
      />
    </div>
  );
}
