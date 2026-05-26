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
  Shield,
  Star,
  Quote,
  Package,
  Truck,
} from 'lucide-react';

// ── Feature Card ────────────────────────────────────────────
const FeatureCard = ({ icon: Icon, title, description }: { icon: any, title: string, description: string }) => (
  <div className="p-5 rounded-lg bg-card border border-border hover:border-primary/30 transition-all duration-200 group hover:shadow-sm">
    <div className="w-8 h-8 rounded-lg bg-primary/5 border border-primary/10 flex items-center justify-center mb-3 group-hover:bg-primary/10 transition-colors">
      <Icon className="w-4 h-4 text-primary" />
    </div>
    <h3 className="text-sm font-semibold mb-1 text-foreground tracking-tight">{title}</h3>
    <p className="text-muted-foreground text-xs leading-relaxed">{description}</p>
  </div>
);

// ── Pricing Card ────────────────────────────────────────────
const PricingCard = ({ name, price, features, highlighted, cta }: {
  name: string; price: string; features: string[]; highlighted?: boolean; cta: string;
}) => (
  <div className={`relative flex flex-col rounded-lg border p-6 transition-all ${
    highlighted
      ? 'border-primary bg-primary text-white shadow-xl shadow-primary/20'
      : 'border-border bg-card hover:border-primary/30'
  }`}>
    {highlighted && (
      <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-white text-primary text-[9px] font-bold rounded-full uppercase tracking-widest">
        Populaire
      </div>
    )}
    <div className="mb-4">
      <p className={`text-[10px] font-bold uppercase tracking-widest mb-1 ${highlighted ? 'text-white/70' : 'text-muted-foreground'}`}>{name}</p>
      <div className="flex items-end gap-1">
        {price === 'Custom' || price === 'Sur mesure' ? (
          <span className={`text-2xl font-bold ${highlighted ? 'text-white' : 'text-foreground'}`}>{price}</span>
        ) : (
          <>
            <span className={`text-2xl font-bold ${highlighted ? 'text-white' : 'text-foreground'}`}>${price}</span>
            <span className={`text-xs pb-1 ${highlighted ? 'text-white/60' : 'text-muted-foreground'}`}>/mo</span>
          </>
        )}
      </div>
    </div>
    <ul className="space-y-2 flex-1 mb-5">
      {features.map((f, i) => (
        <li key={i} className="flex items-start gap-2 text-xs">
          <Check className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${highlighted ? 'text-white/80' : 'text-primary'}`} />
          <span className={highlighted ? 'text-white/80' : 'text-muted-foreground'}>{f}</span>
        </li>
      ))}
    </ul>
    <a
      href={`${process.env.NEXT_PUBLIC_APP_URL}/register`}
      className={`w-full py-2.5 rounded-lg text-[11px] font-bold text-center transition-all ${
        highlighted
          ? 'bg-white text-primary hover:bg-white/90'
          : 'bg-secondary text-foreground hover:bg-border border border-border'
      }`}
    >
      {cta}
    </a>
  </div>
);

// ── Testimonial Card ────────────────────────────────────────
const TestimonialCard = ({ quote, author, role, stars = 5 }: {
  quote: string; author: string; role: string; stars?: number;
}) => (
  <div className="p-5 rounded-lg bg-card border border-border flex flex-col gap-3">
    <div className="flex gap-0.5">
      {Array.from({ length: stars }).map((_, i) => (
        <Star key={i} className="w-3 h-3 text-amber-400 fill-amber-400" />
      ))}
    </div>
    <Quote className="w-4 h-4 text-primary/30" />
    <p className="text-sm text-foreground leading-relaxed flex-1">"{quote}"</p>
    <div>
      <p className="text-xs font-semibold text-foreground">{author}</p>
      <p className="text-[10px] text-muted-foreground">{role}</p>
    </div>
  </div>
);

// ── Main Landing Content ─────────────────────────────────────
export default function LandingContent() {
  const t = useTranslations('Index');
  const tNavbar = useTranslations('Navbar');
  const tShopify = useTranslations('Shopify');
  const tAmazon = useTranslations('Amazon');
  const tWoo = useTranslations('WooCommerce');

  const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
  const demoUrl = process.env.NEXT_PUBLIC_DEMO_URL || 'mailto:contact@michi.app';

  return (
    <div className="relative overflow-x-hidden">

      {/* ── Hero ──────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto pt-16 pb-12 px-4 sm:px-6">
        <div className="flex flex-col items-center text-center justify-center max-w-4xl mx-auto gap-8">

          {/* Text content */}
          <div className="w-full max-w-3xl">
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
              <span className="inline-block px-3 py-1 rounded-lg bg-secondary border border-border text-muted-foreground text-[10px] font-bold tracking-widest uppercase mb-5">
                {t('heroBadge')}
              </span>
              <h1 className="text-[1.7rem] sm:text-[2.2rem] md:text-[3rem] font-bold mb-4 tracking-tight leading-[1.2] text-foreground">
                {t.rich('title', {
                  spanInner: (chunks) => <span className="text-gradient-purple">{chunks}</span>,
                  br: () => <br className="hidden md:block" />,
                })}
              </h1>
              <p className="max-w-2xl mx-auto text-muted-foreground text-[0.95rem] mb-8 leading-relaxed">
                {t('description')}
              </p>
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-3">
                <a
                  href={`${appUrl}/register`}
                  className="bg-primary hover:bg-primary/90 text-white px-8 py-3 min-h-[44px] rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-all active:scale-[0.98] shadow-lg shadow-primary/20"
                >
                  {t('getStarted')} <ArrowRight className="w-3.5 h-3.5 shrink-0" />
                </a>
                <a
                  href={demoUrl}
                  className="border border-border text-foreground px-8 py-3 min-h-[44px] rounded-lg text-sm font-semibold hover:bg-secondary transition-all flex items-center justify-center"
                >
                  {t('bookDemo')}
                </a>
              </div>

              {/* Trust signals inline */}
              <div className="flex items-center gap-5 mt-6 justify-center flex-wrap">
                <span className="flex items-center gap-1.5 text-[10.5px] text-muted-foreground font-medium">
                  <Check className="w-3.5 h-3.5 text-emerald-500" /> {t('trustSignals.noCard')}
                </span>
                <span className="flex items-center gap-1.5 text-[10.5px] text-muted-foreground font-medium">
                  <Check className="w-3.5 h-3.5 text-emerald-500" /> {t('trustSignals.freeTrial')}
                </span>
                <span className="flex items-center gap-1.5 text-[10.5px] text-muted-foreground font-medium">
                  <Check className="w-3.5 h-3.5 text-emerald-500" /> {t('trustSignals.cancel')}
                </span>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ── Trusted by (real platform names) ─────────────── */}
      <section className="max-w-3xl mx-auto mb-14 px-4 sm:px-6 text-center">
        <p className="text-muted-foreground text-[10px] font-bold uppercase tracking-widest mb-6 opacity-50">{t('trustedBy')}</p>
        <div className="flex flex-wrap justify-center items-center gap-8 md:gap-12">
          {[
            { Icon: ShoppingCart, name: 'Shopify', color: 'text-emerald-600' },
            { Icon: Globe, name: 'Amazon FBA', color: 'text-orange-500' },
            { Icon: Boxes, name: 'WooCommerce', color: 'text-blue-500' },
            { Icon: CreditCard, name: 'Stripe', color: 'text-violet-500' },
            { Icon: Package, name: 'CSV / ERP', color: 'text-slate-500' },
          ].map(({ Icon, name, color }) => (
            <div key={name} className="flex items-center gap-2 opacity-40 hover:opacity-70 transition-opacity">
              <Icon className={`w-4 h-4 ${color}`} />
              <span className="text-sm font-bold text-foreground tracking-tight">{name}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Stats ─────────────────────────────────────────── */}
      <section className="max-w-3xl mx-auto mb-14 px-4 sm:px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 border border-border rounded-lg divide-x divide-border">
          {[
            { label: t('stats.accuracyLabel'), value: t('stats.accuracy') },
            { label: t('stats.growthLabel'), value: t('stats.growth') },
            { label: t('stats.reductionLabel'), value: t('stats.reduction') },
            { label: t('stats.integrationsLabel'), value: t('stats.integrations') },
          ].map((stat, idx) => (
            <div key={idx} className={`py-4 text-center ${idx < 2 ? 'border-b border-border md:border-b-0' : ''}`}>
              <div className="text-lg font-bold text-primary mb-0.5">{stat.value}</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">{stat.label}</div>
            </div>
          ))}
        </div>
        <p className="text-center text-[9px] text-muted-foreground/50 mt-2">{t('stats.disclaimer')}</p>
      </section>

      {/* ── Workflow ──────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto mb-14 px-4 sm:px-6 border-t border-border pt-12">
        <div className="mb-8">
          <h2 className="text-base font-semibold text-foreground mb-1">{t('workflowSection.title')}</h2>
          <p className="text-sm text-muted-foreground">{t('workflowSection.subtitle')}</p>
        </div>
        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { icon: Rocket, step: 'step1' },
            { icon: BarChart3, step: 'step2' },
            { icon: Shield, step: 'step3' }
          ].map((item, idx) => (
            <div key={idx} className="p-5 rounded-lg bg-card border border-border hover:border-primary/20 transition-colors">
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

      {/* ── Dropshipping / Supply chain specifics ─────────── */}
      <section className="max-w-5xl mx-auto mb-14 px-4 sm:px-6 border-t border-border pt-12">
        <div className="mb-8">
          <h2 className="text-base font-semibold text-foreground mb-1">{t('dropshipping.title')}</h2>
          <p className="text-sm text-muted-foreground">{t('dropshipping.subtitle')}</p>
        </div>
        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { icon: Truck, key: 'leadTime' },
            { icon: Package, key: 'safetyStock' },
            { icon: Zap, key: 'moq' },
          ].map(({ icon: Icon, key }) => (
            <div key={key} className="p-5 rounded-lg bg-card border border-border flex gap-4 items-start hover:border-primary/20 transition-colors">
              <div className="w-8 h-8 shrink-0 rounded-lg bg-primary/5 border border-primary/10 flex items-center justify-center">
                <Icon className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground mb-0.5">{t(`dropshipping.items.${key}.title` as any)}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">{t(`dropshipping.items.${key}.desc` as any)}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Comparison ───────────────────────────────────── */}
      <section className="max-w-3xl mx-auto mb-14 px-4 sm:px-6 border-t border-border pt-12">
        <div className="mb-6">
          <h2 className="text-base font-semibold text-foreground mb-1">{t('comparison.title')}</h2>
          <p className="text-sm text-muted-foreground">{t('comparison.subtitle')}</p>
        </div>
        <div className="rounded-lg border border-border overflow-hidden">
          <div className="hidden md:grid grid-cols-3 bg-secondary/50 px-5 py-3 border-b border-border">
            <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{t('comparison.labels.feature')}</div>
            <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest text-center">{t('comparison.labels.spreadsheets')}</div>
            <div className="text-[10px] font-bold text-primary uppercase tracking-widest text-center">{t('comparison.labels.michi')}</div>
          </div>
          <div className="md:hidden grid grid-cols-2 bg-secondary/50 px-4 py-2.5 border-b border-border">
            <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest text-center">{t('comparison.labels.spreadsheets')}</div>
            <div className="text-[10px] font-bold text-primary uppercase tracking-widest text-center">{t('comparison.labels.michi')}</div>
          </div>

          {Object.keys(t.raw('comparison.items')).map((key, idx, arr) => (
            <div key={key} className={`px-4 md:px-5 py-3.5 ${idx !== arr.length - 1 ? 'border-b border-border' : ''}`}>
              <div className="md:hidden text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2">
                {t(`comparison.items.${key}.title` as any)}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 items-center gap-2">
                <div className="hidden md:block text-sm font-semibold text-foreground">
                  {t(`comparison.items.${key}.title` as any)}
                </div>
                <div className="flex justify-center items-center gap-1.5 text-xs text-red-500/70 italic">
                  <X className="w-3.5 h-3.5 shrink-0" /> {t(`comparison.items.${key}.manual` as any)}
                </div>
                <div className="flex justify-center items-center gap-1.5 text-xs text-emerald-600 font-medium">
                  <Check className="w-3.5 h-3.5 shrink-0" /> {t(`comparison.items.${key}.michi` as any)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features grid ────────────────────────────────── */}
      <section id="features" className="max-w-5xl mx-auto mb-14 px-4 sm:px-6 border-t border-border pt-12">
        <div className="mb-6">
          <h2 className="text-base font-semibold text-foreground mb-1">{t('featuresSection.title')}</h2>
          <p className="text-sm text-muted-foreground">{t('featuresSection.subtitle')}</p>
        </div>
        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
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

      {/* ── Integrations ──────────────────────────────────── */}
      <section id="integrations" className="max-w-5xl mx-auto mb-14 px-4 sm:px-6 border-t border-border pt-12">
        <div className="flex flex-col lg:flex-row items-start gap-12">
          <div className="flex-1">
            <h2 className="text-base font-semibold text-foreground mb-2">
              {t.rich('integrations.title', {
                spanInner: (chunks) => <span className="text-gradient-purple">{chunks}</span>,
                br: () => <br className="hidden md:block" />,
              }) as any}
            </h2>
            <p className="text-sm text-muted-foreground mb-6 leading-relaxed max-w-sm">
              {t('integrations.description')}
            </p>
            <div className="flex flex-wrap gap-3 mb-5">
              <a href="/integrations/shopify" className="px-4 min-h-[44px] rounded-lg bg-card flex items-center gap-2.5 hover:border-primary/40 transition-colors border border-border">
                <ShoppingCart className="w-4 h-4 text-primary shrink-0" />
                <span className="text-sm font-semibold">{tNavbar('integrationNames.shopify')}</span>
              </a>
              <a href="/integrations/amazon" className="px-4 min-h-[44px] rounded-lg bg-card flex items-center gap-2.5 hover:border-orange-400/40 transition-colors border border-border">
                <Globe className="w-4 h-4 text-orange-500 shrink-0" />
                <span className="text-sm font-semibold">{tNavbar('integrationNames.amazon')}</span>
              </a>
              <a href="/integrations/woocommerce" className="px-4 min-h-[44px] rounded-lg bg-card flex items-center gap-2.5 hover:border-blue-400/40 transition-colors border border-border">
                <Boxes className="w-4 h-4 text-blue-500 shrink-0" />
                <span className="text-sm font-semibold">{tNavbar('integrationNames.woocommerce')}</span>
              </a>
            </div>
            <a href="/integrations" className="flex items-center gap-1.5 text-sm text-primary font-semibold hover:gap-2.5 transition-all">
              {t('integrations.viewAll')} <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </div>

          {/* Visual */}
          <div className="w-full lg:w-72 shrink-0">
            <div className="border border-border rounded-lg overflow-hidden">
              <div className="px-5 py-3 border-b border-border bg-secondary/40">
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">{t('integrations.connectedLabel')}</p>
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

      {/* ── Testimonials ──────────────────────────────────── */}
      <section className="max-w-5xl mx-auto mb-14 px-4 sm:px-6 border-t border-border pt-12">
        <div className="mb-8">
          <h2 className="text-base font-semibold text-foreground mb-1">{t('testimonials.title')}</h2>
          <p className="text-sm text-muted-foreground">{t('testimonials.subtitle')}</p>
        </div>
        <div className="grid sm:grid-cols-3 gap-4">
          <TestimonialCard
            quote={tShopify('testimonial.quote')}
            author={tShopify('testimonial.author')}
            role={tShopify('testimonial.role')}
          />
          <TestimonialCard
            quote={tAmazon('testimonial.quote')}
            author={tAmazon('testimonial.author')}
            role={tAmazon('testimonial.role')}
          />
          <TestimonialCard
            quote={tWoo('testimonial.quote')}
            author={tWoo('testimonial.author')}
            role={tWoo('testimonial.role')}
          />
        </div>
      </section>

      {/* ── Pricing ───────────────────────────────────────── */}
      <section id="pricing" className="max-w-5xl mx-auto mb-14 px-4 sm:px-6 border-t border-border pt-12">
        <div className="mb-8 text-center">
          <h2 className="text-base font-semibold text-foreground mb-1">{t('pricing.title')}</h2>
          <p className="text-sm text-muted-foreground">{t('pricing.subtitle')}</p>
        </div>
        <div className="grid sm:grid-cols-3 gap-4">
          <PricingCard
            name={t('pricing.plans.starter.name')}
            price={t('pricing.plans.starter.price')}
            features={t.raw('pricing.plans.starter.features') as string[]}
            cta={t('getStarted')}
          />
          <PricingCard
            name={t('pricing.plans.pro.name')}
            price={t('pricing.plans.pro.price')}
            features={t.raw('pricing.plans.pro.features') as string[]}
            highlighted
            cta={t('getStarted')}
          />
          <PricingCard
            name={t('pricing.plans.enterprise.name')}
            price={t('pricing.plans.enterprise.price')}
            features={t.raw('pricing.plans.enterprise.features') as string[]}
            cta={t('bookDemo')}
          />
        </div>
      </section>

      {/* ── Final CTA ─────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto mb-20 px-4 sm:px-6 border-t border-border pt-12">
        <div className="bg-primary rounded-lg px-5 sm:px-8 py-8 sm:py-10 text-center text-white">
          <h2 className="text-xl font-bold mb-2 tracking-tight">{t('cta.title')}</h2>
          <p className="text-white/70 text-sm mb-6 max-w-sm mx-auto leading-relaxed">{t('cta.subtitle')}</p>
          <a
            href={`${appUrl}/register`}
            className="bg-white text-primary hover:bg-white/90 px-8 min-h-[44px] rounded-lg font-semibold text-sm transition-all inline-flex items-center justify-center shadow-lg"
          >
            {t('cta.button')}
          </a>
        </div>
      </section>

    </div>
  );
}
