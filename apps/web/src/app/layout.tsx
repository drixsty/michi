/**
 * Root Layout
 * Layout global de l'application Michi 2.0
 */
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ApolloWrapper } from '@/components/providers/ApolloWrapper';
import { StoreProvider } from '@/context/StoreContext';
import { GoogleOAuthProvider } from '@react-oauth/google';
import './globals.css';
import { AssistantMascot } from '@/components/assistant/AssistantMascot';

const inter = Inter({ subsets: ['latin'] });

// Note: In a real app, use environment variables
const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

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
        <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
          <ApolloWrapper>
            <StoreProvider>
              {children}
              <AssistantMascot />
            </StoreProvider>
          </ApolloWrapper>
        </GoogleOAuthProvider>
      </body>
    </html>
  );
}
