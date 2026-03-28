from __future__ import annotations

from cmath import polar
from typing import Union

from telebot import types
from telebot.apihelper import ApiTelegramException
from telebot.async_telebot import AsyncTeleBot
from telebot.util import quick_markup

from ruzbot import markups
from ruzbot.utils import ruz_client

from ruzclient.errors import RuzHttpError
from ruzclient.settings import settings

__version__ = "28.03.26"

# https://core.telegram.org/bots/api#sendmessage (такой же лимит у editMessageText)
TELEGRAM_MAX_MESSAGE_CHARS = 2048
_MESSAGE_TOO_LONG_MARKER = "\n\nMESSAGE TOO LONG"


def _truncate_with_too_long_marker(text: str) -> str:
    """Укладывает текст в лимит Telegram и добавляет маркер в конец."""
    max_body = TELEGRAM_MAX_MESSAGE_CHARS - len(_MESSAGE_TOO_LONG_MARKER)
    if max_body < 1:
        return _MESSAGE_TOO_LONG_MARKER[:TELEGRAM_MAX_MESSAGE_CHARS]
    if len(text) <= max_body:
        return text + _MESSAGE_TOO_LONG_MARKER
    return text[:max_body] + _MESSAGE_TOO_LONG_MARKER


def _is_message_too_long_error(exc: ApiTelegramException) -> bool:
    if exc.error_code != 400:
        return False
    desc = exc.description or ""
    return "MESSAGE_TOO_LONG" in desc or "message is too long" in desc.lower()


class RuzBot(AsyncTeleBot):
    def __init__(self, version: str):
        super().__init__(settings.bot_token)
        self.version = version

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        **kwargs,
    ) -> types.Message:
        try:
            return await super().send_message(chat_id, text, **kwargs)
        except Exception as e:
            if str(type(e)) == "<class 'telebot.asyncio_helper.ApiTelegramException'>":
                if _is_message_too_long_error(e):
                    return await super().send_message(
                        chat_id, _truncate_with_too_long_marker(text), **kwargs
                    )
            else:
                raise(e)

    async def edit_message_text(self, text: str, **kwargs) -> Union[types.Message, bool]:
        try:
            return await super().edit_message_text(text, **kwargs)
        except Exception as e:
            if str(type(e)) == "<class 'telebot.asyncio_helper.ApiTelegramException'>":
                if _is_message_too_long_error(e):
                    return await super().edit_message_text(
                        _truncate_with_too_long_marker(text), **kwargs
                    )
            else:
                raise(e)


bot = RuzBot(__version__)


@bot.message_handler(commands=["start"])
async def startCommand(message):
    """
    /start: главное меню или подсказки, если не заданы группа или подгруппа.
    """
    reply_message = (
        "Привет, я бот для просмотра расписания МГТУ. Что хочешь узнать?\n"
    )
    markup = markups.generateStartMarkup()

    async with ruz_client() as client:
        try:
            user = await client.users.get_by_id(message.from_user.id)
        except RuzHttpError as e:
            if e.status_code == 404:
                user = None
            else:
                raise

        if user is None or not user.get("group_oid"):
            markup = quick_markup(
                {"Установить группу": {"callback_data": "configureGroup"}},
                row_width=1,
            )
            reply_message = (
                "Привет, я бот для просмотра расписания МГТУ. "
                "У тебя не установлена группа, друг.\n"
            )
        elif user.get("subgroup", 0) == 0:
            markup = quick_markup(
                {"Установить подгруппу": {"callback_data": "configureSubGroup"}},
                row_width=1,
            )
            reply_message = (
                "Привет, я бот для просмотра расписания МГТУ. "
                "У тебя не установлена подгруппа, друг.\n"
            )

    await bot.reply_to(message, reply_message, reply_markup=markup)
