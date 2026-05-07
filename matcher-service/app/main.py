import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

from app.db import get_user_skills
from app.recommender import build_recommendation_message
from app.skill_extractor import extract_skills_from_vacancy
from app.scorer import score_vacancy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_RAW = "vacancies.raw"
TOPIC_READY = "vacancies.ready"


async def process_vacancy(raw_message: dict, producer: AIOKafkaProducer):
    vacancy_id = raw_message.get("vacancy_id")
    title = raw_message.get("title", "")
    description = raw_message.get("description", "")
    url = raw_message.get("url", "")
    user_ids = raw_message.get("user_ids", [])
    employer = raw_message.get("employer", "")
    area = raw_message.get("area", "")
    salary_from = raw_message.get("salary_from")
    salary_to = raw_message.get("salary_to")
    currency = raw_message.get("currency")
    key_skills = raw_message.get("key_skills", [])

    combined_text = description + " " + " ".join(key_skills)
    vacancy_skills = extract_skills_from_vacancy(combined_text)
    logger.info(f"[{vacancy_id}] '{title}' — найдено скиллов: {len(vacancy_skills)}")

    for user_id in user_ids:
        user_skills = await get_user_skills(user_id)
        if not user_skills:
            continue

        result = score_vacancy(vacancy_skills, user_skills)
        logger.info(
            f"[{vacancy_id}] user={user_id} "
            f"score={result.final_score:.0%} verdict={result.verdict}"
        )

        if result.verdict == "no_match":
            continue

        message_text = build_recommendation_message(
            result=result,
            vacancy_title=title,
            employer=employer,
            area=area,
            salary_from=salary_from,
            salary_to=salary_to,
            currency=currency,
            key_skills=key_skills,
        )

        payload = {
            "user_id": user_id,
            "vacancy_id": vacancy_id,
            "title": title,
            "url": url,
            "score": result.final_score,
            "verdict": result.verdict,
            "message_text": message_text,
            "missing_skills": result.missing_skills,
        }

        await producer.send(
            TOPIC_READY,
            value=json.dumps(payload, ensure_ascii=False).encode(),
            key=str(user_id).encode()
        )


async def main():
    consumer = AIOKafkaConsumer(
        TOPIC_RAW,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id="matcher-group",
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode())
    )
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)

    await consumer.start()
    await producer.start()
    logger.info("Matcher Service запущен, слушаем vacancies.raw...")

    try:
        async for msg in consumer:
            try:
                await process_vacancy(msg.value, producer)
            except Exception as e:
                logger.error(f"Ошибка обработки вакансии: {e}", exc_info=True)
    finally:
        await consumer.stop()
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())
