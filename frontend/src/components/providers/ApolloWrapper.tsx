/**
 * Apollo Provider Wrapper
 * Nécessaire pour utiliser Apollo Client côté client
 */
'use client';

import { ApolloProvider } from '@apollo/client';
import { apolloClient } from '@/graphql/client';

export function ApolloWrapper({ children }: { children: React.ReactNode }) {
  return <ApolloProvider client={apolloClient}>{children}</ApolloProvider>;
}
