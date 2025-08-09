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
```

## Формат входящих данных

### Входные данные — JSON в формате:

```json
{
  "answer": {
    "id": "<идентификатор_ответа_на_форму>",
    "data": {
      "<идентификатор_вопроса_с_указанием_типа>": {
        "value": "<ответ_на_вопрос>",
        "question": {
          "id": "<идентификатор_вопроса>",
          "slug": "<идентификатор_вопроса_с_указанием_типа>",
          "options": "{ ... }",
          "answer_type": {
            "id": "<идентификатор_типа_вопроса>",
            "slug": "<тип_вопроса>"
          }
        }
      }
    },
    "survey": {
      "id": "<идентификатор_формы>"
    },
    "created": "<дата_ответа>"
  },
  "params": {}
}
```

## Пример преобразования

### Входные данные

```json
{
  "answer": {
    "id": 1797990255,
    "data": {
      "id-question-39745639": {
        "value": [
          {"key": "73924481", "slug": "73924481", "text": "Не применимо"}
        ],
        "question": { }
      },
      "id-question-39745705": {
        "value": [
          {"key": "74071287", "slug": "74071287", "text": "Не применимо"}
        ],
        "question": { }
      }
    },
    "survey": {"id": "655c6622c417f32c6e64d163"},
    "created": "2024-07-30T03:52:14Z"
  },
  "params": {}
}
```

### Выход (преобразованный словарь):

```json
{
  "id-question-39745639": "Не применимо",
  "id-question-39745705": "Не применимо"
}
```

## Переменные окружения
В Yandex Cloud Function эти переменные задаются через настройки функции в разделе **Переменные окружения**

```
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_secure_password
DB_HOST=your_db_host_or_ip
DB_PORT=5432
```

