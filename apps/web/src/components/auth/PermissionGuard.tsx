'use client';

import React from 'react';
import { usePermissions, Permission } from '@/hooks/usePermissions';
import { useRouter } from 'next/navigation';
import { UnauthorizedView } from '@/components/layout/UnauthorizedView';

interface PermissionGuardProps {
  permission: Permission;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  redirectTo?: string;
}

/**
 * PermissionGuard: Wraps components to ensure the user has the required permission.
 * If permission is missing, it shows the UnauthorizedView or redirects if requested.
 */
export const PermissionGuard: React.FC<PermissionGuardProps> = ({ 
  permission, 
  children, 
  fallback,
  redirectTo
}) => {
  const { can, loading } = usePermissions();
  const router = useRouter();

  React.useEffect(() => {
    if (!loading && !can(permission) && redirectTo) {
      router.push(redirectTo);
    }
  }, [can, loading, permission, redirectTo, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[200px]">
        <div className="h-6 w-6 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  if (!can(permission)) {
    if (redirectTo) return null; // Wait for redirection
    return (fallback as React.ReactElement) || <UnauthorizedView />;
  }

  return <>{children}</>;
};
