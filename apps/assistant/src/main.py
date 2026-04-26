from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
import strawberry
from strawberry.fastapi import GraphQLRouter
from contextlib import asynccontextmanager
from loguru import logger

from core.config.settings import settings
from modules.chat.web.resolvers import schema

from core.database import init_db, AsyncSessionLocal

@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("[INFO] Michi Assistant starting...")
    # Initialisation des tables au démarrage
    try:
        await init_db()
        logger.info("[OK] Assistant Database initialized.")
    except Exception as e:
        logger.error(f"[ERROR] Database init failed: {e}")
    yield
    logger.info("[INFO] Michi Assistant shutting down...")

app = FastAPI(
    title="Michi Assistant",
    description="Plugin intelligent pour la plateforme Michi",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db_session():
    """Générateur de session DB avec fermeture automatique"""
    async with AsyncSessionLocal() as session:
        yield session

async def get_context(
    request: Request,
    db = Depends(get_db_session)
):
    """Context GraphQL injectant la session DB gérée par FastAPI"""
    return {
        "request": request,
        "db": db
    }

graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "assistant"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
