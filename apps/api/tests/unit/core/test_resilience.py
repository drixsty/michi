import pytest
import asyncio
from core.utils import retry

class MockService:
    def __init__(self):
        self.attempts = 0

    @retry(retries=3, delay=0.1)
    async def unstable_method(self, fail_until: int):
        self.attempts += 1
        if self.attempts < fail_until:
            raise ConnectionError("Service unavailable")
        return "Success"

@pytest.mark.asyncio
async def test_retry_success_eventually():
    service = MockService()
    # Devrait réussir à la 3ème tentative
    result = await service.unstable_method(fail_until=3)
    assert result == "Success"
    assert service.attempts == 3

@pytest.mark.asyncio
async def test_retry_failure_after_max_retries():
    service = MockService()
    # Devrait échouer car il demande 5 tentatives mais le max est 3
    with pytest.raises(ConnectionError):
        await service.unstable_method(fail_until=5)
    assert service.attempts == 3
