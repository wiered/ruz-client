from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Optional

from ruzclient.http import HttpxTransport

from .client import ClientConfig, RuzClient
from .errors import RuzClientError

_DEFAULT_TIMEOUT_S = 30.0
_DEFAULT_HEADERS: dict[str, str] = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def _print_response(resp: Any) -> None:
    if isinstance(resp, (dict, list)):
        print(json.dumps(resp, ensure_ascii=False))
    else:
        print(resp)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m ruzclient")
    parser.add_argument(
        "--base-url",
        default=os.getenv("BASE_URL"),
        help="Базовый URL сервера без суффикса /api (например, http://localhost:8000).",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=_DEFAULT_TIMEOUT_S,
        help="Таймаут запросов в секундах.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="X-API-Key для эндпоинта /protected (если не передан — используется TOKEN из env).",
    )

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("healthz", help="GET /healthz")
    sub.add_parser("public", help="GET /public")
    sub.add_parser("protected", help="GET /protected (требует X-API-Key)")
    sub.add_parser("group", help="GET /api/group/search?q=... (поиск групп по имени)")
    sub.add_parser(
        "user", help="GET /api/user/{user_id} (получение пользователя по id)"
    )
    sub.add_parser(
        "lecturer_week",
        help="GET /api/search/lecturer/week?lecturer_id=...&date=... (поиск занятий преподавателя за неделю)",
    )
    sub.add_parser(
        "discipline_week",
        help="GET /api/search/discipline/week?discipline_id=...&date=... (поиск занятий дисциплины за неделю)",
    )

    return parser


async def run_command(
    *, base_url: str, timeout_s: float, api_key: Optional[str], command: str
) -> None:
    transport = HttpxTransport(timeout_s=timeout_s)
    client = RuzClient(
        ClientConfig(
            base_url=base_url,
            timeout_s=timeout_s,
            api_key=api_key,
            default_headers=_DEFAULT_HEADERS,
        ),
        transport=transport,
    )

    async with client:
        if command == "healthz":
            resp = await client.healthz()
        elif command == "public":
            resp = await client.public()
        elif command == "protected":
            resp = await client.protected(api_key=api_key)
        elif command == "group":
            resp = await client.groups.search_groups_by_name(q="ИС22")
        elif command == "user":
            resp = await client.users.get_by_id(547334624)
        elif command == "lecturer_week":
            resp = await client.search.lecturer_week(
                lecturer_id=1077,
                schedule_date="2026-03-28",
            )
        elif command == "discipline_week":
            resp = await client.search.discipline_week(
                discipline_id=3752,
                schedule_date="2026-03-28",
            )
        else:  # pragma: no cover
            raise ValueError(f"Unknown command: {command}")

    _print_response(resp)
    await transport.aclose()


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.base_url:
        print("Missing --base-url (or env BASE_URL).", file=sys.stderr)
        return 2

    try:
        asyncio.run(
            run_command(
                base_url=args.base_url,
                timeout_s=args.timeout_s,
                api_key=args.api_key,
                command=args.command,
            )
        )
        return 0
    except RuzClientError as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    run = input("Run? This will load .env file (y/n): ")
    if run.lower() != "y":
        raise SystemExit(1)

    from dotenv import load_dotenv

    load_dotenv()

    raise SystemExit(main())
