import os
from textwrap import dedent

import telegram
from django.utils import timezone
from dotenv import load_dotenv
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, MessageHandler,
                          PreCheckoutQueryHandler, Updater)
from telegram.ext.filters import Filters
from telegram_bot.bot.payment import (cancel_payments, confirm_payment,
                                      get_donation_amount, make_payment)
from telegram_bot.models import Event, Lecture, Person, Question

QUESTIONS_BUTTON = 'Посмотреть вопросы'
ANSWER = 'Ответить'
IGNORE = 'ignore'
FIRST, SECOND = range(2)
SCHEDULE, NETWORKING, MY_QUESTION, DONATE = range(4)


def get_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Узнать расписание", callback_data=str(SCHEDULE)),
            InlineKeyboardButton("Познакомиться с кем нибудь", callback_data=str(NETWORKING))
        ],
        [
            InlineKeyboardButton("Задать вопрос спикеру", callback_data=str(MY_QUESTION)),
            InlineKeyboardButton("Задонатить", callback_data='make_donation')
        ],
        [
            InlineKeyboardButton(QUESTIONS_BUTTON, callback_data=QUESTIONS_BUTTON)
        ]
    ]

    return keyboard


def start(update, context):

    user_telegram_id = update.message.from_user.id
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Здравствуйте, вы зарегистрированы на событие.'
    )
    Person.objects.get_or_create(telegram_id=user_telegram_id)

    reply_markup = InlineKeyboardMarkup(get_keyboard())
    update.message.reply_text(
        text="Чем хотите заняться?", reply_markup=reply_markup
    )


def get_schedule(update, context):
    curr_date=timezone.localtime()
    curr_events = Event.objects.filter(finish__gt=curr_date, start__lte=curr_date)

    if curr_events:
        for event in curr_events:
            lectures = event.lectures.all()
            lectures_schedule = ''
            for lecture in lectures:
                lectures_schedule += f'{lecture.title}\nСпикер: {lecture.speaker}\nНачало: {lecture.start.time()}\nКонец: {lecture.end.time()}\n\n'
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'{event.title}\n{event.description}\n{lectures_schedule}'
            )

    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='На данный момент мероприятий нет'
        )


def ask_question(update, context):
    curr_date_time = timezone.localtime()
    curr_lectures = Lecture.objects.filter(start__lte=curr_date_time, end__gt=curr_date_time)
    if curr_lectures:
        speakers = [
            {'name': f'{lecture.speaker.first_name} {lecture.speaker.last_name}', 'uuid':lecture.speaker.uuid}
            for lecture in curr_lectures
        ]
        keyboard = [
            [
                InlineKeyboardButton(speaker['name'], callback_data=speaker['uuid'])
                for speaker in speakers
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            text='Кому задать вопрос?',
            reply_markup=reply_markup
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='На данный момент лекции не идут'
        )


def make_question_instance(update, context):
    speaker = Person.objects.get(uuid=update.callback_query.data)
    user = Person.objects.get(telegram_id=update.callback_query.message.chat.id)

    user_question = Question.objects.get_or_create(speaker=speaker, guest=user, question='')
    os.environ.setdefault(f'{update.effective_chat.id}', '')
    os.environ[f'{update.effective_chat.id}'] = f'ask_question:{user_question.uuid}'

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Ваш вопрос?'
    )

