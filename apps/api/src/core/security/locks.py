import uuid
import contextlib
import redis.asyncio as aioredis
from loguru import logger
from core.config import settings

class RedisDistributedLock:
    def __init__(self, key: str, lease_time: int = 600):
        self.key = f"lock:store:{key}"
        self.lease_time = lease_time
        self.client_id = str(uuid.uuid4())
        self.redis_client = None

    async def acquire(self) -> bool:
        try:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL, 
                decode_responses=True,
                socket_connect_timeout=1.0,
                socket_timeout=1.0
            )
            # Ping to verify active connection
            await self.redis_client.ping()
            
            # Set key if not exists (NX) with expiry (EX)
            result = await self.redis_client.set(
                self.key,
                self.client_id,
                ex=self.lease_time,
                nx=True
            )
            return bool(result)
        except Exception as e:
            # Fallback to True so we don't break local development or tests if Redis is down
            logger.warning(f"[RedisDistributedLock] Redis is unreachable, bypassing lock for {self.key}: {e}")
            self.redis_client = None
            return True

    async def release(self) -> None:
        if not self.redis_client:
            return
        try:
            # Lua script to release only if client_id matches (atomic release)
            lua_script = """
                if redis.call("get", KEYS[1]) == ARGV[1] then
                    return redis.call("del", KEYS[1])
                else
                    return 0
                end
            """
            await self.redis_client.eval(lua_script, 1, self.key, self.client_id)
        except Exception as e:
            logger.error(f"[RedisDistributedLock] Failed to release lock for {self.key}: {e}")
        finally:
            try:
                await self.redis_client.aclose()
            except Exception:
                pass


@contextlib.asynccontextmanager
async def distributed_lock(key: str, lease_time: int = 600):
    """Context manager asynchrone pour acquérir et libérer un verrou Redis."""
    lock = RedisDistributedLock(key, lease_time)
    acquired = await lock.acquire()
    try:
        yield acquired
    finally:
        if acquired:
            await lock.release()
