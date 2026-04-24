/**
 * Apollo Client Configuration
 * GraphQL client pour communiquer avec le backend
 */
import { ApolloClient, InMemoryCache, createHttpLink, from } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';

const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_URL || 'http://localhost:8000/graphql',
});

// Auth link : Ajoute le token JWT et l'ID de l'organisation à chaque requête
const authLink = setContext((_, { headers }) => {
  if (typeof window === 'undefined') return { headers };
  
  const token = localStorage.getItem('michi_token');
  const orgRaw = localStorage.getItem('michi_current_org');
  let orgId = '';
  
  if (orgRaw) {
    try {
      orgId = JSON.parse(orgRaw).id;
    } catch (e) {}
  }
  
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : '',
      'michi-org-id': orgId || '',
      'apollo-require-preflight': 'true',
    },
  };
});

// Error link : Gestion des erreurs GraphQL
const errorLink = onError(({ graphQLErrors, networkError }) => {
  if (graphQLErrors) {
    graphQLErrors.forEach(({ message, extensions }) => {
      const code = extensions?.code;
      
      // Si UNAUTHENTICATED ou FORBIDDEN, rediriger vers login
      if ((code === 'UNAUTHENTICATED' || code === 'FORBIDDEN') && typeof window !== 'undefined') {
        console.warn(`[Apollo] ${code}: Access denied, clearing local data.`);
        localStorage.removeItem('michi_token');
        localStorage.removeItem('michi_current_org');
        
        // Éviter la boucle de rechargement si on est déjà sur les pages d'auth
        const path = window.location.pathname;
        if (!path.includes('/login') && !path.includes('/forgot-password') && !path.includes('/reset-password')) {
          // On redirige vers la racine qui gérera la locale et le login
          window.location.href = '/';
        }
      }
    });
  }
  
  if (networkError) {
    console.error(`[Network error]: ${networkError}`);
  }
});

// Apollo Client instance
export const apolloClient = new ApolloClient({
  link: from([errorLink, authLink, httpLink]),
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
    },
  },
});
