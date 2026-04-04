/**
 * TypeScript Types
 */

export interface User {
  id: string;
  email: string;
  shopId: string;
  createdAt: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface AuthPayload {
  token: string;
  user: User;
}
