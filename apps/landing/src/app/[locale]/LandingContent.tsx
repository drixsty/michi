'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import {
  TrendingUp,
  BarChart3,
  Layers,
  Zap,
  ShieldCheck,
  ArrowRight,
  Globe,
  ShoppingCart,
  Boxes,
  Check,
  X,
  CreditCard,
  Rocket,
  Shield
} from 'lucide-react';

const FeatureCard = ({ icon: Icon, title, description }: { icon: any, title: string, description: string }) => (
  <div className="p-5 rounded-lg bg-card border border-border hover:border-primary/30 transition-colors group">
    <Icon className="w-4 h-4 text-primary mb-3" />
    <h3 className="text-sm font-semibold mb-1 text-foreground tracking-tight">{title}</h3>
    <p className="text-muted-foreground text-xs leading-relaxed">{description}</p>
  </div>
);

export default function LandingContent() {
  const t = useTranslations('Index');
  const tNavbar = useTranslations('Navbar');

  return (
    <div className="relative overflow-x-hidden">

      {/* Hero */}
      <section className="max-w-3xl mx-auto pt-28 pb-14 px-6 text-center">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <span className="inline-block px-3 py-1 rounded-lg bg-secondary border border-border text-muted-foreground text-[10px] font-bold tracking-widest uppercase mb-5">
            {t('heroBadge')}
          </span>
          <h1 className="text-[1.9rem] md:text-[2.6rem] font-bold mb-3 tracking-tight leading-[1.2] text-foreground">
            {t.rich('title', {
              spanInner: (chunks) => <span className="text-gradient-purple">{chunks}</span>,
              br: () => <br className="hidden md:block" />
            })}
          </h1>
          <p className="max-w-lg mx-auto text-muted-foreground text-[0.9rem] mb-7 leading-relaxed">
            {t('description')}
          </p>
          <div className="flex items-center justify-center gap-2.5">
            <button className="bg-primary hover:bg-primary/90 text-white px-6 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all">
              {t('getStarted')} <ArrowRight className="w-3.5 h-3.5" />
            </button>
            <button className="border border-border text-foreground px-6 py-2.5 rounded-lg text-sm font-semibold hover:bg-secondary transition-all">
              {t('bookDemo')}
            </button>
          </div>
        </motion.div>
      </section>

      {/* Trusted by */}
      <section className="max-w-3xl mx-auto mb-14 px-6 text-center">
        <p className="text-muted-foreground text-[10px] font-bold uppercase tracking-widest mb-6 opacity-50">{t('trustedBy')}</p>
        <div className="flex flex-wrap justify-center items-center gap-10 opacity-25">
          <ShoppingCart className="w-7 h-7" />
          <Globe className="w-7 h-7" />
          <Boxes className="w-7 h-7" />
          <Zap className="w-7 h-7" />
          <Layers className="w-7 h-7" />
        </div>
      </section>

      {/* Stats */}
      <section className="max-w-3xl mx-auto mb-14 px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 border border-border rounded-lg divide-x divide-border">
          {[
            { label: t('stats.accuracyLabel'), value: t('stats.accuracy') },
            { label: t('stats.growthLabel'), value: t('stats.growth') },
            { label: t('stats.reductionLabel'), value: t('stats.reduction') },
            { label: t('stats.integrationsLabel'), value: t('stats.integrations') },
          ].map((stat, idx) => (
            <div key={idx} className="py-4 text-center">
              <div className="text-lg font-bold text-primary mb-0.5">{stat.value}</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Workflow */}
      <section className="max-w-5xl mx-auto mb-14 px-6 border-t border-border pt-12">
        <div className="mb-8">
          <h2 className="text-base font-semibold text-foreground mb-1">{t('workflowSection.title')}</h2>
          <p className="text-sm text-muted-foreground">{t('workflowSection.subtitle')}</p>
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          {[
            { icon: Rocket, step: 'step1' },
            { icon: BarChart3, step: 'step2' },
            { icon: Shield, step: 'step3' }
          ].map((item, idx) => (
            <div key={idx} className="p-5 rounded-lg bg-card border border-border">
              <div className="text-[10px] font-bold text-primary mb-2 tracking-widest uppercase">
                {String(idx + 1).padStart(2, '0')}
              </div>
              <item.icon className="w-4 h-4 text-primary mb-3" />
              <h3 className="text-sm font-semibold text-foreground mb-1">{t(`workflowSection.items.${item.step}.title` as any)}</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">{t(`workflowSection.items.${item.step}.desc` as any)}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Comparison */}
      <section className="max-w-3xl mx-auto mb-14 px-6 border-t border-border pt-12">
        <div className="mb-6">
          <h2 className="text-base font-semibold text-foreground mb-1">{t('comparison.title')}</h2>
          <p className="text-sm text-muted-foreground">{t('comparison.subtitle')}</p>
        </div>
        <div className="rounded-lg border border-border overflow-hidden">
          <div className="grid grid-cols-3 bg-secondary/50 px-5 py-3 border-b border-border">
            <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{t('comparison.labels.feature')}</div>
            <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest text-center">{t('comparison.labels.spreadsheets')}</div>
            <div className="text-[10px] font-bold text-primary uppercase tracking-widest text-center">{t('comparison.labels.michi')}</div>
          </div>
          {Object.keys(t.raw('comparison.items')).map((key, idx, arr) => (
            <div key={key} className={`grid grid-cols-3 px-5 py-3.5 items-center ${idx !== arr.length - 1 ? 'border-b border-border' : ''}`}>
              <div className="text-sm font-semibold text-foreground">{t(`comparison.items.${key}.title` as any)}</div>
              <div className="flex justify-center items-center gap-1.5 text-xs text-red-500/70 italic">
                <X className="w-3.5 h-3.5 shrink-0" /> {t(`comparison.items.${key}.manual` as any)}
              </div>
              <div className="flex justify-center items-center gap-1.5 text-xs text-emerald-600 font-medium">
                <Check className="w-3.5 h-3.5 shrink-0" /> {t(`comparison.items.${key}.michi` as any)}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Features grid */}
      <section id="features" className="max-w-5xl mx-auto mb-14 px-6 border-t border-border pt-12">
        <div className="mb-6">
          <h2 className="text-base font-semibold text-foreground mb-1">{t('featuresSection.title')}</h2>
          <p className="text-sm text-muted-foreground">{t('featuresSection.subtitle')}</p>
        </div>
        <div className="grid md:grid-cols-3 gap-3">
          <a href="/features/forecasting">
            <FeatureCard icon={TrendingUp} title={t('featuresSection.items.predictive.title')} description={t('featuresSection.items.predictive.description')} />
          </a>
          <a href="/features/unified-inventory">
            <FeatureCard icon={Layers} title={t('featuresSection.items.multisync.title')} description={t('featuresSection.items.multisync.description')} />
          </a>
          <a href="/features/replenishment">
            <FeatureCard icon={Zap} title={t('featuresSection.items.replenishment.title')} description={t('featuresSection.items.replenishment.description')} />
          </a>
          <FeatureCard icon={ShieldCheck} title={t('featuresSection.items.risk.title')} description={t('featuresSection.items.risk.description')} />
          <FeatureCard icon={Globe} title={t('featuresSection.items.global.title')} description={t('featuresSection.items.global.description')} />
          <FeatureCard icon={BarChart3} title={t('featuresSection.items.profit.title')} description={t('featuresSection.items.profit.description')} />
        </div>
      </section>

      {/* Integrations */}
      <section id="integrations" className="max-w-5xl mx-auto mb-14 px-6 border-t border-border pt-12">
        <div className="flex flex-col lg:flex-row items-start gap-12">
          <div className="flex-1">
            <h2 className="text-base font-semibold text-foreground mb-2">
              {t.rich('integrations.title', {
                spanInner: (chunks) => <span className="text-gradient-purple">{chunks}</span>,
                br: () => <br className="hidden md:block" />
              }) as any}
            </h2>
            <p className="text-sm text-muted-foreground mb-6 leading-relaxed max-w-sm">
              {t('integrations.description')}
            </p>
            <div className="flex flex-wrap gap-3 mb-5">
              <a href="/integrations/shopify" className="px-4 py-2.5 rounded-lg bg-card flex items-center gap-2.5 hover:border-primary/40 transition-colors border border-border">
                <ShoppingCart className="w-4 h-4 text-primary" />
                <span className="text-sm font-semibold">{tNavbar('integrationNames.shopify')}</span>
              </a>
              <a href="/integrations/amazon" className="px-4 py-2.5 rounded-lg bg-card flex items-center gap-2.5 hover:border-orange-400/40 transition-colors border border-border">
                <Globe className="w-4 h-4 text-orange-500" />
                <span className="text-sm font-semibold">{tNavbar('integrationNames.amazon')}</span>
              </a>
              <a href="/integrations/woocommerce" className="px-4 py-2.5 rounded-lg bg-card flex items-center gap-2.5 hover:border-blue-400/40 transition-colors border border-border">
                <Boxes className="w-4 h-4 text-blue-500" />
                <span className="text-sm font-semibold">{tNavbar('integrationNames.woocommerce')}</span>
              </a>
            </div>
            <button className="flex items-center gap-1.5 text-sm text-primary font-semibold">
              {t('integrations.viewAll')} <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Visual */}
          <div className="w-full lg:w-72 shrink-0">
            <div className="border border-border rounded-lg overflow-hidden">
              <div className="px-5 py-3 border-b border-border bg-secondary/40">
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Connected channels</p>
              </div>
              <ul className="p-5 space-y-3">
                {[
                  { icon: ShoppingCart, name: 'Shopify', color: 'text-primary' },
                  { icon: Globe, name: 'Amazon FBA', color: 'text-orange-500' },
                  { icon: Boxes, name: 'WooCommerce', color: 'text-blue-500' },
                  { icon: CreditCard, name: 'Stripe / payments', color: 'text-emerald-600' },
                ].map((item) => (
                  <li key={item.name} className="flex items-center gap-2.5">
                    <item.icon className={`w-4 h-4 shrink-0 ${item.color}`} />
                    <span className="text-sm text-foreground">{item.name}</span>
                    <Check className="w-3 h-3 text-emerald-500 ml-auto shrink-0" />
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-5xl mx-auto mb-20 px-6 border-t border-border pt-12">
        <div className="bg-primary rounded-lg px-8 py-10 text-center text-white">
          <h2 className="text-xl font-bold mb-2 tracking-tight">{t('cta.title')}</h2>
          <p className="text-white/70 text-sm mb-6 max-w-sm mx-auto leading-relaxed">{t('cta.subtitle')}</p>
          <button className="bg-white text-primary hover:bg-white/90 px-8 py-2.5 rounded-lg font-semibold text-sm transition-all">
            {t('cta.button')}
          </button>
        </div>
      </section>

    </div>
  );
}
