#!/usr/bin/env python3
"""
Streamlit веб-интерфейс для AI ассистента трейдера

Использование:
    poetry run streamlit run src/app/chat_app.py
    streamlit run src/app/chat_app.py
"""

import json

import streamlit as st

from src.app.adapters import FinamAPIClient
from src.app.core import call_llm, get_settings
from src.app.interfaces.utils.base import create_system_prompt, extract_api_request, is_unsafe_method, parse_method_endpoint

def confirm_request(finam_client: FinamAPIClient, method, path, conversation_history):
    """Выполняем запрос после подтверждения"""
    st.session_state.messages.append(
        {"role": "assistant", "content": f"🔍 Выполняю запрос: `{method} {path}`"}
    )
    st.session_state.api_response = finam_client.execute_request(method, path)
    # st.session_state.messages.append(
    #     {"role": "assistant", "content": f"✅ Запрос выполнен: {method} {path}"}
    # )
    if "api_data" not in st.session_state:
        st.session_state.api_data = None
    if st.session_state.api_response:
        api_response = st.session_state.api_response
        st.session_state.api_data = {"method": method, "path": path, "response": api_response}
        st.session_state.api_response = None

        if not st.session_state.mock_run:
            conversation_history.append({"role": "assistant", "content": st.session_state.assistant_message})
            conversation_history.append({
                "role": "user",
                "content": f"Результат API: {json.dumps(api_response, ensure_ascii=False)}\n\nПроанализируй.",
            })

            response = call_llm(conversation_history, temperature=0.3)
            st.session_state.assistant_message = response["choices"][0]["message"]["content"]
        else:
            st.session_state.assistant_message = f"Результат API: {json.dumps(api_response, ensure_ascii=False)}"
    if st.session_state.assistant_message:
        st.markdown(st.session_state.assistant_message)
        message_data = {"role": "assistant", "content": st.session_state.assistant_message}
        if st.session_state.api_data:
            message_data["api_request"] = st.session_state.api_data
            st.session_state.api_data = None
        st.session_state.messages.append(message_data)
        st.session_state.assistant_message = None

def cancel_request(method, path):
    """Отмена запроса"""
    st.session_state.messages.append(
        {"role": "assistant", "content": f"🚫 Действие отменено: {method} {path}"}
    )
    st.session_state.api_response = None


