# ruz-client

`ruz-client` — асинхронный Python-клиент для [ruz-server](https://github.com/wiered/ruz-server).

## Возможности

- асинхронный клиент на `aiohttp`
- дополнительный транспорт на `httpx`
- готовые обертки для групп, пользователей, расписания и поиска
- CLI для быстрых проверок API
- тесты без реальных сетевых запросов

## Требования

- Python 3.10+
- `pip`
- доступный экземпляр `ruz-server`

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

### Разработка и тесты

```bash
python -m pip install -e .[dev]
```

## Конфигурация

Настройки читаются из переменных окружения. Файл `.env` подхватывается **только** при прямом запуске `src/ruzclient/main.py` как скрипта (там вызывается `load_dotenv` из `python-dotenv`). При `python -m ruzclient` файл `.env` не читается — задайте переменные в окружении ОС или передайте аргументы CLI.

Пример `.env` (для прямого запуска `main.py`):

```env
BASE_URL=http://localhost:2201
TOKEN=your-api-key
```

### Переменные окружения

- `BASE_URL` - базовый адрес сервера без обязательного суффикса `/api`, например `http://localhost:2201`
- `TOKEN` - API-ключ для заголовка `X-API-Key`
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

Если `BASE_URL` уже есть в окружении (или подгружен из `.env` при прямом запуске `main.py`), флаг `--base-url` можно не передавать.

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

## Структура проекта

```text
src/
  ruzclient/          библиотека клиента
tests/                тесты
pyproject.toml        зависимости и метаданные пакета
```

## Разработка

- не храните секреты в репозитории, используйте `.env`
- при изменениях авторизации отдельно проверяйте сценарии с `X-API-Key`
- перед merge желательно запускать `python -m pytest`

## Лицензия

MIT
