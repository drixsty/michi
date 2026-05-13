'use client';

import React from 'react';
import { useTranslations } from 'next-intl';
import { Lock, ArrowLeft, Eye, ShieldCheck, Database, Fingerprint, Trash2, Globe, ExternalLink } from 'lucide-react';
import Link from 'next/link';

export default function PrivacyPage() {
  const t = useTranslations('legal');

  const sections = [
    { id: 'transparency', title: '1. Transparence', icon: <Eye className="w-4 h-4" /> },
    { id: 'security', title: '2. Sécurité', icon: <ShieldCheck className="w-4 h-4" /> },
    { id: 'usage', title: '3. Utilisation', icon: <Database className="w-4 h-4" /> },
    { id: 'rights', title: '4. Vos Droits', icon: <Fingerprint className="w-4 h-4" /> },
    { id: 'cookies', title: '5. Cookies', icon: <Globe className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen bg-[#F9FAFB] selection:bg-primary/10">
      {/* HEADER NAV */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link 
            href="/login" 
            className="inline-flex items-center gap-2 text-[13px] font-bold text-slate-500 hover:text-emerald-600 transition-all group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            Retour
          </Link>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold text-[10px]">
              <Lock className="w-3.5 h-3.5" />
            </div>
            <span className="text-[12px] font-bold text-slate-900 tracking-tight">Michi Privacy</span>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-12 lg:py-20 flex flex-col lg:flex-row gap-8 lg:gap-12">
        
        {/* SIDEBAR NAVIGATION (DESKTOP) */}
        <aside className="hidden lg:block w-64 shrink-0 h-fit sticky top-32">
          <div className="space-y-1">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-4 px-3">Sections</p>
            {sections.map((sec) => (
              <a 
                key={sec.id}
                href={`#${sec.id}`}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-bold text-slate-500 hover:bg-white hover:text-emerald-600 hover:shadow-sm border border-transparent transition-all"
              >
                {sec.icon}
                {sec.title}
              </a>
            ))}
          </div>
          
          <div className="mt-8 p-4 bg-emerald-50 rounded-lg border border-emerald-100 space-y-3">
            <p className="text-[12px] font-bold text-emerald-700 text-center">Data Protection Officer</p>
            <p className="text-[11px] text-emerald-600/70 leading-relaxed font-medium text-center italic">Notre DPO est à votre disposition pour toute demande relative à vos données personnelles.</p>
            <button className="w-full h-8 bg-white border border-emerald-200 rounded-lg text-[11px] font-bold text-emerald-700 hover:bg-emerald-50 transition-all flex items-center justify-center gap-1 shadow-sm">
              dpo@michi.com
            </button>
          </div>
        </aside>

        {/* CONTENT */}
        <main className="flex-1 max-w-3xl">
          <div className="space-y-4 mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-100 text-emerald-700 text-[10px] font-bold rounded-lg uppercase tracking-wider">
              <ShieldCheck className="w-3 h-3" />
              Confidentialité Garantie
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-slate-900 tracking-tight leading-tight">
              {t('privacy')}
            </h1>
            <div className="flex items-center gap-4 text-[13px] text-slate-400 font-medium">
              <span>Version 2.0</span>
              <span className="w-1 h-1 rounded-full bg-slate-300" />
              <span>Dernière mise à jour : 24 Avril 2026</span>
            </div>
          </div>

          <div className="space-y-16">
            <section id="transparency" className="scroll-mt-32 space-y-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3 flex-wrap">
                <span className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center text-xs font-bold shadow-lg shadow-emerald-100">1</span>
                Transparence des données
              </h2>
              <div className="p-6 bg-white border border-slate-200 rounded-lg shadow-sm space-y-4 leading-relaxed text-slate-600">
                <p className="font-bold text-slate-900 italic">Nous ne vendons jamais vos données à des tiers.</p>
                <p>
                  Michi 道 s'engage à une transparence totale sur la collecte et l'utilisation de vos informations. Nous collectons uniquement les données nécessaires à la fourniture de nos services de prévision, telles que vos coordonnées professionnelles et les métadonnées de vos boutiques connectées.
                </p>
              </div>
            </section>

            <section id="security" className="scroll-mt-32 space-y-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3 flex-wrap">
                <span className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center text-xs font-bold shadow-lg shadow-emerald-100">2</span>
                Sécurité et Chiffrement
              </h2>
              <div className="p-6 bg-white border border-slate-200 rounded-lg shadow-sm space-y-6 leading-relaxed text-slate-600">
                <p>
                  Nous utilisons des protocoles de sécurité de niveau bancaire pour protéger vos informations stratégiques.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-100 flex gap-3 items-start">
                    <Lock className="w-5 h-5 text-emerald-600 shrink-0" />
                    <div>
                      <p className="text-[12px] font-bold text-slate-900 mb-1">AES-256</p>
                      <p className="text-[11px] text-slate-500 font-medium leading-tight">Chiffrement systématique de vos clés API et tokens de connexion.</p>
                    </div>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-100 flex gap-3 items-start">
                    <Fingerprint className="w-5 h-5 text-emerald-600 shrink-0" />
                    <div>
                      <p className="text-[12px] font-bold text-slate-900 mb-1">Bcrypt</p>
                      <p className="text-[11px] text-slate-500 font-medium leading-tight">Hachage robuste de vos mots de passe avec sel cryptographique.</p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section id="usage" className="scroll-mt-32 space-y-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3 flex-wrap">
                <span className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center text-xs font-bold shadow-lg shadow-emerald-100">3</span>
                Utilisation des données
              </h2>
              <div className="p-6 bg-white border border-slate-200 rounded-lg shadow-sm space-y-4 leading-relaxed text-slate-600">
                <p>
                  Les historiques de vente importés sont traités exclusivement pour alimenter votre moteur de prévision personnalisé.
                </p>
                <div className="bg-emerald-50/50 p-4 rounded-lg border border-emerald-100 text-[13px] text-emerald-800 font-medium">
                  Michi 道 n'utilise pas vos données pour entraîner des modèles IA transversaux sans votre accord explicite, garantissant ainsi le maintien de votre avantage concurrentiel.
                </div>
              </div>
            </section>

            <section id="rights" className="scroll-mt-32 space-y-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3 flex-wrap">
                <span className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center text-xs font-bold shadow-lg shadow-emerald-100">4</span>
                Vos Droits (RGPD)
              </h2>
              <div className="p-6 bg-white border border-slate-200 rounded-lg shadow-sm space-y-8 text-slate-600">
                <div className="grid grid-cols-1 gap-6">
                  <div className="flex gap-4">
                    <div className="w-10 h-10 rounded-lg bg-slate-50 flex items-center justify-center shrink-0 border border-slate-100 font-bold text-slate-900 text-sm">01</div>
                    <div className="space-y-1">
                      <p className="text-[14px] font-bold text-slate-900">Droit d'accès et Portabilité</p>
                      <p className="text-[12px] leading-relaxed text-slate-500 font-medium">Vous pouvez exporter l'intégralité de vos données personnelles et commerciales au format JSON directement depuis votre profil utilisateur.</p>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className="w-10 h-10 rounded-lg bg-slate-50 flex items-center justify-center shrink-0 border border-slate-100 font-bold text-slate-900 text-sm">02</div>
                    <div className="space-y-1">
                      <p className="text-[14px] font-bold text-slate-900">Droit à l'oubli</p>
                      <p className="text-[12px] leading-relaxed text-slate-500 font-medium">La suppression de votre compte entraîne l'effacement immédiat et irréversible de toutes vos données en cascade sur nos serveurs de production.</p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section id="cookies" className="scroll-mt-32 space-y-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3 flex-wrap">
                <span className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center text-xs font-bold shadow-lg shadow-emerald-100">5</span>
                Gestion des Cookies
              </h2>
              <div className="p-6 bg-white border border-slate-200 rounded-lg shadow-sm space-y-4 leading-relaxed text-slate-600">
                <p>
                  Nous utilisons des cookies pour améliorer votre navigation et analyser la performance de notre plateforme.
                </p>
                <div className="flex flex-col md:flex-row gap-4 pt-2">
                  <button 
                    onClick={() => window.dispatchEvent(new Event('michi_open_cookie_settings'))}
                    className="flex-1 min-h-[44px] bg-slate-900 text-white rounded-lg text-[12px] font-bold hover:bg-slate-800 transition-all"
                  >
                    Gérer mes préférences
                  </button>
                  <Link href="/legal/terms" className="flex-1 min-h-[44px] border border-slate-200 text-slate-600 rounded-lg text-[12px] font-bold hover:bg-slate-50 flex items-center justify-center gap-2 transition-all">
                    Conditions d'Utilisation
                    <ExternalLink className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            </section>
          </div>

          <footer className="mt-16 sm:mt-32 py-8 sm:py-12 border-t border-slate-200 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold text-[12px]">
                <Lock className="w-4 h-4" />
              </div>
              <span className="text-sm font-bold text-slate-900">Michi Privacy Protocol</span>
            </div>
            <p className="text-[12px] text-slate-400 font-medium">© 2026 Michi Inc. Privacy First Policy.</p>
          </footer>
        </main>
      </div>
    </div>
  );
}
