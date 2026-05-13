'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslations } from 'next-intl';
import {
  TrendingUp,
  BarChart3,
  Layers,
  Zap,
  ShieldCheck,
  Globe,
  ShoppingCart,
  Boxes,
  ChevronDown,
  ChevronRight,
  Menu,
  X,
} from 'lucide-react';
import LanguageSwitcher from './LanguageSwitcher';

const NavDropdown = ({ title, items, isOpen, onMouseEnter, onMouseLeave }: {
  title: string,
  items: any[],
  isOpen: boolean,
  onMouseEnter: () => void,
  onMouseLeave: () => void
}) => (
  <div className="relative h-full flex items-center" onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave}>
    <button className={`flex items-center gap-1.5 text-sm font-medium transition-colors h-full ${isOpen ? 'text-primary' : 'text-muted-foreground hover:text-primary'}`}>
      {title} <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
    </button>

    <div
      className="absolute top-full left-1/2 -translate-x-1/2 w-80 pt-1.5 z-50"
      style={{ pointerEvents: isOpen ? 'auto' : 'none' }}
    >
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={isOpen ? { opacity: 1, y: 0 } : { opacity: 0, y: 6 }}
        transition={{ duration: 0.15 }}
        className="w-full bg-background border border-border rounded-lg p-4 overflow-hidden"
      >
        <div className="grid gap-1">
          {items.map((item, idx) => (
            <a
              key={idx}
              href={item.href}
              className="flex items-start gap-4 p-3 rounded-lg hover:bg-secondary transition-all group"
            >
              <div className="w-10 h-10 shrink-0 rounded-lg bg-primary/5 flex items-center justify-center group-hover:bg-primary/10 transition-colors border border-border">
                <item.icon className="w-5 h-5 text-primary" />
              </div>
              <div>
                <div className="text-sm font-semibold text-foreground mb-0.5 group-hover:text-primary transition-colors">{item.label}</div>
                <div className="text-xs text-muted-foreground leading-relaxed">{item.description}</div>
              </div>
            </a>
          ))}
        </div>
      </motion.div>
    </div>
  </div>
);

