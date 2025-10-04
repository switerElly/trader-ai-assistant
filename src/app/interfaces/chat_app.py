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
from src.app.core import get_settings
from src.app.core import call_llm
# from src.app.core.local_llm import call_llm
from src.app.interfaces.promt import SYSTEM_PROMT, API_PROMT

from chat import create_system_prompt, extract_message, extract_api_request, extract_is_last_message


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
        # TODO: где-то здесь надо добавить RAG

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
                response = call_llm(conversation_history, temperature=0.3)
                assistant_message = response["choices"][0]["message"]["content"]

                # ЗДЕСЬ надо отправить еще пользователю тот текст, что засунут в message в ответе LLM
                message = extract_message(assistant_message) # вот его
                st.info(message)


                # Проверяем, есть ли API запрос
                finam_requests = extract_api_request(assistant_message)

                if finam_requests:
                    # TODO: Сделать получение апрува пользователя на каждый модифицирующий запрос!!!
                    for finam_request in finam_requests:
                        # Показываем что делаем запрос
                        st.info(f"🔍 Выполняю запрос: `{finam_request.method} {finam_request.url}`")
                        api_response = finam_client.execute_finam_requests(finam_requests)

                        # Проверяем на ошибки
                        if "error" in api_response:
                            st.error(f"⚠️ Ошибка API: {api_response.get('error')}")
                            if "details" in api_response:
                                st.error(f"Детали: {api_response['details']}")
                        else:
                            st.info(f"   📡 Ответ API: {api_response}\n")

                        # Добавляем результат API в контекст
                        conversation_history.append({"role": "assistant", "content": assistant_message})
                        conversation_history.append({
                            "role": "user",
                            "content": f"Результат API запроса: {api_response}\n\nПроанализируй это.",
                        })

                    # TODO: Надо исправить, чтобы в цикле проходилось до тех пор, пока ллмка extract_is_last_message от ответа ассистента не будет равна true
                    # Последнее ли это сообщение extract_is_last_message(llm_response: str) -> is_last: bool
                    # True, если последнее
                    # Доставать message для пользователя из json надо функцией extract_message(llm_response: str) -> message: str

                    # Получаем финальный ответ
                    response = call_llm(conversation_history, temperature=0.3)
                    assistant_message = response["choices"][0]["message"]["content"]

                st.markdown(assistant_message)

                # Сохраняем сообщение ассистента
                message_data = {"role": "assistant", "content": assistant_message}
                if api_response:
                    message_data["api_request"] = api_response
                st.session_state.messages.append(message_data)

            except Exception as e:
                st.error(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
