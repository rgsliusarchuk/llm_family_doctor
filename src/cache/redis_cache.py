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
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        print(f"🔗 Connecting to Redis: {redis_url}")
        _redis_pool = redis.ConnectionPool.from_url(
            redis_url,
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

# New functions for storing both full diagnosis and patient response
async def set_diagnosis_with_patient_response(key: str, full_diagnosis: str, patient_response: str) -> None:
    """Store both full diagnosis and patient response with rolling TTL."""
    r = await get_redis()
    ttl = TTL_DAYS * 24 * 3600
    
    # Store full diagnosis with original key
    await r.set(key, full_diagnosis, ex=ttl)
    
    # Store patient response with patient_ prefix
    patient_key = f"patient_{key}"
    await r.set(patient_key, patient_response, ex=ttl)

async def get_patient_response(key: str) -> Optional[str]:
    """Get patient response from cache."""
    r = await get_redis()
    patient_key = f"patient_{key}"
    return await r.get(patient_key)

async def clear_cache() -> None:
    """Clear all data from Redis cache."""
    r = await get_redis()
    await r.flushall()

async def clear_pattern(pattern: str = "*") -> None:
    """Clear cache keys matching a pattern."""
    r = await get_redis()
    keys = await r.keys(pattern)
    if keys:
        await r.delete(*keys) 