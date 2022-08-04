import os
from dotenv import load_dotenv
from django.utils import timezone

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, MessageHandler, CallbackContext, CommandHandler
from telegram.ext.filters import Filters

from telegram_bot.models import Person, Event, Lecture, Question


QUESTIONS_BUTTON = 'Посмотреть вопросы'
ANSWER = range(1)
FIRST, SECOND = range(2)
SCHEDULE, NETWORKING, MY_QUESTION, DONATE = range(4)


def start(update, context):
    user_telegram_id = update.message.from_user.id
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Здравствуйте, вы зарегистрированы на событие.'
    )
    Person.objects.get_or_create(telegram_id=user_telegram_id)

    keyboard = [
        [
            InlineKeyboardButton("Узнать расписание", callback_data=str(SCHEDULE)),
            InlineKeyboardButton("Познакомиться с кем нибудь", callback_data=str(NETWORKING))
        ],
        [
            InlineKeyboardButton("Задать вопрос спикеру", callback_data=str(MY_QUESTION)),
            InlineKeyboardButton("Задонатить", callback_data=str(DONATE))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        text="Чем хотите заняться?", reply_markup=reply_markup
    )


def get_schedule(update, context):
    curr_date=timezone.localtime()
    curr_events = Event.objects.filter(finish__gt=curr_date, start__lte=curr_date)

    for event in curr_events:
        lectures = event.lectures.all()
        lectures_schedule = ''
        for lecture in lectures:
            lectures_schedule += f'{lecture.title}\nСпикер: {lecture.speaker}\nНачало: {lecture.start.time()}\nКонец: {lecture.end.time()}\n\n'
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'{event.title}\n{event.description}\n{lectures_schedule}'
        )

def button_questions_handler(update: telegram.Update, context: CallbackContext):
    questions_text = []
    questions = Question.objects.all()

    for question in questions:
        to_whom = f'Вопрос для {question.speaker}'
        from_whom = f'От {question.guest}'
        quest = f'Вопрос: {question.question}'
        text = f'{to_whom} \n{from_whom} \n{quest}'
        questions_text.append(text)

    for q_text in questions_text:
        update.message.reply_text(
            text=f'Вопрос: \n\n{q_text}',
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton('Ответить', callback_data=str(ANSWER))
                    ]
                ]
            )
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
    schedule_handler = CommandHandler('schedule', get_schedule)

    updater = Updater(token=tg_bot_token, use_context=True)
    updater.dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(schedule_handler)
    updater.dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