def main() -> None:  # noqa: C901
    """Главная функция Streamlit приложения"""
    st.set_page_config(page_title="AI Трейдер (Finam)", page_icon="🤖", layout="wide")

    # Заголовок
    st.title("🤖 AI Ассистент Трейдера")
    st.caption("Интеллектуальный помощник для работы с Finam TradeAPI")

    # Sidebar с настройками
    with st.sidebar:
        st.header("⚙️ Настройки")
        settings = get_settings()
        st.info(f"**Модель:** {settings.openrouter_model}")

        # Finam API настройки
        with st.expander("🔑 Finam API", expanded=False):
            api_token = st.text_input(
                "Access Token",
                type="password",
                help="Токен доступа к Finam TradeAPI (или используйте FINAM_ACCESS_TOKEN)",
            )
            api_base_url = st.text_input("API Base URL", value="https://api.finam.ru", help="Базовый URL API")

        account_id = st.text_input("ID счета", value="", help="Оставьте пустым если не требуется")

        if st.button("🔄 Очистить историю"):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.markdown("### 💡 Примеры вопросов:")
        st.markdown("""
        - Какая цена Сбербанка?
        - Покажи мой портфель
        - Что в стакане по Газпрому?
        - Покажи свечи YNDX за последние дни
        - Какие у меня активные ордера?
        - Детали моей сессии
        """)

    # Инициализация состояния
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "welcome_shown" not in st.session_state:
        st.session_state.welcome_shown = False 
    if not st.session_state.welcome_shown:
        with st.chat_message("assistant"):
            st.markdown("👋 Привет! Я твой AI-ассистент трейдера.\nВыберите режим работы:")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("mock-run", key="btn_quotes"):
                    st.session_state.messages.append(
                        {"role": "assistant", "content": "Mock режим включён. Пиши 'METHOD endpoint' через пробел, и будет выполнен запрос."}
                    )
                    st.session_state.welcome_shown = True
                    st.session_state.mock_run = True
                    st.rerun()
            with col2:
                if st.button("Real-run", key="btn_portfolio"):
                    st.session_state.messages.append(
                        {"role": "assistant", "content": "Real-mode включён 💼"}
                    )
                    st.session_state.welcome_shown = True
                    st.session_state.mock_run = False
                    st.rerun()

    # Инициализация Finam API клиента
    finam_client = FinamAPIClient(access_token=api_token or None, base_url=api_base_url if api_base_url else None)

    # Проверка токена
    if not finam_client.access_token:
        st.sidebar.warning(
            "⚠️ Finam API токен не установлен. Установите в переменной окружения FINAM_ACCESS_TOKEN или введите выше."
        )
    else:
        st.sidebar.success("✅ Finam API токен установлен")

    # Отображение истории сообщений
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Показываем API запросы
            if "api_request" in message:
                with st.expander("🔍 API запрос"):
                    st.code(f"{message['api_request']['method']} {message['api_request']['path']}", language="http")
                    st.json(message["api_request"]["response"])

    # Поле ввода
    if prompt := st.chat_input("Напишите ваш вопрос..."):
        # Добавляем сообщение пользователя
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Формируем историю для LLM
        conversation_history = [{"role": "system", "content": create_system_prompt()}]
        for msg in st.session_state.messages:
            conversation_history.append({"role": msg["role"], "content": msg["content"]})

        # Получаем ответ от ассистента
        with st.chat_message("assistant"), st.spinner("Думаю..."):
            try:
                method, path = None, None
                api_response = None
                if "assistant_message" not in st.session_state:
                    st.session_state.assistant_message = None
                if st.session_state.mock_run:
                    # Разбираем METHOD endpoint из сообщения пользователя
                    method, path = parse_method_endpoint(prompt)
                    if not method or not path:
                        st.session_state.assistant_message = "Не удалось распознать метод и путь в mock-run"
                else:
                    # real-run: вызываем LLM
                    response = call_llm(conversation_history, temperature=0.3)
                    st.session_state.assistant_message = response["choices"][0]["message"]["content"]
                    method, path = extract_api_request(st.session_state.assistant_message)

                if "api_response" not in st.session_state:
                    st.session_state.api_response = None
                if method and path:
                    if is_unsafe_method(method, path):
                        st.markdown(f"⚠️ Запрос `{method} {path}` требует подтверждения")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.button(
                                "✅ Подтвердить",
                                key=f"confirm_{prompt}",
                                on_click=confirm_request,
                                args=(finam_client, method, path, conversation_history),
                            )
                        with col2:
                            st.button(
                                "❌ Отменить",
                                key=f"cancel_{prompt}",
                                on_click=cancel_request,
                                args=(method, path),
                            )
                    else:
                        st.session_state.api_response = finam_client.execute_request(method, path)

                if "api_data" not in st.session_state:
                    st.session_state.api_data = None
                if st.session_state.api_response:
                    api_response = st.session_state.api_response
                    st.session_state.api_data = {"method": method, "path": path, "response": api_response}
                    st.session_state.api_response = None

                    if not st.session_state.mock_run:
                        conversation_history.append({"role": "assistant", "content": st.session_state.assistant_message})
                        conversation_history.append({
                            "role": "user",
                            "content": f"Результат API: {json.dumps(api_response, ensure_ascii=False)}\n\nПроанализируй.",
                        })

                        response = call_llm(conversation_history, temperature=0.3)
                        st.session_state.assistant_message = response["choices"][0]["message"]["content"]
                    else:
                        st.session_state.assistant_message = f"Результат API: {json.dumps(api_response, ensure_ascii=False)}"
                if st.session_state.assistant_message:
                    st.markdown(st.session_state.assistant_message)
                    message_data = {"role": "assistant", "content": st.session_state.assistant_message}
                    if st.session_state.api_data:
                        message_data["api_request"] = st.session_state.api_data
                        st.session_state.api_data = None
                    st.session_state.messages.append(message_data)
                    st.session_state.assistant_message = None
                

            except Exception as e:
                st.error(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
