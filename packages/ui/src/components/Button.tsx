/**
 * Button — composant agnostique web/mobile Michi 道.
 * Web  : rendu <button> HTML standard.
 * Mobile : l'adaptateur React Native wrappera dans <TouchableOpacity>.
 */
import React from 'react';
import { colors } from '../tokens/colors';
import { spacing, borderRadius } from '../tokens/spacing';
import { typography } from '../tokens/typography';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'destructive';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  /** Icon placed before the label */
  leftIcon?: React.ReactNode;
  /** Icon placed after the label */
  rightIcon?: React.ReactNode;
  children: React.ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  /** Extra CSS class (web only) */
  className?: string;
  /** Extra inline style — usable on both web and mobile */
  style?: React.CSSProperties;
}

const sizeMap: Record<ButtonSize, { paddingH: string; paddingV: string; fontSize: string; minHeight: string }> = {
  sm: { paddingH: spacing[3], paddingV: spacing[2], fontSize: typography.fontSize.sm, minHeight: '32px' },
  md: { paddingH: spacing[4], paddingV: spacing[3], fontSize: typography.fontSize.base, minHeight: spacing.touchTarget },
  lg: { paddingH: spacing[6], paddingV: spacing[4], fontSize: typography.fontSize.lg, minHeight: '52px' },
};

const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
  primary: {
    backgroundColor: colors.primary.DEFAULT,
    color: colors.primary.foreground,
    border: 'none',
  },
  secondary: {
    backgroundColor: 'transparent',
    color: colors.primary.DEFAULT,
    border: `1.5px solid ${colors.primary.DEFAULT}`,
  },
  ghost: {
    backgroundColor: 'transparent',
    color: colors.foreground,
    border: 'none',
  },
  destructive: {
    backgroundColor: colors.destructive,
    color: colors.destructiveForeground,
    border: 'none',
  },
};

export function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  leftIcon,
  rightIcon,
  children,
  onClick,
  type = 'button',
  className,
  style,
}: ButtonProps) {
  const { paddingH, paddingV, fontSize, minHeight } = sizeMap[size];

  const baseStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing[2],
    paddingLeft: paddingH,
    paddingRight: paddingH,
    paddingTop: paddingV,
    paddingBottom: paddingV,
    fontSize,
    fontWeight: typography.fontWeight.medium,
    fontFamily: typography.fontFamily.sans,
    lineHeight: typography.lineHeight.tight,
    borderRadius: borderRadius.DEFAULT,
    minHeight,
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    opacity: disabled || loading ? 0.55 : 1,
    transition: 'opacity 150ms ease, background-color 150ms ease',
    outline: 'none',
    ...variantStyles[variant],
    ...style,
  };

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={className}
      style={baseStyle}
    >
      {loading ? <span aria-hidden>⏳</span> : leftIcon}
      <span>{children}</span>
      {!loading && rightIcon}
    </button>
  );
}
