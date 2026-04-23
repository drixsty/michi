/**
 * Michi Import Domain Types
 * Robust types to prevent 'any' leakage.
 */

export type ImportStep = 'upload' | 'mapping' | 'preview' | 'success';

export interface ColumnMapping {
  sku: string;
  title: string;
  stock: string;
  date?: string;
  units_sold?: string;
}

export interface CSVAnalysis {
  columns: string[];
  columnTypes: Record<string, 'string' | 'number' | 'date'>;
  suggestedMapping: Array<{
    targetField: keyof ColumnMapping;
    csvColumn: string;
    confidence: number;
  }>;
  sampleData: string; // JSON String from backend
  anomalies: string;  // JSON String from backend
  impactSummary?: string;
}

export interface SmartImportInput {
  storeId: string;
  csvContent: string;
  mapping: string; // JSON String
}

export interface SmartImportResult {
  success: boolean;
  message: string;
  count?: number;
}
