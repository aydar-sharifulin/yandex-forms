import json
import psycopg2
import os
from typing import Dict, Any, List

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "safety_db"),
        user=os.getenv("DB_USER", "user"),
        password=os.getenv("DB_PASSWORD", "password"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432))
    )

def extract_values_only(data: Dict[str, Any]) -> Dict[str, Any]:
    values_only = {}
    for key, value in data.items():
        if value is not None and isinstance(value, dict) and 'value' in value:
            v = value['value']
            if isinstance(v, list):
                texts = []
                paths = []
                cleaned_values = []
                for item in v:
                    if isinstance(item, dict):
                        if 'text' in item:
                            texts.append(item['text'])
                        elif 'path' in item:
                            # Автоматическая замена пути к файлу (Яндекс Формы -> S3)
                            new_path = item['path'].replace(
                                'https://forms.yandex.ru/cloud/files?path=%2Fforms-cloud%2F',
                                'https://storage.yandexcloud.net/forms-cloud/'
                            )
                            paths.append(new_path)
                        else:
                            # Очищаем неважные поля для прочих вложенных dict
                            for field in ['key', 'name', 'size', 'slug']:
                                item.pop(field, None)
                            cleaned_values.append(item)
                if texts:
                    values_only[key] = texts[0] if len(texts) == 1 else texts
                elif paths:
                    values_only[key] = ', '.join(paths)
                elif cleaned_values:
                    values_only[key] = cleaned_values
            elif isinstance(v, str):
                values_only[key] = v
            elif isinstance(v, (int, float)):
                values_only[key] = str(v)
            elif isinstance(v, dict) and 'begin' in v and 'end' in v:
                begin_date = v['begin']
                end_date = v['end']
                values_only[key] = f"begin: {begin_date}, end: {end_date}"
                values_only[f"{key}_begin"] = begin_date
                values_only[f"{key}_end"] = end_date
            else:
                values_only[key] = v
    return values_only

def transform_group(group: List[dict]) -> List[dict]:
    return [extract_values_only(item) for item in group]

def transform_answer_data(answer: dict) -> dict:
    """
    Поддерживает плоскую и вложенную структуру (answer->data).
    Обрабатывает группы answer_group*.
    """
    # Универсальный доступ к data
    data = None
    if isinstance(answer, dict) and "answer" in answer and "data" in answer["answer"]:
        data = answer["answer"]["data"]
    elif isinstance(answer, dict) and "data" in answer:
        data = answer["data"]
    else:
        return {}

    transformed_data = {}
    for key, value in data.items():
        if key.startswith('answer_group') and isinstance(value, dict) and 'value' in value:
            transformed_data[key] = transform_group(value['value'])
        else:
            transformed_data.update(extract_values_only({key: value}))
    return transformed_data

def insert_answers(conn, raw_answer, modified_answer):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO answers(answer) VALUES (%s) RETURNING id",
            (json.dumps(raw_answer, ensure_ascii=False),)
        )
        answer_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO modified_answer(id, original_answer, modified_answer) VALUES (%s, %s, %s)",
            (
                answer_id,
                json.dumps(raw_answer, ensure_ascii=False),
                json.dumps(modified_answer, ensure_ascii=False)
            )
        )
        conn.commit()
        return answer_id

def handler(event, context):
    body = event.get('body')
    if isinstance(body, str):
        try:
            data = json.loads(body)
        except Exception:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid JSON in body"}),
                "headers": {"Content-Type": "application/json"}
            }
    else:
        data = body
    raw_answer = data
    modified = transform_answer_data(raw_answer)
    conn = get_connection()
    try:
        answer_id = insert_answers(conn, raw_answer, modified)
    finally:
        conn.close()
    return {
        "statusCode": 200,
        "body": json.dumps({"id": answer_id}),
        "headers": {"Content-Type": "application/json"}
    }
