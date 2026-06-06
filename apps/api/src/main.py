"""
Point d'entrée FastAPI - Michi Backend
"""
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
from strawberry.fastapi import GraphQLRouter
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from core.config import settings

# Initialize Sentry APM if DSN is configured
if settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=1.0 if settings.ENVIRONMENT == "development" else 0.1,
    )
    from loguru import logger
    logger.info("Sentry APM integration initialized successfully.")

from core.graphql.schema import schema
from core.graphql.context import GraphQLContext
from core.di import build_services
import asyncio
import uuid
from core.database import get_db
from core.database import SerializedAsyncSession, ReentrantAsyncLock
from core.middleware.auth import get_current_user_from_token
from core.middleware.security_headers import SecurityHeadersMiddleware
from core.monitoring.prometheus import PrometheusMiddleware, prometheus_metrics
from modules.shopify.adapters.auth_routes import router as shopify_auth_router
from modules.billing.adapters.router import router as billing_router
from core.exceptions import UnauthenticatedException, MichiException
from modules.intelligence.application.worker import worker as intelligence_worker
from loguru import logger
import sys
import logging


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def log_filter(record):
    """Filtre pour éviter les tracebacks complets sur les erreurs d'auth attendues"""
    msg = record["message"].lower()
    if "unauthenticatedexception" in msg or "authentication required" in msg:
        return "[security]" in msg

    if record["extra"].get("exception"):
        exc = record["extra"]["exception"]
        if "UnauthenticatedException" in str(exc):
            return False

    return True


logger.remove()
# Utilisation de la sérialisation JSON en production pour l'agrégation de logs (Loki, Datadog)
logger.add(
    sys.stderr, 
    filter=log_filter, 
    level=settings.LOG_LEVEL,
    serialize=(settings.ENVIRONMENT == "production")
)

logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
logging.getLogger("strawberry").handlers = [InterceptHandler()]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan events (startup/shutdown)"""
    logger.info(f"Michi API starting — env={settings.ENVIRONMENT}")
    logger.info(f"CORS origins: {settings.cors_origins_list}")

    if settings.RUN_BACKGROUND_WORKERS_IN_API:
        logger.info("[Lifespan] Starting background workers inline...")
        from modules.inventory.application.cron_worker import worker as cron_worker
        asyncio.create_task(intelligence_worker.start())
        asyncio.create_task(cron_worker.start())
    else:
        logger.info("[Lifespan] Standalone background workers enabled. Bypassing inline workers.")

    yield

    logger.info("Michi API shutting down")


app = FastAPI(
    title="Michi API",
    description="Inventory Forecasting Platform",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# Security headers — avant CORS pour s'appliquer à toutes les réponses
app.add_middleware(SecurityHeadersMiddleware)

# CORS — origines depuis la config uniquement ; localhost injecté en dev uniquement
CORS_ALLOWED_ORIGINS = list(settings.cors_origins_list)
if settings.ENVIRONMENT == "development":
    for origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
        if origin not in CORS_ALLOWED_ORIGINS:
            CORS_ALLOWED_ORIGINS.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "michi-org-id",
        "Michi-Org-Id",
        "apollo-require-preflight",
        "Stripe-Signature",
    ],
)

app.add_middleware(PrometheusMiddleware)


async def _resolve_org_id_from_header(
    user_id: str, header_org_id: str, db: AsyncSession
) -> str | None:
    """
    Valide que l'utilisateur est bien membre de l'org fournie dans le header.
    Protège contre les attaques IDOR (accès à une org tierce par manipulation du header).
    Retourne l'org_id validé ou None si non autorisé.
    """
    from core.database.models import OrganizationMember
    from core.database.constants import UserRole
    try:
        uid = uuid.UUID(user_id)
        oid = uuid.UUID(header_org_id)
    except ValueError:
        return None

    # Autorisation spéciale : Si l'utilisateur est un agent de support (possède le rôle SUPPORT dans une org)
    support_stmt = select(OrganizationMember.user_id).where(
        OrganizationMember.user_id == uid,
        OrganizationMember.role == UserRole.SUPPORT
    )
    support_result = await db.execute(support_stmt)
    if support_result.scalar():
        logger.info(f"[Support] Impersonation authorized: support_user={user_id} → target_org={header_org_id}")
        return header_org_id

    stmt = select(OrganizationMember.user_id).where(
        OrganizationMember.user_id == uid,
        OrganizationMember.organization_id == oid,
    )
    result = await db.execute(stmt)
    if result.scalar():
        return header_org_id

    logger.warning(
        f"[Security] IDOR attempt blocked: user={user_id} → org={header_org_id} (not a member)"
    )
    import asyncio
    from core.security.alerts import send_slack_alert
    asyncio.create_task(send_slack_alert(
        f"🚨 *[Security Alert]* IDOR attempt blocked!\n"
        f"• *User ID:* `{user_id}`\n"
        f"• *Target Org ID:* `{header_org_id}`\n"
        f"• *Action:* Impersonation/Switch Blocked"
    ))
    return None


async def get_context(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> GraphQLContext:
    """
    Crée le contexte GraphQL pour chaque requête.
    Extrait user_id et org_id du token JWT, valide le header org_id si nécessaire.
    """
    try:
        user_id, org_id, email = await get_current_user_from_token(request)
    except UnauthenticatedException:
        user_id, org_id, email = None, None, None

    # Si le header est fourni, on tente de le résoudre (impersonation support ou switch).
    # Sinon, on conserve l'org_id du token.
    if user_id:
        header_org_id = (
            request.headers.get("michi-org-id")
            or request.headers.get("Michi-Org-Id")
        )
        if header_org_id:
            org_id = await _resolve_org_id_from_header(user_id, header_org_id, db)

    from core.database.session import session_flow_id
    flow_id = str(uuid.uuid4())
    session_flow_id.set(flow_id)

    lock = ReentrantAsyncLock()
    serialized_db = SerializedAsyncSession(db, lock)

    services_container = build_services(serialized_db)
    
    from core.graphql.dataloaders import create_store_loader, create_supplier_loader
    store_loader = create_store_loader(serialized_db)
    supplier_loader = create_supplier_loader(serialized_db)

    return GraphQLContext(
        db=serialized_db,
        user_id=user_id,
        org_id=org_id,
        email=email,
        billing=services_container.billing_service,
        services=services_container,
        store_loader=store_loader,
        supplier_loader=supplier_loader
    )


from graphql import GraphQLError


def custom_process_errors(self, errors: list[GraphQLError], execution_context=None):
    """
    Gestionnaire d'erreurs centralisé (Standard DDD/Hexagonal).
    Intercepte les MichiException pour un logging propre sans stacktrace.
    """
    from core.database.session import session_flow_id
    flow_id = session_flow_id.get()

    actual_errors = errors
    if execution_context and hasattr(execution_context, "result") and execution_context.result:
        actual_errors = execution_context.result.errors or errors

    processed_errors = []
    for error in actual_errors:
        orig = error.original_error

        if error.extensions is None:
            error.extensions = {}
            
        if flow_id:
            error.extensions["flowId"] = str(flow_id)

        if isinstance(orig, MichiException):
            log_msg = f"[Business Error] {orig.code}: {orig.message}"
            if orig.logging_level == "INFO":
                logger.info(log_msg)
            elif orig.logging_level == "WARNING":
                logger.warning(log_msg)
            elif orig.logging_level == "ERROR":
                logger.error(log_msg)
            else:
                logger.warning(log_msg)

            error.extensions.update({
                "code": orig.code,
                "details": orig.details
            })

        elif orig:
            logger.critical(f"[System Error] {str(orig)}", exception=orig)
            error.message = "Internal Server Error"
            error.extensions.update({"code": "INTERNAL_ERROR"})
            
            import asyncio
            from core.security.alerts import send_slack_alert
            asyncio.create_task(send_slack_alert(
                f"🔥 *[System Error]* Critical exception occurred!\n"
                f"• *Error:* `{str(orig)}`\n"
                f"• *Flow ID:* `{flow_id}`"
            ))

        else:
            logger.debug(f"[GraphQL Syntax/Validation] {error.message}")

        processed_errors.append(error.formatted)
    return processed_errors


graphql_app = GraphQLRouter(
    schema,
    graphql_ide="graphiql",
    context_getter=get_context,
)

setattr(graphql_app, "process_errors", custom_process_errors.__get__(graphql_app, GraphQLRouter))

app.include_router(graphql_app, prefix="/graphql")
app.include_router(shopify_auth_router)
app.include_router(billing_router)


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """
    Health check enrichi — vérifie la connectivité DB et Redis.
    Utilisé par les load balancers et le monitoring.
    """
    checks: dict = {"api": "ok", "db": "unknown", "redis": "unknown"}
    status_code = 200

    # DB liveness
    try:
        await db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:
        logger.error(f"[Health] DB check failed: {e}")
        checks["db"] = "error"
        status_code = 503

    # Redis liveness
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        logger.warning(f"[Health] Redis check failed: {e}")
        checks["redis"] = "degraded"

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if status_code == 200 else "degraded",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "checks": checks,
        }
    )


@app.get("/metrics")
def metrics():
    return prometheus_metrics()


@app.get("/")
async def root():
    return {
        "message": "Michi API 道 (Omnichannel)",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else None,
        "graphql": "/graphql",
        "health": "/health",
        "metrics": "/metrics",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )
