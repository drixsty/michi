'use client';

import React, { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Cookie, X, ShieldCheck, Settings, ChevronRight, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CookieSettings {
  essential: boolean;
  analytics: boolean;
  marketing: boolean;
}

export function CookieBanner() {
  const t = useTranslations('legal');
  const [isVisible, setIsVisible] = useState(false);
  const [showCustomize, setShowCustomize] = useState(false);
  const [settings, setSettings] = useState<CookieSettings>({
    essential: true,
    analytics: true,
    marketing: false,
  });

  useEffect(() => {
    const consent = localStorage.getItem('michi_cookie_consent');
    if (!consent) {
      const timer = setTimeout(() => setIsVisible(true), 2000);
      return () => clearTimeout(timer);
    }
  }, []);

  useEffect(() => {
    const handleOpenSettings = () => {
      setIsVisible(true);
      setShowCustomize(true);
    };

    window.addEventListener('michi_open_cookie_settings', handleOpenSettings);
    return () => window.removeEventListener('michi_open_cookie_settings', handleOpenSettings);
  }, []);

  const handleAcceptAll = () => {
    const allSettings = { essential: true, analytics: true, marketing: true };
    localStorage.setItem('michi_cookie_consent', JSON.stringify(allSettings));
    setIsVisible(false);
  };

  const handleSaveSettings = () => {
    localStorage.setItem('michi_cookie_consent', JSON.stringify(settings));
    setIsVisible(false);
    setShowCustomize(false);
  };

  const toggleSetting = (key: keyof CookieSettings) => {
    if (key === 'essential') return; // Toujours requis
    setSettings(prev => ({ ...prev, [key]: !prev[key] }));
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-6 left-6 right-6 md:left-auto md:right-8 md:w-[420px] z-[100] animate-in slide-in-from-bottom-8 duration-700 ease-out">
      <div className="bg-white/95 backdrop-blur-md border border-slate-200 rounded-lg shadow-[0_20px_50px_rgba(0,0,0,0.12)] p-6 overflow-hidden relative group">
        
        {!showCustomize ? (
          /* MAIN VIEW */
          <div className="animate-in fade-in zoom-in-95 duration-300">
            <div className="flex items-start gap-4 relative z-10">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0 border border-primary/20">
                <Cookie className="w-6 h-6" />
              </div>
              
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <h3 className="text-[14px] font-bold text-slate-900 tracking-tight">
                    {t('cookieTitle')}
                  </h3>
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                </div>
                <p className="text-[12px] text-slate-500 leading-relaxed font-medium">
                  {t('cookieDesc')}
                </p>
              </div>
            </div>

            <div className="mt-6 flex flex-col gap-2 relative z-10">
              <button
                onClick={handleAcceptAll}
                className="w-full h-11 bg-slate-900 text-white rounded-lg text-[13px] font-bold hover:bg-slate-800 transition-all active:scale-[0.98] shadow-sm shadow-slate-200"
              >
                {t('cookieAcceptAll')}
              </button>
              
              <div className="flex gap-2">
                <button
                  onClick={() => setIsVisible(false)}
                  className="flex-1 h-10 border border-slate-200 text-slate-600 rounded-lg text-[12px] font-bold hover:bg-slate-50 transition-all active:scale-[0.98]"
                >
                  {t('cookieRejectAll')}
                </button>
                <button
                  onClick={() => setShowCustomize(true)}
                  className="flex-1 h-10 bg-slate-50 text-slate-600 rounded-lg text-[12px] font-bold hover:bg-slate-100 transition-all flex items-center justify-center gap-2"
                >
                  <Settings className="w-3.5 h-3.5" />
                  {t('cookieManage')}
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* CUSTOMIZE VIEW */
          <div className="animate-in slide-in-from-right-4 duration-400">
            <div className="flex items-center gap-3 mb-6">
              <button 
                onClick={() => setShowCustomize(false)}
                className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-4 h-4 text-slate-500" />
              </button>
              <h3 className="text-[14px] font-bold text-slate-900">Préférences des cookies</h3>
            </div>

            <div className="space-y-3">
              <CookieOption 
                title="Essentiels" 
                desc="Nécessaires au fonctionnement de l'app et à la sécurité." 
                enabled={true} 
                required={true}
              />
              <CookieOption 
                title="Analytiques" 
                desc="Nous aident à comprendre comment vous utilisez Michi." 
                enabled={settings.analytics} 
                onClick={() => toggleSetting('analytics')}
              />
              <CookieOption 
                title="Marketing" 
                desc="Utilisés pour personnaliser nos communications." 
                enabled={settings.marketing} 
                onClick={() => toggleSetting('marketing')}
              />
            </div>

            <button
              onClick={handleSaveSettings}
              className="w-full h-11 bg-slate-900 text-white rounded-lg text-[13px] font-bold mt-6 hover:bg-slate-800 transition-all active:scale-[0.98]"
            >
              Enregistrer mes choix
            </button>
          </div>
        )}

        <button 
          onClick={() => setIsVisible(false)}
          className="absolute top-4 right-4 text-slate-300 hover:text-slate-500 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function CookieOption({ title, desc, enabled, required = false, onClick }: any) {
  return (
    <div 
      onClick={onClick}
      className={cn(
        "p-3 rounded-lg border transition-all cursor-pointer flex items-center justify-between gap-4",
        enabled ? "border-primary/20 bg-primary/[0.02]" : "border-slate-100 bg-white hover:border-slate-200"
      )}
    >
      <div className="space-y-0.5">
        <div className="flex items-center gap-2">
          <span className="text-[12px] font-bold text-slate-900">{title}</span>
          {required && (
            <span className="text-[9px] font-bold text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded uppercase tracking-wider">Requis</span>
          )}
        </div>
        <p className="text-[11px] text-slate-400 leading-tight pr-4">{desc}</p>
      </div>
      
      <div className={cn(
        "w-5 h-5 rounded-full flex items-center justify-center transition-all border",
        enabled ? "bg-primary border-primary text-white" : "border-slate-200 bg-white"
      )}>
        {enabled && <Check className="w-3 h-3 stroke-[3]" />}
      </div>
    </div>
  );
}

function ArrowLeft({ className }: { className?: string }) {
  return (
    <svg 
      className={className} 
      fill="none" 
      viewBox="0 0 24 24" 
      stroke="currentColor" 
      strokeWidth={2.5}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
    </svg>
  );
}
