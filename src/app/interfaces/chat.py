import re
import json
import logging
from typing import List, Optional, Dict, Any

from urllib3 import request

from src.app.interfaces.promt import SYSTEM_PROMT, API_PROMT
from src.app.models import FinamRequest


def create_system_prompt() -> str:
    """Создать системный промпт для AI ассистента"""
    return SYSTEM_PROMT + API_PROMT

def extract_api_request(text: str) -> List[FinamRequest]:
    """ Извлечь запросы List[FinamRequest] из ответа ассистента"""
    try:
        requests = _parse_requests(text)
    except ValueError:
        logging.error("chat.extract_api_request: The model doesn't answer correctly!")
        data = _extract_requests_manually(text)
        requests = _create_finam_requests(data)
    return requests

def extract_message(text: str) -> Optional[str]:
    try:
        message = _parse_message_text(text)
    except ValueError:
        logging.error("chat.extract_message: The model doesn't answer correctly!")
        message = _manual_parse_message(text)
    return message


# ============= FOR API REQUESTS ==============================

def _parse_requests(json_str: str) -> List[FinamRequest]:
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON format") from e

    if "requests" not in data:
        return []

    requests = []
    for item in data["requests"]:
        if not all(key in item for key in ("method", "url")):
            continue

        request = FinamRequest(
            method=item["method"],
            url=item["url"],
            body=item.get("body")  # Может быть None или dict
        )
        requests.append(request)

    return requests


def _extract_requests_manually(requests_str: str) -> List[Dict[str, Any]]:
    """
    Ручное извлечение объектов requests из строки с помощью регулярных выражений.
    """
    requests = []

    # Паттерн для поиска отдельных объектов в массиве requests
    object_pattern = r'\{[^{}]*"method"[^{}]*"url"[^{}]*\}'
    matches = re.finditer(object_pattern, requests_str, re.DOTALL)

    for match in matches:
        obj_str = match.group(0)
        try:
            # Пытаемся распарсить отдельный объект
            obj = __parse_single_object(obj_str)
            if obj and 'method' in obj and 'url' in obj:
                requests.append(obj)
        except:
            continue

    return requests


def __parse_single_object(obj_str: str) -> Optional[Dict[str, Any]]:
    """
    Парсит отдельный объект запроса из строки.
    """
    result = {}

    # Извлекаем method
    method_match = re.search(r'"method"\s*:\s*"([^"]*)"', obj_str)
    if method_match:
        result['method'] = method_match.group(1)

    # Извлекаем url
    url_match = re.search(r'"url"\s*:\s*"([^"]*)"', obj_str)
    if url_match:
        result['url'] = url_match.group(1)

    # Извлекаем body (может быть null или объектом)
    body_match = re.search(r'"body"\s*:\s*(null|\{[^{}]*\})', obj_str, re.DOTALL)
    if body_match:
        body_str = body_match.group(1)
        if body_str == 'null':
            result['body'] = None
        else:
            try:
                result['body'] = json.loads(body_str)
            except:
                # Если не получается распарсить body, оставляем None
                result['body'] = None

    return result if result else None


def _create_finam_requests(requests_data: List[Dict[str, Any]]) -> List[FinamRequest]:
    """
    Создает список объектов FinamRequest из данных.
    """
    requests = []

    if not isinstance(requests_data, list):
        return requests

    for item in requests_data:
        if not isinstance(item, dict):
            continue

        if 'method' in item and 'url' in item:
            request = FinamRequest(
                method=item['method'],
                url=item['url'],
                body=item.get('body')
            )
            requests.append(request)

    return requests


## ===================== FOR EXTRACT message =============

def _parse_message_text(text: str) -> Optional[str]:
    """
    Извлекает текстовое содержимое поля message из текста.
    Возвращает только строку с текстом или None, если поле не найдено или содержит не текст.
    """
    # Пытаемся сначала распарсить как корректный JSON
    try:
        data = json.loads(text)
        if "message" in data and isinstance(data["message"], str):
            return data["message"]
        return None
    except json.JSONDecodeError:
        # Если JSON некорректный, ищем поле через регулярные выражения
        raise ValueError("Invalid JSON format")


def _manual_parse_message(text: str) -> Optional[str]:
    # Паттерн для поиска поля message со строковым значением
    pattern = r'"message"\s*:\s*"([^"]*)"'
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1)

    return None