/**
 * TypeScript Types — SaaS Enterprise
 */

export enum UserRole {
  ADMIN = "ADMIN",
  MANAGER = "MANAGER",
  VIEWER = "VIEWER"
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan?: string;
  subscriptionStatus?: string;
  createdAt?: string;
}

export interface OrganizationMember {
  organizationId: string;
  userId?: string;
  role: UserRole | string;
  permissions?: unknown;
  organization?: Organization | null;
}

export interface Store {
  id: string;
  name: string;
  platform: string;
  connected: boolean;
  lastSyncAt?: string | null;
  healthStatus?: string | null;
  organizationId?: string | null;
}

export interface User {
  id: string;
  email: string;
  firstName?: string | null;
  lastName?: string | null;
  currentOrganizationId?: string | null;
  createdAt: string;
  organizations: OrganizationMember[];
  preferences?: string | null;
}

// LoginInput & AuthPayload are now provided by GraphQL Codegen
