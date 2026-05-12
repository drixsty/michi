'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import {
  ArrowRight,
  Check,
  TrendingUp,
  Zap,
  ShieldCheck,
  Globe,
  BarChart3,
  Layers,
  Cloud
} from 'lucide-react';

const IconMap: Record<string, any> = { TrendingUp, Zap, ShieldCheck, Globe, BarChart3, Layers };

interface FeatureTemplateProps {
  namespace?: string;
  iconName: string;
  featureKey: string;
}

export const FeatureTemplate = ({ iconName, featureKey }: FeatureTemplateProps) => {
  const t = useTranslations('Features' as any);
  const tIndex = useTranslations('Index');
  const Icon = IconMap[iconName] || TrendingUp;

  return (
    <div className="overflow-x-hidden">

      {/* Hero */}
      <section className="max-w-3xl mx-auto pt-28 pb-12 px-6 text-center">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-primary/5 border border-border mb-5">
            <Icon className="w-5 h-5 text-primary" />
          </div>
          <h1 className="text-[1.9rem] md:text-[2.6rem] font-bold mb-3 tracking-tight leading-[1.2] text-foreground">
            {t.rich(`${featureKey}.hero.title` as any, {
              spanInner: (chunks) => <span className="text-gradient-purple">{chunks}</span>,
              br: () => <br className="hidden md:block" />
            }) as any}
          </h1>
          <p className="text-muted-foreground text-[0.9rem] max-w-lg mx-auto mb-7 leading-relaxed">
            {t(`${featureKey}.hero.subtitle` as any)}
          </p>
          <div className="flex items-center justify-center gap-2.5">
            <button className="bg-primary hover:bg-primary/90 text-white px-6 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 transition-all">
              {tIndex('getStarted')} <ArrowRight className="w-3.5 h-3.5" />
            </button>
            <button className="border border-border text-foreground px-6 py-2.5 rounded-xl text-sm font-semibold hover:bg-secondary transition-all">
              {tIndex('bookDemo')}
            </button>
          </div>
        </motion.div>
      </section>

      {/* Stats row */}
      <section className="max-w-3xl mx-auto px-6 mb-14">
        <div className="grid grid-cols-3 border border-border rounded-xl divide-x divide-border">
          {[
            { value: tIndex('stats.accuracy'), label: tIndex('stats.accuracyLabel') },
            { value: tIndex('stats.reduction'), label: tIndex('stats.reductionLabel') },
            { value: tIndex('stats.integrations'), label: tIndex('stats.integrationsLabel') },
          ].map((stat, i) => (
            <div key={i} className="py-4 text-center">
              <div className="text-lg font-bold text-primary mb-0.5">{stat.value}</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Capabilities */}
      <section className="max-w-3xl mx-auto px-6 pb-14 border-t border-border pt-12">
        <div className="mb-7">
          <h2 className="text-base font-semibold text-foreground mb-1">{tIndex('common.capabilities.title')}</h2>
          <p className="text-sm text-muted-foreground max-w-md leading-relaxed">{tIndex('common.capabilities.subtitle')}</p>
        </div>
        <div className="grid md:grid-cols-3 gap-3">
          {(['leadTimes', 'multiLocation', 'promotions'] as const).map((key) => (
            <div key={key} className="p-5 rounded-xl border border-border bg-card">
              <Check className="w-3.5 h-3.5 text-primary mb-3" />
              <h3 className="text-sm font-semibold text-foreground mb-1 leading-snug">
                {tIndex(`common.capabilities.items.${key}.title` as any)}
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {tIndex(`common.capabilities.items.${key}.desc` as any)}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Specs */}
      <section className="max-w-3xl mx-auto px-6 pb-20 border-t border-border pt-12">
        <div className="grid md:grid-cols-3 gap-3">
          {[
            { icon: ShieldCheck, title: tIndex('common.specs.enterprise'), desc: tIndex('common.specs.enterpriseDesc') },
            { icon: Cloud, title: tIndex('common.specs.cloud'), desc: tIndex('common.specs.cloudDesc') },
            { icon: Zap, title: tIndex('common.aiEngine'), desc: tIndex('common.aiEngineDesc') }
          ].map((item, i) => (
            <div key={i} className="p-5 rounded-xl border border-border bg-card hover:border-primary/30 transition-colors">
              <item.icon className="w-4 h-4 text-primary mb-3" />
              <h3 className="text-sm font-semibold text-foreground mb-1">{item.title}</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

    </div>
  );
};
