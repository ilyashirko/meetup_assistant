from telegram_bot.bot import tg_bot
import telegram
from telegram.ext import Updater, MessageHandler, CallbackContext
from telegram.ext.filters import Filters
import os
from dotenv import load_dotenv

from telegram_bot.models import Person, Event, Lecture, Question


def message_handler(update: telegram.Update, context: CallbackContext):
    update.message.reply_text(text='Я получил ваше сообщение')


def main():
    load_dotenv()
    tg_bot_token = os.getenv('TG_BOT_TOKEN')

    updater = Updater(token=tg_bot_token, use_context=True)
    updater.dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
