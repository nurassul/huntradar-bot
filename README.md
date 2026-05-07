# HuntRadar Bot

HuntRadar Bot - это микросервисная система, которая:
- собирает вакансии с hh.kz по пользовательским запросам;
- извлекает и нормализует навыки;
- оценивает релевантность вакансии под конкретного пользователя;
- отправляет подходящие вакансии в Telegram.

Проект состоит из трех основных микросервисов (`parser-service`, `matcher-service`, `bot-service`) и инфраструктуры (`PostgreSQL`, `Redis`, `Kafka`).

## 1. Архитектура

### 1.1 Сервисы

- `bot-service`
  - Telegram-бот на `aiogram`.
  - Онбординг пользователя (скиллы, поисковый запрос, регион).
  - Редактирование профиля и управление уведомлениями.
  - Получение готовых рекомендаций из Kafka и отправка в Telegram.
- `parser-service`
  - Периодически читает активные запросы пользователей из PostgreSQL.
  - Ходит в API hh.kz, получает новые вакансии.
  - Дедуплицирует вакансии через Redis (чтобы не отправлять повторно).
  - Публикует сырые вакансии в Kafka topic `vacancies.raw`.
- `matcher-service`
  - Подписан на `vacancies.raw`.
  - Извлекает навыки из текста вакансии.
  - Сравнивает навыки вакансии с навыками пользователя через эмбеддинги и cosine similarity.
  - Формирует рекомендацию и публикует в `vacancies.ready`.

### 1.2 Инфраструктура

- `PostgreSQL` - хранение пользователей, их навыков и запросов.
- `Redis` - кэш дедупликации вакансий и история последних вакансий.
- `Kafka` - транспорт между микросервисами (pipeline событий).

### 1.3 Поток данных (end-to-end)

1. Пользователь проходит `/start` в Telegram-боте.
2. `bot-service` сохраняет:
   - пользователя в `users`;
   - навыки в `user_skills`;
   - активный запрос в `user_queries`.
3. `parser-service` по таймеру читает активные `user_queries`.
4. `parser-service` получает вакансии из hh.kz, фильтрует уже виденные через Redis, отправляет новые в `vacancies.raw`.
5. `matcher-service` читает `vacancies.raw`, оценивает соответствие для каждого `user_id`.
6. Подходящие вакансии отправляются в `vacancies.ready`.
7. `bot-service` читает `vacancies.ready`, отправляет сообщение пользователю и сохраняет запись в Redis-историю.

---

## 2. База данных

Инициализация выполняется через [`init.sql`](/D:/final-project-huntradar-bot/init.sql).

### 2.1 Таблицы

- `users`
  - `user_id BIGINT PRIMARY KEY`
  - `username VARCHAR(100)`
  - `created_at TIMESTAMPTZ`
- `user_skills`
  - `user_id BIGINT` (FK -> `users.user_id`)
  - `skill VARCHAR(100)`
  - PK: (`user_id`, `skill`)
- `user_queries`
  - `id SERIAL PRIMARY KEY`
  - `user_id BIGINT` (FK -> `users.user_id`)
  - `search_query VARCHAR(200)`
  - `area VARCHAR(10)` (по умолчанию `40`)
  - `is_active BOOLEAN` (по умолчанию `TRUE`)
  - `created_at TIMESTAMPTZ`
  - Индекс `idx_user_queries_active` для быстрых выборок активных запросов.

### 2.2 Логика хранения запросов

При обновлении запроса пользователя старая запись не удаляется, а деактивируется (`is_active=False`), после чего создается новый активный запрос. Это удобно для простого аудита изменений.

---

## 3. Kafka топики и контракты

### 3.1 `vacancies.raw`

Публикует `parser-service`. Содержит сырую вакансию + список пользователей, для которых выполнялся запрос.

Ключевые поля payload:
- `vacancy_id`, `title`, `description`, `url`;
- `employer`, `area`, `salary_from`, `salary_to`, `currency`;
- `published_at`, `key_skills`;
- `user_ids` (список подписанных пользователей);
- `search_query`.

### 3.2 `vacancies.ready`

Публикует `matcher-service`. Содержит уже персонализированную рекомендацию.

Ключевые поля payload:
- `user_id`, `vacancy_id`, `title`, `url`;
- `score`, `verdict`;
- `message_text` (готовый текст в Telegram);
- `missing_skills`.

---

## 4. Детально по микросервисам

## 4.1 `bot-service`

