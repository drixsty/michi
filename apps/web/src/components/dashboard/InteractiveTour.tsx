'use client';

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronLeft, X, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/navigation';

interface TourStep {
  target: string;
  tab?: string; 
  titleKey: string;
  descKey: string;
  position: 'top' | 'bottom' | 'left' | 'right';
}

export function InteractiveTour() {
  const t = useTranslations('tour');
  const router = useRouter();
  const [active, setActive] = useState(false);
  const [step, setStep] = useState(0);
  const [coords, setCoords] = useState({ top: 0, left: 0, width: 0, height: 0 });
  const requestRef = useRef<number>();
  
  // Keep track of the last valid tooltip position to prevent jumps to center
  const lastTooltipPos = useRef({ top: 200, left: 200 });

  const TOUR_STEPS: TourStep[] = useMemo(() => [
    {
      target: '#sidebar-logo',
      titleKey: 'steps.welcome.title',
      descKey: 'steps.welcome.desc',
      position: 'right'
    },
    {
      target: '#nav-integrations',
      titleKey: 'steps.connect.title',
      descKey: 'steps.connect.desc',
      position: 'left'
    },
    {
      target: '#nav-inventory',
      titleKey: 'steps.inventory.title',
      descKey: 'steps.inventory.desc',
      position: 'bottom'
    },
    {
      target: '#inventory-sync-btn',
      tab: 'inventory',
      titleKey: 'steps.sync.title',
      descKey: 'steps.sync.desc',
      position: 'bottom'
    },
    {
      target: '#main-search',
      titleKey: 'steps.search.title',
      descKey: 'steps.search.desc',
      position: 'bottom'
    },
    {
      target: '#stat-health',
      tab: 'decisions',
      titleKey: 'steps.health.title',
      descKey: 'steps.health.desc',
      position: 'top'
    },
    {
      target: '#nav-notifications',
      titleKey: 'steps.notifications.title',
      descKey: 'steps.notifications.desc',
      position: 'bottom'
    },
    {
      target: '#nav-language',
      titleKey: 'steps.language.title',
      descKey: 'steps.language.desc',
      position: 'bottom'
    },
    {
      target: '#nav-decisions',
      titleKey: 'steps.decisions.title',
      descKey: 'steps.decisions.desc',
      position: 'right'
    }
  ], []);

  const updateCoords = useCallback(() => {
    const currentStep = TOUR_STEPS[step];
    const targetEl = document.querySelector(currentStep.target);

    if (targetEl) {
      const rect = targetEl.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        setCoords({
          top: rect.top,
          left: rect.left,
          width: rect.width,
          height: rect.height
        });
      }
    } else {
      // Don't reset coords to 0 here, keep them to avoid flickering
    }
    requestRef.current = requestAnimationFrame(updateCoords);
  }, [step, TOUR_STEPS]);

  useEffect(() => {
    if (!active) return;
    const currentStep = TOUR_STEPS[step];
    if (currentStep.tab) {
      router.push(`/dashboard?tab=${currentStep.tab}`);
    }
    if (currentStep.target === '#nav-integrations') {
      const menuBtn = document.querySelector('[data-testid="user-menu-button"]') as HTMLElement;
      if (menuBtn) menuBtn.click();
    }
  }, [step, active, router, TOUR_STEPS]);

  useEffect(() => {
    const completed = localStorage.getItem('michi_tour_completed');
    if (!completed) {
      const timer = setTimeout(() => setActive(true), 3000);
      return () => clearTimeout(timer);
    }
  }, []);

  useEffect(() => {
    if (active) {
      requestRef.current = requestAnimationFrame(updateCoords);
      return () => {
        if (requestRef.current) cancelAnimationFrame(requestRef.current);
      };
    }
  }, [active, updateCoords]);

  useEffect(() => {
    if (active && coords.width > 0) {
      const targetEl = document.querySelector(TOUR_STEPS[step].target);
      if (targetEl) {
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [step, active, TOUR_STEPS, coords.width]);

  const handleNext = () => {
    const targetId = TOUR_STEPS[step].target;
    if (targetId === '#nav-integrations') {
      const overlay = document.querySelector('.fixed.inset-0.z-0') as HTMLElement;
      if (overlay) overlay.click();
    }
    if (step < TOUR_STEPS.length - 1) {
      setStep(s => s + 1);
    } else {
      handleClose();
    }
  };

  const handleClose = () => {
    setActive(false);
    localStorage.setItem('michi_tour_completed', 'true');
    const overlay = document.querySelector('.fixed.inset-0.z-0') as HTMLElement;
    if (overlay) overlay.click();
  };

  if (!active) return null;

  const current = TOUR_STEPS[step];

  const getTooltipStyle = () => {
    const offset = 16;
    let top = 0;
    let left = 0;

    // Use current coords if valid, otherwise use last known position
    const targetCoords = coords.width > 0 ? coords : { ...coords, ...lastTooltipPos.current, width: 288, height: 160 };

    switch (current.position) {
      case 'bottom':
        top = targetCoords.top + targetCoords.height + offset;
        left = targetCoords.left + (targetCoords.width / 2) - 144;
        break;
      case 'top':
        top = targetCoords.top - 240 - offset; // Adjusted for full-width button height
        left = targetCoords.left + (targetCoords.width / 2) - 144;
        break;
      case 'right':
        top = targetCoords.top + (targetCoords.height / 2) - 100;
        left = targetCoords.left + targetCoords.width + offset;
        break;
      case 'left':
        top = targetCoords.top + (targetCoords.height / 2) - 100;
        left = targetCoords.left - 288 - offset;
        break;
    }

    const finalPos = {
      top: Math.max(12, Math.min(window.innerHeight - 280, top)),
      left: Math.max(12, Math.min(window.innerWidth - 300, left))
    };

    // Update last known position ONLY if we have a valid target
    if (coords.width > 0) {
      lastTooltipPos.current = finalPos;
    }

    return finalPos;
  };

  const tooltipStyle = getTooltipStyle();

  return (
    <div className="fixed inset-0 z-[100] pointer-events-none overflow-hidden">
      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        <defs>
          <mask id="tour-mask-v9">
            <rect x="0" y="0" width="100%" height="100%" fill="white" />
            {coords.width > 0 && (
              <motion.rect 
                animate={{
                  x: coords.left - 6,
                  y: coords.top - 6,
                  width: coords.width + 12,
                  height: coords.height + 12,
                }}
                transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                rx="10"
                fill="black" 
              />
            )}
          </mask>
        </defs>
        <rect x="0" y="0" width="100%" height="100%" fill="rgba(15, 23, 42, 0.45)" mask="url(#tour-mask-v9)" />
      </svg>

      {coords.width > 0 && (
        <motion.div 
          animate={{
            top: coords.top - 6,
            left: coords.left - 6,
            width: coords.width + 12,
            height: coords.height + 12,
          }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="absolute border-2 border-white rounded-xl z-[101] pointer-events-none shadow-[0_0_25px_rgba(255,255,255,0.4)]"
        >
          <div className="absolute inset-0 rounded-xl border border-white/30 animate-pulse" />
        </motion.div>
      )}

      <motion.div
        animate={{ 
          top: tooltipStyle.top,
          left: tooltipStyle.left,
        }}
        transition={{ type: 'spring', damping: 28, stiffness: 150 }}
        className="absolute pointer-events-auto w-72 bg-white rounded-xl shadow-[0_30px_60px_-12px_rgba(15,23,42,0.25)] p-6 border border-slate-100 z-[110]"
      >
        <div className="flex gap-1.5 mb-5">
          {TOUR_STEPS.map((_, i) => (
            <div 
              key={i} 
              className={cn(
                "h-1 rounded-full transition-all duration-300",
                i === step ? "w-6 bg-slate-900" : "w-1.5 bg-slate-100"
              )} 
            />
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            transition={{ duration: 0.2 }}
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="text-[13px] font-bold text-slate-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-500" />
                {t(current.titleKey)}
              </h3>
              <button onClick={handleClose} className="text-slate-300 hover:text-slate-900 transition-colors p-1">
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed mb-8">
              {t(current.descKey)}
            </p>
          </motion.div>
        </AnimatePresence>

        <div className="flex items-center">
          <button 
            onClick={handleNext}
            className="flex w-full items-center justify-center gap-2 bg-slate-900 text-white px-5 py-3 rounded-xl text-xs font-bold hover:bg-slate-800 transition-all active:scale-[0.98] shadow-lg shadow-slate-900/10"
          >
            {step === TOUR_STEPS.length - 1 ? t('finish') : t('next')}
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </motion.div>
    </div>
  );
}
