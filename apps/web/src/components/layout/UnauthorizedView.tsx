'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { ShieldAlert, ArrowLeft, Home } from 'lucide-react';
import { useTranslations } from 'next-intl';

export const UnauthorizedView = () => {
  const router = useRouter();
  const t = useTranslations('common.unauthorized');

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] px-4 animate-in fade-in duration-300">
      <div className="mb-8">
        <div className="flex items-center justify-center w-20 h-20 bg-slate-50 rounded-lg border border-border">
          <ShieldAlert className="w-10 h-10 text-primary" />
        </div>
      </div>
      
      <div className="max-w-md text-center space-y-3">
        <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
          {t('title')}
        </h1>
        <p className="text-base text-muted-foreground leading-relaxed">
          {t('description')}
        </p>
      </div>

      <div className="mt-10 flex flex-col sm:flex-row items-center gap-3">
        <button
          onClick={() => router.back()}
          className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-semibold text-foreground bg-white border border-border rounded-lg hover:bg-slate-50 transition-all active:scale-[0.98]"
        >
          <ArrowLeft className="w-4 h-4" />
          {t('goBack')}
        </button>
        
        <button
          onClick={() => router.push('/dashboard')}
          className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-primary rounded-lg hover:bg-primary/95 transition-all active:scale-[0.98]"
        >
          <Home className="w-4 h-4" />
          {t('goHome')}
        </button>
      </div>
      
      <div className="mt-12 text-[10px] text-muted-foreground/50 font-bold tracking-wider">
        Error 403 • Unauthorized access
      </div>
    </div>
  );
};
