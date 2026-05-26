import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';
import { type NextRequest, NextResponse } from 'next/server';

const intlMiddleware = createMiddleware(routing);

/** Routes qui exigent une session active (cookie michi_auth présent). */
const PROTECTED_SEGMENTS = ['/dashboard', '/onboarding'];

/** Routes accessibles uniquement quand on est PAS connecté. */
const AUTH_SEGMENTS = ['/login', '/register'];

function isProtected(pathname: string): boolean {
  return PROTECTED_SEGMENTS.some((s) => pathname.includes(s));
}

function isAuthPage(pathname: string): boolean {
  return AUTH_SEGMENTS.some((s) => pathname.includes(s));
}

export default function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;
  const hasSession = request.cookies.has('michi_auth');

  // Rediriger vers login si la route est protégée et pas de session
  if (isProtected(pathname) && !hasSession) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = '/login';
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Rediriger vers dashboard si déjà connecté et sur une page d'auth
  if (isAuthPage(pathname) && hasSession) {
    const dashboardUrl = request.nextUrl.clone();
    dashboardUrl.pathname = '/dashboard';
    dashboardUrl.search = '';
    return NextResponse.redirect(dashboardUrl);
  }

  // Déléguer l'internationalisation à next-intl
  return intlMiddleware(request);
}

export const config = {
  matcher: [
    // Exclure fichiers statiques et internals Next.js, inclure tout le reste
    '/((?!_next|_vercel|.*\\..*).*)',
  ],
};
