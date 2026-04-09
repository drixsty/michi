/**
 * Root Layout
 * Layout global de l'application Michi 2.0
 */
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ApolloWrapper } from '@/components/providers/ApolloWrapper';
import MainLayout from '@/components/layout/MainLayout';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Michi 道 | Inventory Forecasting',
  description: 'Stoppez les ruptures de stock et les surstocks coûteux',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className="h-full">
      <body className={`${inter.className} h-full antialiased`}>
        <ApolloWrapper>
          <MainLayout>
            {children}
          </MainLayout>
        </ApolloWrapper>
      </body>
    </html>
  );
}
