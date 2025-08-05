import os
import json
import redis
import datetime as dt
from typing import Optional

_r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                          decode_responses=True)

TTL_DAYS = int(os.getenv("REDIS_TTL_DAYS", 30))

def get_md(key: str) -> Optional[str]:
    """Return markdown answer or None."""
    return _r.get(key)

def set_md(key: str, md: str) -> None:
    """Store answer with rolling TTL."""
    _r.set(key, md, ex=TTL_DAYS*24*3600) 