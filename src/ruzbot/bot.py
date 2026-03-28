from telebot.async_telebot import AsyncTeleBot
from telebot.util import quick_markup

from ruzbot import markups
from ruzbot.utils import ruz_client

from ruzclient.errors import RuzHttpError
from ruzclient.settings import settings

__version__ = "28.03.26"


class RuzBot(AsyncTeleBot):
    def __init__(self, version: str):
        super().__init__(settings.bot_token)
        self.version = version


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
