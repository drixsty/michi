'use client';

import React, { useEffect, useState } from 'react';
import { ApolloProvider } from '@apollo/client';
import { apolloClient } from '../graphql/client';
import { Toaster } from 'sonner';
import './globals.css';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <html lang="fr" className="dark">
      <head>
        <title>Michi Support — Operations Console</title>
        <meta name="description" content="Michi 道 Support and Diagnostics Platform" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
        <style>{`
          html, body {
            font-family: 'Outfit', 'Plus Jakarta Sans', sans-serif;
          }
        `}</style>
      </head>
      <body className="antialiased bg-michi-dark text-slate-100 min-h-screen">
        {mounted ? (
          <ApolloProvider client={apolloClient}>
            {children}
            <Toaster richColors position="top-right" closeButton />
          </ApolloProvider>
        ) : (
          <div className="flex items-center justify-center min-h-screen bg-michi-dark text-slate-400">
            Chargement de la Console...
          </div>
        )}
      </body>
    </html>
  );
}
