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
  plan: string;
  subscriptionStatus: string;
  createdAt: string;
}

export interface OrganizationMember {
  organizationId: string;
  userId: string;
  role: UserRole;
  permissions: any;
  organization?: Organization;
}

export interface Store {
  id: string;
  name: string;
  platform: string;
  connected: boolean;
  lastSyncAt?: string;
  healthStatus: string;
}

export interface User {
  id: string;
  email: string;
  currentOrganizationId?: string;
  createdAt: string;
  organizations: OrganizationMember[];
  preferences?: string; // JSON string from backend
}

// LoginInput & AuthPayload are now provided by GraphQL Codegen
