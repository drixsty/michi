'use client';

import { useLocale } from 'next-intl';
import { useRouter, usePathname } from 'next/navigation';
import React from 'react';

const LanguageSwitcher = () => {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const toggleLanguage = () => {
    const nextLocale = locale === 'en' ? 'fr' : 'en';
    // Remove the current locale from the path and prepend the next one
    const newPath = pathname.replace(`/${locale}`, `/${nextLocale}`);
    router.push(newPath);
  };

  return (
    <button 
      onClick={toggleLanguage}
      className="flex items-center gap-1.5 px-3 min-h-[44px] rounded-lg hover:bg-secondary transition-all text-[13px] font-bold text-muted-foreground hover:text-foreground"
    >
      <span className={locale === 'en' ? 'text-primary' : ''}>EN</span>
      <span className="text-border">/</span>
      <span className={locale === 'fr' ? 'text-primary' : ''}>FR</span>
    </button>
  );
};

export default LanguageSwitcher;
