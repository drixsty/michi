export interface Prediction {
  productId: string;
  runRate: number;
  daysOfStock: number | null;
  predictedStockoutDate: string | null;
  reorderQuantity: number;
}

export interface Product {
  id: string;
  shopId: string;
  sku: string;
  title: string;
  currentStock: number;
  leadTime: number;
  moq: number;
  createdAt: string;
  prediction?: Prediction;
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
