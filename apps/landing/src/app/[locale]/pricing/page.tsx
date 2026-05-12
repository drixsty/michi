'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import { Check, ArrowRight } from 'lucide-react';

const PricingCard = ({ plan, isFeatured }: { plan: any; isFeatured?: boolean }) => {
  const t = useTranslations('Index');
  return (
    <div className={`p-7 rounded-xl flex flex-col h-full transition-colors ${
      isFeatured
        ? 'bg-primary text-white border border-primary'
        : 'bg-card border border-border hover:border-primary/30'
    }`}>
      <div className="mb-7">
        {isFeatured && (
          <span className="inline-block text-[10px] font-bold uppercase tracking-widest bg-white/20 text-white px-2.5 py-0.5 rounded-full mb-3">
            Most popular
          </span>
        )}
        <h3 className={`text-base font-semibold mb-3 ${isFeatured ? 'text-white' : 'text-foreground'}`}>
          {plan.name}
        </h3>
        <div className="flex items-baseline gap-0.5">
          <span className={`text-3xl font-bold ${isFeatured ? 'text-white' : 'text-foreground'}`}>
            ${plan.price}
          </span>
          {!isNaN(Number(plan.price)) && (
            <span className={`text-xs font-medium ml-1 ${isFeatured ? 'text-white/60' : 'text-muted-foreground'}`}>
              /{t('pricing.monthly')}
            </span>
          )}
        </div>
      </div>
      <ul className="space-y-3 mb-8 flex-grow">
        {plan.features.map((feature: string, idx: number) => (
          <li key={idx} className="flex items-start gap-2.5 text-sm">
            <div className={`mt-0.5 w-4 h-4 rounded-full flex items-center justify-center shrink-0 ${
              isFeatured ? 'bg-white/20' : 'bg-primary/10'
            }`}>
              <Check className={`w-2.5 h-2.5 ${isFeatured ? 'text-white' : 'text-primary'}`} />
            </div>
            <span className={isFeatured ? 'text-white/85' : 'text-muted-foreground'}>{feature}</span>
          </li>
        ))}
      </ul>
      <button className={`w-full py-3 rounded-xl font-semibold text-sm transition-all active:scale-95 ${
        isFeatured
          ? 'bg-white text-primary hover:bg-white/90'
          : 'bg-primary text-white hover:bg-primary/90'
      }`}>
        {t('getStarted')}
      </button>
    </div>
  );
};

export default function PricingPage() {
  const t = useTranslations('Index');
  const tPricing = useTranslations('Pricing');

  return (
    <div className="overflow-x-hidden min-h-screen">
      <section className="max-w-5xl mx-auto pt-28 pb-20 px-6">

        {/* Header */}
        <motion.div
          className="text-center mb-12"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <span className="inline-block text-[10px] font-bold uppercase tracking-widest text-primary mb-4">
            {tPricing('badge')}
          </span>
          <h1 className="text-[1.9rem] md:text-[2.6rem] font-bold mb-3 tracking-tight leading-[1.2] text-foreground">
            {tPricing.rich('title', {
              spanInner: (chunks) => <span className="text-gradient-purple">{chunks}</span>,
              br: () => <br className="hidden md:block" />
            }) as any}
          </h1>
          <p className="text-muted-foreground text-[0.9rem] max-w-md mx-auto leading-relaxed">
            {t('pricing.subtitle')}
          </p>
        </motion.div>

        {/* Plans */}
        <div className="grid md:grid-cols-3 gap-4 items-stretch mb-10">
          <PricingCard plan={t.raw('pricing.plans.starter')} />
          <PricingCard plan={t.raw('pricing.plans.pro')} isFeatured />
          <PricingCard plan={t.raw('pricing.plans.enterprise')} />
        </div>

        {/* Enterprise CTA */}
        <div className="border border-border rounded-xl p-7 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div>
            <h2 className="text-sm font-semibold text-foreground mb-1">{tPricing('enterprise.title')}</h2>
            <p className="text-xs text-muted-foreground leading-relaxed max-w-sm">
              {tPricing('enterprise.desc')}
            </p>
          </div>
          <button className="flex items-center gap-2 border border-border text-foreground px-5 py-2.5 rounded-xl text-sm font-semibold hover:bg-secondary transition-all whitespace-nowrap shrink-0">
            {tPricing('enterprise.button')} <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

      </section>
    </div>
  );
}
