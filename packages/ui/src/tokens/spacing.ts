/**
 * Tokens espacement Michi 道.
 * Grille de 4px. Touch targets min 44px (WCAG 2.1 AA).
 */
export const spacing = {
  0: '0px',
  1: '4px',
  2: '8px',
  3: '12px',
  4: '16px',
  5: '20px',
  6: '24px',
  8: '32px',
  10: '40px',
  12: '48px',
  16: '64px',
  20: '80px',
  24: '96px',

  // Touch target minimum (WCAG 2.1 AA)
  touchTarget: '44px',
} as const;

export const borderRadius = {
  none: '0px',
  sm: '4px',
  DEFAULT: '6px',
  md: '8px',
  lg: '12px',
  xl: '16px',
  '2xl': '20px',
  full: '9999px',
} as const;

export type SpacingToken = typeof spacing;
export type BorderRadiusToken = typeof borderRadius;
