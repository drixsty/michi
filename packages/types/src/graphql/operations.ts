import { Maybe, Scalars, Exact, InputMaybe } from './base';
import { 
  AuthPayload, 
  UserType, 
  OrganizationType, 
  InvitationType, 
  IngestionResult, 
  PipelineResultType, 
  PredictionRunResultType, 
  StoreType, 
  ProductType, 
  DashboardKpiType, 
  DecisionCenterOverviewType, 
  InvoiceType, 
  OmnichannelProductType, 
  OrganizationMemberType, 
  PredictionType, 
  ValidationReportType,
  CleanedDemandType,
  AlertType
} from './schema';

export type ChangePasswordInput = {
  currentPassword: Scalars['String']['input'];
  newPassword: Scalars['String']['input'];
};

export type GoogleLoginInput = {
  idToken: Scalars['String']['input'];
};

export type LoginInput = {
  email: Scalars['String']['input'];
  password: Scalars['String']['input'];
};

export type RegisterInput = {
  email: Scalars['String']['input'];
  firstName: Scalars['String']['input'];
  lastName: Scalars['String']['input'];
  password: Scalars['String']['input'];
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

// --- Operation Variables ---

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
