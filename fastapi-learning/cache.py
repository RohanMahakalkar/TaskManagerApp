import json
import os
from typing import Optional

from redis import Redis, RedisError

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_TTL = int(os.getenv("REDIS_TTL_SECONDS", "60"))

redis_client: Optional[Redis]

try:
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
except Exception:
    redis_client = None


def get_cache(key: str) -> Optional[str]:
    if not redis_client:
        return None
    try:
        return redis_client.get(key)
    except RedisError:
        return None


def set_cache(key: str, value: dict, ttl: int = REDIS_TTL) -> None:
    if not redis_client:
        return
    try:
        redis_client.set(key, json.dumps(value, default=str), ex=ttl)
    except RedisError:
        pass


def invalidate_user_tasks_cache(user_id: str) -> None:
    if not redis_client:
        return
    try:
        pattern = f"tasks:{user_id}:*"
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except RedisError:
        pass
