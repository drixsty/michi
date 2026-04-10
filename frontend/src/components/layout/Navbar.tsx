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
  BarChart3
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { NotificationPanel } from '../dashboard/NotificationPanel';

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
        const isActive = (item.id === 'inventory' && pathname.startsWith('/dashboard/product')) ||
                        (item.id === 'decisions' && activeTab === 'decisions') ||
                        (item.id === 'overview' && activeTab === 'overview' && !pathname.startsWith('/dashboard/product')) || 
                        (activeTab === item.id);
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
            <span className="text-sentence">{item.label}</span>
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
          
          {/* Logo & Brand */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-primary/20 transition-transform active:scale-95 cursor-pointer">
              道
            </div>
            <span className="text-xl font-bold tracking-tight text-foreground hidden lg:block">Michi</span>
          </div>

          {/* Navigation Links wrapped in Suspense for useSearchParams safety */}
          <Suspense fallback={<div className="flex-1" />}>
            <NavLinks />
          </Suspense>

          {/* Search Bar & Actions */}
          <div className="flex items-center gap-4 flex-1 justify-end max-w-md">
            <div className="relative w-full hidden sm:block group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/40 group-focus-within:text-primary transition-colors" />
              <input
                type="text"
                value={searchValue}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Rechercher un produit..."
                className="w-full h-10 pl-10 pr-4 rounded-lg bg-slate-100/50 border border-transparent text-xs transition-all focus:bg-white focus:ring-4 focus:ring-primary/5 focus:border-primary/20 outline-none placeholder:text-muted-foreground/50"
              />
            </div>
            
            <div className="flex items-center gap-2 shrink-0">
              <button 
                onClick={() => setIsNotificationOpen(true)}
                className="p-2 text-muted-foreground hover:text-foreground transition-colors relative"
              >
                <Bell className="h-5 w-5" />
                <span className="absolute top-2 right-2 w-1.5 h-1.5 bg-primary rounded-full shadow-[0_0_8px_rgba(var(--primary),0.5)]" />
              </button>
              
              <div className="relative group/user">
                <button 
                  onClick={() => router.push('/dashboard/profile')}
                  className="w-9 h-9 rounded-full bg-accent border border-border flex items-center justify-center overflow-hidden cursor-pointer hover:border-primary/30 transition-all ml-1"
                >
                  <User className="h-5 w-5 text-muted-foreground" />
                </button>
                
                {/* User Dropdown */}
                <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-xl border opacity-0 invisible group-hover/user:opacity-100 group-hover/user:visible transition-all duration-200 transform origin-top-right scale-95 group-hover/user:scale-100 py-1">
                  <Link href="/dashboard/profile" className="flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-accent transition-colors">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span>Mon profil</span>
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
