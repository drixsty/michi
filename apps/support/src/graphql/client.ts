import { ApolloClient, InMemoryCache, createHttpLink, from } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';

const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_URL || 'http://localhost:8000/graphql',
});

// Auth link: Ajoute le token JWT et l'ID de l'organisation impersonnée
const authLink = setContext((_, { headers }) => {
  if (typeof window === 'undefined') return { headers };
  
  const token = localStorage.getItem('michi_token');
  const impersonatedOrgId = localStorage.getItem('michi_support_impersonated_org');
  
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : '',
      'michi-org-id': impersonatedOrgId || '',
      'apollo-require-preflight': 'true',
    },
  };
});

// Error link: Gestion des erreurs GraphQL
const errorLink = onError(({ graphQLErrors, networkError }) => {
  if (graphQLErrors) {
    graphQLErrors.forEach(({ message, extensions }) => {
      const code = extensions?.code;
      const flowId = extensions?.flowId;

      if (flowId && typeof window !== 'undefined') {
        sessionStorage.setItem('michi_last_error_flow_id', String(flowId));
      }
      
      // Si UNAUTHENTICATED ou FORBIDDEN, rediriger vers login
      if ((code === 'UNAUTHENTICATED' || code === 'FORBIDDEN') && typeof window !== 'undefined') {
        console.warn(`[Apollo] ${code}: Access denied, clearing local data.`);
        localStorage.removeItem('michi_token');
        localStorage.removeItem('michi_support_impersonated_org');
        
        const path = window.location.pathname;
        if (!path.includes('/login')) {
          window.location.href = '/login';
        }
      }

      // Afficher un message d'erreur toast
      if (typeof window !== 'undefined') {
        import('sonner').then(({ toast }) => {
          toast.error(message || 'Une erreur est survenue', {
            description: flowId ? `Flow ID: ${flowId}` : undefined,
            duration: 6000,
          });
        });
      }
    });
  }
  
  if (networkError && typeof window !== 'undefined') {
    import('sonner').then(({ toast }) => {
      toast.error('Erreur réseau : connexion impossible avec le serveur');
    });
  }
});

// Apollo Client instance
export const apolloClient = new ApolloClient({
  link: from([errorLink, authLink, httpLink]),
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'network-only', // Toujours chercher les dernières données pour le support
    },
  },
});
