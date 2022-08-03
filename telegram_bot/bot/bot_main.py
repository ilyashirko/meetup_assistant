from telegram_bot.bot import tg_bot
import telegram
import os
from dotenv import load_dotenv

from telegram_bot.models import Person, Event, Lecture, Question


def main():
    load_dotenv()
    tg_bot_token = os.getenv('TG_BOT_TOKEN')

    bot = tg_bot.Bot(token=tg_bot_token)
    bot.run_bot()


if __name__ == '__main__':
    main()
