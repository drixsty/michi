/**
 * Card — conteneur surface Michi 道.
 * Découpage : Card, CardHeader, CardBody, CardFooter.
 */
import React from 'react';
import { colors } from '../tokens/colors';
import { spacing, borderRadius } from '../tokens/spacing';
import { typography } from '../tokens/typography';

export interface CardProps {
  /** Ajoute une ombre légère */
  elevated?: boolean;
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export interface CardHeaderProps {
  title: string;
  subtitle?: string;
  /** Slot pour action (ex: Badge, Button) */
  action?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export interface CardBodyProps {
  children: React.ReactNode;
  /** Supprime le padding interne */
  noPadding?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export function Card({ elevated = false, children, className, style }: CardProps) {
  const baseStyle: React.CSSProperties = {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    border: `1px solid ${colors.border}`,
    overflow: 'hidden',
    boxShadow: elevated
      ? '0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05)'
      : 'none',
    ...style,
  };

  return (
    <div className={className} style={baseStyle}>
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action, className, style }: CardHeaderProps) {
  const baseStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: spacing[3],
    padding: `${spacing[4]} ${spacing[4]} 0`,
    ...style,
  };

  return (
    <div className={className} style={baseStyle}>
      <div>
        <p
          style={{
            margin: 0,
            fontSize: typography.fontSize.base,
            fontWeight: typography.fontWeight.semibold,
            fontFamily: typography.fontFamily.sans,
            color: colors.cardForeground,
            lineHeight: typography.lineHeight.tight,
          }}
        >
          {title}
        </p>
        {subtitle && (
          <p
            style={{
              margin: `${spacing[1]} 0 0`,
              fontSize: typography.fontSize.sm,
              fontFamily: typography.fontFamily.sans,
              color: colors.mutedForeground,
              lineHeight: typography.lineHeight.normal,
            }}
          >
            {subtitle}
          </p>
        )}
      </div>
      {action && <div style={{ flexShrink: 0 }}>{action}</div>}
    </div>
  );
}

export function CardBody({ children, noPadding = false, className, style }: CardBodyProps) {
  const baseStyle: React.CSSProperties = {
    padding: noPadding ? 0 : spacing[4],
    ...style,
  };

  return (
    <div className={className} style={baseStyle}>
      {children}
    </div>
  );
}

export function CardFooter({ children, className, style }: CardFooterProps) {
  const baseStyle: React.CSSProperties = {
    padding: `0 ${spacing[4]} ${spacing[4]}`,
    display: 'flex',
    alignItems: 'center',
    gap: spacing[3],
    borderTop: `1px solid ${colors.border}`,
    paddingTop: spacing[3],
    ...style,
  };

  return (
    <div className={className} style={baseStyle}>
      {children}
    </div>
  );
}
