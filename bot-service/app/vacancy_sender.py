import asyncio
# Модуль для отправки готовой вакансии для юзера.
# Из matcher-service по кафке передаем уже обработанный результат и по vacancies.ready топик получаем.

import json
import logging
import os

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiokafka import AIOKafkaConsumer

from app.keyboards.kb import vacancy_keyboard
from app.rd_cache import save_to_history

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_READY = "vacancies.ready"


# Слушаем топик и ждем пока не придет сообщение.
async def vacancy_sender(bot: Bot) -> None:
    logger.info(f"Trying to connect kafka: {KAFKA_BOOTSTRAP}")
    while True:
        try:
            consumer = AIOKafkaConsumer(
                TOPIC_READY,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                group_id="bot-sender-group",
                auto_offset_reset="earliest",
            )
            await consumer.start()
            logger.info("Vacancy sender УСПЕШНО запущен, слушаем vacancies.ready..")
            break
        except Exception as e:
            logger.error(f"Кафка недоступна, ждем 5 сек... Ошибка: {e}")
            await asyncio.sleep(5)

    try:
        async for msg in consumer:
            try:
                payload = json.loads(msg.value.decode())
                await _send_vacancy(bot, payload)
            except json.JSONDecodeError:
                logger.error(f"Not correct JSON file: {msg.value}")
            except Exception as e:
                logger.error(f"Error sending vacancy: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await consumer.stop()


# Тут уже через бот отправляем все вакансии которые нам прислали.
async def _send_vacancy(bot: Bot, payload: dict) -> None:
    user_id = payload["user_id"]
    title = payload.get("title", "")
    url = payload.get("url", "")
    vacancy_id = payload.get("vacancy_id", "")
    score_pct = int(payload.get("score", 0) * 100)
    message_text = payload.get("message_text", "")

    if not message_text:
        return
    try:
        await bot.send_message(
            chat_id=user_id,
            text=message_text,
            reply_markup=vacancy_keyboard(url, vacancy_id)
        )
        await save_to_history(user_id, title, message_text, url)
        logger.info(f"Sent vacancy '{title}' юзеру {user_id} (score={score_pct}%)")
    except TelegramForbiddenError:
        logger.warning(f"Юзер {user_id} заблокировал бота")

    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram API при отправке юзеру {user_id}: {e}")
