export interface Prediction {
  productId: string;
  runRate: number;
  daysOfStock: number | null;
  predictedStockoutDate: string | null;
  reorderQuantity: number;
}

export interface Supplier {
  id: string;
  name: string;
  reliabilityScore: number;
  averageDelayDays: number;
}

export interface Product {
  id: string;
  storeId: string;
  sku: string;
  title: string;
  currentStock: number;
  leadTime: number;
  moq: number;
  createdAt: string;
  warningThreshold: number;
  prediction?: Prediction;
  supplier?: Supplier;
}

export interface CleanedDemand {
  date: string;
  rawUnitsSold: number;
  correctedUnitsSold: number;
  isStockout: boolean;
  isOutlier: boolean;
  correctionType: string;
}

export interface SyncResult {
  success: boolean;
  productsCreated: number;
  salesLogsCreated: number;
  message: string;
}

// ── Omnichannel types (Sprint 9) ───────────────────────────────────────────────

export type PlatformSource = 'shopify' | 'woocommerce' | 'amazon' | 'csv' | 'custom';

export interface ChannelBreakdown {
  platform: PlatformSource;
  productId: string;
  currentStock: number;
  leadTime: number;
  moq: number;
}

export interface OmnichannelProduct {
  sku: string;
  title: string;
  totalStock: number;
  channelCount: number;
  hasConflict: boolean;
  dominantRunRate: number;
  totalReorderQuantity: number;
  predictedStockoutDate: string | null;
  channels: ChannelBreakdown[];
}
