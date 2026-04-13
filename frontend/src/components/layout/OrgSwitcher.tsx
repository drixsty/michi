'use client';

import React, { useState } from 'react';
import { ChevronDown, Building2, Check, ArrowLeftRight } from 'lucide-react';
import { useStore } from '@/context/StoreContext';
import { cn } from '@/lib/utils';

export function OrgSwitcher() {
  const { organizations, currentOrganization, switchOrganization, loading } = useStore();
  const [isOpen, setIsOpen] = useState(false);
  const [hasMounted, setHasMounted] = React.useState(false);

  React.useEffect(() => {
    setHasMounted(true);
  }, []);

  if (!hasMounted || (!currentOrganization && loading)) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 animate-pulse">
        <div className="w-8 h-8 rounded-lg bg-slate-100" />
        <div className="hidden lg:block space-y-1">
          <div className="h-3 w-20 bg-slate-100 rounded" />
          <div className="h-2 w-12 bg-slate-50 rounded" />
        </div>
      </div>
    );
  }

  if (!currentOrganization) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-100 transition-all border border-transparent hover:border-slate-200 active:scale-95 group focus:ring-0 focus:outline-none"
      >
        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-bold shadow-sm group-hover:bg-primary/20 transition-colors">
          {currentOrganization.name.charAt(0)}
        </div>
        <div className="text-left hidden lg:block mr-1">
          <p className="text-xs font-bold text-slate-800 leading-tight">{currentOrganization.name}</p>
          <p className="text-[10px] text-muted-foreground font-semibold">Organisation</p>
        </div>
        <ChevronDown className={cn("h-4 w-4 text-muted-foreground transition-transform duration-300", isOpen && "rotate-180")} />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute left-0 mt-2 w-64 bg-white rounded-lg shadow-2xl border z-50 py-3 animate-in fade-in zoom-in slide-in-from-top-2 duration-200">
             <div className="px-5 py-2 mb-2">
                <p className="text-[11px] font-bold text-muted-foreground flex items-center gap-2">
                  <ArrowLeftRight className="h-3 w-3" />
                  Changer d'organisation
                </p>
             </div>
             <div className="max-h-64 overflow-y-auto px-2 space-y-1">
               {organizations.map((m) => (
                  <button
                    key={m.organizationId}
                    onClick={() => {
                      if (m.organizationId !== currentOrganization.id) {
                          switchOrganization(m.organizationId);
                      }
                      setIsOpen(false);
                    }}
                    className={cn(
                      "w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm transition-all focus:ring-0 focus:outline-none",
                      m.organizationId === currentOrganization.id 
                        ? "bg-primary/5 text-primary border border-primary/10" 
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        "w-9 h-9 rounded-lg flex items-center justify-center font-bold text-xs",
                        m.organizationId === currentOrganization.id ? "bg-primary/20" : "bg-slate-100 text-slate-500"
                      )}>
                          {m.organization?.name?.charAt(0)}
                      </div>
                      <div className="text-left">
                        <p className="font-semibold truncate max-w-[140px]">{m.organization?.name}</p>
                        <p className="text-[10px] text-muted-foreground">{m.role}</p>
                      </div>
                    </div>
                    {m.organizationId === currentOrganization.id && (
                      <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                        <Check className="h-3 w-3 text-white" />
                      </div>
                    )}
                  </button>
               ))}
             </div>
          </div>
        </>
      )}
    </div>
  );
}
