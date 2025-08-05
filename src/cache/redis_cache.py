import os
import json
import redis.asyncio as redis
import datetime as dt
from typing import Optional

# Global Redis connection pool
_redis_pool = None

async def get_redis():
    """Get Redis connection from pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True
        )
    return redis.Redis(connection_pool=_redis_pool)

TTL_DAYS = int(os.getenv("REDIS_TTL_DAYS", 30))

async def get(key: str) -> Optional[str]:
    """Get value from Redis cache."""
    r = await get_redis()
    return await r.get(key)

async def set(key: str, value: str, ttl: int = None) -> None:
    """Set value in Redis cache with TTL."""
    r = await get_redis()
    if ttl is None:
        ttl = TTL_DAYS * 24 * 3600
    await r.set(key, value, ex=ttl)

# Legacy functions for backward compatibility
async def get_md(key: str) -> Optional[str]:
    """Return markdown answer or None."""
    return await get(key)

async def set_md(key: str, md: str) -> None:
    """Store answer with rolling TTL."""
    await set(key, md) 