export const Navbar = () => {
  const t = useTranslations('Navbar');
  const tIndex = useTranslations('Index');
  const [openDropdown, setOpenDropdown] = React.useState<string | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);

  const closeMobile = () => setIsMobileMenuOpen(false);

  const mobileNavSections = [
    {
      label: t('product'),
      links: [
        { label: tIndex('featuresSection.items.predictive.title'), href: '/features/forecasting' },
        { label: tIndex('featuresSection.items.replenishment.title'), href: '/features/replenishment' },
        { label: tIndex('featuresSection.items.multisync.title'), href: '/features/unified-inventory' },
      ],
    },
    {
      label: t('integrationsLabel'),
      links: [
        { label: t('integrationNames.shopify'), href: '/integrations/shopify' },
        { label: t('integrationNames.amazonFBA'), href: '/integrations/amazon' },
        { label: t('integrationNames.woocommerce'), href: '/integrations/woocommerce' },
      ],
    },
    {
      label: t('company'),
      links: [
        { label: t('pricing'), href: '/pricing' },
        { label: t('resources.blogLabel'), href: '/blog' },
        { label: t('resources.aboutLabel'), href: '/about' },
      ],
    },
  ];

  return (
    <nav className="fixed top-0 inset-x-0 z-50 border-b border-border bg-background">
      <div className="max-w-7xl mx-auto flex justify-between items-center h-16 px-4 sm:px-6">

        {/* Left: Logo + Desktop Nav */}
        <div className="flex items-center gap-6 lg:gap-10 h-full">
          <a href="/" className="flex items-center gap-2 shrink-0">
            <div className="w-7 h-7 bg-primary rounded-lg flex items-center justify-center font-bold text-white text-sm">道</div>
            <span className="text-sm font-bold tracking-tight text-foreground">{t('brandName')}</span>
          </a>

          <div className="hidden lg:flex items-center gap-8 h-full">
            <NavDropdown
              title={t('product')}
              isOpen={openDropdown === 'products'}
              onMouseEnter={() => setOpenDropdown('products')}
              onMouseLeave={() => setOpenDropdown(null)}
              items={[
                { label: tIndex('featuresSection.items.predictive.title'), href: '/features/forecasting', description: tIndex('featuresSection.items.predictive.description'), icon: TrendingUp },
                { label: tIndex('featuresSection.items.replenishment.title'), href: '/features/replenishment', description: tIndex('featuresSection.items.replenishment.description'), icon: Zap },
                { label: tIndex('featuresSection.items.multisync.title'), href: '/features/unified-inventory', description: tIndex('featuresSection.items.multisync.description'), icon: Layers },
              ]}
            />
            <NavDropdown
              title={t('integrationsLabel')}
              isOpen={openDropdown === 'integrations'}
              onMouseEnter={() => setOpenDropdown('integrations')}
              onMouseLeave={() => setOpenDropdown(null)}
              items={[
                { label: t('integrationNames.shopify'), href: '/integrations/shopify', description: t('integrations.shopify'), icon: ShoppingCart },
                { label: t('integrationNames.amazonFBA'), href: '/integrations/amazon', description: t('integrations.amazon'), icon: Globe },
                { label: t('integrationNames.woocommerce'), href: '/integrations/woocommerce', description: t('integrations.woo'), icon: Boxes },
              ]}
            />
            <a href="/pricing" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">{t('pricing')}</a>
            <NavDropdown
              title={t('company')}
              isOpen={openDropdown === 'resources'}
              onMouseEnter={() => setOpenDropdown('resources')}
              onMouseLeave={() => setOpenDropdown(null)}
              items={[
                { label: t('resources.blogLabel'), href: '/blog', description: t('resources.blog'), icon: BarChart3 },
                { label: t('resources.aboutLabel'), href: '/about', description: t('resources.about'), icon: ShieldCheck },
              ]}
            />
          </div>
        </div>

        {/* Right: Desktop CTAs + Mobile controls */}
        <div className="flex items-center gap-2">
          <div className="hidden sm:block">
            <LanguageSwitcher />
          </div>
          <a
            href={`${process.env.NEXT_PUBLIC_APP_URL}/login`}
            className="hidden md:flex items-center text-xs font-semibold text-muted-foreground hover:text-foreground px-3 min-h-[44px] transition-all"
          >
            {t('login')}
          </a>
          <a
            href={process.env.NEXT_PUBLIC_DEMO_URL || 'mailto:contact@michi.app'}
            className="hidden lg:flex items-center border border-border hover:bg-secondary text-foreground px-4 min-h-[44px] rounded-lg text-xs font-semibold transition-all"
          >
            {t('bookDemo')}
          </a>
          <a
            href={`${process.env.NEXT_PUBLIC_APP_URL}/register`}
            className="bg-primary hover:bg-primary/90 text-white px-4 min-h-[44px] rounded-lg text-xs font-semibold transition-all flex items-center"
          >
            {t('getStarted')}
          </a>
          {/* Hamburger — visible below lg */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="lg:hidden min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg text-muted-foreground hover:bg-secondary transition-colors"
            aria-label="Menu"
            aria-expanded={isMobileMenuOpen}
          >
            {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile / Tablet — pleine page sous la navbar */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            key="mobile-nav"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            className="lg:hidden fixed top-16 left-0 right-0 bottom-0 z-40 bg-background overflow-y-auto"
          >
            <div className="max-w-7xl mx-auto px-4 py-6 flex flex-col min-h-full">

              {/* Nav sections */}
              <div className="flex-1 space-y-1">
                {mobileNavSections.map((section) => (
                  <div key={section.label} className="mb-3">
                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest px-3 pb-1">
                      {section.label}
                    </p>
                    {section.links.map((link) => (
                      <a
                        key={link.href}
                        href={link.href}
                        onClick={closeMobile}
                        className="flex items-center justify-between w-full px-3 py-3.5 text-sm font-medium text-foreground hover:bg-secondary rounded-lg min-h-[52px] transition-colors"
                      >
                        {link.label}
                        <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
                      </a>
                    ))}
                  </div>
                ))}
              </div>

              {/* CTAs en bas — toujours visibles */}
              <div className="border-t border-border pt-5 mt-4 space-y-3 pb-8">
                {/* Language switcher — xs uniquement (sm+ l'a dans la topbar) */}
                <div className="sm:hidden">
                  <LanguageSwitcher />
                </div>
                {/* Login — xs/sm uniquement (md+ l'a dans la topbar) */}
                <a
                  href={`${process.env.NEXT_PUBLIC_APP_URL}/login`}
                  onClick={closeMobile}
                  className="md:hidden flex items-center justify-between w-full px-4 py-3.5 text-sm font-medium text-muted-foreground hover:bg-secondary rounded-xl min-h-[52px] transition-colors border border-border"
                >
                  {t('login')}
                  <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
                </a>
                <a
                  href={process.env.NEXT_PUBLIC_DEMO_URL || 'mailto:contact@michi.app'}
                  onClick={closeMobile}
                  className="flex items-center justify-center w-full px-4 py-3.5 text-sm font-semibold border border-border text-foreground hover:bg-secondary rounded-xl min-h-[52px] transition-colors"
                >
                  {t('bookDemo')}
                </a>
                <a
                  href={`${process.env.NEXT_PUBLIC_APP_URL}/register`}
                  onClick={closeMobile}
                  className="flex items-center justify-center w-full px-4 py-4 text-sm font-bold bg-primary hover:bg-primary/90 text-white rounded-xl min-h-[56px] transition-colors shadow-lg shadow-primary/20"
                >
                  {t('getStarted')}
                </a>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};
