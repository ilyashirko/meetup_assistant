import telegram
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, MessageHandler, CallbackContext
from telegram.ext.filters import Filters
import os
from dotenv import load_dotenv

from telegram_bot.models import Person, Event, Lecture, Question


QUESTIONS_BUTTON = 'Посмотреть вопросы'


def button_questions_handler(update: telegram.Update, context: CallbackContext):
    update.message.reply_text(
        text='Список вопросов: '

    )


def message_handler(update: telegram.Update, context: CallbackContext):
    text = update.message.text
    if text == QUESTIONS_BUTTON:
        return button_questions_handler(update=update, context=context)
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=QUESTIONS_BUTTON)
            ]
        ],
        resize_keyboard=True
    )

    update.message.reply_text(
        text='Wellcome',
        reply_markup=reply_markup
    )


def main():
    load_dotenv()
    tg_bot_token = os.getenv('TG_BOT_TOKEN')

    updater = Updater(token=tg_bot_token, use_context=True)
    updater.dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
