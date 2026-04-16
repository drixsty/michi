'use client';
import { useTranslations } from 'next-intl';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, ArrowRight, Zap, ShoppingBag, Globe, FileSpreadsheet } from 'lucide-react';
import { cn } from '@/lib/utils';

interface OnboardingWizardProps {
  userName?: string;
  onComplete: () => void;
  onSync: (platform: string) => Promise<void>;
}

export default function OnboardingWizard({ userName, onComplete, onSync }: OnboardingWizardProps) {
  const t = useTranslations('onboarding.wizard');
  const [currentStep, setCurrentStep] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);

  const STEPS = [
    {
      title: t('steps.0.title'),
      description: t('steps.0.description'),
      cta: t('steps.0.cta'),
      testid: 'wizard-start',
      icon: <CheckCircle2 className="text-primary h-12 w-12" /> // Added default icon if missing
    },
    {
      id: 'connect',
      title: t('steps.connect.title'),
      description: t('steps.connect.description'),
      icon: <ShoppingBag className="text-blue-500 h-12 w-12" />,
      cta: t('steps.connect.cta'),
      testid: 'wizard-next'
    },
    {
      id: 'analysis',
      title: t('steps.analysis.title'),
      description: t('steps.analysis.description'),
      icon: <Zap className="text-amber-500 h-12 w-12" />,
      cta: t('steps.analysis.cta'),
      testid: 'wizard-finish'
    },
    {
      id: 'ready',
      title: t('steps.ready.title'),
      description: t('steps.ready.description'),
      icon: <CheckCircle2 className="text-emerald-500 h-12 w-12" />,
      cta: t('steps.ready.cta'),
      testid: 'wizard-enter'
    }
  ];

  const handleNext = async () => {
    if (currentStep === 1) {
      if (!selectedPlatform) return;
      setIsSyncing(true);
      await onSync(selectedPlatform);
      setIsSyncing(false);
      setCurrentStep(currentStep + 1);
    } else if (currentStep === STEPS.length - 1) {
      localStorage.setItem('michi_onboarded', 'true');
      onComplete();
    } else {
      setCurrentStep(currentStep + 1);
    }
  };

  const step = STEPS[currentStep];

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Immersive backdrop */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-slate-950/40 backdrop-blur-xl" 
      />
      
      <motion.div 
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="relative bg-white/90 backdrop-blur-3xl rounded-lg shadow-[0_32px_64px_-16px_rgba(0,0,0,0.2)] border border-white max-w-md w-full overflow-hidden flex flex-col"
      >
        {/* Progress header */}
        <div className="px-6 pt-6 pb-2 flex items-center justify-between">
            <div className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-sm bg-slate-900 flex items-center justify-center text-white font-bold text-xs ring-4 ring-slate-900/5">道</div>
                <span className="text-[11px] font-bold tracking-tight text-slate-400">Assistant Michi</span>
            </div>
            <div className="flex gap-2">
                {STEPS.map((_, i) => (
                    <div key={i} className={cn(
                        "h-1 rounded-full transition-all duration-700",
                        i === currentStep ? "w-6 bg-primary shadow-[0_0_10px_rgba(var(--primary-rgb),0.3)]" : "w-1.5 bg-slate-200"
                    )} />
                ))}
            </div>
        </div>

        <div className="px-8 pb-8 flex-1">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.05 }}
              transition={{ duration: 0.4, ease: "circOut" }}
              className="space-y-6 flex flex-col items-center text-center"
            >
               <div className="relative group/icon">
                  <div className="absolute inset-0 bg-primary/20 blur-2xl rounded-full scale-110 group-hover/icon:scale-125 transition-transform duration-700" />
                  <div className={cn(
                    "relative p-4 rounded-lg transition-all mb-1",
                    currentStep === 0 ? "bg-transparent border-transparent" : "bg-white/80 backdrop-blur-sm border border-white shadow-sm"
                  )}>
                     {step.icon}
                  </div>
               </div>
               
               <div className="space-y-2">
                 <h2 className="text-2xl font-bold text-slate-900 tracking-tight leading-tight">
                     {step.title}
                 </h2>
                 <p className="text-slate-500 text-sm leading-relaxed max-w-[280px] mx-auto font-medium opacity-80">{step.description}</p>
               </div>

              {currentStep === 1 && (
                 <div className="grid grid-cols-3 gap-3 w-full pt-2">
                    {[
                        { id: 'shopify', label: 'Shopify', icon: <ShoppingBag className="h-5 w-5" /> },
                        { id: 'amazon', label: 'Amazon', icon: <Globe className="h-5 w-5" /> },
                        { id: 'csv', label: 'CSV/Excel', icon: <FileSpreadsheet className="h-5 w-5" /> },
                    ].map((plat) => (
                        <button
                            key={plat.id}
                            data-testid={`wizard-platform-${plat.id}`}
                            onClick={() => setSelectedPlatform(plat.id)}
                            className={cn(
                                "flex flex-col items-center justify-center p-3 rounded-lg border-2 transition-all gap-2 group/item hover:scale-[1.02] active:scale-[0.98]",
                                selectedPlatform === plat.id 
                                    ? "bg-white border-primary text-primary shadow-xl shadow-primary/10" 
                                    : "bg-slate-50/50 border-transparent text-slate-400 hover:bg-white hover:border-slate-100"
                            )}
                        >
                            <div className={cn(
                                "p-2 rounded-lg transition-all",
                                selectedPlatform === plat.id ? "bg-primary text-white scale-110 shadow-lg shadow-primary/20" : "bg-white text-slate-400 group-hover/item:text-slate-600 shadow-sm"
                            )}>{plat.icon}</div>
                            <span className="text-[10px] font-bold tracking-tight">{plat.label}</span>
                        </button>
                    ))}
                 </div>
              )}

              <div className="w-full pt-6">
                <button
                  onClick={handleNext}
                  data-testid={step.testid}
                  disabled={isSyncing || (currentStep === 1 && !selectedPlatform)}
                  className={cn(
                    "w-full flex items-center justify-center gap-3 py-4 rounded-lg text-[13px] font-bold tracking-tight transition-all",
                    isSyncing || (currentStep === 1 && !selectedPlatform)
                      ? "bg-slate-100 text-slate-300 cursor-not-allowed" 
                      : "bg-slate-900 text-white hover:bg-slate-800 hover:shadow-xl hover:shadow-slate-900/20 active:scale-[0.98]"
                  )}
                >
                  {isSyncing ? (
                    <>
                      <div className="animate-spin h-4 w-4 border-2 border-slate-400 border-t-white rounded-full" />
                      {t('syncing')}
                    </>
                  ) : (
                    <>
                      <span>{step.cta}</span>
                      <ArrowRight size={16} />
                    </>
                  )}
                </button>
                
                {currentStep === 0 && (
                  <button 
                    onClick={() => {
                      localStorage.setItem('michi_onboarded', 'true');
                      onComplete();
                    }}
                    className="mt-4 text-[11px] font-bold text-slate-400 hover:text-primary tracking-tight transition-colors"
                  >
                    {t('skip')}
                  </button>
                )}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}
