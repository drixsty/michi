/**
 * @michi/ui — barrel principal.
 * Exporte tokens de design + composants agnostiques.
 */

// Tokens
export { colors, typography, spacing, borderRadius } from './tokens';
export type { ColorToken, TypographyToken, SpacingToken, BorderRadiusToken } from './tokens';

// Composants
export { Button, Badge, Card, CardHeader, CardBody, CardFooter } from './components';
export type {
  ButtonProps,
  ButtonVariant,
  ButtonSize,
  BadgeProps,
  BadgeVariant,
  CardProps,
  CardHeaderProps,
  CardBodyProps,
  CardFooterProps,
} from './components';
