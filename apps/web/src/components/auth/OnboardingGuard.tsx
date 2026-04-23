'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { gql, useQuery } from '@apollo/client';
import { Loader2 } from 'lucide-react';

const GET_ONBOARDING_STATUS = gql`
  query GetOnboardingStatus {
    currentOrganization {
      id
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
    if (!loading && data?.currentOrganization) {
      const isCompleted = data.currentOrganization.onboardingCompleted;
      const isOnboardingPage = pathname.includes('/onboarding');
      
      if (!isCompleted && !isOnboardingPage) {
        router.replace('/onboarding');
      } else if (isCompleted && isOnboardingPage) {
        router.replace('/dashboard');
      } else {
        // État valide : soit complété sur dashboard, soit non-complété sur onboarding
        setIsChecking(false);
      }
    } else if (error) {
      // En cas d'erreur, on laisse passer pour éviter de bloquer l'utilisateur
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
