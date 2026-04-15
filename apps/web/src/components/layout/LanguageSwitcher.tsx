'use client';

import React from 'react';
import { useLocale } from 'next-intl';
import { useRouter, usePathname } from '@/i18n/navigation';
import { Globe } from 'lucide-react';
import { cn } from '@/lib/utils';

const LOCALE_LABELS: Record<string, string> = {
  fr: 'FR',
  en: 'EN',
};

const LOCALE_FULL: Record<string, string> = {
  fr: 'Français',
  en: 'English',
};

/**
 * US 21.29 — Sélecteur de langue.
 * Switch /fr/ ↔ /en/ via next-intl routing.
 * Persistance dans localStorage (michi_locale).
 * Responsive : texte court sur mobile, texte long au survol.
 */
export function LanguageSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  // Close on outside click
  React.useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const switchLocale = (nextLocale: string) => {
    if (nextLocale === locale) { setOpen(false); return; }

    // Persist preference
    try { localStorage.setItem('michi_locale', nextLocale); } catch { /* SSR */ }

    // next-intl's router handles locale prefix automatically
    router.replace(pathname, { locale: nextLocale });

    setOpen(false);
  };

  return (
    <div ref={ref} className="relative" data-testid="language-switcher">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label="Changer la langue"
        aria-haspopup="listbox"
        aria-expanded={open}
        className={cn(
          'flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium',
          'text-muted-foreground hover:text-foreground hover:bg-accent',
          'transition-colors border border-transparent hover:border-border/50',
          open && 'bg-accent text-foreground border-border/50'
        )}
      >
        <Globe className="h-3.5 w-3.5 shrink-0" />
        <span className="tabular-nums">{LOCALE_LABELS[locale] ?? locale.toUpperCase()}</span>
      </button>

      {open && (
        <div
          role="listbox"
          className={cn(
            'absolute right-0 top-full mt-1 z-50',
            'w-32 bg-white rounded-lg shadow-xl border border-border/50 py-1',
            'animate-in fade-in-0 zoom-in-95 duration-100'
          )}
        >
          {(['fr', 'en'] as const).map((loc) => (
            <button
              key={loc}
              role="option"
              aria-selected={locale === loc}
              onClick={() => switchLocale(loc)}
              className={cn(
                'w-full flex items-center gap-2.5 px-3 py-2 text-sm transition-colors',
                locale === loc
                  ? 'text-primary font-semibold bg-primary/5'
                  : 'text-foreground hover:bg-accent'
              )}
            >
              <span className="text-xs font-mono tabular-nums text-muted-foreground w-5">
                {LOCALE_LABELS[loc]}
              </span>
              <span>{LOCALE_FULL[loc]}</span>
              {locale === loc && (
                <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
