"""Async helper utilities."""
import asyncio
from typing import Any, Callable, Coroutine
from functools import wraps

async def with_timeout(coro: Coroutine, timeout: float) -> Any:
    """Run coroutine with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation timed out after {timeout} seconds")

def async_retry(retries: int = 3, delay: float = 1.0):
    """Retry async operation decorator."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < retries - 1:
                        await asyncio.sleep(delay)
            raise last_error
        return wrapper
    return decorator
