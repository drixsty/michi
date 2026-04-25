'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@apollo/client';
import { Check, Loader2, ArrowRight } from 'lucide-react';
import { CREATE_CHECKOUT_SESSION } from '@/graphql/mutations/createCheckoutSession';
import { cn } from '@/lib/utils';
import { useTranslations } from 'next-intl';

const plans = [
  {
    id: 'BASIC',
    price: '0€',
    popular: false,
  },
  {
    id: 'PRO',
    price: '49€',
    popular: true,
  },
  {
    id: 'ENTERPRISE',
    price: '99€',
    popular: false,
  }
];

export default function PricingPage() {
  const t = useTranslations('pricing');
  const router = useRouter();
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);

  const [createCheckout, { loading }] = useMutation(CREATE_CHECKOUT_SESSION, {
    onCompleted: (data) => {
      const url = data.createCheckoutSession;
      if (url) {
        window.location.href = url; // Redirect to Stripe
      }
    },
    onError: (err) => {
      console.error('Checkout error:', err);
    }
  });

  const handleSelectPlan = (planId: string) => {
    setSelectedPlan(planId);
    createCheckout({
      variables: {
        plan: planId,
        successUrl: `${window.location.origin}/dashboard?onboarding=true`,
        cancelUrl: `${window.location.origin}/pricing`
      }
    });
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center py-8 px-4 font-sans justify-center">
      <div className="text-center mb-8 space-y-2">
        <div className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-primary text-white font-bold text-lg shadow-lg shadow-primary/20 mb-2">
          道
        </div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">{t('title')}</h1>
        <p className="text-base text-slate-500 max-w-xl mx-auto">
          {t('subtitle')}
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6 max-w-6xl w-full">
        {plans.map((plan) => {
          const planKey = plan.id.toLowerCase();
          // Type casting for next-intl array retrieval if needed, 
          // but here we can just map the features manually
          const features = t.raw(`plans.${planKey}.features`) as string[];

          return (
            <div 
              key={plan.id}
              className={cn(
                "relative bg-white rounded-lg p-6 border flex flex-col transition-all duration-300",
                plan.popular ? "border-primary shadow-xl scale-[1.02] z-10" : "border-slate-200 shadow-sm hover:shadow-md"
              )}
            >
              {plan.popular && (
                <div className="absolute -top-3 inset-x-0 flex justify-center">
                  <span className="bg-primary text-white text-[9px] font-bold uppercase tracking-wider py-0.5 px-3 rounded-full">
                    {t('popular')}
                  </span>
                </div>
              )}
              
              <div className="mb-4">
                <h3 className="text-lg font-bold text-slate-900">{t(`plans.${planKey}.name`)}</h3>
                <div className="mt-1 flex items-baseline">
                  <span className="text-3xl font-extrabold text-slate-900">{plan.price}</span>
                  <span className="text-slate-500 text-xs ml-1">{t('period')}</span>
                </div>
                <p className="text-xs text-slate-500 mt-1 min-h-[32px]">{t(`plans.${planKey}.description`)}</p>
              </div>
              
              <ul className="space-y-2 mb-6 flex-1">
                {features.map((feat, idx) => (
                  <li key={idx} className="flex items-start text-[13px] text-slate-700">
                    <Check className="h-3.5 w-3.5 text-primary shrink-0 mr-2.5 mt-0.5" />
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
              
              <button
                onClick={() => handleSelectPlan(plan.id)}
                disabled={loading}
                className={cn(
                  "w-full py-2.5 rounded-lg font-bold text-[13px] transition-all flex items-center justify-center gap-2",
                  plan.popular 
                    ? "bg-primary text-white hover:bg-primary/90 shadow-lg shadow-primary/20" 
                    : "bg-slate-100 text-slate-900 hover:bg-slate-200"
                )}
              >
                {loading && selectedPlan === plan.id ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    {t('select')}
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
