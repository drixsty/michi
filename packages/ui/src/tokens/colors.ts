/**
 * Tokens couleur Michi 道 — source unique de vérité.
 * Reflète les variables CSS de globals.css (apps/web).
 * Utilisable dans web (Tailwind via CSS vars) et mobile (StyleSheet).
 */
export const colors = {
  // Brand Michi — violet
  primary: {
    DEFAULT: 'hsl(262, 83%, 58%)',
    foreground: 'hsl(210, 40%, 98%)',
    50: 'hsl(262, 83%, 96%)',
    100: 'hsl(262, 83%, 90%)',
    500: 'hsl(262, 83%, 58%)',
    600: 'hsl(262, 83%, 50%)',
    700: 'hsl(262, 83%, 42%)',
  },

  // Neutrals
  background: 'hsl(0, 0%, 100%)',
  foreground: 'hsl(0, 0%, 9%)',
  card: 'hsl(0, 0%, 100%)',
  cardForeground: 'hsl(0, 0%, 9%)',
  muted: 'hsl(210, 40%, 96.1%)',
  mutedForeground: 'hsl(215.4, 16.3%, 46.9%)',
  border: 'hsl(214.3, 31.8%, 91.4%)',

  // Sémantique
  destructive: 'hsl(0, 84.2%, 60.2%)',
  destructiveForeground: 'hsl(210, 40%, 98%)',

  // Status stock
  status: {
    critical: 'hsl(0, 84%, 60%)',      // rouge — rupture
    warning: 'hsl(38, 92%, 50%)',      // orange — tendu
    healthy: 'hsl(142, 71%, 45%)',     // vert — sain
    neutral: 'hsl(215, 16%, 47%)',     // gris — neutre
  },
} as const;

export type ColorToken = typeof colors;
