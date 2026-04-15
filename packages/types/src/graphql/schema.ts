import { Maybe, Scalars } from './base';

export type AlertType = {
  __typename?: 'AlertType';
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  isRead: Scalars['Boolean']['output'];
  message: Scalars['String']['output'];
  productId: Scalars['ID']['output'];
  severity: Scalars['Int']['output'];
  type: Scalars['String']['output'];
};

export type AuthPayload = {
  __typename?: 'AuthPayload';
  token: Scalars['String']['output'];
  user: UserType;
};

export type ChannelBreakdownType = {
  __typename?: 'ChannelBreakdownType';
  currentStock: Scalars['Int']['output'];
  leadTime: Scalars['Int']['output'];
  moq: Scalars['Int']['output'];
  platform: Scalars['String']['output'];
  productId: Scalars['ID']['output'];
  runRate: Scalars['Float']['output'];
  stockWeight: Scalars['Float']['output'];
};

export type CleanedDemandType = {
  __typename?: 'CleanedDemandType';
  computedAt: Scalars['DateTime']['output'];
  correctedUnitsSold: Scalars['Float']['output'];
  correctionType: Scalars['String']['output'];
  date: Scalars['Date']['output'];
  id: Scalars['ID']['output'];
  inventoryLevel?: Maybe<Scalars['Int']['output']>;
  isOutlier: Scalars['Boolean']['output'];
  isStockout: Scalars['Boolean']['output'];
  productId: Scalars['ID']['output'];
  rawUnitsSold: Scalars['Float']['output'];
};

export type DashboardKpiType = {
  __typename?: 'DashboardKPIType';
  actualStockouts: Scalars['Int']['output'];
  message: Scalars['String']['output'];
  predictedStockouts30d: Scalars['Int']['output'];
  totalProducts: Scalars['Int']['output'];
  urgentAlerts: Scalars['Int']['output'];
};

export type DecisionCenterOverviewType = {
  __typename?: 'DecisionCenterOverviewType';
  activePlatforms: Array<Scalars['String']['output']>;
  capitalBreakdown: Array<PlatformCapitalType>;
  healthScore: Scalars['Int']['output'];
  kpis: FinancialKpiType;
  message?: Maybe<Scalars['String']['output']>;
  topRisks: Array<TopRiskType>;
  totalRunRate: Scalars['Float']['output'];
  totalStock: Scalars['Int']['output'];
};

export type FinancialKpiType = {
  __typename?: 'FinancialKpiType';
  currency: Scalars['String']['output'];
  inventoryValueCost: Scalars['Float']['output'];
  inventoryValueSale: Scalars['Float']['output'];
  isMutualized: Scalars['Boolean']['output'];
  revenueAtRisk: Scalars['Float']['output'];
  stockCoverageAvgDays: Scalars['Float']['output'];
};

export type IngestionResult = {
  __typename?: 'IngestionResult';
  message: Scalars['String']['output'];
  platform: Scalars['String']['output'];
  productsCount: Scalars['Int']['output'];
  salesLogsCount: Scalars['Int']['output'];
  success: Scalars['Boolean']['output'];
};

export type InvitationType = {
  __typename?: 'InvitationType';
  code?: Maybe<Scalars['String']['output']>;
  createdAt: Scalars['DateTime']['output'];
  email: Scalars['String']['output'];
  expiresAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  organizationId: Scalars['ID']['output'];
  role: Scalars['String']['output'];
  status: Scalars['String']['output'];
};

export type InvoiceType = {
  __typename?: 'InvoiceType';
  amount: Scalars['Float']['output'];
  currency: Scalars['String']['output'];
  date: Scalars['DateTime']['output'];
  hostedUrl?: Maybe<Scalars['String']['output']>;
  id: Scalars['String']['output'];
  number: Scalars['String']['output'];
  pdfUrl?: Maybe<Scalars['String']['output']>;
  status: Scalars['String']['output'];
};

export type OmnichannelProductType = {
  __typename?: 'OmnichannelProductType';
  abcRank: Scalars['String']['output'];
  annualGrossProfit: Scalars['Float']['output'];
  channelCount: Scalars['Int']['output'];
  channels: Array<ChannelBreakdownType>;
  dominantRunRate: Scalars['Float']['output'];
  hasConflict: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  predictedStockoutDate?: Maybe<Scalars['String']['output']>;
  sku: Scalars['String']['output'];
  title: Scalars['String']['output'];
  totalReorderQuantity: Scalars['Int']['output'];
  totalStock: Scalars['Int']['output'];
};

export type OrganizationMemberType = {
  __typename?: 'OrganizationMemberType';
  organization?: Maybe<OrganizationType>;
  organizationId: Scalars['ID']['output'];
  permissions: Scalars['String']['output'];
  role: Scalars['String']['output'];
  user?: Maybe<UserType>;
  userId: Scalars['ID']['output'];
};

