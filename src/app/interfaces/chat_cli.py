#!/usr/bin/env python3
"""
Интерактивный CLI чат с AI ассистентом трейдера

Использование:
    poetry run chat-cli
    python -m src.app.chat_cli
"""

import sys

import click

from src.app.adapters import FinamAPIClient
from src.app.core import call_llm, get_settings
from src.app.interfaces.promt import SYSTEM_PROMT, API_PROMT


from .chat import create_system_prompt, extract_message, extract_api_request, extract_is_last_message



@click.command()
@click.option("--account-id", default=None, help="ID счета для работы (опционально)")
@click.option("--api-token", default=None, help="Finam API токен (или используйте FINAM_ACCESS_TOKEN)")
def main(account_id: str | None, api_token: str | None) -> None:  # noqa: C901
    """Запустить интерактивный CLI чат с AI ассистентом"""
    settings = get_settings()

    # Инициализируем клиент Finam API
    finam_client = FinamAPIClient(access_token=api_token)

    # Проверяем подключение
    if finam_client.access_token:
        click.echo("✅ Finam API токен установлен")
    else:
        click.echo("⚠️  Внимание: Finam API токен не установлен!")
        click.echo("   Установите переменную окружения FINAM_ACCESS_TOKEN")
        click.echo("   или используйте --api-token")

    click.echo("=" * 70)
    click.echo("🤖 AI Ассистент Трейдера (Finam TradeAPI)")
    click.echo("=" * 70)
    click.echo(f"Модель: {settings.openrouter_model}")
    click.echo(f"API URL: {finam_client.base_url}")
    if account_id:
        click.echo(f"Счет: {account_id}")
    click.echo("\nКоманды:")
    click.echo("  - Просто пишите свои вопросы на русском")
    click.echo("  - 'exit' или 'quit' - выход")
    click.echo("  - 'clear' - очистить историю")
    click.echo("=" * 70)

    conversation_history = [{"role": "system", "content": create_system_prompt()}]

    while True:
        try:
            # Получаем вопрос от пользователя
            user_input = click.prompt("\n👤 Вы", type=str, prompt_suffix=": ")

            if user_input.lower() in ["exit", "quit", "выход"]:
                click.echo("\n👋 До свидания!")
                break

            if user_input.lower() in ["clear", "очистить"]:
                conversation_history = [{"role": "system", "content": create_system_prompt()}]
                click.echo("🔄 История очищена")
                continue


            # TODO: где-то здесь надо добавить RAG

            # Добавляем вопрос в историю
            conversation_history.append({"role": "user", "content": user_input})

            # Получаем ответ от LLM
            response = call_llm(conversation_history, temperature=0.3)
            assistant_message = response["choices"][0]["message"]["content"]

            # Проверяем, есть ли API запрос
            finam_requests = extract_api_request(assistant_message)

            if finam_requests:
                click.echo("🤖 Ассистент: ", nl=False)
                for finam_request in finam_requests:
                    # Выполняем API запрос
                    click.echo(f"\n   🔍 Выполняю запрос: {finam_request.method} {finam_request.url}")
                    api_response = finam_client.execute_finam_requests([finam_request])

                    # Проверяем на ошибки
                    if "error" in api_response:
                        click.echo(f"   ⚠️  Ошибка API: {api_response.get('error')}", err=True)
                        if "details" in api_response:
                            click.echo(f"   Детали: {api_response['details']}", err=True)
                    else:
                        click.echo(f"   📡 Ответ API: {api_response}\n")

                    # Добавляем результат API в контекст
                    conversation_history.append({"role": "assistant", "content": assistant_message})
                    conversation_history.append({
                        "role": "user",
                        "content": f"Результат API запроса: {api_response}\n\nПроанализируй это.",
                    })

                # Получаем финальный ответ
                response = call_llm(conversation_history, temperature=0.3)
                assistant_message = response["choices"][0]["message"]["content"]

            # Извлекаем сообщение для пользователя
            user_message = extract_message(assistant_message)
            if user_message:
                click.echo("🤖 Ассистент: ", nl=False)
                click.echo(f"{user_message}\n")
            else:
                click.echo("🤖 Ассистент: ", nl=False)
                click.echo(f"{assistant_message}\n")
            
            conversation_history.append({"role": "assistant", "content": assistant_message})


        except KeyboardInterrupt:
            click.echo("\n\n👋 До свидания!")
            sys.exit(0)
        except Exception as e:
            click.echo(f"\n❌ Ошибка: {e}", err=True)


if __name__ == "__main__":
    main()
