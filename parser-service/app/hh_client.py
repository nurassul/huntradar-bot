
# Модуль для связи с api.hh
# Берем токен приложения из .env

import asyncio
import logging
import os
from dataclasses import dataclass

import aiohttp

logger = logging.getLogger(__name__)

HH_API_BASE = "https://api.hh.kz"

# Токен приложения из dev.hh.kz
APP_TOKEN = os.getenv("HH_APP_TOKEN")
USER_AGENT = "TechHuntRadar/1.0 (zh.nurasul@gmail.com)"


@dataclass
class Vacancy:
    vacancy_id: str
    title: str
    description: str
    url: str
    employer: str
    area: str
    salary_from: int | None
    salary_to: int | None
    currency: str | None
    published_at: str
    key_skills: list[str]


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {APP_TOKEN}",
        "User-Agent": USER_AGENT,
        "HH-User-Agent": USER_AGENT,
        "Accept": "application/json",
    }


# Тут отправляем запрос в api.hh
# Ожидаем список свежих и актуальных вакансии.
# Лимитируем до 20
async def fetch_vacancies(
        session: aiohttp.ClientSession,
        query: str,
        area: str = "40",
        per_page: int = 20,
        page: int = 0
) -> list[dict]:
    params = {
        "text": query,
        "area": area,
        "per_page": per_page,
        "page": page,
        "order_by": "publication_time"
    }

    async with session.get(
            f"{HH_API_BASE}/vacancies",
            params=params,
            headers=_headers()
    ) as resp:

        # Для статуса Too Many Requests
        if (resp.status == 429):
            retry_after = int(resp.headers.get("Retry-After", 60))
            logger.warning(f"Rate limit, waiting {retry_after}s")
            await asyncio.sleep(retry_after)
            return await fetch_vacancies(session, query, area, per_page, page)

        # Для статуса Bad Request
        if (resp.status == 400):
            body = await resp.text()
            logger.error(f"hh.kz 400 Bad Request: {body}")
            return []

        # Чекаем что статус ответа 2xx. Если другой тогда вылетает ошибка.
        resp.raise_for_status()
        data = await resp.json()
        return data.get("items", [])\


# Тут отправляем запрос в api.hh
# Но тут уже конкретно по одной вакансии. Типо фулл инфа про вакансию
async def fetch_vacancy_detail(
        session: aiohttp.ClientSession,
        vacancy_id: str
) -> dict | None:
    async with session.get(
            f"{HH_API_BASE}/vacancies/{vacancy_id}",
            headers=_headers(),
    ) as resp:
        if resp.status == 404:
            return None
        if resp.status == 429:
            retry_after = int(resp.headers.get("Retry-After", 60))
            await asyncio.sleep(retry_after)
            return await fetch_vacancy_detail(session,vacancy_id)

        resp.raise_for_status()
        return await resp.json()

# Простой парсер который из dict в -> Vacancy object
def parse_vacancy(raw: dict) -> Vacancy:
    salary = raw.get("salary") or {}
    employer = raw.get("employer") or {}
    area = raw.get("area") or {}
    key_skills = [s["name"] for s in raw.get("key_skills", [])]

    return Vacancy(
        vacancy_id=str(raw["id"]),
        title=raw.get("name", ""),
        description=raw.get("description", ""),
        url=raw.get("alternate_url", ""),
        employer=employer.get("name", ""),
        area=area.get("name", ""),
        salary_from=salary.get("from"),
        salary_to=salary.get("to"),
        currency=salary.get("currency"),
        published_at=raw.get("published_at", ""),
        key_skills=key_skills,
    )




















