import { GeistSans } from 'geist/font/sans';
import { GeistMono } from 'geist/font/mono';
import "../globals.css";
import { getTranslations, setRequestLocale, getMessages } from 'next-intl/server';
import { ReactNode } from 'react';

const locales = ['en', 'fr'];

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({ params: { locale } }: { params: { locale: string } }) {
  const t = await getTranslations({ locale, namespace: 'Metadata' });

  return {
    title: t('title'),
    description: t('description'),
    keywords: ["Forecasting", "Omnichannel", "Shopify", "Amazon", "WooCommerce", "AI", "Michi"],
    alternates: {
      canonical: `https://michi.app/${locale}`,
      languages: {
        'en': 'https://michi.app/en',
        'fr': 'https://michi.app/fr',
      },
    },
    other: {
      "google-site-verification": "verification_token_here",
    }
  };
}

export function generateViewport() {
  return {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 5,
    themeColor: '#000000',
  };
}

import { NextIntlClientProvider } from 'next-intl';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { CookieConsent } from '@/components/CookieConsent';

export default async function LocaleLayout({
  children,
  params: { locale }
}: {
  children: ReactNode;
  params: { locale: string };
}) {
  // Enable static rendering
  setRequestLocale(locale);
  const messages = await getMessages({ locale });

  return (
    <html lang={locale} className={`scroll-smooth overflow-x-hidden ${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="font-sans flex flex-col min-h-screen">
        <NextIntlClientProvider locale={locale} messages={messages}>
          <div className="fixed inset-0 -z-10 bg-background grid-subtle opacity-10" />
          <div className="fixed inset-0 -z-10 hero-glow opacity-30" />
          <Navbar />
          <main className="flex-grow pt-20">
            {children}
          </main>
          <Footer />
          <CookieConsent />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
