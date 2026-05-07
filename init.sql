-- Пользователи бота
CREATE TABLE IF NOT EXISTS users (
    user_id   BIGINT PRIMARY KEY,
    username  VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Скиллы пользователя (для Matcher Service)
CREATE TABLE IF NOT EXISTS user_skills (
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    skill   VARCHAR(100) NOT NULL,
    PRIMARY KEY (user_id, skill)
);

-- Поисковые запросы пользователя (для Parser Service)
CREATE TABLE IF NOT EXISTS user_queries (
    id           SERIAL PRIMARY KEY,
    user_id      BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    search_query VARCHAR(200) NOT NULL,
    area         VARCHAR(10) DEFAULT '40',
    is_active    BOOLEAN DEFAULT TRUE,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_queries_active ON user_queries(is_active) WHERE is_active = TRUE;
