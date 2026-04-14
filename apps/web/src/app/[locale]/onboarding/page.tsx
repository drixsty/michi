'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, gql } from '@apollo/client';
import { 
  Building2, 
  CheckCircle2, 
  ArrowRight, 
  Rocket, 
  ShieldCheck, 
  Zap,
  ChevronLeft,
  Sparkles,
  Layout,
  CreditCard
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useStore } from '@/context/StoreContext';
import { LoadingOverlay } from '@/components/ui/LoadingOverlay';

const CREATE_ORGANIZATION = gql`
  mutation CreateOrganization($name: String!, $plan: String!) {
    createOrganization(name: $name, plan: $plan) {
      token
      user {
        id
        currentOrganizationId
      }
    }
  }
`;

const CREATE_CHECKOUT_SESSION = gql`
  mutation CreateCheckoutSession($plan: String!, $successUrl: String!, $cancelUrl: String!) {
    createCheckoutSession(plan: $plan, successUrl: $successUrl, cancelUrl: $cancelUrl)
  }
`;

const PLANS = [
  {
    id: 'BASIC',
    name: 'Basic',
    price: '0€',
    description: 'Parfait pour débuter et valider vos premiers pas.',
    features: ['100 SKUs maximum', '1 Boutique Shopify', 'Analyses basiques'],
    icon: Zap,
    color: 'text-blue-500',
    bg: 'bg-blue-50'
  },
  {
    id: 'PRO',
    name: 'Pro',
    price: '49€',
    description: 'L\'expérience complète Michi pour les marchands en croissance.',
    features: ['Produits illimités', 'Prévisions IA avancées', 'Multi-Canaux (Amazon/Woo)', 'Alertes temps réel'],
    icon: Rocket,
    color: 'text-primary',
    bg: 'bg-primary/5',
    popular: true
  },
  {
    id: 'ENTERPRISE',
    name: 'Enterprise',
    price: 'Sur devis',
    description: 'Sur mesure pour les grands comptes et marques établies.',
    features: ['Multi-Boutiques illimitées', 'Support Dédié 24/7', 'SLA Garanti', 'Accès API'],
    icon: ShieldCheck,
    color: 'text-amber-500',
    bg: 'bg-amber-50'
  }
];

