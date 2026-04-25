'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { Navbar } from './Navbar';
import { useStore } from '@/context/StoreContext';
import { LoadingOverlay } from '../ui/LoadingOverlay';
import { InteractiveTour } from '../dashboard/InteractiveTour';

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { loading: storeLoading, currentOrganization } = useStore();
  const isAuthPage = pathname.endsWith('/login') || 
                    pathname.endsWith('/register') || 
                    pathname.endsWith('/onboarding');

  // Afficher l'overlay global uniquement lors du tout premier chargement (aucune org en cache).
  // Quand une org est déjà connue (localStorage hydraté), le contenu s'affiche directement
  // et chaque vue gère son propre état de chargement — évite la superposition de loaders.
  const showGlobalLoader = storeLoading && !currentOrganization;

  if (isAuthPage) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-slate-50/50">
      {showGlobalLoader && <LoadingOverlay />}
      <InteractiveTour />
      <React.Suspense fallback={null}>
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-in fade-in duration-700">
            {children}
          </div>
        </main>
      </React.Suspense>
    </div>
  );
}
