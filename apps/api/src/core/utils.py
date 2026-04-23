import asyncio
import functools
from loguru import logger
from typing import Callable, Any, TypeVar, cast

T = TypeVar("T", bound=Callable[..., Any])

def retry(retries: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator to retry an async function with exponential backoff.
    """
    def decorator(func: T) -> T:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            _retries, _delay = retries, delay
            while _retries > 1:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(f"Retrying {func.__name__} due to {e}. {_retries-1} retries left...")
                    await asyncio.sleep(_delay)
                    _retries -= 1
                    _delay *= backoff
            return await func(*args, **kwargs)
        return cast(T, wrapper)
    return decorator
