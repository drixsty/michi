'use client';

import { useTranslations } from 'next-intl';
import React from 'react';

export default function NotFound() {
  const t = useTranslations('NotFound');
  
  return (
    <div className="min-h-screen flex items-center justify-center text-center px-6">
      <div className="max-w-md">
        <h1 className="font-sans text-8xl font-bold mb-6 text-primary opacity-20">404</h1>
        <p className="text-foreground text-xl mb-10 font-bold tracking-tight">{t('title')}</p>
        <a 
          href="/" 
          className="inline-block bg-primary hover:bg-primary/90 text-white px-10 py-4 rounded-lg font-bold transition-all shadow-xl shadow-primary/20"
        >
          {t('button')}
        </a>
      </div>
    </div>
  );
}
