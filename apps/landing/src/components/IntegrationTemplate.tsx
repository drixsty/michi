'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslations } from 'next-intl';
import {
  ArrowRight,
  Check,
  ChevronDown,
  Zap,
  BarChart3,
  Link,
  ShoppingCart,
  Globe,
  Boxes
} from 'lucide-react';

const IconMap: Record<string, any> = { ShoppingCart, Globe, Boxes, Zap, BarChart3, Link };

interface IntegrationTemplateProps {
  namespace: string;
  iconName: string;
  platformName: string;
}

const FAQItem = ({ question, answer }: { question: string; answer: string }) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="border-b border-border last:border-0">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full py-4 flex items-center justify-between text-left gap-4"
      >
        <span className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">{question}</span>
        <ChevronDown className={`w-4 h-4 text-muted-foreground shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <p className="pb-4 text-sm text-muted-foreground leading-relaxed">{answer}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export const IntegrationTemplate = ({ namespace, iconName, platformName }: IntegrationTemplateProps) => {
  const t = useTranslations(namespace as any);
  const tIndex = useTranslations('Index');
  const tNavbar = useTranslations('Navbar');
  const Icon = IconMap[iconName] || Link;

  return (
    <div className="overflow-x-hidden">

      {/* Hero */}
      <section className="max-w-5xl mx-auto pt-28 pb-14 px-4 sm:px-6">
        <div className="flex flex-col lg:flex-row gap-12 items-start">

          {/* Left */}
          <motion.div
            className="flex-1"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground mb-5 font-medium uppercase tracking-wider">
              <Icon className="w-3.5 h-3.5" />
              <span>{tNavbar('integrationsSlash')} {platformName}</span>
            </div>
            <h1 className="text-[1.9rem] md:text-[2.4rem] font-bold mb-3 tracking-tight leading-[1.2] text-foreground">
              {t.rich('hero.title', {
                spanInner: (chunks) => <span className="text-gradient-purple">{chunks}</span>,
                br: () => <br className="hidden md:block" />
              }) as any}
            </h1>
            <p className="text-muted-foreground text-[0.9rem] mb-7 leading-relaxed max-w-md">
              {t('hero.subtitle')}
            </p>
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
              <button className="bg-primary hover:bg-primary/90 text-white px-6 min-h-[44px] rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-all active:scale-[0.98]">
                {tIndex('getStarted')} <ArrowRight className="w-3.5 h-3.5 shrink-0" />
              </button>
              <button className="border border-border text-foreground px-6 min-h-[44px] rounded-lg text-sm font-semibold hover:bg-secondary transition-all flex items-center justify-center">
                {tIndex('bookDemo')}
              </button>
            </div>
          </motion.div>

          {/* Right — feature list */}
          <motion.div
            className="w-full lg:w-72 shrink-0"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <div className="border border-border rounded-lg overflow-hidden">
              <div className="px-5 py-3 border-b border-border bg-secondary/40">
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  {t('features.title')}
                </p>
              </div>
              <ul className="p-5 space-y-3">
                {Object.keys(t.raw('features.items') as object).map((key) => (
                  <li key={key} className="flex items-start gap-2.5">
                    <Check className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0" />
                    <span className="text-sm text-foreground leading-snug">{t(`features.items.${key}` as any)}</span>
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>

        </div>
      </section>

      {/* How it works */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 pb-14 border-t border-border pt-12">
        <h2 className="text-base font-semibold text-foreground mb-8">{t('workflow.title')}</h2>
        <div className="grid md:grid-cols-3 gap-5">
          {(['step1', 'step2', 'step3'] as const).map((step, idx) => (
            <div key={step} className="relative p-5 rounded-lg border border-border bg-card">
              <div className="text-[10px] font-bold text-primary mb-2 tracking-widest uppercase">
                {String(idx + 1).padStart(2, '0')}
              </div>
              <h3 className="text-sm font-semibold text-foreground mb-1.5">
                {t(`workflow.${step}.title` as any)}
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {t(`workflow.${step}.desc` as any)}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 pb-20 border-t border-border pt-12">
        <h2 className="text-base font-semibold text-foreground mb-5">{t('faq.title')}</h2>
        <div>
          <FAQItem question={t('faq.q1')} answer={t('faq.a1')} />
          <FAQItem question={t('faq.q2')} answer={t('faq.a2')} />
          <FAQItem question={t('faq.q3')} answer={t('faq.a3')} />
        </div>
      </section>

    </div>
  );
};

