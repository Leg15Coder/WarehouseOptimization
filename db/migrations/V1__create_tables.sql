-- Таблица "product" — типы товаров на складе
CREATE TABLE IF NOT EXISTS product (
    sku SERIAL PRIMARY KEY, -- Артикул товара
    name VARCHAR NOT NULL, -- Название товара
    time_to_select FLOAT NOT NULL, -- Среднее время на отбор из ячейки (в секундах)
    time_to_ship FLOAT NOT NULL, -- Среднее время на отгрузку из ячейки (в секундах)
    max_amount INTEGER, -- Максимальное количество в ячейке
    product_type VARCHAR -- Категория товара
);

-- Таблица "zone" — зоны хранения
CREATE TABLE IF NOT EXISTS zone (
    zone_id SERIAL PRIMARY KEY,
    zone_name VARCHAR NOT NULL, -- Название зоны
    zone_type VARCHAR -- Тип зоны (например, "стеллаж", "полка", "паллет")
);

-- Таблица "cell" — ячейки хранения на складе
CREATE TABLE IF NOT EXISTS cell (
    cell_id SERIAL PRIMARY KEY,
    x INTEGER NOT NULL, -- Координата X
    y INTEGER NOT NULL, -- Координата Y
    product_sku INTEGER REFERENCES product(sku), -- Артикул товара, который лежит в ячейке
    count INTEGER NOT NULL, -- Кол-во товара в ячейке
    zone_id INTEGER REFERENCES zone(zone_id) -- Зона, которой принадлежит ячейка
);

-- Таблица "user" — пользователи
CREATE TABLE IF NOT EXISTS "user" (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    surname VARCHAR NOT NULL,
    phone_number VARCHAR UNIQUE,
    is_admin BOOLEAN DEFAULT FALSE,
    password VARCHAR NOT NULL -- Хэш пароля
);

-- Таблица "user_x_zone" — зоны, которые может посещать данный пользователь (многие ко многим)
CREATE TABLE IF NOT EXISTS user_x_zone (
    user_id INTEGER REFERENCES "user"(user_id),
    zone_id INTEGER REFERENCES zone(zone_id),
    PRIMARY KEY (user_id, zone_id)
);
