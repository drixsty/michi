/**
 * Badge — indicateur de statut / label compact Michi 道.
 * Utilise les tokens status pour les variantes sémantiques.
 */
import React from 'react';
import { colors } from '../tokens/colors';
import { spacing, borderRadius } from '../tokens/spacing';
import { typography } from '../tokens/typography';

export type BadgeVariant =
  | 'default'
  | 'primary'
  | 'critical'
  | 'warning'
  | 'healthy'
  | 'neutral';

export interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

const variantStyles: Record<BadgeVariant, React.CSSProperties> = {
  default: {
    backgroundColor: colors.muted,
    color: colors.mutedForeground,
  },
  primary: {
    backgroundColor: colors.primary[100],
    color: colors.primary[700],
  },
  critical: {
    backgroundColor: 'hsl(0, 84%, 94%)',
    color: colors.status.critical,
  },
  warning: {
    backgroundColor: 'hsl(38, 92%, 90%)',
    color: 'hsl(38, 92%, 28%)',
  },
  healthy: {
    backgroundColor: 'hsl(142, 71%, 90%)',
    color: 'hsl(142, 71%, 25%)',
  },
  neutral: {
    backgroundColor: colors.muted,
    color: colors.status.neutral,
  },
};

export function Badge({ variant = 'default', children, className, style }: BadgeProps) {
  const baseStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    paddingLeft: spacing[2],
    paddingRight: spacing[2],
    paddingTop: '2px',
    paddingBottom: '2px',
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.medium,
    fontFamily: typography.fontFamily.sans,
    lineHeight: typography.lineHeight.normal,
    borderRadius: borderRadius.full,
    whiteSpace: 'nowrap',
    ...variantStyles[variant],
    ...style,
  };

  return (
    <span className={className} style={baseStyle}>
      {children}
    </span>
  );
}
