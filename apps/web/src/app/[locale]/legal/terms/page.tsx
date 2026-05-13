'use client';

import React from 'react';
import { useTranslations } from 'next-intl';
import { Shield, ArrowLeft, BookOpen, Scale, UserCheck, FileText, ExternalLink } from 'lucide-react';
import Link from 'next/link';

export default function TermsPage() {
  const t = useTranslations('legal');

  const sections = [
    { id: 'acceptance', title: '1. Acceptation', icon: <UserCheck className="w-4 h-4" /> },
    { id: 'service', title: '2. Le Service', icon: <BookOpen className="w-4 h-4" /> },
    { id: 'accounts', title: '3. Comptes', icon: <Shield className="w-4 h-4" /> },
    { id: 'intellectual', title: '4. Propriété', icon: <Scale className="w-4 h-4" /> },
    { id: 'liability', title: '5. Responsabilité', icon: <FileText className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen bg-[#F9FAFB] selection:bg-primary/10">
      {/* HEADER NAV */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link 
            href="/login" 
            className="inline-flex items-center gap-2 text-[13px] font-bold text-slate-500 hover:text-primary transition-all group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            Retour
          </Link>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-[10px]">
              道
            </div>
            <span className="text-[12px] font-bold text-slate-900 tracking-tight">Michi Legal</span>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-12 lg:py-20 flex flex-col lg:flex-row gap-8 lg:gap-12">
        
        {/* SIDEBAR NAVIGATION (DESKTOP) */}
        <aside className="hidden lg:block w-64 shrink-0 h-fit sticky top-32">
          <div className="space-y-1">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-4 px-3">Sommaire</p>
            {sections.map((sec) => (
              <a 
                key={sec.id}
                href={`#${sec.id}`}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-bold text-slate-500 hover:bg-white hover:text-primary hover:shadow-sm border border-transparent transition-all"
              >
                {sec.icon}
                {sec.title}
              </a>
            ))}
          </div>
          
          <div className="mt-8 p-4 bg-primary/5 rounded-lg border border-primary/10 space-y-3">
            <p className="text-[12px] font-bold text-primary">Besoin d'aide ?</p>
            <p className="text-[11px] text-slate-500 leading-relaxed font-medium">Contactez notre équipe juridique pour toute question relative à nos conditions.</p>
            <button className="text-[11px] font-bold text-primary flex items-center gap-1 hover:underline">
              legal@michi.com
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>
        </aside>

        {/* CONTENT */}
        <main className="flex-1 max-w-3xl">
          <div className="space-y-4 mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary text-[10px] font-bold rounded-lg uppercase tracking-wider">
              <Scale className="w-3 h-3" />
              Document Juridique
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-slate-900 tracking-tight leading-tight">
              {t('terms')}
            </h1>
            <div className="flex items-center gap-4 text-[13px] text-slate-400 font-medium">
              <span>Version 2.0</span>
              <span className="w-1 h-1 rounded-full bg-slate-300" />
              <span>Dernière mise à jour : 24 Avril 2026</span>
            </div>
          </div>

          <div className="space-y-16">
            <section id="acceptance" className="scroll-mt-32 space-y-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3 flex-wrap">
                <span className="w-8 h-8 rounded-lg bg-slate-900 text-white flex items-center justify-center text-xs font-bold shadow-lg shadow-slate-200">1</span>
                Acceptation des conditions
              </h2>
              <div className="p-6 bg-white border border-slate-200 rounded-lg shadow-sm space-y-4 leading-relaxed text-slate-600">
                <p className="font-bold text-slate-900">En utilisant Michi 道, vous concluez un accord juridiquement contraignant.</p>
                <p>
                  Les présentes Conditions d'Utilisation régissent votre accès et votre utilisation de la plateforme Michi 道. En créant un compte ou en accédant au Service, vous reconnaissez avoir lu, compris et accepté d'être lié par ces termes. Si vous agissez au nom d'une entreprise, vous garantissez avoir l'autorité nécessaire pour engager ladite entité.
                </p>
              </div>
            </section>

            <section id="service" className="scroll-mt-32 space-y-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3 flex-wrap">
                <span className="w-8 h-8 rounded-lg bg-slate-900 text-white flex items-center justify-center text-xs font-bold shadow-lg shadow-slate-200">2</span>
                Nature du Service
              </h2>
              <div className="p-6 bg-white border border-slate-200 rounded-lg shadow-sm space-y-4 leading-relaxed text-slate-600">
                <p>
                  Michi 道 fournit une solution logicielle en tant que service (SaaS) dédiée à l'optimisation de la supply chain et au forecasting omnicanal. 
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                    <p className="text-[12px] font-bold text-slate-900 mb-1">Inclus</p>
                    <p className="text-[11px] text-slate-500 font-medium italic">Analyse IA, synchronisation API, rapports stratégiques et alertes prédictives.</p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                    <p className="text-[12px] font-bold text-slate-900 mb-1">Exclus</p>
                    <p className="text-[11px] text-slate-500 font-medium italic">Conseil en gestion physique des stocks, exécution logistique ou garanties de vente.</p>
                  </div>
                </div>
              </div>
            </section>

            <section id="accounts" className="scroll-mt-32 space-y-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3 flex-wrap">
                <span className="w-8 h-8 rounded-lg bg-slate-900 text-white flex items-center justify-center text-xs font-bold shadow-lg shadow-slate-200">3</span>
                Gestion et Sécurité des Comptes
              </h2>
              <div className="p-6 bg-white border border-slate-200 rounded-lg shadow-sm space-y-4 leading-relaxed text-slate-600">
                <p>
                  L'intégrité de votre compte est une priorité absolue. Vous êtes seul responsable de la protection de vos identifiants de connexion.
                </p>
                <div className="flex gap-4 items-start p-4 bg-amber-50 rounded-lg border border-amber-100">
                   <Shield className="w-5 h-5 text-amber-600 shrink-0 mt-1" />
                   <div className="space-y-1">
                     <p className="text-[12px] font-bold text-amber-900">Standard de Sécurité</p>
                     <p className="text-[11px] text-amber-700 leading-relaxed font-medium italic">
                       Nous exigeons l'utilisation de mots de passe complexes et recommandons vivement l'activation de la Double Authentification (2FA). Michi 道 décline toute responsabilité en cas d'accès non autorisé résultant d'une négligence de sécurité de votre part.
                     </p>
                   </div>
                </div>
              </div>
            </section>

            <section id="intellectual" className="scroll-mt-32 space-y-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3 flex-wrap">
                <span className="w-8 h-8 rounded-lg bg-slate-900 text-white flex items-center justify-center text-xs font-bold shadow-lg shadow-slate-200">4</span>
                Propriété Intellectuelle
              </h2>
              <div className="p-6 bg-white border border-slate-200 rounded-lg shadow-sm space-y-4 leading-relaxed text-slate-600">
                <p>
                  Tous les éléments constituant le Service, y compris mais sans s'y limiter, les interfaces graphiques, les logos, les algorithmes de prévision, le code source et les marques, sont la propriété exclusive de Michi Inc.
                </p>
                <p className="bg-slate-50 p-4 rounded-lg text-[13px] italic border-l-4 border-primary">
                  "Michi 道" est une marque déposée. Toute reproduction, modification ou distribution non autorisée du Service fera l'objet de poursuites judiciaires.
                </p>
              </div>
            </section>

            <section id="liability" className="scroll-mt-32 space-y-6">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3 flex-wrap">
                <span className="w-8 h-8 rounded-lg bg-slate-900 text-white flex items-center justify-center text-xs font-bold shadow-lg shadow-slate-200">5</span>
                Limitation de Responsabilité
              </h2>
              <div className="p-6 bg-white border border-slate-200 rounded-lg shadow-sm space-y-4 leading-relaxed text-slate-600">
                <p className="font-bold text-slate-900">Le Service est fourni "tel quel" sans garantie de résultat commercial.</p>
                <p>
                  Bien que Michi 道 utilise des modèles d'IA de pointe pour assurer la précision des prévisions, les décisions commerciales finales incombent exclusivement à l'Utilisateur. Michi 道 ne pourra être tenu responsable des pertes de profits, d'opportunités commerciales ou de toute interruption d'activité liée à l'utilisation ou à l'impossibilité d'utiliser le Service.
                </p>
              </div>
            </section>
          </div>

          <footer className="mt-16 sm:mt-32 py-8 sm:py-12 border-t border-slate-200 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold text-[12px]">道</div>
              <span className="text-sm font-bold text-slate-900">Michi 道 Protocol</span>
            </div>
            <p className="text-[12px] text-slate-400 font-medium">© 2026 Michi Inc. Tous droits réservés.</p>
          </footer>
        </main>
      </div>
    </div>
  );
}
