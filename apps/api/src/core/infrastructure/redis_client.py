"""
Client Redis partagé (singleton async).
Utilisé par le rate limiter distribué et tout cache applicatif.
"""
from __future__ import annotations

import redis.asyncio as aioredis
from loguru import logger
from core.config import settings

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Retourne le client Redis singleton, le crée si nécessaire."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        try:
            await _redis_client.ping()
            logger.info(f"[Redis] Connected to {settings.REDIS_URL}")
        except Exception as e:
            logger.warning(f"[Redis] Connection failed: {e} — rate limiting will fall back to in-memory")
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
