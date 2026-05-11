import type { Config } from "tailwindcss"

const config = {
  darkMode: ["class"],
  content: [
    './src/app/**/*.{ts,tsx}',
    './src/components/**/*.{ts,tsx}',
    '../../packages/ui/src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        michi: {
          purple: '#6C5CE7',
          dark: '#0F1419',
          gray: '#8B98A5',
          light: '#F7F9FC',
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config

export default config
