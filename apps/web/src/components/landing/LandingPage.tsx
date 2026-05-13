'use client';

import React, { useState, useEffect } from 'react';
import { Link } from '@/i18n/navigation';
import { useTranslations } from 'next-intl';
import {
  ArrowRight,
  Menu,
  X,
  BarChart3,
  Package,
  Bell,
  Zap,
  Globe,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// ─── Types ────────────────────────────────────────────────────────────────────

interface StatItem {
  value: string;
  label: string;
}

// ─── Mock Dashboard (Hero visual) ─────────────────────────────────────────────

function MockDashboard() {
  const products = [
    { name: 'Nike Air Max 270', sku: 'NK-270-BLK', stock: 12, status: 'warning', bar: 20 },
    { name: 'Adidas Ultraboost 23', sku: 'AD-UB-WHT', stock: 247, status: 'good', bar: 85 },
    { name: "Levi's 501 Original", sku: 'LV-501-BLU', stock: 3, status: 'critical', bar: 5 },
    { name: 'Sony WH-1000XM5', sku: 'SN-WH-BLK', stock: 89, status: 'good', bar: 65 },
  ];

  const statusColors: Record<string, string> = {
    good: 'bg-emerald-500',
    warning: 'bg-amber-400',
    critical: 'bg-red-500',
  };

  const barColors: Record<string, string> = {
    good: 'bg-emerald-400',
    warning: 'bg-amber-400',
    critical: 'bg-red-400',
  };

  return (
    // Le wrapper n'a plus de glow -inset-4 (cause de scroll horizontal)
    // Le badge flottant est repositionné à l'intérieur du flux
    <div className="relative w-full">

      {/* Halo décoratif — contenu dans le wrapper, pas -inset */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-violet-200/30 rounded-2xl blur-2xl -z-10 scale-105" />

      {/* Carte principale */}
      <div className="relative bg-white rounded-2xl border border-slate-200 shadow-2xl overflow-hidden">

        {/* Header bar */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-primary flex items-center justify-center text-white text-xs font-bold shrink-0">
              道
            </div>
            <span className="text-xs font-semibold text-slate-700">Michi Dashboard</span>
          </div>
          <div className="flex items-center gap-2">
            {/* Badge IA Active intégré dans le header — plus de positionnement absolu en dehors */}
            <div className="flex items-center gap-1 bg-primary/5 border border-primary/10 rounded-full px-2 py-0.5">
              <Sparkles className="h-2.5 w-2.5 text-primary" />
              <span className="text-[9px] font-semibold text-primary">IA Active</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-[9px] text-slate-500 font-medium">Live</span>
            </div>
          </div>
        </div>

        {/* KPI strip */}
        <div className="grid grid-cols-3 divide-x divide-slate-100 border-b border-slate-100">
          {[
            { label: 'Produits', value: '1 247', sub: 'Total', color: 'text-slate-800' },
            { label: 'Ruptures', value: '3', sub: 'Critiques', color: 'text-red-500' },
            { label: 'Précision IA', value: '98.2%', sub: 'Prévisions', color: 'text-primary' },
          ].map((kpi) => (
            <div key={kpi.label} className="px-3 py-2.5 text-center">
              <div className={cn('text-sm sm:text-base font-bold', kpi.color)}>{kpi.value}</div>
              <div className="text-[9px] text-slate-400 mt-0.5">{kpi.sub}</div>
            </div>
          ))}
        </div>

        {/* Mini chart */}
        <div className="px-4 pt-3 pb-1">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[9px] sm:text-[10px] font-semibold text-slate-500 uppercase tracking-wide">Prévisions 30j</span>
            <span className="text-[9px] text-emerald-500 font-medium flex items-center gap-1">
              <TrendingUp className="h-2.5 w-2.5" /> +12% vs M-1
            </span>
          </div>
          <div className="flex items-end gap-0.5 sm:gap-1 h-8 sm:h-10">
            {[40, 55, 45, 60, 52, 70, 65, 80, 72, 85, 78, 90, 82, 88, 95].map((h, i) => (
              <div
                key={i}
                className={cn(
                  'flex-1 rounded-t-sm transition-all',
                  i >= 10 ? 'bg-primary/20' : 'bg-primary/50'
                )}
                style={{ height: `${h}%` }}
              />
            ))}
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-[9px] text-slate-400">Réel</span>
            <span className="text-[9px] text-primary/70">IA →</span>
          </div>
        </div>

        {/* Product list */}
        <div className="px-4 pb-3 space-y-1.5">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[9px] sm:text-[10px] font-semibold text-slate-500 uppercase tracking-wide">Inventaire critique</span>
            <AlertCircle className="h-3 w-3 text-amber-400" />
          </div>
          {products.map((p) => (
            <div key={p.sku} className="flex items-center gap-2">
              <div className={cn('w-1.5 h-1.5 rounded-full shrink-0', statusColors[p.status])} />
              <div className="flex-1 min-w-0">
                <div className="text-[10px] font-medium text-slate-700 truncate">{p.name}</div>
                <div className="w-full bg-slate-100 rounded-full h-1 mt-0.5">
                  <div
                    className={cn('h-1 rounded-full', barColors[p.status])}
                    style={{ width: `${p.bar}%` }}
                  />
                </div>
              </div>
              <span className="text-[10px] font-semibold text-slate-600 shrink-0">{p.stock}u</span>
            </div>
          ))}
        </div>

        {/* Alert strip */}
        <div className="mx-4 mb-3 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-2">
          <Bell className="h-3 w-3 text-amber-500 shrink-0" />
          <span className="text-[9px] sm:text-[10px] text-amber-700 font-medium leading-snug">
            Levi's 501 · Rupture dans <strong>4 jours</strong> — Cmd 150u
          </span>
        </div>
      </div>
    </div>
  );
}

// ─── Navigation ───────────────────────────────────────────────────────────────

function LandingNav() {
  const t = useTranslations('landing');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 10);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Fermer le menu sur clic hash (anchor)
  const handleAnchorClick = () => setIsMenuOpen(false);

  const navLinks = [
    { label: t('nav.features'), href: '#features' },
    { label: t('nav.howItWorks'), href: '#how-it-works' },
    { label: t('nav.pricing'), href: '/pricing' },
  ];

  return (
    <header
      className={cn(
        'sticky top-0 z-50 w-full transition-all duration-200',
        isScrolled
          ? 'bg-white/95 backdrop-blur-md border-b border-slate-200/60 shadow-sm'
          : 'bg-white border-b border-slate-100'
      )}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-14 sm:h-16">

          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-sm shadow-md shadow-primary/20">
              道
            </div>
            <span className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">Michi</span>
          </Link>

          {/* Desktop nav — centré */}
          <nav className="hidden md:flex items-center gap-1 flex-1 justify-center">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors whitespace-nowrap min-h-[44px] flex items-center"
              >
                {link.label}
              </a>
            ))}
          </nav>

          {/* Desktop CTAs */}
          <div className="hidden md:flex items-center gap-2 shrink-0">
            <Link
              href="/login"
              className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition-colors min-h-[44px] flex items-center"
            >
              {t('nav.login')}
            </Link>
            <Link
              href="/register"
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-semibold text-white bg-primary hover:bg-primary/90 rounded-lg transition-all shadow-sm shadow-primary/20 min-h-[44px]"
            >
              {t('nav.cta')}
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {/* Mobile : hamburger seul — login dans le drawer */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
            aria-label="Menu"
            aria-expanded={isMenuOpen}
          >
            {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu drawer */}
      {isMenuOpen && (
        <div className="md:hidden border-t border-slate-100 bg-white shadow-lg animate-in slide-in-from-top-1 duration-150">
          <div className="max-w-6xl mx-auto px-4 py-3 space-y-1">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                onClick={handleAnchorClick}
                className="flex items-center justify-between w-full px-4 py-3.5 text-sm font-medium text-slate-700 hover:bg-slate-50 rounded-xl transition-colors min-h-[52px]"
              >
                {link.label}
                <ChevronRight className="h-4 w-4 text-slate-300 shrink-0" />
              </a>
            ))}
            <div className="border-t border-slate-100 pt-1">
              <Link
                href="/login"
                onClick={() => setIsMenuOpen(false)}
                className="flex items-center justify-between w-full px-4 py-3.5 text-sm font-medium text-slate-600 hover:bg-slate-50 rounded-xl transition-colors min-h-[52px]"
              >
                {t('nav.login')}
                <ChevronRight className="h-4 w-4 text-slate-300 shrink-0" />
              </Link>
            </div>
            <div className="pt-2 pb-1">
              <Link
                href="/register"
                onClick={() => setIsMenuOpen(false)}
                className="flex items-center justify-center gap-2 w-full px-4 py-3.5 text-sm font-bold text-white bg-primary hover:bg-primary/90 rounded-xl transition-colors min-h-[52px]"
              >
                {t('nav.cta')}
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

// ─── Hero ─────────────────────────────────────────────────────────────────────

function HeroSection() {
  const t = useTranslations('landing');

  return (
    // overflow-x-hidden empêche le scroll horizontal causé par les décorations bg
    <section className="relative overflow-x-hidden pt-10 pb-16 sm:pt-16 sm:pb-24 lg:pt-20 lg:pb-32">
      {/* Décorations background — contenues dans la section */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] sm:w-[800px] h-[300px] sm:h-[400px] bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-[200px] sm:w-[400px] h-[200px] sm:h-[400px] bg-violet-100/60 rounded-full blur-3xl" />
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex flex-col lg:flex-row items-center gap-10 lg:gap-16">

          {/* Texte */}
          <div className="flex-1 text-center lg:text-left w-full">

            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 border border-primary/20 rounded-full mb-5 sm:mb-6">
              <Sparkles className="h-3.5 w-3.5 text-primary shrink-0" />
              <span className="text-xs font-semibold text-primary">{t('hero.badge')}</span>
            </div>

            {/* Headline — taille adaptative mobile-first */}
            <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 leading-[1.1] tracking-tight mb-4">
              {t('hero.title1')}
              <br />
              <span className="text-primary">{t('hero.title2')}</span>
            </h1>

            {/* Subtitle */}
            <p className="text-sm sm:text-lg text-slate-500 leading-relaxed max-w-lg mx-auto lg:mx-0 mb-7 sm:mb-8">
              {t('hero.subtitle')}
            </p>

            {/* CTAs — stacked sur mobile, inline sur sm+ */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 justify-center lg:justify-start">
              <Link
                href="/register"
                className="flex items-center justify-center gap-2 px-6 py-3.5 text-sm font-bold text-white bg-primary hover:bg-primary/90 rounded-xl transition-all shadow-lg shadow-primary/25 min-h-[52px] active:scale-[0.98]"
              >
                {t('hero.ctaPrimary')}
                <ArrowRight className="h-4 w-4 shrink-0" />
              </Link>
              <a
                href="#how-it-works"
                className="flex items-center justify-center gap-2 px-6 py-3.5 text-sm font-semibold text-slate-700 bg-white border border-slate-200 hover:border-slate-300 rounded-xl transition-all min-h-[52px] active:scale-[0.98]"
              >
                {t('hero.ctaSecondary')}
                <ChevronRight className="h-4 w-4 shrink-0" />
              </a>
            </div>

            {/* Social proof */}
            <div className="flex flex-wrap items-center gap-2.5 mt-6 justify-center lg:justify-start">
              <div className="flex -space-x-1.5 shrink-0">
                {['#6C5CE7', '#00B894', '#0984E3', '#E17055'].map((color, i) => (
                  <div
                    key={i}
                    className="w-7 h-7 rounded-full border-2 border-white flex items-center justify-center text-white text-[9px] font-bold shadow-sm"
                    style={{ backgroundColor: color }}
                  >
                    {['JD', 'SM', 'AB', 'CL'][i]}
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-500">
                <span className="font-semibold text-slate-700">+500 marchands</span>{' '}
                {t('hero.socialProof')}
              </p>
            </div>
          </div>

          {/* Mock Dashboard — pleine largeur sur mobile */}
          <div className="flex-1 w-full lg:max-w-none">
            <MockDashboard />
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Stats Strip ──────────────────────────────────────────────────────────────

function StatsSection() {
  const t = useTranslations('landing');

  const stats: StatItem[] = [
    { value: '40%', label: t('stats.stockouts') },
    { value: '98%', label: t('stats.accuracy') },
    { value: '4', label: t('stats.channels') },
    { value: '48h', label: t('stats.setup') },
  ];

  return (
    <section className="border-y border-slate-100 bg-slate-50/60">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-8">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl sm:text-4xl font-extrabold text-primary tracking-tight">
                {stat.value}
              </div>
              <div className="text-xs sm:text-sm text-slate-500 font-medium mt-1.5 leading-snug">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Features ─────────────────────────────────────────────────────────────────

function FeaturesSection() {
  const t = useTranslations('landing');

  const features = [
    { icon: Zap,     key: 'ai',        color: 'text-violet-500', bg: 'bg-violet-50' },
    { icon: Globe,   key: 'omni',      color: 'text-blue-500',   bg: 'bg-blue-50'   },
    { icon: Bell,    key: 'alerts',    color: 'text-amber-500',  bg: 'bg-amber-50'  },
    { icon: BarChart3, key: 'decisions', color: 'text-emerald-500', bg: 'bg-emerald-50' },
  ];

  return (
    <section id="features" className="py-14 sm:py-24">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-10 sm:mb-16">
          <h2 className="text-2xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mb-3">
            {t('features.title')}
          </h2>
          <p className="text-slate-500 text-sm sm:text-lg max-w-xl mx-auto leading-relaxed">
            {t('features.subtitle')}
          </p>
        </div>

        <div className="grid sm:grid-cols-2 gap-4 sm:gap-6">
          {features.map(({ icon: Icon, key, color, bg }) => (
            <div
              key={key}
              className="p-5 sm:p-8 bg-white rounded-2xl border border-slate-200 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 active:scale-[0.99] transition-all duration-200"
            >
              <div className={cn('w-11 h-11 rounded-xl flex items-center justify-center mb-4 shrink-0', bg)}>
                <Icon className={cn('h-5 w-5', color)} />
              </div>
              <h3 className="text-sm sm:text-lg font-bold text-slate-900 mb-2">
                {t(`features.${key}.title`)}
              </h3>
              <p className="text-sm text-slate-500 leading-relaxed">
                {t(`features.${key}.desc`)}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── How It Works ─────────────────────────────────────────────────────────────

function HowItWorksSection() {
  const t = useTranslations('landing');

  const steps = [
    { key: 'connect', icon: Package, step: '01' },
    { key: 'analyze', icon: Zap,     step: '02' },
    { key: 'pilot',   icon: TrendingUp, step: '03' },
  ];

  return (
    <section id="how-it-works" className="py-14 sm:py-24 bg-slate-50/60">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-10 sm:mb-16">
          <h2 className="text-2xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mb-3">
            {t('howItWorks.title')}
          </h2>
          <p className="text-slate-500 text-sm sm:text-lg">{t('howItWorks.subtitle')}</p>
        </div>

        {/* Layout mobile : colonne avec ligne de connexion visuelle */}
        {/* Layout desktop : 3 colonnes avec ligne horizontale */}
        <div className="relative">

          {/* Ligne horizontale — desktop uniquement, basée sur le centre des icônes */}
          <div
            aria-hidden="true"
            className="hidden md:block absolute top-8 left-[calc(16.67%+2rem)] right-[calc(16.67%+2rem)] h-px bg-gradient-to-r from-slate-200 via-primary/30 to-slate-200"
          />

          <div className="grid md:grid-cols-3 gap-0 md:gap-10">
            {steps.map(({ key, icon: Icon, step }, i) => (
              <div key={key} className="flex md:flex-col items-start md:items-start gap-4 md:gap-0">

                {/* Colonne gauche mobile : icône + ligne verticale */}
                <div className="flex flex-col items-center md:block">
                  <div className="relative shrink-0">
                    <div className="w-16 h-16 rounded-2xl bg-white border-2 border-slate-200 flex items-center justify-center shadow-sm">
                      <Icon className="h-7 w-7 text-primary" />
                    </div>
                    <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-primary text-white text-[10px] font-bold flex items-center justify-center shadow-sm">
                      {step}
                    </div>
                  </div>
                  {/* Ligne verticale entre les étapes sur mobile */}
                  {i < steps.length - 1 && (
                    <div
                      aria-hidden="true"
                      className="md:hidden w-px flex-1 min-h-[40px] bg-gradient-to-b from-primary/20 to-transparent mt-3"
                    />
                  )}
                </div>

                {/* Texte */}
                <div className="flex-1 pb-8 md:pb-0 md:mt-5">
                  <h3 className="text-sm sm:text-base font-bold text-slate-900 mb-1.5">
                    {t(`howItWorks.steps.${key}.title`)}
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed">
                    {t(`howItWorks.steps.${key}.desc`)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Integrations Strip ───────────────────────────────────────────────────────

function IntegrationsSection() {
  const t = useTranslations('landing');

  const platforms = ['Shopify', 'WooCommerce', 'Amazon', 'CSV / Excel'];

  return (
    <section className="py-10 sm:py-14 border-y border-slate-100">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <p className="text-center text-[10px] sm:text-xs font-bold text-slate-400 uppercase tracking-widest mb-5 sm:mb-6">
          {t('integrations.label')}
        </p>
        <div className="flex flex-wrap justify-center gap-2 sm:gap-4">
          {platforms.map((p) => (
            <div
              key={p}
              className="px-4 sm:px-5 py-2 sm:py-2.5 bg-white border border-slate-200 rounded-full text-xs sm:text-sm font-semibold text-slate-600 shadow-sm"
            >
              {p}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── CTA Section ──────────────────────────────────────────────────────────────

function CtaSection() {
  const t = useTranslations('landing');

  return (
    <section className="py-14 sm:py-24">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="relative overflow-hidden bg-primary rounded-2xl sm:rounded-3xl px-6 py-12 sm:px-12 sm:py-20 text-center">
          {/* Décorations internes */}
          <div aria-hidden="true" className="absolute inset-0 overflow-hidden">
            <div className="absolute top-0 left-1/4 w-48 sm:w-64 h-48 sm:h-64 bg-white/5 rounded-full blur-3xl" />
            <div className="absolute bottom-0 right-1/4 w-48 sm:w-64 h-48 sm:h-64 bg-white/5 rounded-full blur-3xl" />
          </div>

          <div className="relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/15 rounded-full mb-5 sm:mb-6">
              <CheckCircle2 className="h-3.5 w-3.5 text-white shrink-0" />
              <span className="text-xs font-semibold text-white">{t('cta.badge')}</span>
            </div>

            {/* Titre — taille réduite sur mobile pour le texte long */}
            <h2 className="text-2xl sm:text-3xl lg:text-5xl font-extrabold text-white leading-[1.15] tracking-tight mb-4 max-w-2xl mx-auto">
              {t('cta.title')}
            </h2>
            <p className="text-white/70 text-sm sm:text-lg max-w-xl mx-auto mb-8 leading-relaxed">
              {t('cta.subtitle')}
            </p>

            <Link
              href="/register"
              className="inline-flex items-center justify-center gap-2 w-full sm:w-auto px-8 py-4 text-sm font-bold text-primary bg-white hover:bg-slate-50 rounded-xl transition-all shadow-lg hover:-translate-y-0.5 active:scale-[0.98] min-h-[52px]"
            >
              {t('cta.button')}
              <ArrowRight className="h-4 w-4 shrink-0" />
            </Link>

            <p className="text-white/50 text-xs mt-4">{t('cta.noCb')}</p>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Footer ───────────────────────────────────────────────────────────────────

function LandingFooter() {
  const t = useTranslations('landing');
  const tLegal = useTranslations('legal');

  return (
    <footer className="border-t border-slate-100 bg-slate-50/50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-5 sm:gap-4">

          {/* Logo */}
          <div className="flex items-center gap-2 shrink-0">
            <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center text-white text-sm font-bold">
              道
            </div>
            <span className="text-sm font-bold text-slate-800">Michi</span>
          </div>

          {/* Liens légaux — touch targets agrandis */}
          <div className="flex items-center gap-1 flex-wrap justify-center">
            {[
              { href: '/legal/privacy', label: tLegal('privacy') },
              { href: '/legal/terms', label: tLegal('terms') },
              { href: '/pricing', label: t('nav.pricing') },
            ].map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="px-3 py-2 text-xs text-slate-500 hover:text-slate-800 transition-colors rounded-lg hover:bg-slate-100 min-h-[44px] flex items-center"
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Copyright */}
          <p className="text-xs text-slate-400 shrink-0">{t('footer.rights')}</p>
        </div>
      </div>
    </footer>
  );
}

// ─── Main Export ──────────────────────────────────────────────────────────────

export function LandingPage() {
  return (
    <main className="min-h-screen bg-white">
      <LandingNav />
      <HeroSection />
      <StatsSection />
      <FeaturesSection />
      <IntegrationsSection />
      <HowItWorksSection />
      <CtaSection />
      <LandingFooter />
    </main>
  );
}