Основные файлы:
- [`main.py`](/D:/final-project-huntradar-bot/bot-service/app/main.py)
- [`handlers/onboarding.py`](/D:/final-project-huntradar-bot/bot-service/app/handlers/onboarding.py)
- [`handlers/profile.py`](/D:/final-project-huntradar-bot/bot-service/app/handlers/profile.py)
- [`vacancy_sender.py`](/D:/final-project-huntradar-bot/bot-service/app/vacancy_sender.py)
- [`db.py`](/D:/final-project-huntradar-bot/bot-service/app/db.py)
- [`rd_cache.py`](/D:/final-project-huntradar-bot/bot-service/app/rd_cache.py)

Что делает сервис:
- запускает Telegram polling;
- параллельно запускает Kafka consumer для `vacancies.ready`;
- обслуживает пользовательский FSM-флоу (онбординг, редактирование данных, уведомления);
- отправляет карточки вакансий и хранит последние 5 отправок в Redis.

### Алгоритм онбординга

1. `/start`:
   - `register_user(...)`;
   - если навыки уже есть -> сразу главное меню.
2. Ввод навыков:
   - ожидается строка через запятую;
   - `extract_skills_from_user_input(...)` нормализует и приводит к каноническим названиям.
3. Ввод поискового запроса.
4. Выбор региона (`area:40`, `area:113`, `area:all`).
5. Сохранение в БД:
   - `save_user_skills(...)`;
   - `save_user_query(...)`.

### Алгоритм отправки вакансий

1. Consumer читает `vacancies.ready`.
2. Для каждого payload:
   - проверяет `message_text` (если пусто, пропускает);
   - отправляет сообщение + inline-кнопки (`Открыть вакансию`, `Good/Bad`);
   - сохраняет в Redis историю (`LPUSH`, `LTRIM 0..4`, TTL 3 дня).

---

## 4.2 `parser-service`

Основные файлы:
- [`main.py`](/D:/final-project-huntradar-bot/parser-service/app/main.py)
- [`hh_client.py`](/D:/final-project-huntradar-bot/parser-service/app/hh_client.py)
- [`db.py`](/D:/final-project-huntradar-bot/parser-service/app/db.py)
- [`redis_cache.py`](/D:/final-project-huntradar-bot/parser-service/app/redis_cache.py)

Что делает сервис:
- с заданным интервалом (`PARSE_INTERVAL_SEC`) запускает цикл парсинга;
- группирует одинаковые запросы пользователей (по `search_query + area`);
- для каждого уникального запроса забирает вакансии из hh.kz;
- по каждой вакансии получает подробную карточку (`/vacancies/{id}`);
- отправляет только новые вакансии (через Redis-контроль `seen:*`) в Kafka.

### Алгоритм `parse_cycle`

1. Читает активные запросы `get_active_user_queries()`.
2. Строит `unique_queries: dict[(search_query, area)] -> [user_ids]`.
3. Для каждой уникальной пары:
   - вызывает `process_query(...)`;
   - делает `REQUEST_DELAY_SEC` между запросами.

### Алгоритм `process_query`

1. `fetch_vacancies(...)` (список вакансий по query/area).
2. Для каждой вакансии:
   - если `is_seen(vacancy_id)` -> skip;
   - иначе `fetch_vacancy_detail(...)`;
   - `parse_vacancy(...)` -> нормализованный объект;
   - публикация в `vacancies.raw` с `user_ids`;
   - `mark_seen(vacancy_id)` в Redis на 7 дней.

### Защита от лимитов hh.kz

- При `429` (Too Many Requests): читает `Retry-After`, ждет и повторяет запрос.
- При `400`: логирует тело ответа, возвращает пустой результат.

---

## 4.3 `matcher-service`

Основные файлы:
- [`main.py`](/D:/final-project-huntradar-bot/matcher-service/app/main.py)
- [`skill_extractor.py`](/D:/final-project-huntradar-bot/matcher-service/app/skill_extractor.py)
- [`scorer.py`](/D:/final-project-huntradar-bot/matcher-service/app/scorer.py)
- [`embedder.py`](/D:/final-project-huntradar-bot/matcher-service/app/embedder.py)
- [`recommender.py`](/D:/final-project-huntradar-bot/matcher-service/app/recommender.py)
- [`db.py`](/D:/final-project-huntradar-bot/matcher-service/app/db.py)

Что делает сервис:
- читает сырые вакансии из `vacancies.raw`;
- извлекает навыки из описания и `key_skills`;
- для каждого пользователя считает match-score;
- отправляет подходящие рекомендации в `vacancies.ready`.

