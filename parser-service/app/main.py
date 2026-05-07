import asyncio
import os
import logging
import json
from dataclasses import asdict
from enum import unique

import aiohttp
from aiokafka import AIOKafkaProducer

from app.db import get_active_user_queries
from app.hh_client import fetch_vacancies, fetch_vacancy_detail, parse_vacancy

from app.redis_cache import is_seen, mark_seen

from app.redis_cache import close_redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_RAW = "vacancies.raw"

REQUEST_DELAY = float(os.getenv("REQUEST_DELAY_SEC", "1.0"))

PARSE_INTERVAL = int(os.getenv("PARSE_INTERVAL_SEC", str(60 * 15)))


async def parse_cycle(
        session: aiohttp.ClientSession,
        producer: AIOKafkaProducer
) -> None:
    queries = await get_active_user_queries()
    if not queries:
        logger.info("Not found active queries, pass this cycle")
        return

    # Только уникалные запросы делаем, без повторения
    # tuple(str, str) - search_query и area. А вот list[int] - для айдишки юзеров которые ищут такой запрос.
    unique_queries: dict[tuple[str, str], list[int]] = {}
    for uq in queries:
        key = (uq.search_query, uq.area)
        if key not in unique_queries:
            unique_queries[key] = []
        unique_queries[key].append(uq.user_id)
    logger.info(f"Unique queries to hh.kz: {len(unique_queries)}")

    # Тут уже отправляем запросы на поиск вакансии.
    for (search_query, area), user_ids in unique_queries.items():
        try:
            await process_query(session, producer, search_query, area, user_ids)
        except Exception as e:
            logger.error(f"Error processing request '{search_query}': {e}", exc_info=True)

        await asyncio.sleep(REQUEST_DELAY)


async def process_query(
        session: aiohttp.ClientSession,
        producer: AIOKafkaProducer,
        search_query: str,
        area: str,
        user_ids: list[int]
) -> None:
    logger.info(f"Parcing: '{search_query}' area={area} for {len(user_ids)} users.")

    # Делаем запрос и получаем все вакансии
    raw_items = await fetch_vacancies(session, search_query, area, per_page=20)
    new_count = 0

    # Проверяем смотрели ли эту вакансию
    for item in raw_items:
        vacancy_id = str(item["id"])

        if await is_seen(vacancy_id):
            continue

        detail = await fetch_vacancy_detail(session, vacancy_id)
        if not detail:
            continue

        vacancy = parse_vacancy(detail)

        payload = {
            **asdict(vacancy),
            "user_ids": user_ids,
            "search_query": search_query
        }

        await producer.send(
            TOPIC_RAW,
            value=json.dumps(payload, ensure_ascii=False).encode(),
            key=vacancy_id.encode()
        )

        await mark_seen(vacancy_id)
        new_count += 1

        await asyncio.sleep(REQUEST_DELAY)

    logger.info(f"'{search_query}': send {new_count} new vacancies in {len(raw_items)}")


async def main():
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
    await producer.start()
    logger.info("Parser-Service running")

    async with aiohttp.ClientSession() as session:
        try:
            while True:
                logger.info("Running cycle parcing")
                await parse_cycle(session, producer)
                logger.info(f"Cycle is complete, next after {PARSE_INTERVAL}s")
                await asyncio.sleep(PARSE_INTERVAL)
        finally:
            await producer.stop()
            await close_redis()


if __name__ == "__main__":
    asyncio.run(main())