def button_questions_handler(update: telegram.Update, context: CallbackContext):
    user = context.user_data['chat_id']

    questions_text = []
    questions = Question.objects.filter(speaker__telegram_id=user, processed=False)

    for question in questions:
        serialize_question = {
            'uuid': question.uuid,
            'speaker': question.speaker,
            'guest': question.guest,
            'question': question.question,
        }
        questions_text.append(serialize_question)
    
    if not questions_text:
        reply_markup = InlineKeyboardMarkup(get_keyboard())
        context.bot.send_message(
            chat_id=user,
            text='Вам пока не задали вопросов.',
            reply_markup=reply_markup
        )
    else:
        for q_text in questions_text:
            question_uuid = 'id вопроса {}'.format(q_text['uuid'])
            to_whom = 'Вопрос для {}'.format(q_text['speaker'])
            from_whom = 'От {}'.format(q_text['guest'])
            quest = 'Вопрос: {}'.format(q_text['question'])
            answer_text = f'{question_uuid} \n{to_whom} \n{from_whom} \n{quest}'

            callback = '{}_{}'.format(ANSWER, q_text['uuid'])
            ignore_callback = '{}_{}'.format(IGNORE, q_text['uuid'])

            context.bot.send_message(
                chat_id=user,
                text=f'Вопрос: \n\n{answer_text}',
                reply_markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(ANSWER, callback_data=callback),
                            InlineKeyboardButton('Игнорировать', callback_data=ignore_callback)
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
        uuid = data[9:]
        question = Question.objects.get(uuid=uuid)
        context.bot.send_message(
            chat_id=chat_id,
            text=f'Введите ответ на вопрос от пользователя {question.guest}. Для того что бы ваш ответ был зарегистрирован и отправлен пользователю задавшему вопрос начните ответ со слова "+Ответ+"',
        )
        context.user_data['queston_uuid'] = question.uuid
    
    if IGNORE in data:
        uuid = data[7:]
        question = Question.objects.get(uuid=uuid)
        question.processed = True
        question.save()

        reply_markup = InlineKeyboardMarkup(get_keyboard())
        context.bot.send_message(
            chat_id=chat_id,
            text='Вопрос {} оставлен без ответа и убран из списка вопросов.'.format(uuid),
            reply_markup=reply_markup
        )
    
    if data == QUESTIONS_BUTTON:
        context.user_data['chat_id'] = chat_id
        return button_questions_handler(update=update, context=context)


def speaker_answer_handler(update: telegram.Update, context: CallbackContext):
    text = update.message.text
    uuid = context.user_data['queston_uuid']

    question = Question.objects.get(uuid=uuid)
    question.answer = text
    question.processed = True
    question.save()

    guest = question.guest.telegram_id

    context.bot.send_message(
        chat_id=guest,
        text=f'Спикер ответил на ваш вопрос {uuid}: \n\n\n{text}'
    )

    reply_markup = InlineKeyboardMarkup(get_keyboard())
    update.message.reply_text(
        text=f'Ответ на вопрос: {uuid} отправлен пользователю',
        reply_markup=reply_markup
    )


def message_handler(update: telegram.Update, context: CallbackContext):
    # Записать вопрос в базу данных
    if 'ask_question' in os.getenv(f'{update.effective_chat.id}'):
        _, question_uuid = os.getenv(f'{update.effective_chat.id}').split(':')
        question = Question.objects.get(uuid=question_uuid)
        question.question = update.message.text
        question.save()
        os.environ.pop(f'{update.effective_chat.id}')

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
    
    if '+Ответ+' in text:
        return speaker_answer_handler(update=update, context=context)


def main():
    load_dotenv()
    tg_bot_token = os.getenv('TG_BOT_TOKEN')

    start_handler = CommandHandler('start', start)
    # answer_button_handler = CallbackQueryHandler(callback=button_answer_handler, pattern=ANSWER)
    answer_button_handler = CallbackQueryHandler(callback=button_answer_handler)
    schedule_handler = CommandHandler('schedule', get_schedule)
    ask_question_handler = CommandHandler('ask', ask_question)
    make_question_handler = CallbackQueryHandler(callback=make_question_instance)


    updater = Updater(token=tg_bot_token, use_context=True)
    
    updater.dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(schedule_handler)
    updater.dispatcher.add_handler(ask_question_handler)
    updater.dispatcher.add_handler(make_question_handler)
    
    updater.dispatcher.add_handler(answer_button_handler)
    
    updater.dispatcher.add_handler(CallbackQueryHandler(get_donation_amount, pattern='make_donation'))
    updater.dispatcher.add_handler(CallbackQueryHandler(cancel_payments, pattern='cancel_donation'))
    updater.dispatcher.add_handler(PreCheckoutQueryHandler(confirm_payment))
    updater.dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
