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
  const [organizations, setOrganizations] = useState<OrgMember[]>([]);
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
        if (!pathname.endsWith('/onboarding')) {
          window.location.href = '/login';
        }
      }
    },
    onCompleted: (data) => {
      if (data?.me) {
        const memberships = (data.me.organizations || []) as OrgMember[];
        const currentOrgId = data.me.currentOrganizationId;
        
        // US 19.2: Redirect to onboarding if no organization found or onboarding not completed
        const isAuthOrOnboarding = isAuthPage || pathname.includes('/onboarding');
        
        const activeMembership = memberships.find(m => m.organizationId === currentOrgId);
        const serverOnboardingCompleted = (activeMembership?.organization as any)?.onboardingCompleted ?? false;
        
        // Anti-redirection loop: check if we just finished onboarding
        const clientOnboardingFinished = typeof window !== 'undefined' && localStorage.getItem('michi_onboarding_finished') === 'true';
        const onboardingCompleted = serverOnboardingCompleted || clientOnboardingFinished;

        if (!isAuthOrOnboarding) {
          if (memberships.length > 0) {
            console.log(">>> [STORE] FIRST MEMBERSHIP KEYS:", Object.keys(memberships[0]));
            console.log(">>> [STORE] FIRST MEMBERSHIP DATA:", JSON.stringify(memberships[0]));
          }
          if (memberships.length === 0 && !clientOnboardingFinished) {
            console.warn("[Store] No organizations. Redirecting to onboarding...");
            window.location.href = '/onboarding';
            return;
          }
          
          if (!onboardingCompleted) {
            console.warn("[Store] Onboarding not completed. Redirecting...");
            window.location.href = '/onboarding';
            return;
          }
          
          console.log(">>> [STORE] ACCESS GRANTED <<<");
        }
        
        // 1. Sync currentOrganization with fresh server data
        if (memberships.length > 0) {
          const currentOrgId = String(userData?.me?.currentOrganizationId || localStorage.getItem('michi_current_org_id'));
          const matchingMembership = memberships.find((m: any) => String(m.organizationId) === currentOrgId) 
                                   || memberships.find((m: any) => String(m.organization?.id) === currentOrgId)
                                   || memberships[0];
          
          if (matchingMembership?.organization) {
            const org = matchingMembership.organization as any;
            const freshOrg = {
              id: String(org.id),
              name: org.name,
              slug: org.slug,
              onboardingCompleted: org.onboardingCompleted
            };
            
            if (JSON.stringify(currentOrganization) !== JSON.stringify(freshOrg)) {
              setCurrentOrganization(freshOrg);
              localStorage.setItem('michi_current_org', JSON.stringify(freshOrg));
              localStorage.setItem('michi_current_org_id', freshOrg.id);
            }

            // 2. Force update organizations list with cleaned data
            const cleaned = memberships.map((m: any) => {
              const mOrgId = String(m.organizationId || m.organization?.id);
              const isCurr = mOrgId === freshOrg.id;
              
              if (isCurr && freshOrg.name) {
                return { 
                  ...m, 
                  organization: { ...m.organization, name: freshOrg.name, id: freshOrg.id } 
                };
              }
              return m;
            });
            
            setOrganizations(cleaned);
          }
        }
      } else if (!isAuthPage) {
        // Fallback: If network query returns null but we thought we were logged in
        console.warn("[Store] User is null on a non-auth page. Clearing session.");
        localStorage.removeItem('michi_token');
        localStorage.removeItem('michi_current_org');
        if (!pathname.endsWith('/onboarding') && !pathname.includes('/verify-email')) {
          window.location.href = '/login';
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
    if (!orgId) {
      console.error("[Store] switchOrganization called without orgId");
      return;
    }
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

        // Clear active store and onboarding flags when switching org
        localStorage.removeItem('activeStoreId');
        localStorage.removeItem('michi_onboarding_finished');
        
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
    organizations: organizations.length > 0 ? organizations : (userData?.me?.organizations || []),
    currentOrganization,
    stores,
    loading: userLoading || sourcesLoading,
    switchOrganization,
    refreshUser: async () => {
      console.log("[Store] Manual refresh requested...");
      await refetchUser();
    }
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
