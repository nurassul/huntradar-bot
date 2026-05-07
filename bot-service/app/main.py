import asyncio
import logging
import os
from email.policy import default

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.handlers import onboarding, profile
from app.vacancy_sender import vacancy_sender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в переменных окружения")


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Регаем роутеры
    dp.include_router(onboarding.router)
    dp.include_router(profile.router)

    # Запускаем Kafka consumer параллельно с polling
    sender_task = asyncio.create_task(vacancy_sender(bot))

    logger.info("Bot Service запущен")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        sender_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
