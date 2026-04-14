'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { Navbar } from './Navbar';
import { useStore } from '@/context/StoreContext';
import { LoadingOverlay } from '../ui/LoadingOverlay';

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { loading: storeLoading } = useStore();
  const isAuthPage = pathname === '/login' || pathname === '/register' || pathname === '/onboarding';

  if (isAuthPage) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-slate-50/50">
      {storeLoading && <LoadingOverlay />}
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
