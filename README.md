# Yandex Forms Answer Transformer

Python-сервис для приёма, очистки и сохранения ответов из Яндекс Форм в PostgreSQL.

## Описание

- **Входные данные**: JSON-ответ формы Яндекс (ключ `answer` с вложенной структурой `data`)
- **Результат**: Очищенный (плоский) словарь только с содержательными значениями.  
- **Запись**: Сохраняет оригинальный и очищенный ответ в две разные таблицы.
- **Применение**: Аналитика, BI-дашборды, интеграции.

---

## Структура таблиц в PostgreSQL

```sql
-- Оригинальные (сырые) ответы формы
CREATE TABLE answers (
    id SERIAL PRIMARY KEY,
    answer JSONB NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Очищенные (плоские) ответы
CREATE TABLE modified_answer (
    id INTEGER PRIMARY KEY,  -- совпадает с id из answers
    original_answer JSONB NOT NULL,
    modified_answer JSONB NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
