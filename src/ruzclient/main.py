from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any, Optional

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
        help="Базовый URL сервера (например, http://localhost:8000).",
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

    return parser


async def run_command(*, base_url: str, timeout_s: float, api_key: Optional[str], command: str) -> None:
    client = RuzClient(
        ClientConfig(
            base_url=base_url,
            timeout_s=timeout_s,
            api_key=api_key,
            default_headers=settings.default_headers,
        )
    )

    async with client:
        if command == "healthz":
            resp = await client.healthz()
        elif command == "public":
            resp = await client.public()
        elif command == "protected":
            resp = await client.protected(api_key=api_key)
        else:  # pragma: no cover
            raise ValueError(f"Unknown command: {command}")

    _print_response(resp)


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