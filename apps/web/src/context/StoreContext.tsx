"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import type { GetMeQuery, GetSourcesQuery, Organization, Store } from '@michi/types';
import { GET_ME } from '../graphql/queries/getMe';
import { SWITCH_ORGANIZATION } from '../graphql/mutations/switchOrganization';
import { GET_SOURCES } from '../graphql/queries/getSources';
import { useRouter, usePathname } from 'next/navigation';

type MeUser = GetMeQuery['me'];
type OrgMember = GetMeQuery['me']['organizations'][number];
type SourceStore = GetSourcesQuery['sources'][number];

interface StoreContextType {
  user: MeUser | null;
  organizations: OrgMember[];
  currentOrganization: Organization | null;
  stores: SourceStore[];
  loading: boolean;
  switchOrganization: (orgId: string) => Promise<void>;
  refreshUser: () => void;
}

const StoreContext = createContext<StoreContextType | undefined>(undefined);

export const StoreProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const pathname = usePathname();
  // Support both root paths and localized paths (e.g. /fr/login)
  const isAuthPage = pathname.endsWith('/login') || pathname.endsWith('/register');
  
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [stores, setStores] = useState<Store[]>([]);

  // Hydrate from local storage on mount ONLY to avoid hydration mismatch
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('michi_current_org');
      if (saved) {
        try {
          setCurrentOrganization(JSON.parse(saved));
        } catch (e) {
          console.error("Failed to parse cached org", e);
        }
      }
    }
  }, []);

  // 1. Fetch User & Organizations memberships
  const { data: userData, loading: userLoading, refetch: refetchUser } = useQuery(GET_ME, {
    skip: isAuthPage,
    fetchPolicy: 'network-only',
    onError: (error) => {
      // If we get an unauthenticated error during GET_ME, clear the stale session
      const isUnauthenticated = error.graphQLErrors.some(e => e.extensions?.code === 'UNAUTHENTICATED');
      if (isUnauthenticated && !isAuthPage) {
        console.warn("[Store] Session expired or invalid, clearing context.");
        localStorage.removeItem('michi_token');
        localStorage.removeItem('michi_current_org');
        if (pathname !== '/onboarding') {
          window.location.href = '/login';
        }
      }
    },
    onCompleted: (data) => {
      if (data?.me) {
        const memberships = (data.me.organizations || []) as OrgMember[];
        const currentOrgId = data.me.currentOrganizationId;
        
        // US 19.2: Redirect to onboarding if no organization found
        const isAuthOrOnboarding = isAuthPage || pathname === '/onboarding';
        if (memberships.length === 0 && !isAuthOrOnboarding) {
          console.log("[Store] No organizations found. Waiting 1.5s before redirecting to onboarding...");
          setTimeout(() => {
            // Re-check memberships before redirecting (might have updated if refetch happened)
            if (memberships.length === 0 && !isAuthOrOnboarding) {
               window.location.href = '/onboarding';
            }
          }, 1500);
          return;
        }

        const activeMembership = memberships.find(m => m.organizationId === currentOrgId);
        
        if (activeMembership?.organization) {
          const org = activeMembership.organization;
          setCurrentOrganization(org);
          localStorage.setItem('michi_current_org', JSON.stringify({
            id: org.id,
            name: org.name
          }));
        } else if (memberships.length > 0 && memberships[0].organization) {
          const org = memberships[0].organization;
          setCurrentOrganization(org);
          localStorage.setItem('michi_current_org', JSON.stringify({
            id: org.id,
            name: org.name
          }));
        }
      }
    }
  });

  // 2. Fetch Stores for the active Organization
  const { data: sourcesData, loading: sourcesLoading } = useQuery(GET_SOURCES, {
    skip: !currentOrganization,
    fetchPolicy: 'network-only',
    onCompleted: (data) => {
      if (data?.sources) {
        setStores(data.sources);
      }
    }
  });

  // 3. Mutation for Organization Switching
  const [switchOrgMutation] = useMutation(SWITCH_ORGANIZATION);

  const switchOrganization = async (orgId: string) => {
    try {
      const { data } = await switchOrgMutation({ 
        variables: { organizationId: orgId } 
      });
      
      if (data?.switchOrganization?.token) {
        localStorage.setItem('michi_token', data.switchOrganization.token);
        
        // Pre-heat the org cache before reload so the UI shows the NEW org immediately on refresh
        const targetOrg = (userData?.me?.organizations as OrgMember[])?.find(m => m.organizationId === orgId);
        if (targetOrg?.organization) {
          localStorage.setItem('michi_current_org', JSON.stringify({
            id: targetOrg.organization.id,
            name: targetOrg.organization.name
          }));
        }

        // Clear active store when switching org to force re-selection
        localStorage.removeItem('activeStoreId');
        
        // Redirect to dashboard while reloading to refresh all Apollo data with new org context
        // and satisfy "repart sur la page dashboard" requirement
        window.location.href = '/dashboard';
      }
    } catch (err) {
      console.error("Failed to switch organization:", err);
    }
  };


  const value = {
    user: userData?.me || null,
    organizations: userData?.me?.organizations || [],
    currentOrganization,
    stores,
    loading: userLoading || sourcesLoading,
    switchOrganization,
    refreshUser: refetchUser
  };

  return (
    <StoreContext.Provider value={value}>
      {children}
    </StoreContext.Provider>
  );
};

export const useStore = () => {
  const context = useContext(StoreContext);
  if (context === undefined) {
    throw new Error('useStore must be used within a StoreProvider');
  }
  return context;
};
