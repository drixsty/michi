'use client';

import React from 'react';
import { useTranslations } from 'next-intl';
import { X, Linkedin, Play } from 'lucide-react';

export const Footer = () => {
  const t = useTranslations('Footer');

  return (
    <footer className="max-w-5xl mx-auto mt-14 pt-12 border-t border-border pb-8 px-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-10 mb-12">

        {/* Brand */}
        <div className="col-span-2 md:col-span-1">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-7 h-7 bg-primary rounded-lg flex items-center justify-center font-bold text-white text-xs">道</div>
            <span className="text-sm font-bold text-foreground tracking-tight">{t('brandName')}</span>
          </div>
          <p className="text-muted-foreground text-xs leading-relaxed mb-5">
            {t('description')}
          </p>
          <div className="flex gap-3">
            <a href="#" aria-label="X (Twitter)" className="w-8 h-8 rounded-lg bg-secondary border border-border flex items-center justify-center text-muted-foreground hover:text-primary transition-colors">
              <X className="w-3.5 h-3.5" />
            </a>
            <a href="#" aria-label="LinkedIn" className="w-8 h-8 rounded-lg bg-secondary border border-border flex items-center justify-center text-muted-foreground hover:text-primary transition-colors">
              <Linkedin className="w-3.5 h-3.5" />
            </a>
            <a href="#" aria-label="YouTube" className="w-8 h-8 rounded-lg bg-secondary border border-border flex items-center justify-center text-muted-foreground hover:text-primary transition-colors">
              <Play className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* Product */}
        <div>
          <h4 className="font-semibold text-foreground mb-4 text-[10px] uppercase tracking-widest">{t('product')}</h4>
          <ul className="space-y-3 text-xs text-muted-foreground">
            <li><a href="/features/forecasting" className="hover:text-primary transition-colors">{t('links.forecasting')}</a></li>
            <li><a href="/features/replenishment" className="hover:text-primary transition-colors">{t('links.replenishment')}</a></li>
            <li><a href="/features/unified-inventory" className="hover:text-primary transition-colors">{t('links.unifiedInventory')}</a></li>
            <li><a href="/pricing" className="hover:text-primary transition-colors">{t('links.pricing')}</a></li>
          </ul>
        </div>

        {/* Integrations */}
        <div>
          <h4 className="font-semibold text-foreground mb-4 text-[10px] uppercase tracking-widest">{t('solutions')}</h4>
          <ul className="space-y-3 text-xs text-muted-foreground">
            <li><a href="/integrations/shopify" className="hover:text-primary transition-colors">{t('links.shopify')}</a></li>
            <li><a href="/integrations/amazon" className="hover:text-primary transition-colors">{t('links.amazon')}</a></li>
            <li><a href="/integrations/woocommerce" className="hover:text-primary transition-colors">{t('links.woo')}</a></li>
          </ul>
        </div>

        {/* Company */}
        <div>
          <h4 className="font-semibold text-foreground mb-4 text-[10px] uppercase tracking-widest">{t('company')}</h4>
          <ul className="space-y-3 text-xs text-muted-foreground">
            <li><a href="/about" className="hover:text-primary transition-colors">{t('links.about')}</a></li>
            <li><a href="/blog" className="hover:text-primary transition-colors">{t('links.blog')}</a></li>
            <li><a href="/legal" className="hover:text-primary transition-colors">{t('legal')}</a></li>
            <li><a href="#" className="hover:text-primary transition-colors">{t('links.careers')}</a></li>
          </ul>
        </div>

      </div>

      <div className="flex flex-col md:flex-row justify-between items-center pt-6 border-t border-border gap-4">
        <div className="text-muted-foreground text-xs">{t('copyright')}</div>
        <div className="flex gap-6 text-xs text-muted-foreground">
          <a href="/privacy" className="hover:text-primary transition-colors">{t('links.privacy')}</a>
          <a href="/terms" className="hover:text-primary transition-colors">{t('links.terms')}</a>
        </div>
      </div>
    </footer>
  );
};
