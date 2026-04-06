'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, BarChart2, CheckCircle2, ArrowRight, Layers, Zap } from 'lucide-react';

interface OnboardingWizardProps {
  onComplete: () => void;
  onSync: () => Promise<void>;
}

const STEPS = [
  {
    id: 'welcome',
    title: 'Bienvenue sur Michi 道',
    description: 'Transformons vos données e-commerce en décisions logistiques intelligentes.',
    icon: <Sparkles className="text-purple-500 h-8 w-8" />,
    cta: 'Commencer',
  },
  {
    id: 'sync',
    title: 'Synchronisation Intelligente',
    description: 'Nous allons importer vos produits et l\'historique de vos ventes pour nourrir notre IA.',
    icon: <Zap className="text-amber-500 h-8 w-8" />,
    cta: 'Lancer la Synchronisation',
  },
  {
    id: 'analysis',
    title: 'Analyse IA en cours',
    description: 'Michi nettoie vos données (ruptures, outliers) et calcule votre Run Rate et vos dates de rupture.',
    icon: <BarChart2 className="text-blue-500 h-8 w-8" />,
    cta: 'Voir mes Prévisions',
  },
  {
    id: 'discovery',
    title: 'Vous êtes prêt !',
    description: 'Découvrez vos besoins de réapprovisionnement et gérez vos stocks multi-canaux avec précision.',
    icon: <CheckCircle2 className="text-emerald-500 h-8 w-8" />,
    cta: 'Accéder au Dashboard',
  }
];

export default function OnboardingWizard({ onComplete, onSync }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);

  const handleNext = async () => {
    if (currentStep === 1) {
      setIsSyncing(true);
      await onSync();
      setIsSyncing(false);
      setCurrentStep(currentStep + 1);
    } else if (currentStep === STEPS.length - 1) {
      onComplete();
      localStorage.setItem('michi_onboarded', 'true');
    } else {
      setCurrentStep(currentStep + 1);
    }
  };

  const step = STEPS[currentStep];

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-gray-900/40 backdrop-blur-sm p-4">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="bg-white rounded-[32px] shadow-2xl border border-gray-100 max-w-lg w-full overflow-hidden"
      >
        {/* Progress Bar */}
        <div className="h-1.5 w-full bg-gray-100 flex">
          {STEPS.map((_, i) => (
            <div 
              key={i} 
              className={`h-full flex-1 transition-all duration-500 ${i <= currentStep ? 'bg-gradient-to-r from-purple-600 to-indigo-600' : ''}`}
            />
          ))}
        </div>

        <div className="p-10 text-center">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div className="inline-flex items-center justify-center p-4 bg-gray-50 rounded-2xl">
                {step.icon}
              </div>
              
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">{step.title}</h2>
                <p className="text-gray-500 text-sm leading-relaxed px-4">{step.description}</p>
              </div>

              <div className="pt-6">
                <button
                  onClick={handleNext}
                  disabled={isSyncing}
                  className={`
                    w-full flex items-center justify-center gap-2 py-4 rounded-2xl text-sm font-bold transition-all shadow-lg
                    ${isSyncing 
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                      : 'bg-gray-900 text-white hover:bg-black hover:shadow-xl active:scale-95'}
                  `}
                >
                  {isSyncing ? (
                    <>
                      <div className="animate-spin h-4 w-4 border-2 border-gray-300 border-t-white rounded-full" />
                      Analyse en cours...
                    </>
                  ) : (
                    <>
                      {step.cta}
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
                    className="mt-4 text-xs text-gray-400 hover:text-gray-600 underline font-medium"
                  >
                    Passer (expert)
                  </button>
                )}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
        
        {/* Footer info */}
        <div className="bg-gray-50 px-10 py-4 flex items-center justify-center gap-6">
          <div className="flex items-center gap-1.5 opacity-40">
            <Layers size={12} />
            <span className="text-[10px] font-bold uppercase tracking-widest">Omnicanal</span>
          </div>
          <div className="flex items-center gap-1.5 opacity-40">
            <Zap size={12} />
            <span className="text-[10px] font-bold uppercase tracking-widest">Temps Réel</span>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
