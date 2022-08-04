import os
from textwrap import dedent

import telegram
from django.utils import timezone
from dotenv import load_dotenv
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, MessageHandler,
                          PreCheckoutQueryHandler, Updater)
from telegram.ext.filters import Filters
from telegram_bot.bot.payment import (cancel_payments, confirm_payment,
                                      get_donation_amount, make_payment)
from telegram_bot.models import Event, Lecture, Person, Question

QUESTIONS_BUTTON = 'Посмотреть вопросы'
ANSWER = 'Ответить'
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
            InlineKeyboardButton("Задонатить", callback_data='make_donation')
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
        serialize_question = {
            'uuid': question.uuid,
            'speaker': question.speaker,
            'guest': question.guest,
            'question': question.question,
        }
        questions_text.append(serialize_question)

    for q_text in questions_text:
        question_uuid = 'id вопроса {}'.format(q_text['uuid'])
        to_whom = 'Вопрос для {}'.format(q_text['speaker'])
        from_whom = 'От {}'.format(q_text['guest'])
        quest = 'Вопрос: {}'.format(q_text['question'])
        answer_text = f'{question_uuid} \n{to_whom} \n{from_whom} \n{quest}'

        callback = '{}_{}'.format(ANSWER, q_text['uuid'])

        update.message.reply_text(
            text=f'Вопрос: \n\n{answer_text}',
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(ANSWER, callback_data=callback)
                    ]
                ]
            )
        )


def button_answer_handler(update: telegram.Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    chat_id = update.effective_message.chat_id
    current_text = update.effective_message.text
    
    if ANSWER in data:
        context.bot.send_message(
            chat_id=chat_id,
            text=data
        )


def message_handler(update: telegram.Update, context: CallbackContext):

    # ДОНАТ
    print(os.getenv(f'{update.effective_chat.id}'))
    try:
        if 'donation' in os.getenv(f'{update.effective_chat.id}'):
            try:
                _, payment_id = os.getenv(f'{update.effective_chat.id}').split(':')
                return make_payment(update, context, payment_id, int(update.message.text))
            except ValueError:
                return context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=dedent(
                        """
                        Введена недопустимая сумма перевода.
                        Проверьте, должны быть только цифры.
                        
                        Если передумали донатить, нажмите кнопку отмены.
                        """
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[[
                            InlineKeyboardButton('Отменить донат', callback_data='cancel_donation')
                        ]]
                    )
                )
    except TypeError:
        pass
    # ДОНАТ ЗАВЕРШЕН

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
    answer_button_handler = CallbackQueryHandler(callback=button_answer_handler, pattern=ANSWER)
    schedule_handler = CommandHandler('schedule', get_schedule)

    updater = Updater(token=tg_bot_token, use_context=True)
    
    updater.dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(schedule_handler)
    
    updater.dispatcher.add_handler(answer_button_handler)
    
    updater.dispatcher.add_handler(CallbackQueryHandler(get_donation_amount, pattern='make_donation'))
    updater.dispatcher.add_handler(CallbackQueryHandler(cancel_payments, pattern='cancel_donation'))
    updater.dispatcher.add_handler(PreCheckoutQueryHandler(confirm_payment))
    updater.dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
