
# Чисто для кэширования вакансии которые мы получили через кафку.
# В vacancy_sender когда мы получили в топик сообщение о вакансии мы сначала отправляем юзеру. Потом кэшируем в Redis

import json
import os
import logging
from email.quoprimime import decode

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
TTL_SECONDS = 60 * 60 * 24 * 1


# Глобальная переменная только в этом файле. Типо как final или const
_redis: aioredis.Redis | None = None


# Чисто для подключения к Редису. Подключаем конфиги и возвращаем готовый объект.
async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis


# Тут сохраняем в Редис. Типо как история поиска.
# Вакансии в редисе живут 1 день. Потом удаляется.
# Сохраняется как по user_id.
# Сохраняем только title, типо как description текст сообщения и ссылку на вакансию.
async def save_to_history(user_id: int, title: str, message_text: str, url: str) -> None:
    try:
        r = await get_redis()
        key = f"user:{user_id}:history"

        data = json.dumps({"title": title, "message_text": message_text, "url": url, }, ensure_ascii=False)
        await r.lpush(key, data)
        await r.ltrim(key, 0, 4)
        await r.expire(key, TTL_SECONDS)

    except Exception as e:
        logging.error(f"Error saving history in Redis for user: {user_id}: {e}")


# Тут берем из Редиса все вакансии которые сохранили.
# Получаем по user_id
async def get_history(user_id: int) -> list[dict]:
    try:
        r = await get_redis()
        key = f"user:{user_id}:history"

        items = await r.lrange(key, 0, -1)
        return [json.loads(i) for i in items]
    except Exception as e:
        logging.error(f"Error in reading history in Redis for user: {user_id}: {e}")
        return []

# Тут просто закрываем редис чтобы не жрало память.
async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
        logger.info("Connection with Redis is close")
