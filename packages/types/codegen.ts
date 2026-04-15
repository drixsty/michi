import type { CodegenConfig } from '@graphql-codegen/cli';

const config: CodegenConfig = {
  overwrite: true,
  schema: "packages/types/schema.graphql",
  documents: [
    "apps/web/src/graphql/**/*.ts"
  ],
  generates: {
    "packages/types/src/index.ts": {
      plugins: [
        "typescript",
        "typescript-operations",
        "typed-document-node",
        {
          add: {
            content: `
/** ALIASES FOR FRONTEND COMPATIBILITY **/
export type Organization = {
  id: string;
  name: string;
  slug: string;
  createdAt?: string;
  plan?: string;
  settings?: string;
  subscriptionStatus?: string;
};

export type Store = {
  id: string;
  name: string;
  platform: string;
  connected: boolean;
  lastSyncAt?: string | null;
  healthStatus?: string | null;
  organizationId?: string | null;
};

export type Source = Store;

export type CleanedDemand = {
  date: string;
  correctedUnitsSold: number;
  inventoryLevel?: number | null;
  rawUnitsSold?: number;
  isOutlier?: boolean;
  isStockout?: boolean;
  correctionType?: string;
  computedAt?: string;
  id?: string;
  productId?: string;
};

export type OmnichannelProduct = {
  id?: string;
  sku: string;
  title: string;
  totalStock: number;
  channelCount: number;
  hasConflict: boolean;
  dominantRunRate: number;
  totalReorderQuantity: number;
  predictedStockoutDate?: string | null;
  abcRank: string;
  annualGrossProfit: number;
  channels: any[];
};

export type DashboardKpi = DashboardKpiType;

export type PlatformSource = 'shopify' | 'amazon' | 'woocommerce' | 'csv' | 'custom';
`
          }
        }
      ],
      config: {
        useTypeImports: true,
        scalars: {
          DateTime: "string",
          Date: "string",
          ID: "string"
        }
      }
    }
  }
};

export default config;
