# ruz-client

`ruz-client` - асинхронный Python-клиент для `ruz-server` и Telegram-бот для работы с расписанием.

В репозитории есть две основные части:

- `ruzclient` - библиотека клиента и CLI для запросов к API
- `ruzbot` - Telegram-бот поверх `ruzclient`

## Возможности

- асинхронный клиент на `aiohttp`
- дополнительный транспорт на `httpx`
- готовые обертки для групп, пользователей, расписания и поиска
- CLI для быстрых проверок API
- Telegram-бот для конечного пользователя
- тесты без реальных сетевых запросов

## Требования

- Python 3.10+
- `pip`
- доступный экземпляр `ruz-server`

Для запуска бота нужен токен Telegram-бота.

## Установка

### Только библиотека

```bash
python -m pip install -e .
```

### Библиотека и CLI

CLI использует `httpx`, поэтому нужен extra-пакет:

```bash
python -m pip install -e .[httpx]
```

### Разработка, тесты и бот

```bash
python -m pip install -e .[dev]
```

## Конфигурация

Настройки читаются из переменных окружения и файла `.env`.

Пример `.env`:

```env
BASE_URL=http://localhost:2201
TOKEN=your-api-key
BOT_TOKEN=your-telegram-bot-token
PAYMENT_URL=https://example.com/donate
PORT=2201
```

### Переменные окружения

- `BASE_URL` - базовый адрес сервера без обязательного суффикса `/api`, например `http://localhost:2201`
- `TOKEN` - API-ключ для заголовка `X-API-Key`
- `BOT_TOKEN` - токен Telegram-бота, обязателен для `ruzbot`
- `PAYMENT_URL` - необязательная ссылка, которая добавляется в сообщения бота
- `PORT` - вспомогательная локальная настройка порта

## Запуск

### CLI клиента

```bash
python -m ruzclient --base-url http://localhost:2201 healthz
python -m ruzclient --base-url http://localhost:2201 public
python -m ruzclient --base-url http://localhost:2201 --api-key your-api-key protected
```

Доступные встроенные команды:

- `healthz`
- `public`
- `protected`
- `group`
- `user`
- `lecturer_week`
- `discipline_week`

Если `BASE_URL` указан в `.env`, флаг `--base-url` можно не передавать.

### Telegram-бот

```bash
python -m ruzbot.main
```

Перед запуском проверьте:

- задан `BOT_TOKEN`
- `BASE_URL` указывает на доступный `ruz-server`
- `TOKEN` задан, если сервер требует `X-API-Key`
- сервер, контейнер или локальная машина имеют доступ к `https://api.telegram.org`

## Пример использования в коде

```python
import asyncio

from ruzclient import ClientConfig, RuzClient


async def main() -> None:
    async with RuzClient(
        ClientConfig(
            base_url="http://localhost:2201",
            api_key="your-api-key",
        )
    ) as client:
        groups = await client.groups.search_groups_by_name("ИС22")
        print(groups)


asyncio.run(main())
```

Основные методы клиента:

- `client.groups.search_groups_by_name(...)`
- `client.schedule.get_user_day(...)`
- `client.schedule.get_user_week(...)`
- `client.search.lecturer_day(...)`
- `client.search.lecturer_week(...)`
- `client.search.discipline_day(...)`
- `client.search.discipline_week(...)`
- `client.users.create_user(...)`
- `client.users.update_user(...)`
- `client.users.get_by_id(...)`

## Тесты

Запуск всех тестов:

```bash
python -m pytest
```

Тесты лежат в `tests/` и используют фикстуры и фейковые транспорты, поэтому не требуют реального `ruz-server`.

## Деплой

### Docker

В репозитории есть `Dockerfile`, который запускает Telegram-бота.

Сборка образа:

```bash
docker build -t ruz-client .
```

Запуск контейнера:

```bash
docker run --rm -e BASE_URL=http://host.docker.internal:2201 -e TOKEN=your-api-key -e BOT_TOKEN=your-telegram-bot-token -e PAYMENT_URL=https://example.com/donate ruz-client
```

Контейнер запускает команду:

```bash
python -m ruzbot.main
```

### Деплой на сервер

Базовый порядок действий:

1. Установить Python 3.10+ или Docker.
2. Передать переменные `BASE_URL`, `TOKEN` и `BOT_TOKEN` через `.env` или окружение.
3. Проверить сетевой доступ до `ruz-server` и Telegram API.
4. Запустить процесс командой `python -m ruzbot.main` или поднять Docker-контейнер.
5. Настроить автоперезапуск через `systemd`, Docker restart policy или другой менеджер процессов.

## Структура проекта

```text
src/
  ruzclient/          библиотека клиента
  ruzbot/             Telegram-бот
tests/                тесты
Dockerfile            контейнер для деплоя бота
pyproject.toml        зависимости и метаданные пакета
```

## Разработка

- не храните секреты в репозитории, используйте `.env`
- при изменениях авторизации отдельно проверяйте сценарии с `X-API-Key`
- перед merge желательно запускать `python -m pytest`

## Лицензия

MIT
