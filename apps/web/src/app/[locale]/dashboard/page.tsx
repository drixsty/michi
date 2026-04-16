'use client';

import { useQuery, useMutation } from '@apollo/client';
import { useRouter, useSearchParams } from 'next/navigation';
import React, { useEffect, useState, useMemo, Suspense } from 'react';
import { GET_ME } from '@/graphql/queries/getMe';
import { TRIGGER_MOCK_DATA_SYNC } from '@/graphql/mutations/syncInventory';
import { GET_DASHBOARD_STATS, FINANCIAL_OVERVIEW } from '@/graphql/queries/getDashboardStats';
import { GET_UNREAD_ALERTS } from '@/graphql/queries/getUnreadAlerts';
import { INGEST_CSV_DATA } from '@/graphql/mutations/ingestCSV';
import { AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import { gql } from '@apollo/client';
import { useTranslations } from 'next-intl';

import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { ProductQuickView } from '@/components/dashboard/ProductQuickView';
import OnboardingWizard from '@/components/dashboard/OnboardingWizard';

import { OverviewView } from '@/components/dashboard/views/OverviewView';
import { InventoryView } from '@/components/dashboard/views/InventoryView';
import { SourcesView } from '@/components/dashboard/views/SourcesView';
import { DecisionsView } from '@/components/dashboard/views/DecisionsView';
import { OrganizationView } from '@/components/dashboard/views/OrganizationView';

import { GET_OMNICHANNEL_INVENTORY } from '@/graphql/queries/getOmnichannelInventory';
import type { OmnichannelProduct } from '@michi/types';
import { useStore } from '@/context/StoreContext';

const DELETE_ALERT = gql`
  mutation DeleteAlert($id: ID!) {
    deleteAlert(alertId: $id)
  }
`;

function DashboardContent() {
  const t = useTranslations('dashboard');
  const tExport = useTranslations('dashboard.export');
  const tToast = useTranslations('dashboard.toast');
  const [isMounted, setIsMounted] = React.useState(false);
  const searchParams = useSearchParams();
  const router = useRouter();

  React.useEffect(() => {
    setIsMounted(true);
  }, []);

  const [showOnboarding, setShowOnboarding] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);

  const activeTab = searchParams.get('tab') || 'overview';
  const searchQuery = searchParams.get('q') || '';

  useEffect(() => {
    const onboarded = localStorage.getItem('michi_onboarded');
    if (!onboarded) setShowOnboarding(true);
  }, []);

  const { currentOrganization } = useStore();

  const { data: meData, loading: meLoading, error: meError } = useQuery(GET_ME);

  const isAuthReady = !meLoading && !!meData;

  const { data: omnichannelData, loading: productsLoading, refetch: refetchProducts } = useQuery(GET_OMNICHANNEL_INVENTORY, {
    skip: !currentOrganization || !isAuthReady
  });
  const { data: statsData, refetch: refetchStats } = useQuery(GET_DASHBOARD_STATS, {
    skip: !currentOrganization || !isAuthReady
  });
  const { data: financialData, refetch: refetchFinancial } = useQuery(FINANCIAL_OVERVIEW, {
    skip: !currentOrganization || !isAuthReady
  });
  const { data: alertsData, refetch: refetchAlerts } = useQuery(GET_UNREAD_ALERTS, {
    skip: !currentOrganization || !isAuthReady,
    pollInterval: 30000
  });

  const [triggerSync, { loading: syncing }] = useMutation(TRIGGER_MOCK_DATA_SYNC, {
    onCompleted: (data) => {
      setToast({ message: data.triggerOmnichannelSync.message, type: 'success' });
      refetchProducts();
      refetchStats();
      refetchFinancial();
      refetchAlerts();
      setTimeout(() => setToast(null), 5000);
    },
    onError: (err) => {
      setToast({ message: err.message, type: 'error' });
      setTimeout(() => setToast(null), 5000);
    },
  });

  const [ingestCSV] = useMutation(INGEST_CSV_DATA, {
    onCompleted: () => {
      setToast({ message: tToast('importSuccess'), type: 'success' });
      refetchProducts();
      refetchStats();
      setTimeout(() => setToast(null), 5000);
    },
  });

  const [deleteAlert] = useMutation(DELETE_ALERT, {
    onCompleted: () => refetchAlerts(),
  });

  const handleCSVUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (event) => {
      const content = event.target?.result as string;
      if (content) {
        await ingestCSV({
          variables: {
            csvContent: content,
            skuCol: 'sku', dateCol: 'date', salesCol: 'sales', stockCol: 'stock', titleCol: 'title'
          }
        });
      }
    };
    reader.readAsText(file);
  };

  const handleExport = () => {
    try {
      const products = (omnichannelData?.omnichannelInventory || []) as OmnichannelProduct[];
      const headers = [tExport('product'), tExport('sku'), tExport('stock'), tExport('reorder')];
      const rows = products.map(p => [p.title, p.sku, p.totalStock, Math.round(p.totalReorderQuantity || 0)]);
      const csvContent = [headers, ...rows].map(e => e.join(',')).join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `michi_export_${format(new Date(), 'yyyy-MM-dd')}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setToast({ message: tToast('exportSuccess'), type: 'success' });
      setTimeout(() => setToast(null), 5000);
    } catch (err) {
      setToast({ message: tToast('exportError'), type: 'error' });
    }
  };

  const kpis = useMemo(() => {
    if (statsData?.dashboardKpis) {
      const s = statsData.dashboardKpis;
      return {
        total: s.totalProducts || 0,
        urgent: s.actualStockouts || 0,
        warning: s.urgentAlerts || 0,
        healthy: (s.totalProducts || 0) - (s.urgentAlerts || 0) - (s.actualStockouts || 0)
      };
    }
    return { total: 0, urgent: 0, warning: 0, healthy: 0 };
  }, [statsData]);

  const isAdmin = useMemo(() => {
    const orgs = meData?.me?.organizations || [];
    const currentOrgId = meData?.me?.currentOrganizationId;
    const currentOrg = orgs.find((o: any) => o.organizationId === currentOrgId);
    return currentOrg?.role?.toLowerCase() === 'admin';
  }, [meData]);

  useEffect(() => {
    if (meError) {
      console.warn("Auth error, redirecting to login...");
      router.replace('/login');
    }
  }, [meError, router]);

  if (!isMounted) return null;

  const tabConfigs: Record<string, { title: string; subtitle: string }> = {
    overview: {
      title: t('tabs.overview.title'),
      subtitle: t('tabs.overview.subtitle'),
    },
    inventory: {
      title: t('tabs.inventory.title'),
      subtitle: t('tabs.inventory.subtitle'),
    },
    sources: {
      title: t('tabs.sources.title'),
      subtitle: t('tabs.sources.subtitle'),
    },
    decisions: {
      title: t('tabs.decisions.title'),
      subtitle: t('tabs.decisions.subtitle'),
    },
    organization: {
      title: t('tabs.organization.title'),
      subtitle: t('tabs.organization.subtitle'),
    },
  };

  const { title, subtitle } = tabConfigs[activeTab] || tabConfigs.overview;

  return (
    <div className="space-y-6">
      <AnimatePresence>
        {showOnboarding && (
          <OnboardingWizard
            userName={meData?.me?.firstName ?? undefined}
            onSync={() => triggerSync() as any}
            onComplete={() => setShowOnboarding(false)}
          />
        )}
      </AnimatePresence>

      {toast && (
        <div className="fixed top-4 right-4 z-50 px-4 py-2 rounded-md shadow-lg text-sm bg-primary text-white border border-white/20 animate-in slide-in-from-right-2">
          {toast.message}
        </div>
      )}

      <DashboardHeader
        title={title}
        subtitle={subtitle}
        syncing={syncing}
        onSync={() => triggerSync()}
        onExport={activeTab === 'decisions' ? () => {} : handleExport}
        showActions={activeTab === 'inventory'}
      />

      <div className="mt-2">
        {activeTab === 'overview' && (
          <OverviewView
            stats={kpis}
            alerts={alertsData?.unreadAlerts || []}
            onDeleteAlert={(id) => deleteAlert({ variables: { id } })}
            omnichannelInventory={(omnichannelData?.omnichannelInventory || []) as OmnichannelProduct[]}
            financialData={financialData?.financialOverview?.kpis}
            onProductClick={(id) => setSelectedProductId(id)}
            onOpenInventory={() => router.push('/dashboard?tab=inventory')}
            onOpenNotifications={() => window.dispatchEvent(new CustomEvent('michi:open-notifications'))}
          />
        )}

        {activeTab === 'inventory' && (
          <InventoryView
            loading={productsLoading}
            data={(omnichannelData?.omnichannelInventory || []) as OmnichannelProduct[]}
            searchQuery={searchQuery}
            onRowClick={(id) => setSelectedProductId(id)}
          />
        )}

        {activeTab === 'sources' && (
          <SourcesView
            onImport={handleCSVUpload}
            isAdmin={isAdmin}
          />
        )}

        {activeTab === 'decisions' && <DecisionsView />}
        {activeTab === 'organization' && <OrganizationView />}
      </div>

      <ProductQuickView
        productId={selectedProductId}
        onClose={() => setSelectedProductId(null)}
      />
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="h-6 w-6 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
