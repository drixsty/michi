'use client';

import React, { Suspense } from 'react';
import Link from 'next/link';
import { usePathname, useSearchParams, useRouter } from 'next/navigation';
import { 
  LayoutDashboard, 
  Package, 
  User, 
  Search,
  Bell,
  LogOut,
  Settings,
  Database,
  BarChart3,
  Building2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useQuery } from '@apollo/client';
import { GET_UNREAD_ALERTS } from '@/graphql/queries/getUnreadAlerts';
import { NotificationPanel } from '../dashboard/NotificationPanel';
import { OrgSwitcher } from './OrgSwitcher';
import { useStore } from '@/context/StoreContext';

const navItems = [
  { id: 'overview', label: 'Aperçu', icon: LayoutDashboard, href: '/dashboard' },
  { id: 'inventory', label: 'Inventaire', icon: Package, href: '/dashboard?tab=inventory' },
  { id: 'sources', label: 'Sources', icon: Database, href: '/dashboard?tab=sources' },
  { id: 'decisions', label: 'Décisions', icon: BarChart3, href: '/dashboard?tab=decisions' },
];

function NavLinks() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overview';

  return (
    <div className="hidden md:flex items-center gap-1 flex-1">
      {navItems.map((item) => {
        const isProductDetail = pathname.startsWith('/dashboard/product');
        const isDashboardHome = pathname === '/dashboard';
        
        // Un item est actif si :
        // 1. C'est l'inventaire et on est dans un détail produit
        // 2. Le tab correspond à l'ID (seulement si on est sur /dashboard)
        // 3. C'est 'overview' et on est sur /dashboard sans paramètres (ou tab=overview)
        const isActive = (item.id === 'inventory' && isProductDetail) ||
                        (isDashboardHome && activeTab === item.id);
        const Icon = item.icon;
        
        return (
          <Link
            key={item.id}
            href={item.href}
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
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const [searchValue, setSearchValue] = React.useState(searchParams.get('q') || '');
  const [isNotificationOpen, setIsNotificationOpen] = React.useState(false);

  const { user, currentOrganization } = useStore();
  
  const { data: alertsData } = useQuery(GET_UNREAD_ALERTS, {
    skip: !user || !currentOrganization,
    pollInterval: 30000 // Synchronisé avec la page dashboard
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
      params.set('tab', 'inventory'); // Switch to inventory automatically when searching
    } else {
      params.delete('q');
    }
    
    // Always navigate to /dashboard if we are searching (ensures redirection from /dashboard/decisions or others)
    const targetPath = '/dashboard';
    router.replace(`${targetPath}?${params.toString()}`);
  };

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-white/70 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center gap-8">
          
          {/* Logo & Org Switcher */}
          <div className="flex items-center gap-4 shrink-0">
            <OrgSwitcher />
          </div>

          {/* Navigation Links wrapped in Suspense for useSearchParams safety */}
          <Suspense fallback={<div className="flex-1" />}>
            <NavLinks />
          </Suspense>

          {/* Action Area: Search & Notifications & Profile */}
          <div className="flex items-center gap-4 flex-1 justify-end">
            
            <div className="relative w-full hidden md:block group max-w-md transition-all focus-within:max-w-xl">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/40 group-focus-within:text-primary transition-colors" />
              <input
                type="text"
                value={searchValue}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Rechercher un produit, une commande..."
                className="w-full h-10 pl-10 pr-4 rounded-lg bg-slate-100/50 border border-transparent text-xs transition-all focus:bg-white focus:ring-4 focus:ring-primary/5 focus:border-primary/20 focus:ring-0 focus:outline-none placeholder:text-muted-foreground/50 shadow-sm"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border bg-white px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                  <span className="text-xs">⌘</span>K
                </kbd>
              </div>
            </div>
            
            <div className="flex items-center gap-1 shrink-0 ml-2">
              <button 
                onClick={() => setIsNotificationOpen(true)}
                className="p-2 text-muted-foreground hover:text-foreground transition-all relative hover:bg-accent rounded-lg"
              >
                <Bell className="h-5 w-5" />
                {hasUnread && (
                  <span className="absolute top-2 right-2 w-1.5 h-1.5 bg-primary rounded-full shadow-[0_0_8px_rgba(var(--primary),0.5)]" />
                )}
              </button>
              
              <div className="relative group/user">
                <button 
                  className="w-9 h-9 rounded-full bg-accent border border-border flex items-center justify-center overflow-hidden cursor-default ml-1"
                >
                  <User className="h-5 w-5 text-muted-foreground" />
                </button>
                
                {/* User Dropdown */}
                <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-xl border opacity-0 invisible group-hover/user:opacity-100 group-hover/user:visible transition-all duration-200 transform origin-top-right scale-95 group-hover/user:scale-100 py-1">
                  <Link href="/dashboard/profile" className="flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-accent transition-colors">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span>Mon profil</span>
                  </Link>
                  <Link href="/dashboard?tab=organization" className="flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-accent transition-colors">
                    <Building2 className="h-4 w-4 text-muted-foreground" />
                    <span>Mon organisation</span>
                  </Link>
                  <div className="h-px bg-border my-1" />
                  <button 
                    onClick={() => {
                      localStorage.removeItem('michi_token');
                      router.push('/login');
                      router.refresh();
                    }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 transition-colors font-medium"
                  >
                    <LogOut className="h-4 w-4" />
                    <span>Déconnexion</span>
                  </button>
                </div>
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
