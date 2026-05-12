'use client';

import React, { useState, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './ui/Button';
import { ShieldCheck, X, Check } from 'lucide-react';

interface CookiePreferences {
  necessary: boolean;
  analytics: boolean;
  marketing: boolean;
  timestamp?: string;
}

export const CookieConsent = () => {
  const t = useTranslations('Legal.cookies');
  const locale = useLocale();
  const [isVisible, setIsVisible] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const [preferences, setPreferences] = useState<CookiePreferences>({
    necessary: true,
    analytics: false,
    marketing: false
  });

  useEffect(() => {
    try {
      const consentStr = localStorage.getItem('michi_cookie_consent');
      if (!consentStr) {
        const timer = setTimeout(() => setIsVisible(true), 2000);
        return () => clearTimeout(timer);
      } else {
        const parsed = JSON.parse(consentStr);
        setPreferences({
          necessary: true,
          analytics: !!parsed.analytics,
          marketing: !!parsed.marketing
        });
      }
    } catch (e) {
      // If it was the old string like "accepted" or invalid JSON
      localStorage.removeItem('michi_cookie_consent');
      setIsVisible(true);
    }
  }, []);

  const savePreferences = (prefs: CookiePreferences) => {
    localStorage.setItem('michi_cookie_consent', JSON.stringify({
      ...prefs,
      timestamp: new Date().toISOString()
    }));
    setPreferences(prefs);
    setIsVisible(false);
    setIsModalOpen(false);
    
    // Potentially trigger a custom event so other components/scripts know consent changed
    window.dispatchEvent(new Event('cookie_consent_updated'));
  };

  const handleAcceptAll = () => {
    savePreferences({ necessary: true, analytics: true, marketing: true });
  };

  const handleDeclineAll = () => {
    savePreferences({ necessary: true, analytics: false, marketing: false });
  };

  const handleSavePreferences = () => {
    savePreferences(preferences);
  };

  const togglePreference = (key: keyof CookiePreferences) => {
    if (key === 'necessary') return;
    setPreferences(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <>
      {/* Floating Banner */}
      <AnimatePresence>
        {isVisible && !isModalOpen && (
          <motion.div
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 100, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed bottom-4 sm:bottom-6 left-4 sm:left-6 right-4 sm:right-6 z-[100] flex justify-center pointer-events-none"
          >
            <div className="max-w-3xl w-full bg-card text-card-foreground border border-border rounded-[24px] shadow-[0_8px_30px_rgb(0,0,0,0.12)] p-5 sm:p-6 relative overflow-hidden pointer-events-auto flex flex-col gap-4">
              
              <div className="flex flex-col sm:flex-row gap-4 sm:gap-8 items-start sm:items-center">
                
                <div className="flex-grow">
                  <h3 className="font-bold text-lg mb-1.5">{t('title')}</h3>
                  <p className="text-muted-foreground text-xs sm:text-sm leading-relaxed max-w-lg">
                    {t('description')}
                  </p>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-2.5 w-full sm:w-auto shrink-0">
                  <button 
                    onClick={() => setIsModalOpen(true)}
                    className="w-full sm:w-auto px-4 py-2.5 rounded-lg text-sm font-semibold border border-border bg-transparent text-foreground hover:bg-muted transition-colors shadow-sm"
                  >
                    {t('manage')}
                  </button>
                  <button 
                    onClick={handleAcceptAll}
                    className="w-full sm:w-auto px-4 py-2.5 rounded-lg text-sm font-semibold bg-primary text-primary-foreground hover:opacity-90 transition-opacity shadow-sm"
                  >
                    {t('acceptAll')}
                  </button>
                </div>
              </div>

              <div className="flex justify-between items-center text-[11px] sm:text-xs text-muted-foreground pt-1">
                <ShieldCheck className="w-3.5 h-3.5 opacity-50" />
                <a href={`/${locale}/privacy`} className="hover:text-foreground transition-colors underline underline-offset-2 decoration-border">
                  {t('privacyLink')}
                </a>
                <div className="w-3.5 h-3.5" /> {/* Placeholder to balance layout */}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Preferences Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-background/80 backdrop-blur-sm"
              onClick={() => setIsModalOpen(false)}
            />
            
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="w-full max-w-2xl bg-card border border-border rounded-2xl shadow-2xl overflow-hidden relative z-10 flex flex-col max-h-[90vh]"
            >
              <div className="p-6 border-b border-border flex justify-between items-center bg-muted/30">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <ShieldCheck className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-foreground">{t('modalTitle')}</h2>
                    <p className="text-xs text-muted-foreground mt-0.5 max-w-lg">{t('modalDesc')}</p>
                  </div>
                </div>
                <button 
                  onClick={() => setIsModalOpen(false)}
                  className="text-muted-foreground hover:text-foreground transition-colors self-start mt-1"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-6 overflow-y-auto flex-grow space-y-6">
                {/* Necessary Cookies */}
                <div className="flex gap-4">
                  <div className="flex-grow">
                    <h4 className="text-sm font-bold text-foreground mb-1">{t('categories.necessary.title')}</h4>
                    <p className="text-xs text-muted-foreground leading-relaxed">{t('categories.necessary.desc')}</p>
                  </div>
                  <div className="shrink-0 flex items-center">
                    <span className="text-xs font-semibold text-primary/70 mr-3 hidden sm:block">{t('categories.necessary.alwaysActive')}</span>
                    <div className="w-11 h-6 rounded-full bg-primary/50 relative flex items-center px-1 opacity-50 cursor-not-allowed">
                      <div className="w-4 h-4 rounded-full bg-white absolute right-1"></div>
                    </div>
                  </div>
                </div>

                <div className="h-px w-full bg-border" />

                {/* Analytics Cookies */}
                <div className="flex gap-4">
                  <div className="flex-grow">
                    <h4 className="text-sm font-bold text-foreground mb-1">{t('categories.analytics.title')}</h4>
                    <p className="text-xs text-muted-foreground leading-relaxed">{t('categories.analytics.desc')}</p>
                  </div>
                  <div className="shrink-0 flex items-center">
                    <button 
                      onClick={() => togglePreference('analytics')}
                      className={`w-11 h-6 rounded-full relative flex items-center px-1 transition-colors duration-300 ${preferences.analytics ? 'bg-primary' : 'bg-muted-foreground/30'}`}
                    >
                      <motion.div 
                        layout
                        initial={false}
                        animate={{ x: preferences.analytics ? 20 : 0 }}
                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        className="w-4 h-4 rounded-full bg-white shadow-sm flex items-center justify-center"
                      >
                        {preferences.analytics && <Check className="w-2.5 h-2.5 text-primary" />}
                      </motion.div>
                    </button>
                  </div>
                </div>

                <div className="h-px w-full bg-border" />

                {/* Marketing Cookies */}
                <div className="flex gap-4">
                  <div className="flex-grow">
                    <h4 className="text-sm font-bold text-foreground mb-1">{t('categories.marketing.title')}</h4>
                    <p className="text-xs text-muted-foreground leading-relaxed">{t('categories.marketing.desc')}</p>
                  </div>
                  <div className="shrink-0 flex items-center">
                    <button 
                      onClick={() => togglePreference('marketing')}
                      className={`w-11 h-6 rounded-full relative flex items-center px-1 transition-colors duration-300 ${preferences.marketing ? 'bg-primary' : 'bg-muted-foreground/30'}`}
                    >
                      <motion.div 
                        layout
                        initial={false}
                        animate={{ x: preferences.marketing ? 20 : 0 }}
                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        className="w-4 h-4 rounded-full bg-white shadow-sm flex items-center justify-center"
                      >
                        {preferences.marketing && <Check className="w-2.5 h-2.5 text-primary" />}
                      </motion.div>
                    </button>
                  </div>
                </div>

              </div>

              <div className="p-6 border-t border-border flex flex-col sm:flex-row justify-end gap-3 bg-muted/10">
                <button 
                  onClick={handleDeclineAll}
                  className="w-full sm:w-auto px-6 py-2.5 rounded-lg text-sm font-semibold border border-border bg-transparent text-foreground hover:bg-muted transition-colors shadow-sm"
                >
                  {t('declineAll')}
                </button>
                <button 
                  onClick={handleSavePreferences}
                  className="w-full sm:w-auto px-6 py-2.5 rounded-lg text-sm font-semibold bg-primary text-primary-foreground hover:opacity-90 transition-opacity shadow-sm"
                >
                  {t('savePreferences')}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
};

