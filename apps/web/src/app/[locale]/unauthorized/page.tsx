'use client';

import { UnauthorizedView } from '@/components/layout/UnauthorizedView';

export default function UnauthorizedPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <UnauthorizedView />
    </div>
  );
}