export type OrganizationType = {
  __typename?: 'OrganizationType';
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  plan: Scalars['String']['output'];
  settings: Scalars['String']['output'];
  slug: Scalars['String']['output'];
  subscriptionStatus: Scalars['String']['output'];
};

export type PipelineResultType = {
  __typename?: 'PipelineResultType';
  message: Scalars['String']['output'];
  outlierCorrections: Scalars['Int']['output'];
  productsProcessed: Scalars['Int']['output'];
  rowsWritten: Scalars['Int']['output'];
  stockoutCorrections: Scalars['Int']['output'];
  success: Scalars['Boolean']['output'];
};

export type PlatformCapitalType = {
  __typename?: 'PlatformCapitalType';
  platform: Scalars['String']['output'];
  value: Scalars['Float']['output'];
};

export type PredictionRunResultType = {
  __typename?: 'PredictionRunResultType';
  message: Scalars['String']['output'];
  productsProcessed: Scalars['Int']['output'];
  success: Scalars['Boolean']['output'];
};

export type PredictionType = {
  __typename?: 'PredictionType';
  abcRank?: Maybe<Scalars['String']['output']>;
  annualGrossProfit?: Maybe<Scalars['Float']['output']>;
  computedAt: Scalars['DateTime']['output'];
  currentStockSnapshot: Scalars['Float']['output'];
  daysOfStock?: Maybe<Scalars['Float']['output']>;
  id: Scalars['ID']['output'];
  leadTimeSnapshot: Scalars['Int']['output'];
  mapeScore?: Maybe<Scalars['Float']['output']>;
  moqSnapshot: Scalars['Int']['output'];
  predictedStockoutDate?: Maybe<Scalars['Date']['output']>;
  productId: Scalars['ID']['output'];
  reorderQuantity: Scalars['Int']['output'];
  runRate: Scalars['Float']['output'];
};

export type ProductType = {
  __typename?: 'ProductType';
  boostFactor: Scalars['Float']['output'];
  channels: Array<ChannelBreakdownType>;
  cleanedDemands: Array<CleanedDemandType>;
  costPrice?: Maybe<Scalars['Float']['output']>;
  currentStock: Scalars['Int']['output'];
  id: Scalars['ID']['output'];
  leadTime: Scalars['Int']['output'];
  moq: Scalars['Int']['output'];
  prediction?: Maybe<PredictionType>;
  salePrice?: Maybe<Scalars['Float']['output']>;
  sku: Scalars['String']['output'];
  stockWeight: Scalars['Float']['output'];
  storeId: Scalars['ID']['output'];
  supplier?: Maybe<SupplierType>;
  supplierId?: Maybe<Scalars['ID']['output']>;
  title: Scalars['String']['output'];
  warningThreshold: Scalars['Float']['output'];
};

export type StoreType = {
  __typename?: 'StoreType';
  connected: Scalars['Boolean']['output'];
  healthStatus?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  lastSyncAt?: Maybe<Scalars['DateTime']['output']>;
  name: Scalars['String']['output'];
  organizationId?: Maybe<Scalars['ID']['output']>;
  platform: Scalars['String']['output'];
};

export type SupplierType = {
  __typename?: 'SupplierType';
  averageDelayDays: Scalars['Float']['output'];
  contactEmail?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  reliabilityScore: Scalars['Float']['output'];
};

export type TopRiskType = {
  __typename?: 'TopRiskType';
  costPrice: Scalars['Float']['output'];
  daysOfStock: Scalars['Float']['output'];
  productId: Scalars['ID']['output'];
  reorderQuantity: Scalars['Int']['output'];
  riskValue: Scalars['Float']['output'];
  runRate: Scalars['Float']['output'];
  salePrice: Scalars['Float']['output'];
  sku: Scalars['String']['output'];
  sourcePlatform?: Maybe<Scalars['String']['output']>;
  stockoutDate?: Maybe<Scalars['Date']['output']>;
  supplierId?: Maybe<Scalars['ID']['output']>;
  title: Scalars['String']['output'];
};

export type UserType = {
  __typename?: 'UserType';
  createdAt: Scalars['DateTime']['output'];
  currentOrganizationId?: Maybe<Scalars['ID']['output']>;
  email: Scalars['String']['output'];
  firstName?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  lastName?: Maybe<Scalars['String']['output']>;
  organizations: Array<OrganizationMemberType>;
  preferences: Scalars['String']['output'];
  shopId?: Maybe<Scalars['ID']['output']>;
};

export type ValidationIssueType = {
  __typename?: 'ValidationIssueType';
  detail: Scalars['String']['output'];
  rule: Scalars['String']['output'];
  severity: Scalars['String']['output'];
};

export type ValidationReportType = {
  __typename?: 'ValidationReportType';
  isValid: Scalars['Boolean']['output'];
  issues: Array<ValidationIssueType>;
  productCount: Scalars['Int']['output'];
  salesLogCount: Scalars['Int']['output'];
  stockoutRatio: Scalars['Float']['output'];
  summary: Scalars['String']['output'];
};
