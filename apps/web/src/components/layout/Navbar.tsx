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
  Building2,
  Menu,
  X,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useQuery } from '@apollo/client';
import { GET_UNREAD_ALERTS } from '@/graphql/queries/getUnreadAlerts';
import { NotificationPanel } from '../dashboard/NotificationPanel';
import { OrgSwitcher } from './OrgSwitcher';
import { LanguageSwitcher } from './LanguageSwitcher';
import { useStore } from '@/context/StoreContext';
import { useTranslations } from 'next-intl';
import { usePermissions, Permission } from '@/hooks/usePermissions';
import { clearAuthToken } from '@/lib/auth';

function NavLinks() {
  const t = useTranslations('navigation');
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overview';
  const { hasPermission } = usePermissions();

  const navItems = [
    { id: 'overview', label: t('overview'), icon: LayoutDashboard, href: '/dashboard', permission: Permission.ORG_VIEW },
    { id: 'inventory', label: t('inventory'), icon: Package, href: '/dashboard?tab=inventory', permission: Permission.INVENTORY_VIEW },
    { id: 'decisions', label: t('decisions'), icon: BarChart3, href: '/dashboard?tab=decisions', permission: Permission.FORECAST_VIEW },
  ];

  return (
    <div className="hidden md:flex items-center gap-1 flex-1">
      {navItems.filter(item => hasPermission(item.permission)).map((item) => {
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

// Mobile nav links for the drawer
function MobileNavLinks({ onClose }: { onClose: () => void }) {
  const t = useTranslations('navigation');
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overview';
  const { hasPermission } = usePermissions();

  const navItems = [
    { id: 'overview', label: t('overview'), icon: LayoutDashboard, href: '/dashboard', permission: Permission.ORG_VIEW },
    { id: 'inventory', label: t('inventory'), icon: Package, href: '/dashboard?tab=inventory', permission: Permission.INVENTORY_VIEW },
    { id: 'decisions', label: t('decisions'), icon: BarChart3, href: '/dashboard?tab=decisions', permission: Permission.FORECAST_VIEW },
  ];

  return (
    <>
      {navItems.filter(item => hasPermission(item.permission)).map((item) => {
        const isProductDetail = pathname.startsWith('/dashboard/product');
        const isDashboardHome = pathname === '/dashboard';
        const isActive = (item.id === 'inventory' && isProductDetail) ||
                        (isDashboardHome && activeTab === item.id);
        const Icon = item.icon;
        return (
          <Link
            key={item.id}
            href={item.href}
            onClick={onClose}
            className={cn(
              "flex items-center justify-between gap-3 w-full px-4 py-3.5 rounded-xl text-sm font-medium transition-colors min-h-[52px]",
              isActive
                ? "bg-primary/8 text-primary"
                : "text-slate-700 hover:bg-slate-50"
            )}
          >
            <div className="flex items-center gap-3">
              <div className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center",
                isActive ? "bg-primary/10" : "bg-slate-100"
              )}>
                <Icon className={cn("h-4 w-4", isActive ? "text-primary" : "text-slate-500")} />
              </div>
              <span>{item.label}</span>
            </div>
            <ChevronRight className={cn("h-4 w-4", isActive ? "text-primary" : "text-slate-300")} />
          </Link>
        );
      })}
    </>
  );
}

export function Navbar() {
  const t = useTranslations('navigation');
  const router = useRouter();
  const searchParams = useSearchParams();
  const [searchValue, setSearchValue] = React.useState(searchParams.get('q') || '');
  const [isUserMenuOpen, setIsUserMenuOpen] = React.useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = React.useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);
  const [isMobileSearchOpen, setIsMobileSearchOpen] = React.useState(false);

  const { user, currentOrganization } = useStore();
  const { hasPermission } = usePermissions();

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

  // Close mobile menu on route change
  React.useEffect(() => {
    setIsMobileMenuOpen(false);
    setIsMobileSearchOpen(false);
  }, [searchParams]);

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
    <>
      <nav className="sticky top-0 z-50 w-full border-b bg-white/70 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center gap-4">

            {/* Logo & Org Switcher */}
            <div className="flex items-center gap-4 shrink-0" id="sidebar-logo">
              <OrgSwitcher />
            </div>

            {/* Desktop Navigation Links */}
            <Suspense fallback={<div className="flex-1" />}>
              <NavLinks />
            </Suspense>

            {/* Action Area */}
            <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">

              {/* Desktop search */}
              <div className="relative hidden md:block group max-w-md w-64 lg:w-80 transition-all focus-within:w-96">
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

              {/* Mobile search toggle */}
              <button
                onClick={() => setIsMobileSearchOpen(!isMobileSearchOpen)}
                className="md:hidden min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
                aria-label="Rechercher"
              >
                <Search className="h-5 w-5" />
              </button>

              {/* Language switcher */}
              <div id="nav-language" className="hidden sm:block">
                <LanguageSwitcher />
              </div>

              {/* Notifications */}
              <button
                onClick={() => setIsNotificationOpen(true)}
                id="nav-notifications"
                data-testid="notification-bell"
                className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground transition-all relative hover:bg-accent"
              >
                <Bell className="h-5 w-5" />
                {hasUnread && (
                  <span
                    data-testid="notification-badge"
                    className="absolute top-2.5 right-2.5 w-1.5 h-1.5 bg-primary rounded-full shadow-[0_0_8px_rgba(var(--primary),0.5)]"
                  />
                )}
              </button>

              {/* User menu — desktop */}
              <div className="relative hidden md:block">
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  data-testid="user-menu-button"
                  data-user-loaded={!!user}
                  className="w-9 h-9 rounded-full bg-accent border border-border flex items-center justify-center overflow-hidden hover:bg-accent/80 transition-colors"
                >
                  <User className={cn("h-5 w-5 transition-colors", isUserMenuOpen ? "text-primary" : "text-muted-foreground")} />
                </button>

                {isUserMenuOpen && (
                  <>
                    <div className="fixed inset-0 z-0" onClick={() => setIsUserMenuOpen(false)} />
                    <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-xl border z-10 py-1 animate-in fade-in zoom-in-95 duration-100">
                      <Link
                        href="/dashboard/profile"
                        onClick={() => setIsUserMenuOpen(false)}
                        className="flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-accent transition-colors"
                      >
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span>{t('myProfile')}</span>
                      </Link>
                      {hasPermission(Permission.ORG_EDIT) && (
                        <Link
                          href="/dashboard?tab=organization"
                          onClick={() => setIsUserMenuOpen(false)}
                          className="flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-accent transition-colors"
                        >
                          <Building2 className="h-4 w-4 text-muted-foreground" />
                          <span>{t('myOrg')}</span>
                        </Link>
                      )}
                      {hasPermission(Permission.SETTINGS_MANAGE_APIS) && (
                        <Link
                          href="/dashboard/settings/connections"
                          id="nav-integrations"
                          onClick={() => setIsUserMenuOpen(false)}
                          className="flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-accent transition-colors"
                        >
                          <Database className="h-4 w-4 text-muted-foreground" />
                          <span>Intégrations</span>
                        </Link>
                      )}
                      <div className="h-px bg-border my-1" />
                      <button
                        onClick={() => {
                          setIsUserMenuOpen(false);
                          clearAuthToken();
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

              {/* Mobile hamburger */}
              <button
                onClick={() => {
                  setIsMobileMenuOpen(!isMobileMenuOpen);
                  setIsUserMenuOpen(false);
                }}
                className="md:hidden min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
                aria-label="Menu"
              >
                {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
            </div>
          </div>

          {/* Mobile search bar — expandable */}
          {isMobileSearchOpen && (
            <div className="md:hidden pb-3 animate-in slide-in-from-top-1 duration-150">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/40" />
                <input
                  type="text"
                  value={searchValue}
                  onChange={(e) => handleSearch(e.target.value)}
                  autoFocus
                  placeholder={t('searchPlaceholder')}
                  className="w-full h-11 pl-10 pr-10 rounded-lg bg-slate-100 border border-transparent text-sm focus:bg-white focus:border-primary/20 focus:outline-none placeholder:text-muted-foreground/50"
                />
                {searchValue && (
                  <button
                    onClick={() => { handleSearch(''); }}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Mobile navigation drawer */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-slate-100 bg-white shadow-xl animate-in slide-in-from-top-2 duration-200">
            <div className="max-w-7xl mx-auto px-4 py-4 space-y-1">

              {/* Nav links */}
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-4 pb-1">
                Navigation
              </p>
              <Suspense fallback={null}>
                <MobileNavLinks onClose={() => setIsMobileMenuOpen(false)} />
              </Suspense>

              <div className="h-px bg-slate-100 my-3" />

              {/* Account links */}
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-4 pb-1">
                Compte
              </p>

              <Link
                href="/dashboard/profile"
                onClick={() => setIsMobileMenuOpen(false)}
                className="flex items-center justify-between gap-3 w-full px-4 py-3.5 rounded-xl text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors min-h-[52px]"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center">
                    <User className="h-4 w-4 text-slate-500" />
                  </div>
                  <span>{t('myProfile')}</span>
                </div>
                <ChevronRight className="h-4 w-4 text-slate-300" />
              </Link>

              {hasPermission(Permission.ORG_EDIT) && (
                <Link
                  href="/dashboard?tab=organization"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center justify-between gap-3 w-full px-4 py-3.5 rounded-xl text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors min-h-[52px]"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center">
                      <Building2 className="h-4 w-4 text-slate-500" />
                    </div>
                    <span>{t('myOrg')}</span>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-300" />
                </Link>
              )}

              {hasPermission(Permission.SETTINGS_MANAGE_APIS) && (
                <Link
                  href="/dashboard/settings/connections"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center justify-between gap-3 w-full px-4 py-3.5 rounded-xl text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors min-h-[52px]"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center">
                      <Database className="h-4 w-4 text-slate-500" />
                    </div>
                    <span>Intégrations</span>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-300" />
                </Link>
              )}

              {/* Language switcher in drawer */}
              <div className="sm:hidden flex items-center justify-between px-4 py-3.5 rounded-xl border border-slate-100">
                <span className="text-sm font-medium text-slate-700">Langue</span>
                <LanguageSwitcher />
              </div>

              <div className="h-px bg-slate-100 my-3" />

              {/* Logout */}
              <button
                onClick={() => {
                  setIsMobileMenuOpen(false);
                  localStorage.removeItem('michi_token');
                  router.push('/login');
                  router.refresh();
                }}
                data-testid="logout-button"
                className="flex items-center gap-3 w-full px-4 py-3.5 rounded-xl text-sm font-semibold text-red-500 hover:bg-red-50 transition-colors min-h-[52px]"
              >
                <div className="w-8 h-8 rounded-lg bg-red-50 flex items-center justify-center">
                  <LogOut className="h-4 w-4 text-red-400" />
                </div>
                <span>{t('logout')}</span>
              </button>
            </div>
          </div>
        )}
      </nav>

      <NotificationPanel
        isOpen={isNotificationOpen}
        onClose={() => setIsNotificationOpen(false)}
      />
    </>
  );
}
