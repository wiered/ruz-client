"""Точка входа: long polling для AsyncTeleBot."""

from __future__ import annotations

import asyncio
import logging
import sys

from ruzclient.settings import settings


def main() -> None:
    if not settings.bot_token:
        print("Задайте BOT_TOKEN в окружении или в .env.", file=sys.stderr)
        sys.exit(1)

    # Импорт после проверки токена: иначе AsyncTeleBot падает на пустом токене.
    from ruzbot.bot import bot
    from ruzbot.callbacks import register_handlers

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    async def _run() -> None:
        register_handlers(bot)
        await bot.infinity_polling()

    asyncio.run(_run())


if __name__ == "__main__":
    main()
