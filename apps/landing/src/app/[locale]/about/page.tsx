'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import { Shield, Target, Heart, Zap } from 'lucide-react';

const values = [
  { icon: Shield, key: 'trust' },
  { icon: Target, key: 'precision' },
  { icon: Heart, key: 'user' },
  { icon: Zap, key: 'speed' },
] as const;

export default function AboutPage() {
  const t = useTranslations('About');

  return (
    <div className="overflow-x-hidden min-h-screen">

      {/* Hero */}
      <section className="max-w-3xl mx-auto pt-28 pb-14 px-6 text-center">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <span className="inline-block text-[10px] font-bold uppercase tracking-widest text-primary mb-5">
            {t('badge')}
          </span>
          <h1 className="text-[1.9rem] md:text-[2.6rem] font-bold mb-3 tracking-tight leading-[1.2] text-foreground">
            {t.rich('hero.title', {
              spanInner: (chunks) => <span className="text-gradient-purple">{chunks}</span>,
              br: () => <br className="hidden md:block" />
            }) as any}
          </h1>
          <p className="text-muted-foreground text-[0.9rem] max-w-lg mx-auto leading-relaxed">
            {t('hero.subtitle')}
          </p>
        </motion.div>
      </section>

      {/* Story + Values */}
      <section className="max-w-5xl mx-auto px-6 pb-14 border-t border-border pt-12">
        <div className="grid md:grid-cols-2 gap-12 items-start">

          {/* Story */}
          <div>
            <span className="inline-block text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-4">
              {t('story.badge')}
            </span>
            <h2 className="text-xl font-semibold text-foreground mb-3 tracking-tight">{t('story.title')}</h2>
            <p className="text-sm text-muted-foreground leading-relaxed mb-8">{t('story.content')}</p>

            {/* Brand mark */}
            <div className="inline-flex items-center gap-3 px-4 py-3 border border-border rounded-xl bg-card">
              <div className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center font-bold text-white text-base">道</div>
              <div>
                <p className="text-sm font-semibold text-foreground">Michi</p>
                <p className="text-[11px] text-muted-foreground">Founded 2024</p>
              </div>
            </div>
          </div>

          {/* Values */}
          <div>
            <span className="inline-block text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-4">
              Values
            </span>
            <div className="grid grid-cols-2 gap-3">
              {values.map(({ icon: Icon, key }) => (
                <div key={key} className="p-4 border border-border rounded-xl bg-card">
                  <Icon className="w-4 h-4 text-primary mb-2.5" />
                  <h4 className="text-sm font-semibold text-foreground mb-0.5">
                    {t(`values.${key}.title` as any)}
                  </h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {t(`values.${key}.desc` as any)}
                  </p>
                </div>
              ))}
            </div>
          </div>

        </div>
      </section>

      {/* Team */}
      <section className="max-w-5xl mx-auto px-6 pb-20 border-t border-border pt-12">
        <h2 className="text-base font-semibold text-foreground mb-8">
          {t.rich('team.title', {
            spanInner: (chunks) => <span className="text-gradient-purple">{chunks}</span>,
            br: () => <br />
          }) as any}
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="group">
              <div className="aspect-square bg-secondary rounded-xl mb-3 border border-border group-hover:border-primary/30 transition-colors" />
              <div className="w-20 h-3 bg-muted rounded-full mb-1.5 opacity-40" />
              <div className="w-14 h-2.5 bg-muted rounded-full opacity-25" />
            </div>
          ))}
        </div>
      </section>

    </div>
  );
}
