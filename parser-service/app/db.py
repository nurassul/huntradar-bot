
# Модуль для связи с бд.
# Все методы и функции для типо CRUD операции.
# Чисто для получения запросов юзера.

import os
from dataclasses import dataclass

# Добавили нужные импорты для создания Модели БД
from sqlalchemy import select, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Путь нашего postgresql. Все внутри докера крутиться.
DATABASE_URL = os.getenv(
    "DATABASE_URL",  # Берем с docker-compose файла. Но если нет, второй параметр идет как дефолтный. ->
    "postgresql+asyncpg://postgres:postgres@postgres:5432/huntradar"
)

# Асинхронный движок для общения с базой. echo=True - типо логгер каждого запроса в базу.
engine = create_async_engine(DATABASE_URL, echo=True)

# Фабрика сессий типо как Курьеры, которые доставляют наши запросы к базе.
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Создаем базовый класс для всех таблиц
class Base(DeclarativeBase):
    pass


# --- 1. SQLALCHEMY МОДЕЛЬ (ДЛЯ ОБЩЕНИЯ С БАЗОЙ) ---
class DBUserQuery(Base):
    __tablename__ = "user_queries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    search_query = Column(String, nullable=False)
    area = Column(String)
    is_active = Column(Boolean, default=True)

@dataclass
class UserQuery:
    user_id: int
    search_query: str
    area: str
    is_active: bool


# Возвращает все активные запросы юзеров.
async def get_active_user_queries() -> list[UserQuery]:
    async with AsyncSessionLocal() as session:
        stmt = select(DBUserQuery.user_id,
                      DBUserQuery.search_query,
                      DBUserQuery.area).where(
            DBUserQuery.is_active == True
        )
        result = await session.execute(stmt)
        return [
            UserQuery(user_id=row[0], search_query=row[1], area=row[2], is_active=True)
            for row in result.fetchall()
        ]


# Тут ищем какие юзеры подписаны на переданный запрос.
async def get_user_ids_for_query(search_query: str) -> list[int]:
    async with AsyncSessionLocal() as session:
        stmt = select(
            DBUserQuery.user_id
        ).distinct().where(
            DBUserQuery.search_query == search_query,
            DBUserQuery.is_active == True
        )
        result = await session.execute(stmt)
        return [row[0] for row in result.fetchall()]









