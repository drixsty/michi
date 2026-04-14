/**
 * Locale Layout — wraps all locale-aware routes with NextIntlClientProvider.
 * Inherits the root RootLayout (html, body, ApolloWrapper, etc.).
 */
import { NextIntlClientProvider, hasLocale } from 'next-intl';
import { notFound } from 'next/navigation';
import { routing } from '@/i18n/routing';

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

interface LocaleLayoutProps {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}

import MainLayout from '@/components/layout/MainLayout';

export default async function LocaleLayout({ children, params }: LocaleLayoutProps) {
  const { locale } = await params;

  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  const messages = (await import(`../../../messages/${locale}.json`)).default;

  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      <MainLayout>
        {children}
      </MainLayout>
    </NextIntlClientProvider>
  );
}
