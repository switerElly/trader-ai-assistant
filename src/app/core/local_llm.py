import requests
from typing import Any, Optional

import json

MODEL_NAME = "deepseek-v2:16b-lite-chat-fp16"
OLLAMA_URL = "http://localhost:11434"


def call_llm(messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: Optional[int] = None) -> dict[
    str, Any]:
    """Простой вызов локальной LLM через Ollama"""

    # Базовые настройки для Ollama
    ollama_base =  OLLAMA_URL
    model_name = MODEL_NAME

    # Подготавливаем payload для Ollama API
    payload: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "stream": False,  # Отключаем streaming для простоты
        "options": {
            "temperature": temperature,
        }
    }

    # Добавляем max_tokens если указан (в Ollama это 'num_predict')
    # if max_tokens:
    #     payload["options"]["num_predict"] = max_tokens

    try:
        # Отправляем запрос к локальному серверу Ollama
        r = requests.post(
            f"{ollama_base}/api/chat",
            headers={
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        r.raise_for_status()
        return r.json()

    except requests.exceptions.ConnectionError:
        raise Exception("Не удается подключиться к Ollama. Убедитесь, что сервер запущен: 'ollama serve'")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ошибка при запросе к Ollama: {e}")


def ask_ollama(prompt, model=MODEL_NAME):
    url = 'http://localhost:11434/api/generate'
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()['response']
    else:
        return f"Error: {response.text}"



# Пример использования
if __name__ == "__main__":
    # Тестовые сообщения
    messages = [
        {"role": "system", "content": "Ты полезный ассистент"},
        {"role": "user", "content": "Привет! Сколько сообщений я тебе задал?"}
    ]

    try:
        # Использование HTTP версии
        result = call_llm(messages, temperature=0.2, max_tokens=100)
        print("Ответ:", result["message"]["content"])
        result = call_llm(messages, temperature=0.2, max_tokens=100)
        print("Ответ:", result["message"]["content"])
        result = call_llm(messages, temperature=0.2, max_tokens=100)
        print("Ответ:", result["message"]["content"])
        result = call_llm(messages, temperature=0.2, max_tokens=100)
        print("Ответ:", result["message"]["content"])
        # Или использование библиотечной версии
        # result = call_llm_ollama_lib(messages, temperature=0.7, max_tokens=100)
        # print("Ответ:", result["choices"][0]["message"]["content"])

    except Exception as e:
        print(f"Ошибка: {e}")

    # # Использование
    # response = ask_ollama("Почему небо синее?")
    # print(response)

