import hashlib
import json
from typing import Optional, Any

import redis.asyncio as aioredis

from app.config import settings


_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


def make_cache_key(model: str, messages: list, **kwargs) -> str:
    payload = json.dumps({"model": model, "messages": messages, **kwargs},
                         sort_keys=True)
    return f"cache:{hashlib.sha256(payload.encode()).hexdigest()}"


async def get_cached_response(key: str) -> Optional[Any]:
    client = await get_redis()
    data = await client.get(key)
    if data:
        return json.loads(data)
    return None


async def set_cached_response(key: str, value: Any, ttl: int = None) -> None:
    client = await get_redis()
    await client.setex(key, ttl or settings.CACHE_TTL, json.dumps(value))


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
