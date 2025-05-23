import uuid
from functools import wraps
from typing import Any, Callable

from fastapi_cache.decorator import cache


def generate_unique_id() -> str:
    """Generate a unique ID string."""
    return str(uuid.uuid4())


def cached(
    expire: int = 60,
    namespace: str = "api",
    key_builder: Callable = None
):
    """
    Cache decorator that uses FastAPI-cache with custom defaults.
    
    Args:
        expire: Cache expiration time in seconds
        namespace: Cache namespace
        key_builder: Custom key builder function
        
    Returns:
        Decorated function with caching
    """
    return cache(expire=expire, namespace=namespace, key_builder=key_builder) 