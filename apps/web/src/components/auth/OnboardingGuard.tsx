'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { gql, useQuery } from '@apollo/client';
import { Loader2 } from 'lucide-react';

const GET_ONBOARDING_STATUS = gql`
  query GetOnboardingStatus {
    me {
      id
      hasOrganization
      emailVerifiedAt
    }
    currentOrganization {
      id
      plan
      subscriptionStatus
      trialEndsAt
      onboardingCompleted
    }
  }
`;

interface OnboardingGuardProps {
  children: React.ReactNode;
}

export function OnboardingGuard({ children }: OnboardingGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isChecking, setIsChecking] = useState(true);
  
  const { data, loading, error } = useQuery(GET_ONBOARDING_STATUS, {
    fetchPolicy: 'network-only' 
  });

  useEffect(() => {
    if (!loading) {
      if (data && !data.me) {
        // User not logged in
        const isAuthPage = pathname.includes('/login') || pathname.includes('/register');
        if (!isAuthPage) {
          router.replace('/login');
          return;
        }
      }

      if (data?.me) {
        const isEmailVerified = !!data.me.emailVerifiedAt;
        const isVerifyEmailPage = pathname.includes('/verify-email');

        // Force email verification if not verified
        if (!isEmailVerified && !isVerifyEmailPage) {
           router.replace('/verify-email');
           return;
        }

        if (!data.me.hasOrganization && !pathname.includes('/pricing') && !isVerifyEmailPage) {
           router.replace('/pricing');
           return;
        }
      }

      if (data?.currentOrganization) {
        const isCompleted = data.currentOrganization.onboardingCompleted;
        const hasPlan = !!data.currentOrganization.plan && data.currentOrganization.plan !== "";
        const subStatus = data.currentOrganization.subscriptionStatus;
        const trialEndsAt = data.currentOrganization.trialEndsAt;
        
        const isOnboardingPage = pathname.includes('/onboarding');
        const isPricingPage = pathname.includes('/pricing');
        
        // Check for trial expiration
        let isTrialExpired = false;
        if (subStatus === "TRIALING" && trialEndsAt) {
          if (new Date() > new Date(trialEndsAt)) {
            isTrialExpired = true;
          }
        }

        if (isTrialExpired && !isPricingPage) {
          router.replace('/pricing');
          return;
        }

        // Force pricing if no plan selected
        if (!hasPlan && !isPricingPage) {
           router.replace('/pricing');
           return;
        }

        if (!isCompleted && !isOnboardingPage && !isPricingPage) {
          router.replace('/onboarding');
        } else if (isCompleted && (isOnboardingPage || (isPricingPage && hasPlan && !isTrialExpired))) {
          router.replace('/dashboard');
        } else {
          // État valide : soit complété sur dashboard, soit non-complété sur onboarding, soit pricing (si trial expired)
          setIsChecking(false);
        }
      } else {
         // Pas d'organisation et on est bien sur /pricing (géré plus haut)
         if (pathname.includes('/pricing')) {
             setIsChecking(false);
         }
      }
    } else if (error) {
      // En cas d'erreur (autre que 401), on laisse passer pour éviter de bloquer l'utilisateur
      // Si c'est une erreur d'auth, StoreContext s'en chargera aussi
      setIsChecking(false);
    }
  }, [data, loading, error, pathname, router]);

  // Loader pendant le fetch Apollo ET pendant la validation de redirection
  if (loading || isChecking) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-white">
        <div className="relative">
          <Loader2 className="w-8 h-8 text-slate-900 animate-spin" />
          <div className="absolute inset-0 blur-xl bg-slate-900/10 animate-pulse" />
        </div>
        <p className="mt-4 text-xs font-bold text-slate-400">
          Michi journey
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