export default function OnboardingPage() {
  const router = useRouter();
  const { user, refreshUser } = useStore();
  const [orgName, setOrgName] = useState('');
  const [selectedPlan, setSelectedPlan] = useState('BASIC');
  const [step, setStep] = useState(1); // 1: Org Name, 2: Plan Selection
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [createCheckoutSession, { loading: checkoutLoading }] = useMutation(CREATE_CHECKOUT_SESSION);

  const [createOrganization, { loading: creatingOrg }] = useMutation(CREATE_ORGANIZATION, {
    onCompleted: async (data) => {
      const { token } = data.createOrganization;
      localStorage.setItem('michi_token', token);
      
      if (selectedPlan === 'BASIC') {
        refreshUser();
        window.location.href = '/dashboard?welcome=true';
      } else {
        try {
          const { data: checkoutData } = await createCheckoutSession({
            variables: {
              plan: selectedPlan,
              successUrl: `${window.location.origin}/dashboard?subscription=success`,
              cancelUrl: `${window.location.origin}/onboarding?subscription=cancel`
            }
          });
          if (checkoutData?.createCheckoutSession) {
            window.location.href = checkoutData.createCheckoutSession;
          }
        } catch (err) {
          setErrorMessage("Erreur de paiement. Veuillez réessayer.");
        }
      }
    },
    onError: (err) => {
      setErrorMessage(err.message || "Une erreur est survenue.");
    }
  });

  const handleNext = () => {
    if (step === 1 && orgName.trim().length > 2) {
      setStep(2);
    }
  };

  const handleFinish = async () => {
    if (orgName.trim().length <= 2) return;
    await createOrganization({
      variables: {
        name: orgName,
        plan: selectedPlan
      }
    });
  };

  const loading = creatingOrg || checkoutLoading;

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 overflow-hidden bg-slate-50">
      {/* Immersive Background - Light Theme */}
      <div className="absolute inset-0 z-0 opacity-100 transition-opacity duration-1000">
        <img 
          src="/onboarding-bg-light.png" 
          alt="background" 
          className="w-full h-full object-cover grayscale-[0.2] opacity-80"
        />
        <div className="absolute inset-0 bg-white/40" />
      </div>

      {loading && <LoadingOverlay message="Configuration de votre espace Michi..." />}
      
      <div className="w-full max-w-4xl z-10 grid grid-cols-1 lg:grid-cols-12 gap-0 bg-white/70 backdrop-blur-3xl border border-white rounded-2xl shadow-2xl shadow-slate-200/50 overflow-hidden min-h-[500px]">
        
        {/* Left Side: Brand & Progress (4 cols) - Light Premium */}
        <div className="lg:col-span-4 bg-slate-50/50 p-8 flex flex-col justify-between border-r border-slate-200/50">
          <div className="space-y-10">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center font-bold text-lg text-white shadow-lg shadow-primary/20">
                道
              </div>
              <span className="text-lg font-bold text-slate-900 tracking-tight">Michi</span>
            </div>
            
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-slate-900 leading-tight tracking-tight">
                Initialisez <br/> 
                votre espace.
              </h2>
              <p className="text-slate-500 text-[13px] leading-relaxed">
                Connectez vos sources de données et laissez notre IA optimiser vos stocks.
              </p>
            </div>
          </div>

          <div className="space-y-4 mt-8">
             <div className="relative space-y-6">
               <div className="absolute left-[9px] top-2 bottom-2 w-px bg-slate-200" />
               {[
                 { id: 1, label: "Identité", description: "Nom de l'espace" },
                 { id: 2, label: "Forfait", description: "Capacité de calcul" }
               ].map((s) => (
                 <div key={s.id} className="relative flex items-center gap-3.5 group">
                   <div className={cn(
                     "w-[20px] h-[20px] rounded-full flex items-center justify-center text-[9px] font-bold border transition-all z-10",
                     step === s.id ? "bg-primary border-primary text-white shadow-md shadow-primary/20" : 
                     step > s.id ? "bg-emerald-500 border-emerald-500 text-white" : "bg-white border-slate-200 text-slate-300"
                   )}>
                     {step > s.id ? <CheckCircle2 className="h-2.5 w-2.5" /> : s.id}
                   </div>
                   <div className="flex flex-col">
                     <span className={cn(
                       "text-[12px] font-bold",
                       step >= s.id ? "text-slate-900" : "text-slate-300"
                     )}>
                       {s.label}
                     </span>
                     <span className="text-[10px] text-slate-400 font-medium whitespace-nowrap">
                       {s.description}
                     </span>
                   </div>
                 </div>
               ))}
             </div>
          </div>
        </div>

        {/* Right Side: Content Area (8 cols) */}
        <div className="lg:col-span-8 p-8 lg:p-12 flex flex-col justify-center relative overflow-y-auto">
          
          <div className="space-y-8">
            {errorMessage && (
              <div className="animate-in slide-in-from-top-2 duration-300">
                <div className="bg-red-50 border border-red-100 rounded-lg p-3 flex items-center gap-3 shadow-sm">
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse shrink-0" />
                  <p className="text-red-600 text-[12px] font-bold leading-tight">
                    {errorMessage}
                  </p>
                </div>
              </div>
            )}

            {step === 1 && (
            <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
              <div className="space-y-3">
                <div className="inline-flex items-center gap-2 px-2.5 py-0.5 bg-slate-100 border border-slate-200 rounded-md text-[10px] font-bold text-slate-500">
                  Nom de l'organisation
                </div>
                <h3 className="text-3xl font-bold text-slate-900 tracking-tight">
                  Quel est le nom <br/> de votre boutique ?
                </h3>
              </div>

              <div className="space-y-4">
                <input 
                  type="text" 
                  placeholder="ex: Bloom Industries"
                  value={orgName}
                  data-testid="org-name-input"
                  onChange={(e) => setOrgName(e.target.value)}
                  autoFocus
                  className="w-full h-14 px-6 bg-slate-50/50 border border-slate-200 rounded-xl text-xl text-slate-900 placeholder:text-slate-300 focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/5 transition-all font-semibold tracking-tight"
                />
                <div className="flex items-center gap-2 text-[10px] text-slate-400">
                  <CheckCircle2 className={cn("h-3 w-3", orgName.length >= 3 ? "text-emerald-500" : "text-slate-200")} />
                  À moins de 3 caractères requis.
                </div>
              </div>

              <button 
                onClick={handleNext}
                disabled={orgName.trim().length <= 2}
                data-testid="onboarding-next"
                className="w-full h-14 bg-slate-900 text-white rounded-xl font-bold text-md hover:bg-slate-800 transition-all disabled:opacity-50 flex items-center justify-center gap-2 shadow-xl shadow-slate-900/10"
              >
                Continuer
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
              <div className="space-y-2">
                <div className="inline-flex items-center gap-2 px-2.5 py-0.5 bg-slate-100 border border-slate-200 rounded-md text-[10px] font-bold text-slate-500">
                  Sélection du plan
                </div>
                <h3 className="text-3xl font-bold text-slate-900 tracking-tight">
                  Choisissez un forfait.
                </h3>
              </div>

              <div className="grid grid-cols-1 gap-2.5">
                {PLANS.map((plan) => (
                  <button
                    key={plan.id}
                    onClick={() => setSelectedPlan(plan.id)}
                    className={cn(
                      "relative flex items-center gap-5 p-4 rounded-xl border transition-all text-left",
                      selectedPlan === plan.id 
                        ? "border-primary bg-primary/5 shadow-[0_0_20px_rgba(var(--primary-rgb),0.05)]" 
                        : "border-slate-100 bg-white hover:border-slate-200"
                    )}
                  >
                    <div className={cn("p-2.5 rounded-lg shrink-0 transition-all shadow-sm", plan.bg, plan.color)}>
                      <plan.icon className={cn("h-5 w-5", selectedPlan === plan.id ? "scale-110" : "")} />
                    </div>
                    
                    <div className="flex-1 min-w-0 pr-16 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900">{plan.name}</span>
                        {plan.popular && <span className="text-[8px] bg-primary text-white px-1.5 py-0.5 rounded uppercase font-bold tracking-wider">Recommandé</span>}
                      </div>
                      <p className="text-slate-500 truncate mt-0.5 font-medium">{plan.description}</p>
                    </div>

                    <div className="absolute right-6 text-right">
                       <span className="text-sm font-bold text-slate-900">{plan.price}</span>
                       <p className="text-[8px] text-slate-400 font-bold uppercase">/ mois</p>
                    </div>

                    {selectedPlan === plan.id && (
                      <div className="absolute top-1/2 -translate-y-1/2 right-2">
                        <CheckCircle2 className="h-3 w-3 text-primary" />
                      </div>
                    )}
                  </button>
                ))}
              </div>

              <div className="flex gap-3 pt-2">
                <button 
                  onClick={() => setStep(1)}
                  className="h-12 px-5 bg-white border border-slate-200 text-slate-500 rounded-xl font-bold text-xs hover:bg-slate-50 transition-all"
                >
                  Retour
                </button>
                <button 
                  onClick={handleFinish}
                  data-testid="onboarding-finish"
                  className="flex-1 h-12 bg-slate-900 text-white rounded-xl font-bold text-[15px] hover:bg-slate-800 transition-all flex items-center justify-center gap-2 shadow-xl shadow-slate-900/10"
                >
                  {selectedPlan === 'BASIC' ? "Activer l'espace" : "Finaliser sur Stripe"}
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
          </div>
        </div>
      </div>

      {/* Footer minimal info */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-4 text-[9px] font-bold text-slate-400 uppercase tracking-[0.2em] pointer-events-none">
        <span className="capitalize">Stripe secure</span>
        <div className="w-1 h-1 rounded-full bg-slate-200" />
        <span className="capitalize">Michi 道 v2.5</span>
      </div>
    </div>
  );
}
