import os
import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
# 2 дня не парсим одну вакансию дважды. Только один раз отправляем
TTL_SECONDS = 60 * 60 * 24 * 2

_redis: aioredis.Redis | None = None

async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis

# Чекаем отправляли ли вакансию в Кафку
async def is_seen(vacancy_id: str) -> bool:
    r = await get_redis()
    return await r.exists(f"seen:{vacancy_id}") == 1


# Помечаем вакансию как обработанную.
async def mark_seen(vacancy_id: str) -> None:
    r = await get_redis()
    await r.setex(f"seen:{vacancy_id}", TTL_SECONDS, "1")


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None