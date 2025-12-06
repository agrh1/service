-- Создание основной БД выполняется автоматически
-- Начальная схема для спринтов 1-5

CREATE SCHEMA IF NOT EXISTS public;

-- Таблица для Django портала (Sprint 1)
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER UNIQUE,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Таблица для логов (Sprint 1)
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES tickets(id),
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица для Seafile ссылок (Sprint 4)
CREATE TABLE IF NOT EXISTS seafile_links (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES tickets(id),
    upload_link TEXT,
    download_link TEXT,
    password VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
