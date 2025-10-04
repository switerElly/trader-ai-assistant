

Пример LLM ответа
``` json
{
 "instructions": "Сначала я запрошу с помощью api информацию об аккаунте, затем отвечу пользователю уважительно и грамотно",
 "messages": null,
 "requests": [ {
      "method": "GET",
      "url": "https://api.finam.ru/v1/accounts/1899011",
      "body": null
    }
 ]
}
```

Формат запросов:
``` json
 "requests": [ {
      "method": "GET",
      "url": "https://api.finam.ru/v1/accounts/1899011",
      "body": null
    }
 ]
```