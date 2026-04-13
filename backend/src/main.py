"""
Point d'entrée FastAPI - Michi Backend 
"""
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.graphql.schema import schema
from src.core.graphql.context import GraphQLContext
import asyncio
from src.core.database import get_db
from src.core.database_utils import SerializedAsyncSession
from src.core.middleware.auth import get_current_user_from_token
from src.modules.shopify.auth_routes import router as shopify_auth_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan events (startup/shutdown)"""
    # Startup
    print("[INFO] Michi API starting...")
    print(">>> [DEBUG] CHARGEMENT DE MICI MAIN.PY OK <<<")
    print("[INFO] Sprint 13: Strategic BI active.")
    print(f"[INFO] Environment: {settings.ENVIRONMENT}")
    print(f"[INFO] CORS Origins: {settings.cors_origins_list}")
    
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Apollo-Require-Preflight",
        "X-Requested-With",
        "Accept"
    ],
)


# Context factory pour GraphQL
async def get_context(
    request: Request, 
    db: AsyncSession = Depends(get_db)
) -> GraphQLContext:
    """
    Crée le context GraphQL pour chaque requête.
    Extrait user_id et org_id du token JWT.
    """
    # Extraire user_id/org_id du token JWT
    user_id, org_id = await get_current_user_from_token(request)
    
    # Sérialiser la session DB pour GraphQL (concurrence inter-résolveurs)
    lock = asyncio.Lock()
    serialized_db = SerializedAsyncSession(db, lock)
    
    return GraphQLContext(
        db=serialized_db,
        user_id=user_id,
        org_id=org_id,
    )


# GraphQL Router
graphql_app = GraphQLRouter(
    schema,
    graphiql=settings.ENVIRONMENT == "development",
    context_getter=get_context,
)

app.include_router(graphql_app, prefix="/graphql")
app.include_router(shopify_auth_router)


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
        "message": "Michi API 道",
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
