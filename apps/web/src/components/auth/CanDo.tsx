'use client';

import React from 'react';
import { usePermissions } from '@/hooks/usePermissions';
import type { Permission } from '@/hooks/usePermissions';

interface CanDoProps {
  /** La permission requise pour afficher le contenu */
  permission?: Permission | string;
  /** Plusieurs permissions (toutes requises) */
  all?: (Permission | string)[];
  /** Plusieurs permissions (au moins une requise) */
  any?: (Permission | string)[];
  /** Rôle minimum requis (ex: 'ADMIN') */
  minRole?: string;
  /** Contenu à afficher si autorisé */
  children: React.ReactNode;
  /** Contenu alternatif si refusé (optionnel) */
  fallback?: React.ReactNode;
}

/**
 * Composant wrapper qui conditionne l'affichage selon les permissions.
 *
 * @example
 * // Afficher un bouton uniquement pour les admins
 * <CanDo permission={Permission.INVENTORY_EDIT}>
 *   <Button>Modifier</Button>
 * </CanDo>
 *
 * @example
 * // Avec fallback
 * <CanDo permission={Permission.ORG_MANAGE_MEMBERS} fallback={<span>Lecture seule</span>}>
 *   <InviteButton />
 * </CanDo>
 *
 * @example
 * // Rôle minimum
 * <CanDo minRole="ADMIN">
 *   <DangerZone />
 * </CanDo>
 */
export function CanDo({ permission, all, any, minRole, children, fallback = null }: CanDoProps) {
  const { can, canAll, canAny, isAtLeast, loading } = usePermissions();

  // Pendant le chargement, ne rien afficher pour éviter le flash
  if (loading) return null;

  let allowed = true;

  if (permission) {
    allowed = can(permission);
  } else if (all && all.length > 0) {
    allowed = canAll(all);
  } else if (any && any.length > 0) {
    allowed = canAny(any);
  } else if (minRole) {
    allowed = isAtLeast(minRole);
  }

  return allowed ? <>{children}</> : <>{fallback}</>;
}
