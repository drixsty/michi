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
    metadataBase: new URL('https://michi.app'),
    title: t('title'),
    description: t('description'),
    keywords: [
      'inventory forecasting software', 'demand planning', 'omnichannel inventory management',
      'Shopify inventory forecasting', 'Amazon FBA restock', 'WooCommerce stock management',
      'AI supply chain', 'stockout prevention', 'dropshipping inventory', 'automated replenishment',
      'réapprovisionnement automatique', 'gestion de stock IA', 'logiciel prévision demande e-commerce',
      'Michi', 'supply chain automation', 'FBA inventory', 'safety stock calculation',
    ],
    alternates: {
      canonical: `https://michi.app/${locale}`,
      languages: {
        'en': 'https://michi.app/en',
        'fr': 'https://michi.app/fr',
      },
    },
    openGraph: {
      title: t('title'),
      description: t('description'),
      url: `https://michi.app/${locale}`,
      siteName: 'Michi 道',
      images: [
        {
          url: 'https://michi.app/dashboard.png',
          width: 1200,
          height: 630,
          alt: 'Michi — AI-powered omnichannel inventory forecasting dashboard',
        },
      ],
      locale: locale === 'fr' ? 'fr_FR' : 'en_US',
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title: t('title'),
      description: t('description'),
      images: ['https://michi.app/dashboard.png'],
      creator: '@michiapp',
    },
  };
}

export function generateViewport() {
  return {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 5,
    themeColor: '#6c5ce7',
  };
}

import { NextIntlClientProvider } from 'next-intl';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { CookieConsent } from '@/components/CookieConsent';

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'Michi 道',
  applicationCategory: 'BusinessApplication',
  operatingSystem: 'Web',
  description: 'AI-powered omnichannel inventory forecasting and supply chain automation for Shopify, Amazon, and WooCommerce sellers.',
  offers: {
    '@type': 'AggregateOffer',
    priceCurrency: 'USD',
    lowPrice: '99',
    highPrice: '249',
    offerCount: '3',
  },
  url: 'https://michi.app',
  provider: {
    '@type': 'Organization',
    name: 'Michi AI Solutions',
    url: 'https://michi.app',
  },
  aggregateRating: {
    '@type': 'AggregateRating',
    ratingValue: '4.9',
    reviewCount: '200',
  },
};

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
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
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
