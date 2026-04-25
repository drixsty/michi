'use client';

import { useStore } from '@/context/StoreContext';

/**
 * Enum de tous les codes de permission — source de vérité frontend.
 * Doit rester synchronisé avec modules.auth.domain.permissions.PermissionCode (backend).
 */
export enum Permission {
  // Organisation
  ORG_VIEW            = "org:view",
  ORG_EDIT            = "org:edit",
  ORG_MANAGE_MEMBERS  = "org:manage_members",
  ORG_BILLING         = "org:billing",
  ORG_EXPORT          = "org:export",
  ORG_DELETE          = "org:delete",
  ORG_AUDIT           = "org:audit",

  // Membres
  MEMBERS_VIEW        = "members:view",
  MEMBERS_INVITE      = "members:invite",
  MEMBERS_REMOVE      = "members:remove",
  MEMBERS_EDIT_ROLE   = "members:edit_role",

  // Inventaire
  INVENTORY_VIEW      = "inventory:view",
  INVENTORY_EDIT      = "inventory:edit",
  INVENTORY_DELETE    = "inventory:delete",
  INVENTORY_IMPORT    = "inventory:import",

  // Fournisseurs
  SUPPLIER_VIEW       = "supplier:view",
  SUPPLIER_EDIT       = "supplier:edit",
  SUPPLIER_DELETE     = "supplier:delete",

  // Prévisions
  FORECAST_VIEW       = "forecast:view",
  FORECAST_SIMULATE   = "forecast:simulate",
  FORECAST_EXPORT     = "forecast:export",
  FORECAST_RUN        = "forecast:run",

  // Stores / Connexions
  STORES_VIEW         = "stores:view",
  STORES_MANAGE       = "stores:manage",

  // Paramètres
  SETTINGS_VIEW       = "settings:view",
  SETTINGS_EDIT       = "settings:edit",
  SETTINGS_MANAGE_APIS = "settings:manage_apis",

  // Billing
  BILLING_VIEW        = "billing:view",
  BILLING_MANAGE      = "billing:manage",

  // Audit
  AUDIT_VIEW          = "audit:view",
}

const ROLE_HIERARCHY = ["VIEWER", "MANAGER", "ADMIN", "OWNER"] as const;
type Role = typeof ROLE_HIERARCHY[number];

/**
 * Hook centralisé pour la gestion des permissions.
 * 
 * Lit les données depuis le StoreContext (cache Apollo GET_ME) —
 * aucun appel réseau supplémentaire.
 * 
 * @example
 * const { can, isAdmin } = usePermissions();
 * if (can(Permission.INVENTORY_EDIT)) { ... }
 */
export function usePermissions() {
  const { organizations, currentOrganization, loading } = useStore();

  // Trouver le membership de l'organisation courante
  const currentMembership = organizations.find((m: any) => {
    const mId = String(m.organization?.id || m.organizationId || '');
    const cId = String(currentOrganization?.id || '');
    return mId === cId;
  }) ?? organizations[0];

  const rawPermissions: string[] = (currentMembership as any)?.computedPermissions ?? [];
  const rawRole: string = ((currentMembership as any)?.role ?? 'VIEWER').toUpperCase();
  const role = (ROLE_HIERARCHY.includes(rawRole as Role) ? rawRole : 'VIEWER') as Role;

  const isOwner = role === 'OWNER';
  const isAdmin = role === 'ADMIN' || role === 'OWNER';
  const isManager = isAdmin || role === 'MANAGER';

  /**
   * Vérifie si l'utilisateur possède UNE permission donnée.
   * OWNER a toujours accès à tout.
   */
  const can = (permission: Permission | string): boolean => {
    if (isOwner) return true;
    return rawPermissions.includes(permission as string);
  };

  /**
   * Vérifie si l'utilisateur possède AU MOINS UNE des permissions listées.
   */
  const canAny = (permissions: (Permission | string)[]): boolean => {
    if (isOwner) return true;
    return permissions.some(p => rawPermissions.includes(p as string));
  };

  /**
   * Vérifie si l'utilisateur possède TOUTES les permissions listées.
   */
  const canAll = (permissions: (Permission | string)[]): boolean => {
    if (isOwner) return true;
    return permissions.every(p => rawPermissions.includes(p as string));
  };

  /**
   * Vérifie si le rôle de l'utilisateur est au moins égal au rôle cible.
   * @example isAtLeast('ADMIN') → true pour ADMIN et OWNER
   */
  const isAtLeast = (targetRole: Role | string): boolean => {
    const currentIndex = ROLE_HIERARCHY.indexOf(role);
    const targetIndex = ROLE_HIERARCHY.indexOf(targetRole.toUpperCase() as Role);
    return currentIndex >= targetIndex;
  };

  // Alias legacy pour compatibilité avec le Navbar existant
  const hasPermission = can;
  const hasAnyPermission = canAny;

  return {
    // Données brutes
    permissions: rawPermissions,
    role,

    // Helpers de rôle rapides
    isOwner,
    isAdmin,
    isManager,

    // Vérification de permissions
    can,
    canAny,
    canAll,
    isAtLeast,

    // Aliases legacy
    hasPermission,
    hasAnyPermission,

    loading,
  };
}
