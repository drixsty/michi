export interface Product {
  id: string;
  shopId: string;
  sku: string;
  title: string;
  currentStock: number;
  leadTime: number;
  moq: number;
  createdAt: string;
}

export interface SyncResult {
  success: boolean;
  productsCreated: number;
  salesLogsCreated: number;
  message: string;
}
