'use client';

import React, { Suspense } from 'react';
import { usePathname, useRouter, Link } from '@/i18n/navigation';
import { useSearchParams } from 'next/navigation';
import {
  LayoutDashboard,
  Package,
  User,
  Search,
  Bell,
  LogOut,
  Database,
  BarChart3,
  Building2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useQuery } from '@apollo/client';
import { GET_UNREAD_ALERTS } from '@/graphql/queries/getUnreadAlerts';
import { NotificationPanel } from '../dashboard/NotificationPanel';
import { OrgSwitcher } from './OrgSwitcher';
import { LanguageSwitcher } from './LanguageSwitcher';
import { useStore } from '@/context/StoreContext';
import { useTranslations } from 'next-intl';

function NavLinks() {
  const t = useTranslations('navigation');
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overview';

  const navItems = [
    { id: 'overview', label: t('overview'), icon: LayoutDashboard, href: '/dashboard' },
    { id: 'inventory', label: t('inventory'), icon: Package, href: '/dashboard?tab=inventory' },
    { id: 'decisions', label: t('decisions'), icon: BarChart3, href: '/dashboard?tab=decisions' },
  ];

  return (
    <div className="hidden md:flex items-center gap-1 flex-1">
      {navItems.map((item) => {
        const isProductDetail = pathname.startsWith('/dashboard/product');
        const isDashboardHome = pathname === '/dashboard';

        const isActive = (item.id === 'inventory' && isProductDetail) ||
                        (isDashboardHome && activeTab === item.id);
        const Icon = item.icon;

        return (
          <Link
            key={item.id}
            href={item.href}
            id={`nav-${item.id}`}
            data-testid={`nav-${item.id}`}
            data-tab={item.id}
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all group",
              isActive
                ? "text-primary bg-primary/5"
                : "text-muted-foreground hover:text-foreground hover:bg-accent"
            )}
          >
            <Icon className={cn("h-4 w-4 transition-colors", isActive ? "text-primary" : "group-hover:text-foreground")} />
            <span className="text-sm font-medium">{item.label}</span>
          </Link>
        );
      })}
    </div>
  );
}

export function Navbar() {
  const t = useTranslations('navigation');
  const router = useRouter();
  const searchParams = useSearchParams();
  const [searchValue, setSearchValue] = React.useState(searchParams.get('q') || '');
  const [isUserMenuOpen, setIsUserMenuOpen] = React.useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = React.useState(false);

  const { user, currentOrganization } = useStore();

  const { data: alertsData } = useQuery(GET_UNREAD_ALERTS, {
    skip: !user || !currentOrganization,
    pollInterval: 30000
  });

  const hasUnread = alertsData?.unreadAlerts && alertsData.unreadAlerts.length > 0;

  React.useEffect(() => {
    const handleOpen = () => setIsNotificationOpen(true);
    window.addEventListener('michi:open-notifications', handleOpen);
    return () => window.removeEventListener('michi:open-notifications', handleOpen);
  }, []);

  const handleSearch = (val: string) => {
    setSearchValue(val);
    const params = new URLSearchParams(searchParams.toString());
    if (val) {
      params.set('q', val);
      params.set('tab', 'inventory');
    } else {
      params.delete('q');
    }
    router.replace(`/dashboard?${params.toString()}`);
  };

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-white/70 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center gap-8">

          {/* Logo & Org Switcher */}
          <div className="flex items-center gap-4 shrink-0" id="sidebar-logo">
            <OrgSwitcher />
          </div>

          {/* Navigation Links */}
          <Suspense fallback={<div className="flex-1" />}>
            <NavLinks />
          </Suspense>

          {/* Action Area */}
          <div className="flex items-center gap-4 flex-1 justify-end">

            <div className="relative w-full hidden md:block group max-w-md transition-all focus-within:max-w-xl">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/40 group-focus-within:text-primary transition-colors" />
              <input
                type="text"
                id="main-search"
                value={searchValue}
                onChange={(e) => handleSearch(e.target.value)}
                data-testid="search-input"
                placeholder={t('searchPlaceholder')}
                className="w-full h-10 pl-10 pr-4 rounded-lg bg-slate-100/50 border border-transparent text-xs transition-all focus:bg-white focus:ring-4 focus:ring-primary/5 focus:border-primary/20 focus:ring-0 focus:outline-none placeholder:text-muted-foreground/50 shadow-sm"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border bg-white px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                  <span className="text-xs">⌘</span>K
                </kbd>
              </div>
            </div>

            <div className="flex items-center gap-1 shrink-0 ml-2">
              <LanguageSwitcher />

              <button
                onClick={() => setIsNotificationOpen(true)}
                data-testid="notification-bell"
                className="p-2 text-muted-foreground hover:text-foreground transition-all relative hover:bg-accent rounded-lg"
              >
                <Bell className="h-5 w-5" />
                {hasUnread && (
                  <span
                    data-testid="notification-badge"
                    className="absolute top-2 right-2 w-1.5 h-1.5 bg-primary rounded-full shadow-[0_0_8px_rgba(var(--primary),0.5)]"
                  />
                )}
              </button>

              <div className="relative">
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  data-testid="user-menu-button"
                  data-user-loaded={!!user}
                  className="w-9 h-9 rounded-full bg-accent border border-border flex items-center justify-center overflow-hidden ml-1 hover:bg-accent/80 transition-colors"
                >
                  <User className={cn("h-5 w-5 transition-colors", isUserMenuOpen ? "text-primary" : "text-muted-foreground")} />
                </button>

                {/* User Dropdown */}
                {isUserMenuOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-0"
                      onClick={() => setIsUserMenuOpen(false)}
                    />
                    <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-xl border z-10 py-1 animate-in fade-in zoom-in-95 duration-100">
                      <Link
                        href="/dashboard/profile"
                        onClick={() => setIsUserMenuOpen(false)}
                        className="flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-accent transition-colors"
                      >
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span>{t('myProfile')}</span>
                      </Link>
                      <Link
                        href="/dashboard?tab=organization"
                        onClick={() => setIsUserMenuOpen(false)}
                        className="flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-accent transition-colors"
                      >
                        <Building2 className="h-4 w-4 text-muted-foreground" />
                        <span>{t('myOrg')}</span>
                      </Link>
                      <Link
                        href="/dashboard/settings/connections"
                        onClick={() => setIsUserMenuOpen(false)}
                        className="flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-accent transition-colors"
                      >
                        <LayoutDashboard className="h-4 w-4 text-muted-foreground" />
                        <span>Intégrations</span>
                      </Link>
                      <div className="h-px bg-border my-1" />
                      <button
                        onClick={() => {
                          setIsUserMenuOpen(false);
                          localStorage.removeItem('michi_token');
                          router.push('/login');
                          router.refresh();
                        }}
                        data-testid="logout-button"
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 transition-colors font-medium"
                      >
                        <LogOut className="h-4 w-4" />
                        <span>{t('logout')}</span>
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      <NotificationPanel
        isOpen={isNotificationOpen}
        onClose={() => setIsNotificationOpen(false)}
      />
    </nav>
  );
}
