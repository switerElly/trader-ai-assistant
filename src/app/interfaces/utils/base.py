#!/usr/bin/env python3

def create_system_prompt() -> str:
    """Создать системный промпт для AI ассистента"""
    return """Ты - AI ассистент трейдера, работающий с Finam TradeAPI.

Твоя задача - помогать пользователю анализировать рынки и управлять портфелем.

Когда пользователь задает вопрос, ты должен:
1. Определить, какой API запрос нужен
2. Сформулировать запрос в формате: HTTP_METHOD /api/path
3. Я выполню этот запрос и верну результат
4. Ты должен проанализировать результат и дать понятный ответ пользователю

Доступные API endpoints:
- GET /v1/instruments/{symbol}/quotes/latest - текущая котировка
- GET /v1/instruments/{symbol}/orderbook - биржевой стакан
- GET /v1/instruments/{symbol}/bars - исторические свечи
- GET /v1/accounts/{account_id} - информация о счете и позициях
- GET /v1/accounts/{account_id}/orders - список ордеров
- POST /v1/accounts/{account_id}/orders - создание ордера
- DELETE /v1/accounts/{account_id}/orders/{order_id} - отмена ордера

Формат твоего ответа должен быть таким:
```
API_REQUEST: GET /v1/instruments/SBER@MISX/quotes/latest

<После получения ответа от API, проанализируй его и дай понятное объяснение>
```

Отвечай на русском языке, будь полезным и дружелюбным."""

def extract_api_request(text: str) -> tuple[str | None, str | None]:
    """Извлечь API запрос из ответа LLM"""
    if "API_REQUEST:" not in text:
        return None, None

    lines = text.split("\n")
    for line in lines:
        if line.strip().startswith("API_REQUEST:"):
            request = line.replace("API_REQUEST:", "").strip()
            parts = request.split(maxsplit=1)
            if len(parts) == 2:
                return parts[0], parts[1]
    return None, None

UNSAFE_METHODS = [
    "POST /v1/accounts/{account_id}/orders",
    "DELETE /v1/accounts/{account_id}/orders/{order_id}",
    "GET /v1/accounts/{account_id}"
]

def is_unsafe_method(method: str, path: str) -> bool:
    for unsafe in UNSAFE_METHODS:
        unsafe_method, unsafe_path = unsafe.split(maxsplit=1)
        if method == unsafe_method and unsafe_path.split("{")[0] in path:
            return True
    return False

def parse_method_endpoint(text: str) -> tuple[str | None, str | None]:
    for line in text.splitlines():
        if " " in line:
            parts = line.split(" ", 1)
            method = parts[0].strip().upper()
            path = parts[1].strip()
            if method in ["GET", "POST", "DELETE", "PUT", "PATCH"] and path:
                return method, path
    return None, None

