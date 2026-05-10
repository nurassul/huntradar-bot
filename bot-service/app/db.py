
# Модуль для связи с бд.
# Все методы и функции для типо CRUD операции.
# Чисто для сохранения и edit user inputs там скиллы, запросы все это.


import os
from datetime import datetime
from operator import index

from sqlalchemy.dialects.postgresql import insert

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped
from sqlalchemy import text, BigInteger, String, DateTime, func, ForeignKey, Integer, Boolean, delete, select, update
from sqlalchemy.testing.schema import mapped_column

# Путь нашего postgresql. Все внутри докера крутиться.
DATABASE_URL = os.getenv(
    "DATABASE_URL",  # Берем с docker-compose файла. Но если нету второй параметр как дефолтный идет. ->
    "postgresql+asyncpg://postgres:postgres@postgres:5432/huntradar"
)

# Асинхронный движок для общения с базой. echo=True - типо логгер каждого запроса в базу.
engine = create_async_engine(DATABASE_URL, echo=True)

# Фабрика сессий типо как Курьеры которые доставляют наши запросы к базе.
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Просто базовая моделька. Чтобы SQLAlchemy понимал что это моделька.
class Base(DeclarativeBase):
    pass


# 1. User model - Моделька для пользователя (table = users). Но все таблицы все равно создаются через init.sql файл. Модельки чтобы показать через код.
class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# 2. UserSkills - Моделька для пользовательских скиллов. (table = user_skills)
class UserSkills(Base):
    __tablename__ = "user_skills"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    skill: Mapped[str] = mapped_column(String(100), primary_key=True)


# 3. UserQuery - Моделька для пользовательских запросов. (table = user_queries)
class UserQuery(Base):
    __tablename__ = "user_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"))
    search_query: Mapped[str] = mapped_column(String(200))
    area: Mapped[str] = mapped_column(String(10), server_default="40")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# Функция чтобы регать новых юзеров.
async def register_user(user_id: int, username: str | None) -> None:
    async with AsyncSessionLocal() as session:
        # Insert statement. Сохраняем в нашу базу
        stmt = insert(User).values(
            user_id=user_id,
            username=username
        )
        # Если существует такой юзер тогда просто update username делаем.
        # Типо такой запрос "ON CONFLICT (user_id) DO UPDATE SET username = EXCLUDED.username"
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_=dict(username=stmt.excluded.username)
        )
        await session.execute(stmt)
        await session.commit()


# Функция чтобы сохранять пользовательские скиллы.
async def save_user_skills(user_id: int, skills: list[str]) -> None:
    async with AsyncSessionLocal() as session:
        # Самое главное удаляем старые скиллы юзера
        await session.execute(
            delete(UserSkills).where(UserSkills.user_id == user_id)
        )

        # Если скиллы есть тогда добавляем новые.
        if skills:
            new_skills = [UserSkills(user_id=user_id, skill=skill_name) for skill_name in skills]

            session.add_all(new_skills)

        await session.commit()


# Фукнция для сохранения запросов юзера. Самое главное в начале отключаем старые запросы и сохраняем новый запрос юзера.
async def save_user_query(user_id: int, search_query: str, area: str = "40") -> None:
    async with AsyncSessionLocal() as session:
        # Старые запросы отключаем
        await session.execute(
            update(UserQuery)
            .where(UserQuery.user_id == user_id)
            .values(is_active=False)
        )
        # Новый запрос сохраняем
        new_query = insert(UserQuery).values(
            user_id=user_id,
            search_query=search_query,
            area=area
        )
        await session.execute(new_query)
        await session.commit()



# Функция для получения скиллов юзера по user_id
async def get_user_skills(user_id: int) -> list[str]:
    async with AsyncSessionLocal() as session:
        stmt = select(UserSkills.skill).where(UserSkills.user_id == user_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())


# Функция для получения запроса юзера по user_id
async def get_user_query(user_id: int) -> str | None:
    async with AsyncSessionLocal() as session:
        stmt = select(UserQuery.search_query
                      ).where(UserQuery.user_id == user_id,
                              UserQuery.is_active == True)
        return await session.scalar(stmt)

async def get_user_query_area(user_id: int) -> str | None:
    async with AsyncSessionLocal() as session:
        stmt = select(UserQuery.area).where(
            UserQuery.user_id == user_id,
            UserQuery.is_active == True
        )
        return await session.scalar(stmt)



async def toggle_notifications(user_id: int, active: bool) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserQuery)
            .where(UserQuery.user_id == user_id)
            .values(is_active=active)
        )

        await session.commit()













