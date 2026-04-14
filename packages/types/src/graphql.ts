export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  /** Date (isoformat) */
  Date: { input: any; output: any; }
  /** Date with time (isoformat) */
  DateTime: { input: any; output: any; }
};

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

export type ChangePasswordInput = {
  currentPassword: Scalars['String']['input'];
  newPassword: Scalars['String']['input'];
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

export type GoogleLoginInput = {
  idToken: Scalars['String']['input'];
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

export type LoginInput = {
  email: Scalars['String']['input'];
  password: Scalars['String']['input'];
};

export type Mutation = {
  __typename?: 'Mutation';
  acceptInvitation: Scalars['Boolean']['output'];
  changePassword: Scalars['Boolean']['output'];
  createBillingPortalSession: Scalars['String']['output'];
  createCheckoutSession: Scalars['String']['output'];
  createOrganization: AuthPayload;
  deleteAlert: Scalars['Boolean']['output'];
  deleteInvitation: Scalars['Boolean']['output'];
  googleLogin: AuthPayload;
  ingestCsvData: IngestionResult;
  inviteMember: InvitationType;
  login: AuthPayload;
  markAlertAsRead: Scalars['Boolean']['output'];
  register: AuthPayload;
  removeMember: Scalars['Boolean']['output'];
  runCleaningPipeline: PipelineResultType;
  runPredictionPipeline: PredictionRunResultType;
  switchOrganization: AuthPayload;
  toggleSource: StoreType;
  triggerMockDataSync: IngestionResult;
  triggerOmnichannelSync: IngestionResult;
  updateMemberRole: Scalars['Boolean']['output'];
  updateOrganization?: Maybe<OrganizationType>;
  updateProductSettings: ProductType;
  updateProfile: UserType;
  updateStrategicSettings: Scalars['Boolean']['output'];
};


export type MutationAcceptInvitationArgs = {
  code: Scalars['String']['input'];
};


export type MutationChangePasswordArgs = {
  input: ChangePasswordInput;
};


export type MutationCreateBillingPortalSessionArgs = {
  returnUrl: Scalars['String']['input'];
};


export type MutationCreateCheckoutSessionArgs = {
  cancelUrl: Scalars['String']['input'];
  plan: Scalars['String']['input'];
  successUrl: Scalars['String']['input'];
};


export type MutationCreateOrganizationArgs = {
  name: Scalars['String']['input'];
  plan?: Scalars['String']['input'];
};


export type MutationDeleteAlertArgs = {
  alertId: Scalars['ID']['input'];
};


export type MutationDeleteInvitationArgs = {
  invitationId: Scalars['ID']['input'];
};


export type MutationGoogleLoginArgs = {
  input: GoogleLoginInput;
};


export type MutationIngestCsvDataArgs = {
  csvContent: Scalars['String']['input'];
  dateCol?: Scalars['String']['input'];
  salesCol?: Scalars['String']['input'];
  skuCol?: Scalars['String']['input'];
  stockCol?: Scalars['String']['input'];
  storeId: Scalars['ID']['input'];
  titleCol?: Scalars['String']['input'];
};


export type MutationInviteMemberArgs = {
  email: Scalars['String']['input'];
  role: Scalars['String']['input'];
};


export type MutationLoginArgs = {
  input: LoginInput;
};


export type MutationMarkAlertAsReadArgs = {
  alertId: Scalars['ID']['input'];
};


export type MutationRegisterArgs = {
  input: RegisterInput;
};


export type MutationRemoveMemberArgs = {
  userId: Scalars['ID']['input'];
};


export type MutationRunCleaningPipelineArgs = {
  storeId: Scalars['ID']['input'];
};


export type MutationRunPredictionPipelineArgs = {
  storeId: Scalars['ID']['input'];
};


export type MutationSwitchOrganizationArgs = {
  organizationId: Scalars['ID']['input'];
};


export type MutationToggleSourceArgs = {
  connected: Scalars['Boolean']['input'];
  platform: Scalars['String']['input'];
  storeId?: InputMaybe<Scalars['ID']['input']>;
};


export type MutationTriggerMockDataSyncArgs = {
  platform: Scalars['String']['input'];
  storeId: Scalars['ID']['input'];
};


export type MutationTriggerOmnichannelSyncArgs = {
  storeId: Scalars['ID']['input'];
};


export type MutationUpdateMemberRoleArgs = {
  role: Scalars['String']['input'];
  userId: Scalars['ID']['input'];
};


export type MutationUpdateOrganizationArgs = {
  input: UpdateOrganizationInput;
};


export type MutationUpdateProductSettingsArgs = {
  id: Scalars['ID']['input'];
  leadTime: Scalars['Int']['input'];
  moq: Scalars['Int']['input'];
};


export type MutationUpdateProfileArgs = {
  input: UpdateProfileInput;
};


export type MutationUpdateStrategicSettingsArgs = {
  currency?: InputMaybe<Scalars['String']['input']>;
  isMutualized?: InputMaybe<Scalars['Boolean']['input']>;
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

export type Query = {
  __typename?: 'Query';
  cleanedDemand: Array<CleanedDemandType>;
  currentOrganization?: Maybe<OrganizationType>;
  dashboardKpis: DashboardKpiType;
  financialOverview: DecisionCenterOverviewType;
  invoices: Array<InvoiceType>;
  me: UserType;
  omnichannelInventory: Array<OmnichannelProductType>;
  organizationMembers: Array<OrganizationMemberType>;
  pendingInvitations: Array<InvitationType>;
  predictions: Array<PredictionType>;
  products: Array<ProductType>;
  replenishmentAlerts: Array<PredictionType>;
  sources: Array<StoreType>;
  unreadAlerts: Array<AlertType>;
  validateMockData: ValidationReportType;
};


export type QueryCleanedDemandArgs = {
  limit?: Scalars['Int']['input'];
  productId: Scalars['ID']['input'];
};


export type QueryDashboardKpisArgs = {
  storeId?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryFinancialOverviewArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  storeId?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryPredictionsArgs = {
  storeId?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryProductsArgs = {
  id?: InputMaybe<Scalars['ID']['input']>;
  storeId?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryReplenishmentAlertsArgs = {
  storeId?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryUnreadAlertsArgs = {
  storeId?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryValidateMockDataArgs = {
  storeId: Scalars['ID']['input'];
};

export type RegisterInput = {
  email: Scalars['String']['input'];
  firstName: Scalars['String']['input'];
  lastName: Scalars['String']['input'];
  password: Scalars['String']['input'];
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

export type UpdateOrganizationInput = {
  currency?: InputMaybe<Scalars['String']['input']>;
  isMutualized?: InputMaybe<Scalars['Boolean']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
};

export type UpdateProfileInput = {
  email?: InputMaybe<Scalars['String']['input']>;
  emailAlertsEnabled?: InputMaybe<Scalars['Boolean']['input']>;
  firstName?: InputMaybe<Scalars['String']['input']>;
  lastName?: InputMaybe<Scalars['String']['input']>;
  minSeverity?: InputMaybe<Scalars['Int']['input']>;
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

export type GoogleLoginMutationVariables = Exact<{
  input: GoogleLoginInput;
}>;


export type GoogleLoginMutation = { __typename?: 'Mutation', googleLogin: { __typename?: 'AuthPayload', token: string, user: { __typename?: 'UserType', id: string, email: string, firstName?: string | null, lastName?: string | null, currentOrganizationId?: string | null } } };

export type IngestCsvDataMutationVariables = Exact<{
  storeId: Scalars['ID']['input'];
  csvContent: Scalars['String']['input'];
  skuCol?: InputMaybe<Scalars['String']['input']>;
  dateCol?: InputMaybe<Scalars['String']['input']>;
  salesCol?: InputMaybe<Scalars['String']['input']>;
  stockCol?: InputMaybe<Scalars['String']['input']>;
  titleCol?: InputMaybe<Scalars['String']['input']>;
}>;


export type IngestCsvDataMutation = { __typename?: 'Mutation', ingestCsvData: { __typename?: 'IngestionResult', success: boolean, message: string, platform: string, productsCount: number, salesLogsCount: number } };

export type LoginMutationVariables = Exact<{
  input: LoginInput;
}>;


export type LoginMutation = { __typename?: 'Mutation', login: { __typename?: 'AuthPayload', token: string, user: { __typename?: 'UserType', id: string, email: string, currentOrganizationId?: string | null, organizations: Array<{ __typename?: 'OrganizationMemberType', organizationId: string, role: string, organization?: { __typename?: 'OrganizationType', id: string, name: string, slug: string } | null }> } } };

export type RegisterMutationVariables = Exact<{
  input: RegisterInput;
}>;


export type RegisterMutation = { __typename?: 'Mutation', register: { __typename?: 'AuthPayload', token: string, user: { __typename?: 'UserType', id: string, email: string, firstName?: string | null, lastName?: string | null, currentOrganizationId?: string | null } } };

export type SwitchOrganizationMutationVariables = Exact<{
  organizationId: Scalars['ID']['input'];
}>;


export type SwitchOrganizationMutation = { __typename?: 'Mutation', switchOrganization: { __typename?: 'AuthPayload', token: string, user: { __typename?: 'UserType', id: string, email: string, currentOrganizationId?: string | null } } };

export type TriggerOmnichannelSyncMutationVariables = Exact<{
  storeId: Scalars['ID']['input'];
}>;


export type TriggerOmnichannelSyncMutation = { __typename?: 'Mutation', triggerOmnichannelSync: { __typename?: 'IngestionResult', success: boolean, productsCount: number, salesLogsCount: number, message: string } };

export type UpdateProductSettingsMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  leadTime: Scalars['Int']['input'];
  moq: Scalars['Int']['input'];
}>;


export type UpdateProductSettingsMutation = { __typename?: 'Mutation', updateProductSettings: { __typename?: 'ProductType', id: string, title: string, sku: string, leadTime: number, moq: number, currentStock: number, boostFactor: number, stockWeight: number } };

export type GetDashboardStatsQueryVariables = Exact<{
  storeId?: InputMaybe<Scalars['ID']['input']>;
}>;


export type GetDashboardStatsQuery = { __typename?: 'Query', dashboardKpis: { __typename?: 'DashboardKPIType', totalProducts: number, actualStockouts: number, urgentAlerts: number, predictedStockouts30d: number, message: string } };

export type GetReplenishmentAlertsQueryVariables = Exact<{
  storeId?: InputMaybe<Scalars['ID']['input']>;
}>;


export type GetReplenishmentAlertsQuery = { __typename?: 'Query', replenishmentAlerts: Array<{ __typename?: 'PredictionType', productId: string, runRate: number, daysOfStock?: number | null, predictedStockoutDate?: any | null, reorderQuantity: number }> };

export type GetMeQueryVariables = Exact<{ [key: string]: never; }>;


export type GetMeQuery = { __typename?: 'Query', me: { __typename?: 'UserType', id: string, email: string, firstName?: string | null, lastName?: string | null, currentOrganizationId?: string | null, createdAt: any, organizations: Array<{ __typename?: 'OrganizationMemberType', organizationId: string, role: string, organization?: { __typename?: 'OrganizationType', id: string, name: string, slug: string } | null }> } };

export type GetOmnichannelInventoryQueryVariables = Exact<{ [key: string]: never; }>;


export type GetOmnichannelInventoryQuery = { __typename?: 'Query', omnichannelInventory: Array<{ __typename?: 'OmnichannelProductType', sku: string, title: string, totalStock: number, channelCount: number, hasConflict: boolean, dominantRunRate: number, totalReorderQuantity: number, predictedStockoutDate?: string | null, abcRank: string, annualGrossProfit: number, channels: Array<{ __typename?: 'ChannelBreakdownType', platform: string, productId: string, currentStock: number, leadTime: number, moq: number, runRate: number, stockWeight: number }> }> };

export type GetAllPredictionsQueryVariables = Exact<{
  storeId: Scalars['ID']['input'];
}>;


export type GetAllPredictionsQuery = { __typename?: 'Query', predictions: Array<{ __typename?: 'PredictionType', productId: string, runRate: number, daysOfStock?: number | null, predictedStockoutDate?: any | null, reorderQuantity: number }> };

export type GetProductDetailQueryVariables = Exact<{
  storeId?: InputMaybe<Scalars['ID']['input']>;
  id: Scalars['ID']['input'];
}>;


export type GetProductDetailQuery = { __typename?: 'Query', productDetail: Array<{ __typename?: 'ProductType', id: string, sku: string, title: string, currentStock: number, leadTime: number, moq: number, boostFactor: number, stockWeight: number, costPrice?: number | null, salePrice?: number | null, warningThreshold: number, supplier?: { __typename?: 'SupplierType', name: string, reliabilityScore: number } | null, prediction?: { __typename?: 'PredictionType', runRate: number, daysOfStock?: number | null, predictedStockoutDate?: any | null, reorderQuantity: number } | null, cleanedDemands: Array<{ __typename?: 'CleanedDemandType', date: any, rawUnitsSold: number, correctedUnitsSold: number, inventoryLevel?: number | null, isStockout: boolean, isOutlier: boolean, correctionType: string }>, channels: Array<{ __typename?: 'ChannelBreakdownType', platform: string, productId: string, currentStock: number, runRate: number, leadTime: number, moq: number, stockWeight: number }> }> };

export type GetProductsQueryVariables = Exact<{
  storeId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
}>;


export type GetProductsQuery = { __typename?: 'Query', products: Array<{ __typename?: 'ProductType', id: string, sku: string, title: string, currentStock: number, leadTime: number, moq: number, storeId: string, warningThreshold: number, prediction?: { __typename?: 'PredictionType', runRate: number, daysOfStock?: number | null, predictedStockoutDate?: any | null, reorderQuantity: number } | null, cleanedDemands: Array<{ __typename?: 'CleanedDemandType', date: any, correctedUnitsSold: number, inventoryLevel?: number | null }>, supplier?: { __typename?: 'SupplierType', id: string, name: string } | null }> };

export type GetSourcesQueryVariables = Exact<{ [key: string]: never; }>;


export type GetSourcesQuery = { __typename?: 'Query', sources: Array<{ __typename?: 'StoreType', id: string, name: string, platform: string, connected: boolean, lastSyncAt?: any | null, healthStatus?: string | null, organizationId?: string | null }> };

export type ToggleSourceMutationVariables = Exact<{
  platform: Scalars['String']['input'];
  connected: Scalars['Boolean']['input'];
  storeId?: InputMaybe<Scalars['ID']['input']>;
}>;


export type ToggleSourceMutation = { __typename?: 'Mutation', toggleSource: { __typename?: 'StoreType', id: string, connected: boolean, platform: string } };

export type GetUnreadAlertsQueryVariables = Exact<{
  storeId?: InputMaybe<Scalars['ID']['input']>;
}>;


export type GetUnreadAlertsQuery = { __typename?: 'Query', unreadAlerts: Array<{ __typename?: 'AlertType', id: string, productId: string, type: string, message: string, isRead: boolean, severity: number, createdAt: any }> };

export type MarkAlertAsReadMutationVariables = Exact<{
  alertId: Scalars['ID']['input'];
}>;


export type MarkAlertAsReadMutation = { __typename?: 'Mutation', markAlertAsRead: boolean };
