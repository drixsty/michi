/**
 * Gestion centralisée du token d'authentification.
 * Écrit dans localStorage ET dans un cookie SameSite=Strict
 * pour permettre la protection SSR via middleware Next.js.
 */

const TOKEN_KEY = 'michi_token';
const COOKIE_NAME = 'michi_auth';
const COOKIE_MAX_AGE = 60 * 60 * 24; // 24 h — aligné sur ACCESS_TOKEN_EXPIRE_HOURS

export function setAuthToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
  document.cookie = [
    `${COOKIE_NAME}=1`,
    'path=/',
    `max-age=${COOKIE_MAX_AGE}`,
    'SameSite=Strict',
    process.env.NODE_ENV === 'production' ? 'Secure' : '',
  ]
    .filter(Boolean)
    .join('; ');
}

export function clearAuthToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem('michi_current_org');
  localStorage.removeItem('michi_current_org_id');
  // Expirer le cookie immédiatement
  document.cookie = `${COOKIE_NAME}=; path=/; max-age=0; SameSite=Strict`;
}

export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}
