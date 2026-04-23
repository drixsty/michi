'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronLeft, X, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TourStep {
  target: string; // Sélecteur CSS ou ID
  title: string;
  description: string;
  position: 'top' | 'bottom' | 'left' | 'right';
}

const TOUR_STEPS: TourStep[] = [
  {
    target: '#sidebar-logo',
    title: 'Bienvenue sur Michi 道',
    description: 'Votre nouveau copilote intelligent pour la gestion d\'inventaire omnicanal.',
    position: 'right'
  },
  {
    target: '#add-source-btn',
    title: 'Connectez vos données',
    description: 'Cliquez ici pour lier votre première boutique Shopify, Amazon ou importer un CSV.',
    position: 'bottom'
  },
  {
    target: '#main-search',
    title: 'Recherche Intelligente',
    description: 'Accédez instantanément à n\'importe quel produit, variante ou fournisseur.',
    position: 'bottom'
  },
  {
    target: '#nav-decisions',
    title: 'Centre de Décision',
    description: 'Pilotez l\'impact financier et optimisez votre trésorerie ici.',
    position: 'right'
  }
];

export function InteractiveTour() {
  const [active, setActive] = useState(false);
  const [step, setStep] = useState(0);
  const [coords, setCoords] = useState({ top: 0, left: 0, width: 0, height: 0 });

  const updateCoords = useCallback(() => {
    const targetEl = document.querySelector(TOUR_STEPS[step].target);
    if (targetEl) {
      const rect = targetEl.getBoundingClientRect();
      setCoords({
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height
      });
      targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [step]);

  useEffect(() => {
    // Vérifier si c'est la première fois ou via un flag global
    const completed = localStorage.getItem('michi_tour_completed');
    if (!completed) {
      // Petit délai pour laisser le dashboard charger
      const timer = setTimeout(() => setActive(true), 2000);
      return () => clearTimeout(timer);
    }
  }, []);

  useEffect(() => {
    if (active) {
      updateCoords();
      window.addEventListener('resize', updateCoords);
      return () => window.removeEventListener('resize', updateCoords);
    }
  }, [active, updateCoords]);

  const handleNext = () => {
    if (step < TOUR_STEPS.length - 1) {
      setStep(s => s + 1);
    } else {
      handleClose();
    }
  };

  const handlePrev = () => {
    if (step > 0) setStep(s => s - 1);
  };

  const handleClose = () => {
    setActive(false);
    localStorage.setItem('michi_tour_completed', 'true');
  };

  if (!active) return null;

  const current = TOUR_STEPS[step];

  return (
    <div className="fixed inset-0 z-[100] pointer-events-none">
      {/* Backdrop with Spotlight */}
      <div 
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-[2px]"
        style={{
          clipPath: `polygon(
            0% 0%, 0% 100%, 
            ${coords.left}px 100%, 
            ${coords.left}px ${coords.top}px, 
            ${coords.left + coords.width}px ${coords.top}px, 
            ${coords.left + coords.width}px ${coords.top + coords.height}px, 
            ${coords.left}px ${coords.top + coords.height}px, 
            ${coords.left}px 100%, 
            100% 100%, 100% 0%
          )`
        }}
      />

      {/* Tooltip Card */}
      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ opacity: 0, scale: 0.9, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 10 }}
          className={cn(
            "absolute pointer-events-auto w-72 bg-white rounded-lg shadow-2xl p-5 border border-slate-200 z-[110]",
            current.position === 'right' && "ml-4",
            current.position === 'bottom' && "mt-4",
            current.position === 'top' && "mb-4"
          )}
          style={{
            top: Math.max(20, Math.min(window.innerHeight - 200, 
                 current.position === 'bottom' ? coords.top + coords.height + 12 : 
                 current.position === 'top' ? coords.top - 180 : 
                 coords.top + (coords.height / 2) - 80)),
            left: Math.max(20, Math.min(window.innerWidth - 300,
                  current.position === 'right' ? coords.left + coords.width + 12 : 
                  current.position === 'left' ? coords.left - 300 :
                  coords.left + (coords.width / 2) - 144))
          }}
        >
          {/* Progress dots */}
          <div className="flex gap-1 mb-3">
            {TOUR_STEPS.map((_, i) => (
              <div 
                key={i} 
                className={cn(
                  "h-1 rounded-full transition-all",
                  i === step ? "w-4 bg-indigo-600" : "w-1 bg-slate-200"
                )} 
              />
            ))}
          </div>

          <div className="flex items-start justify-between mb-2">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              {current.title}
            </h3>
            <button onClick={handleClose} className="text-slate-400 hover:text-slate-600">
              <X className="w-4 h-4" />
            </button>
          </div>

          <p className="text-xs text-slate-500 leading-relaxed mb-4">
            {current.description}
          </p>

          <div className="flex items-center justify-between">
            <button 
              onClick={handlePrev}
              disabled={step === 0}
              className="p-2 text-slate-400 hover:text-slate-600 disabled:opacity-0 transition-all"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>

            <button 
              onClick={handleNext}
              className="flex items-center gap-1 bg-slate-900 text-white px-4 py-2 rounded-lg text-xs font-bold hover:bg-slate-800 transition-all"
            >
              {step === TOUR_STEPS.length - 1 ? 'Terminer' : 'Suivant'}
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Tooltip Arrow */}
          <div 
            className={cn(
              "absolute w-3 h-3 bg-white rotate-45 border-slate-200",
              current.position === 'right' && "-left-1.5 top-1/2 -translate-y-1/2 border-l border-b",
              current.position === 'bottom' && "-top-1.5 left-1/2 -translate-x-1/2 border-l border-t",
              current.position === 'top' && "-bottom-1.5 left-1/2 -translate-x-1/2 border-r border-b"
            )}
          />
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