### Алгоритм извлечения навыков

1. Нормализация текста (`normalize_text`):
   - lower-case;
   - удаление HTML;
   - очистка спецсимволов;
   - схлопывание пробелов.
2. Разбиение на предложения (`split_into_sentences`) для контекста.
3. Поиск скиллов по словарю алиасов (`SKILLS_DICT`) регулярками.
4. Назначение веса:
   - `1.0` для обязательных;
   - `0.5` если предложение содержит маркеры `nice-to-have`.
5. Дедупликация: оставляется максимальный вес на канонический скилл.

### Алгоритм скоринга

Используется `sentence-transformers/all-MiniLM-L6-v2` (384-мерные векторы, L2-нормализованные).

1. Для каждого `vacancy_skill` ищется лучший `user_skill` по cosine similarity.
2. Match, если `similarity >= 0.75` (`MATCH_THRESHOLD`).
3. Итоговый `final_score`:
   - `sum(weights_matched) / sum(weights_total)`.
4. Вердикт:
   - `full_match`, если `score >= 0.75`;
   - `partial_match`, если `0.2 <= score < 0.75`;
   - `no_match`, если `score < 0.2`.
5. В `missing_skills` попадают только незакрытые обязательные (`weight=1.0`) навыки.

### Алгоритм формирования рекомендации

`build_recommendation_message(...)` строит HTML-сообщение:
- заголовок с типом совпадения (`full`/`partial`);
- метаданные: компания, регион, зарплата;
- список ключевых навыков;
- при частичном совпадении: блок навыков для подтягивания + учебные подсказки (`LEARNING_TIPS`).

---

## 5. Redis-ключи

- `parser-service`
  - `seen:{vacancy_id}` -> дедупликация вакансий, TTL 7 дней.
- `bot-service`
  - `user:{user_id}:history` -> последние 5 отправленных вакансий, TTL 3 дня.

---

## 6. Конфигурация через переменные окружения

Общие:
- `KAFKA_BOOTSTRAP_SERVERS` (по умолчанию `kafka:9092`)
- `DATABASE_URL`
- `REDIS_URL` (нужен `parser-service` и `bot-service`)

Parser:
- `HH_APP_TOKEN`
- `REQUEST_DELAY_SEC` (по умолчанию `1.0`)
- `PARSE_INTERVAL_SEC` (по умолчанию `900`, в compose - `300`)

Bot:
- `BOT_TOKEN`

---

## 7. Запуск

1. Создать `.env` в корне проекта:
   - `HH_APP_TOKEN=...`
   - `BOT_TOKEN=...`
2. Запустить:

```bash
docker compose up --build
```

После старта:
- бот принимает `/start`;
- парсер начинает циклы поиска;
- matcher публикует подходящие вакансии;
- бот рассылает рекомендации.

---

## 8. Используемые технологии

- Python 3.11+ (в контейнерах)
- `aiogram` (Telegram)
- `aiohttp` (HTTP-клиент)
- `aiokafka` (Kafka producer/consumer)
- `SQLAlchemy async` + `asyncpg` (PostgreSQL)
- `redis[asyncio]` (кэш и история)
- `sentence-transformers` + `numpy` (семантический матчинг навыков)
- Docker Compose (локальная оркестрация)

---

## 9. Важные особенности и ограничения

- Повторы вакансий ограничены TTL Redis (7 дней), но между разными пользователями одна вакансия может быть релевантна и отправляться каждому отдельно через `user_ids`.
- `auto_offset_reset=earliest` в consumer'ах значит, что при новой consumer-group может читаться история топика.
- `save_user_query(...)` всегда деактивирует предыдущие запросы пользователя, оставляя один активный контекст поиска.
- `toggle_notifications(...)` изменяет `is_active` у всех запросов пользователя сразу.

---

## 10. Идеи для улучшений

- Добавить DLQ (dead-letter topic) для невалидных сообщений.
- Добавить idempotency-key на уровне отправки в Telegram.
- Перенести словари скиллов в внешнюю конфигурацию (JSON/YAML + hot reload).
- Добавить метрики Prometheus (время цикла, rate матчей, ошибки API/Telegram).
- Ввести A/B thresholds для подбора `MATCH_THRESHOLD`, `SEND_THRESHOLD`.
- Добавить feedback-loop по кнопкам `Good/Bad` для авто-калибровки скоринга.

