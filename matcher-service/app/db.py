
# Модуль для связи с бд.
# Все методы и функции для типо CRUD операции.
# Чисто для получения скиллов юзера.

import os
from dataclasses import dataclass
from sqlalchemy import select, String, BigInteger, ForeignKey

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

# Путь нашего postgresql. Все внутри докера крутиться.
DATABASE_URL = os.getenv(
    "DATABASE_URL",  # Берем с docker-compose файла. Но если нет, второй параметр идет как дефолтный. ->
    "postgresql+asyncpg://postgres:postgres@postgres:5432/huntradar"
)

# Асинхронный движок для общения с базой. echo=True - типо логгер каждого запроса в базу.
engine = create_async_engine(DATABASE_URL, echo=True)

# Фабрика сессий типо как Курьеры, которые доставляют наши запросы к базе.
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass


class DBUserSkills(Base):
    __tablename__ = "user_skills"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    skill: Mapped[str] = mapped_column(String(100), primary_key=True)

# Возвращает список нормализованных скиллов пользователя из бд.
async def get_user_skills(user_id: int) -> list[str]:
    async with AsyncSessionLocal() as session:
        stmt = select(
            DBUserSkills.skill
        ).where(
            DBUserSkills.user_id == user_id
        )
        result = await session.execute(stmt)
        return [row[0] for row in result.fetchall()]