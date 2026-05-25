"""
Point d'entrée FastAPI - Michi Backend 
"""
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from .env if present (Hexagonal Adapter logic)
load_dotenv()
from strawberry.fastapi import GraphQLRouter
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.graphql.schema import schema
from core.graphql.context import GraphQLContext
from core.di import build_services
import asyncio
import uuid
from core.database import get_db
from core.database import SerializedAsyncSession, ReentrantAsyncLock
from core.middleware.auth import get_current_user_from_token
from modules.shopify.adapters.auth_routes import router as shopify_auth_router
from modules.billing.adapters.router import router as billing_router
from core.exceptions import UnauthenticatedException, ForbiddenException, MichiException
from modules.intelligence.application.worker import worker as intelligence_worker
from loguru import logger
import sys

# Configuration Loguru pour filtrer les tracebacks d'auth bruyants
import logging

class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def log_filter(record):
    """Filtre pour éviter les tracebacks complets sur les erreurs d'auth attendues"""
    msg = record["message"].lower()
    # On masque les UnauthenticatedException et les "Authentication required" du flux standard
    if "unauthenticatedexception" in msg or "authentication required" in msg:
        # On ne garde que si c'est taggué [Security] explicitement (audit)
        return "[security]" in msg
    
    # Éviter les logs de pollution de strawberry/graphql-core sur les erreurs d'auth
    if record["extra"].get("exception"):
        exc = record["extra"]["exception"]
        if "UnauthenticatedException" in str(exc):
            return False

    return True

logger.remove()
logger.add(sys.stderr, filter=log_filter, level="INFO")

# Intercepter les logs standards (FastAPI, Uvicorn, GraphQL)
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
logging.getLogger("strawberry").handlers = [InterceptHandler()]



@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan events (startup/shutdown)"""
    # Startup
    print("[INFO] Michi API starting...")
    print(">>> [DEBUG] CHARGEMENT DE MICI MAIN.PY OK <<<")
    print("[INFO] Sprint 13: Strategic BI active.")
    print(f"[INFO] Environment: {settings.ENVIRONMENT}")
    print(f"[INFO] CORS Origins: {settings.cors_origins_list}")
    
    # Lancement des Workers de Background (SaaS Architecture)
    from modules.inventory.application.cron_worker import worker as cron_worker
    asyncio.create_task(intelligence_worker.start())
    asyncio.create_task(cron_worker.start())
    
    yield
    
    # Shutdown
    print("[INFO] Michi API shutting down...")


# Créer l'app FastAPI
app = FastAPI(
    title="Michi API",
    description="Inventory Forecasting Platform",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)


# CORS Middleware (Configuration standard FastAPI optimisée)
# En dev, on autorise explicitement localhost:3000 avec credentials pour Apollo Client
CORS_ALLOWED_ORIGINS = settings.cors_origins_list
if "http://localhost:3000" not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append("http://localhost:3000")
if "http://127.0.0.1:3000" not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append("http://127.0.0.1:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


async def get_context(
    request: Request, 
    db: AsyncSession = Depends(get_db)
) -> GraphQLContext:
    """
    Crée le context GraphQL pour chaque requête.
    Extrait user_id et org_id du token JWT.
    """
    # Extraire user_id/org_id/email du token JWT
    try:
        user_id, org_id, email = await get_current_user_from_token(request)
    except UnauthenticatedException:
        user_id, org_id, email = None, None, None
    
    # Fallback sur le header si org_id n'est pas dans le token (onboarding/switch)
    if user_id and not org_id:
        org_id = request.headers.get("michi-org-id") or request.headers.get("Michi-Org-Id")
    
    # Initialiser l'ID de flux unique pour cette requête
    from core.database.session import session_flow_id
    flow_id = str(uuid.uuid4())
    session_flow_id.set(flow_id)
    
    # Sérialiser la session DB pour GraphQL (concurrence inter-résolveurs)
    lock = ReentrantAsyncLock()
    serialized_db = SerializedAsyncSession(db, lock)
    
    # DI Container (Sprint 21)
    services_container = build_services(serialized_db)
    
    return GraphQLContext(
        db=serialized_db,
        user_id=user_id,
        org_id=org_id,
        email=email,
        billing=services_container.billing_service,
        services=services_container
    )


from graphql import GraphQLError

def custom_process_errors(self, errors: list[GraphQLError], execution_context=None):
    """
    Gestionnaire d'erreurs centralisé (Standard DDD/Hexagonal).
    Intercepte les MichiException pour un logging propre sans stacktrace.
    """
    # Pour Strawberry 0.315+, on récupère les erreurs depuis le résultat si dispo
    actual_errors = errors
    if execution_context and hasattr(execution_context, "result") and execution_context.result:
        actual_errors = execution_context.result.errors or errors

    processed_errors = []
    for error in actual_errors:
        orig = error.original_error
        
        # 1. Gestion des exceptions métier Michi
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
            
            # Formater pour GraphQL
            if error.extensions is None:
                error.extensions = {}
            error.extensions.update({
                "code": orig.code,
                "details": orig.details
            })
        
        # 2. Gestion des erreurs inattendues (Sûreté)
        elif orig:
            # On logue l'erreur réelle avec stacktrace uniquement pour les erreurs système
            logger.critical(f"[System Error] {str(orig)}", exception=orig)
            error.message = "Internal Server Error"
            if error.extensions is None:
                error.extensions = {}
            error.extensions.update({"code": "INTERNAL_ERROR"})
        
        else:
            # Erreurs de syntaxe GraphQL etc.
            logger.debug(f"[GraphQL Syntax/Validation] {error.message}")

        processed_errors.append(error.formatted)
    return processed_errors

# GraphQL Router
graphql_app = GraphQLRouter(
    schema,
    graphql_ide="graphiql",
    context_getter=get_context,
)

# On injecte la gestion d'erreurs personnalisée
setattr(graphql_app, "process_errors", custom_process_errors.__get__(graphql_app, GraphQLRouter))

app.include_router(graphql_app, prefix="/graphql")
app.include_router(shopify_auth_router)
app.include_router(billing_router)


# Health Check
@app.get("/health")
async def health():
    """
    Health check endpoint.
    Utilisé par les load balancers et monitoring.
    """
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint avec liens utiles"""
    return {
        "message": "Michi API 道 (Omnichannel)",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else None,
        "graphql": "/graphql",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )
