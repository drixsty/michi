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
  const t = useTranslations('Onboarding');
  const [currentStep, setCurrentStep] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);

  const STEPS = [
    {
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
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 backdrop-blur-md p-4">
      <motion.div 
        initial={{ opacity: 0, scale: 0.9, y: 30 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="bg-white rounded-[40px] shadow-2xl border border-slate-100 max-w-xl w-full overflow-hidden flex flex-col"
      >
        {/* Progress header */}
        <div className="px-10 pt-10 pb-6 flex items-center justify-between">
            <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-sm">道</div>
                <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">Onboarding</span>
            </div>
            <div className="flex gap-1.5">
                {STEPS.map((_, i) => (
                    <div key={i} className={cn(
                        "h-1 rounded-full transition-all duration-500",
                        i === currentStep ? "w-8 bg-primary" : "w-1.5 bg-slate-100"
                    )} />
                ))}
            </div>
        </div>

        <div className="px-10 pb-10 flex-1">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.05 }}
              transition={{ duration: 0.4, ease: "circOut" }}
              className="space-y-8 flex flex-col items-center text-center"
            >
              <div className="relative">
                 <div className="absolute inset-0 bg-primary/5 blur-3xl rounded-full scale-150" />
                 <div className="relative p-6 bg-slate-50/50 rounded-[30px] border border-slate-100 mb-2">
                    {step.icon}
                 </div>
              </div>
              
              <div className="space-y-3">
                <h2 className="text-3xl font-bold text-slate-900 tracking-tight">
                    {currentStep === 0 && userName ? t('welcome', { name: userName }) : step.title}
                </h2>
                <p className="text-slate-500 text-sm leading-relaxed max-w-xs mx-auto">{step.description}</p>
              </div>

              {currentStep === 1 && (
                 <div className="grid grid-cols-3 gap-4 w-full pt-2">
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
                                "flex flex-col items-center justify-center p-5 rounded-3xl border-2 transition-all gap-3 group hover:scale-[1.02] active:scale-[0.98]",
                                selectedPlatform === plat.id 
                                    ? "bg-primary/5 border-primary text-primary shadow-xl shadow-primary/10" 
                                    : "bg-white border-slate-50 text-slate-400 hover:border-slate-200"
                            )}
                        >
                            <div className={cn(
                                "p-2.5 rounded-xl transition-colors",
                                selectedPlatform === plat.id ? "bg-primary text-white" : "bg-slate-50 group-hover:bg-slate-100"
                            )}>{plat.icon}</div>
                            <span className="text-[10px] font-bold tracking-widest uppercase">{plat.label}</span>
                        </button>
                    ))}
                 </div>
              )}

              <div className="w-full pt-8">
                <button
                  onClick={handleNext}
                  data-testid={step.testid}
                  disabled={isSyncing || (currentStep === 1 && !selectedPlatform)}
                  className={cn(
                    "w-full flex items-center justify-center gap-3 py-4 rounded-[20px] text-sm font-bold tracking-widest uppercase transition-all shadow-2xl",
                    isSyncing || (currentStep === 1 && !selectedPlatform)
                      ? "bg-slate-100 text-slate-300 cursor-not-allowed shadow-none" 
                      : "bg-slate-900 text-white hover:bg-slate-800 hover:shadow-slate-900/20 active:scale-[0.98]"
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
                    className="mt-6 text-[10px] font-bold text-slate-400 hover:text-primary tracking-[0.2em] uppercase transition-colors"
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
