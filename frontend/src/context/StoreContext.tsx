"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { User, Organization, Store, OrganizationMember } from '../types/user';
import { GET_ME } from '../graphql/queries/getMe';
import { SWITCH_ORGANIZATION } from '../graphql/mutations/switchOrganization';
import { GET_SOURCES } from '../graphql/queries/getSources';
import { useRouter, usePathname } from 'next/navigation';

interface StoreContextType {
  user: User | null;
  organizations: OrganizationMember[];
  currentOrganization: Organization | null;
  stores: Store[];
  loading: boolean;
  switchOrganization: (orgId: string) => Promise<void>;
  refreshUser: () => void;
}

const StoreContext = createContext<StoreContextType | undefined>(undefined);

export const StoreProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const pathname = usePathname();
  const isAuthPage = pathname === '/login' || pathname === '/register';
  
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [stores, setStores] = useState<Store[]>([]);

  // 1. Fetch User & Organizations memberships
  const { data: userData, loading: userLoading, refetch: refetchUser } = useQuery(GET_ME, {
    skip: isAuthPage,
    fetchPolicy: 'network-only',
    onCompleted: (data) => {
      if (data?.me) {
        const currentOrgId = data.me.currentOrganizationId;
        const memberships = data.me.organizations as OrganizationMember[];
        const activeMembership = memberships.find(m => m.organizationId === currentOrgId);
        
        if (activeMembership?.organization) {
          setCurrentOrganization(activeMembership.organization);
        } else if (memberships.length > 0 && memberships[0].organization) {
          setCurrentOrganization(memberships[0].organization);
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
        // Clear active store when switching org to force re-selection
        localStorage.removeItem('activeStoreId');
        // Reload to refresh all Apollo data with new org context
        window.location.reload(); 
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
