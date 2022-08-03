import telegram
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, MessageHandler, CallbackContext, CommandHandler
from telegram.ext.filters import Filters
import os
from dotenv import load_dotenv


from telegram_bot.models import Person, Event, Lecture, Question


QUESTIONS_BUTTON = 'Посмотреть вопросы'


def start(update, context):
    user_telegram_id = update.message.from_user.id
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Здравствуйте, вы зарегистрированы на событие'
    )
    Person.objects.get_or_create(telegram_id=user_telegram_id)


def button_questions_handler(update: telegram.Update, context: CallbackContext):
    questions_text = []
    questions = Question.objects.all()

    for question in questions:
        to_whom = f'Вопрос для {question.speaker}'
        from_whom = f'От {question.guest}'
        quest = f'Вопрос: {question.question}'
        text = f'{to_whom} \n{from_whom} \n{quest}'
        questions_text.append(text)

    answer_text = ''
    for q_text in questions_text:
        answer_text += f'{q_text} \n\n'

    update.message.reply_text(
        text=f'Список вопросов: \n\n\n{answer_text}'
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

    start_handler = CommandHandler('start', start)

    updater = Updater(token=tg_bot_token, use_context=True)
    updater.dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
