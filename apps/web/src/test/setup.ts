import React from 'react';
import '@testing-library/react';
import '@testing-library/jest-dom';
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

import { vi } from 'vitest';

// Runs a cleanup after each test case (e.g. clearing jsdom)
afterEach(() => {
  cleanup();
});

// Mock next-intl
vi.mock('next-intl', () => {
  const messages = {
    'stats.totalProducts': 'Total produits',
    'stats.totalProductsSub': 'Inventaire complet',
    'stats.criticalStockouts': 'Ruptures critiques',
    'stats.criticalStockoutsSub': 'Rupture immédiate',
    'stats.toWatch': 'À surveiller',
    'stats.toWatchSub': 'Stock < 20u.',
    'stats.healthy': 'Sains',
    'stats.healthySub': 'Stock optimisé',
    'stats.units': 'Unités',
    'dashboard.header.sync': 'Synchroniser',
    'dashboard.header.syncing': 'Synchronisation...',
    'dashboard.header.export': 'Exporter',
    'common.emptyTitle': 'Données vides',
    'inventory.emptySubtitle': 'Aucun produit ne correspond à votre sélection.',
  };

  return {
    useTranslations: (namespace?: string) => (key: string) => {
      const fullKey = namespace ? `${namespace}.${key}` : key;
      return messages[fullKey as keyof typeof messages] || key;
    },
    useLocale: () => 'fr',
    useTimeZone: () => 'Europe/Paris',
    useNow: () => new Date(),
  };
});

// Mock framer-motion (often causes issues in JSDOM tests)
vi.mock('framer-motion', async () => {
    const actual = await vi.importActual('framer-motion');
    return {
        ...actual as any,
        motion: {
            div: ({ children, ...props }: any) => React.createElement('div', props, children),
        },
        AnimatePresence: ({ children }: any) => children,
    };
});
