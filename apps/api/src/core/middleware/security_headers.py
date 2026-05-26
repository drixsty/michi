"""
Middleware de sécurité HTTP.
Injecte les headers de sécurité standard sur toutes les réponses.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injecte les headers de sécurité recommandés par OWASP.
    Adapte CSP et HSTS selon l'environnement.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Empêche le MIME-sniffing (type confusion attacks)
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Clickjacking — on bloque l'intégration dans des iframes tierces
        response.headers["X-Frame-Options"] = "DENY"

        # Force HTTPS pendant 1 an en production (preload eligible)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Referrer minimal — évite les fuites d'URL dans les headers HTTP Referer
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy — désactive les APIs navigateur inutilisées
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # CSP — restreint les sources de contenu exécutable
        # En dev on autorise unsafe-inline pour GraphiQL et les hot-reload tools
        if settings.ENVIRONMENT == "development":
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self' ws: wss:;"
            )
        else:
            csp = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
        response.headers["Content-Security-Policy"] = csp

        # Supprime le header serveur pour réduire la surface d'empreinte
        if "server" in response.headers:
            del response.headers["server"]
        if "Server" in response.headers:
            del response.headers["Server"]

        return response
