import pytest
from unittest.mock import MagicMock
import redis.asyncio as aioredis
from core.security.locks import distributed_lock, RedisDistributedLock

class MockRedis:
    def __init__(self):
        self.storage = {}

    async def ping(self):
        return True

    async def set(self, key, value, ex=None, nx=False):
        if nx and key in self.storage:
            return None
        self.storage[key] = value
        return True

    async def eval(self, script, keys_num, key, client_id):
        if self.storage.get(key) == client_id:
            del self.storage[key]
            return 1
        return 0

    async def aclose(self):
        pass


@pytest.fixture
def mock_redis_connection(monkeypatch):
    mock_client = MockRedis()
    def mock_from_url(*args, **kwargs):
        return mock_client
    monkeypatch.setattr(aioredis, "from_url", mock_from_url)
    return mock_client


async def test_distributed_lock_acquire_and_release(mock_redis_connection):
    key = "store_test_lock"
    
    # 1. Premier acquéreur
    async with distributed_lock(key) as acquired1:
        assert acquired1 is True
        
        # 2. Tente d'acquérir le même verrou pendant qu'il est détenu
        # On utilise une instance différente du verrou pour simuler un autre processus
        lock2 = RedisDistributedLock(key)
        acquired2 = await lock2.acquire()
        assert acquired2 is False
        
    # 3. Une fois libéré, le verrou doit être disponible à nouveau
    async with distributed_lock(key) as acquired3:
        assert acquired3 is True
