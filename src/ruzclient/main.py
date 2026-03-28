from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any, Optional

from ruzclient.http import HttpxTransport

from .client import ClientConfig, RuzClient
from .errors import RuzClientError
from .settings import settings


def _print_response(resp: Any) -> None:
    if isinstance(resp, (dict, list)):
        print(json.dumps(resp, ensure_ascii=False))
    else:
        print(resp)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m ruzclient")
    parser.add_argument(
        "--base-url",
        default=settings.base_url,
        help="Базовый URL сервера без суффикса /api (например, http://localhost:8000).",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=settings.timeout_s,
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
    sub.add_parser("user", help="GET /api/user/{user_id} (получение пользователя по id)")

    return parser


async def run_command(*, base_url: str, timeout_s: float, api_key: Optional[str], command: str) -> None:
    transport = HttpxTransport(timeout_s=timeout_s)
    client = RuzClient(
        ClientConfig(
            base_url=base_url,
            timeout_s=timeout_s,
            api_key=api_key,
            default_headers=settings.default_headers,
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
    raise SystemExit(main())