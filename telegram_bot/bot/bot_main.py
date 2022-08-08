import os
from textwrap import dedent

import telegram
from django.utils import timezone
from dotenv import load_dotenv
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, MessageHandler,
                          PreCheckoutQueryHandler, Updater,
                          ConversationHandler)
from telegram.ext.filters import Filters

from telegram_bot.bot.payment import (cancel_payments, confirm_payment,
                                      get_donation_amount, make_payment)
from telegram_bot.models import Event, Lecture, Person, Question

QUESTIONS_BUTTON = 'Посмотреть вопросы'
ANSWER = 'Ответить'
IGNORE = 'ignore'
BEGGINNING_STATE, MAKE_NEW_QUESTION, ANSWER_QUESTIONS = range(3)
LASTNAME, FIRSTNAME, PHONE, EMAIL, COMPANY, SEND_MESSAGE = range(3, 9)
SCHEDULE, NETWORKING, ASK_QUESTION, DONATE, START_OVER = range(9, 14)


def get_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Узнать расписание", callback_data=str(SCHEDULE)),
            InlineKeyboardButton("Познакомиться с кем нибудь", callback_data=str(NETWORKING))
        ],
        [
            InlineKeyboardButton("Задать вопрос спикеру", callback_data=str(ASK_QUESTION)),
            InlineKeyboardButton("Задонатить", callback_data='make_donation')
        ],
        [
            InlineKeyboardButton(QUESTIONS_BUTTON, callback_data=QUESTIONS_BUTTON)
        ]
    ]

    return keyboard


def build_menu(menu_buttons):
    n_cols = 2
    buttons = [
        InlineKeyboardButton(button_name, callback_data=button_callback)
        for button_name, button_callback in menu_buttons.items()
    ]
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]

    return menu


def start(update, context):

    user_telegram_id = update.effective_chat.id
    curr_person = Person.objects.get_or_create(telegram_id=user_telegram_id)
    print(curr_person)

    if curr_person[1]:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Здравствуйте, вы зарегистрированы на событие.'
        )
    curr_date = timezone.localtime()

    start_menu_button_info = {
        "Узнать расписание": str(SCHEDULE),
        "Познакомиться с кем нибудь": str(NETWORKING),
        "Задать вопрос спикеру": str(ASK_QUESTION),
        "Задонатить": 'make_donation'
    }

    curr_event = Event.objects.get(start__lt=curr_date, finish__gt=curr_date)
    if curr_person[0].is_speaker(curr_event):
        start_menu_button_info[QUESTIONS_BUTTON] = QUESTIONS_BUTTON

    reply_markup = InlineKeyboardMarkup(build_menu(start_menu_button_info))
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Чем хотите заняться?",
        reply_markup=reply_markup
    )

    return BEGGINNING_STATE


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

        return start(update, context)

    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='На данный момент мероприятий нет'
        )
        return start(update, context)

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
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Кому задать вопрос?',
            reply_markup=reply_markup
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='На данный момент лекции не идут'
        )
        return start(update, context)
    return MAKE_NEW_QUESTION


def make_question_instance(update, context):
    speaker = Person.objects.get(uuid=update.callback_query.data)
    user = Person.objects.get(telegram_id=update.callback_query.message.chat.id)

    user_question = Question.objects.get_or_create(speaker=speaker, guest=user, question='')[0]
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
        return ANSWER_QUESTIONS


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

    update.message.reply_text(
        text=f'Ответ на вопрос: {uuid} отправлен пользователю'
    )


def show_networking_possibilities(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Выберите, с кем хотели бы пообщаться:'
    )
    available_contacts = Person.objects.exclude(first_name='').order_by('?')[:3]
    for contact in available_contacts:
        text = f'{contact.first_name} {contact.last_name}\n{contact.company}'
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton('Написать', callback_data=f'Telegram id:{contact.telegram_id}')]]
            )
        )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Найти других гостей?',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton('Другие варианты', callback_data=str(NETWORKING)),
                    InlineKeyboardButton('Вернуться в основное меню', callback_data=str(START_OVER))
                ]
            ]
        )
    )


def forward_message_to_guest(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'{update.callback_query.data}'
    )


def start_networking(update, context):
    curr_user = Person.objects.get(telegram_id=update.effective_chat.id)
    if curr_user.last_name:
        show_networking_possibilities(update, context)
    else:
        chat_id = update.effective_chat.id
        text = (
            'Для знакомства заполните свой профиль\n'
            'Ваша Фамилия:'
        )

        context.bot.send_message(
            chat_id=chat_id,
            text=text
        )

        return LASTNAME


def get_first_name(update, context):
    chat_id = update.effective_chat.id
    context.user_data['lastname'] = update.message.text

    text = (
        'Ваше имя:'
    )

    context.bot.send_message(
        chat_id=chat_id,
        text=text
    )

    return FIRSTNAME


def get_email(update, context):
    chat_id = update.effective_chat.id
    context.user_data['firstname'] = update.message.text

    text = (
        'Ваш email:'
    )

    context.bot.send_message(
        chat_id=chat_id,
        text=text
    )

    return EMAIL


def get_company_name(update, context):
    chat_id = update.effective_chat.id
    context.user_data['email'] = update.message.text

    text = (
        'В какой компании работаете?'
    )

    context.bot.send_message(
        chat_id=chat_id,
        text=text
    )

    return COMPANY


def get_phone(update, context):
    chat_id = update.effective_chat.id
    context.user_data['company'] = update.message.text

    text = (
        'Поделитесь своим номером телефона, пожалуйста'
    )

    reply_markup = ReplyKeyboardMarkup([[
        KeyboardButton(text='Поделиться контатной информацией', request_contact=True)
    ]], one_time_keyboard=True, resize_keyboard=True)

    context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup
    )

    return PHONE


def finish_profile(update, context):
    curr_user = Person.objects.get(telegram_id=update.effective_chat.id)
    curr_user.first_name = context.user_data['firstname']
    curr_user.last_name = context.user_data['lastname']
    curr_user.email = context.user_data['email']
    curr_user.company = context.user_data['company']
    curr_user.phone_number = update.message.contact.phone_number
    curr_user.save()
    print('Регистрация завершена')

    return start_networking(update, context)


def message_handler(update: telegram.Update, context: CallbackContext):
    # Записать вопрос в базу данных
    try:
        if 'ask_question' in os.getenv(f'{update.effective_chat.id}'):
            _, question_uuid = os.getenv(f'{update.effective_chat.id}').split(':')
            question = Question.objects.get(uuid=question_uuid)
            question.question = update.message.text
            question.save()
            os.environ.pop(f'{update.effective_chat.id}')
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Ваш вопрос отправлен спикеру'
            )
    except TypeError:
        pass

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
    try:
        if '+Ответ+' in text:
            return speaker_answer_handler(update=update, context=context)
    except TypeError:
        pass

def main():
    load_dotenv()
    tg_bot_token = os.getenv('TG_BOT_TOKEN')

    # answer_button_handler = CallbackQueryHandler(callback=button_answer_handler, pattern=ANSWER)
    #answer_button_handler = CallbackQueryHandler(callback=button_answer_handler)

    updater = Updater(token=tg_bot_token, use_context=True)

    main_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
        ],
        states={
            BEGGINNING_STATE:[
                CallbackQueryHandler(start, pattern=f'^{START_OVER}$'),
                CallbackQueryHandler(get_schedule, pattern=f'^{SCHEDULE}$'),
                CallbackQueryHandler(ask_question, pattern=f'^{ASK_QUESTION}$'),
                CallbackQueryHandler(get_donation_amount, pattern='make_donation'),
                CallbackQueryHandler(button_answer_handler, pattern=QUESTIONS_BUTTON),
                CallbackQueryHandler(cancel_payments, pattern='cancel_donation')
            ],
            MAKE_NEW_QUESTION:[
                CallbackQueryHandler(callback=make_question_instance),
                MessageHandler(filters=Filters.all, callback=message_handler)
            ],
            ANSWER_QUESTIONS:[
                CallbackQueryHandler(button_answer_handler),
                MessageHandler(filters=Filters.all, callback=message_handler)
            ]
        },
        fallbacks=[
            CommandHandler('start', start)
        ],
        allow_reentry=True
    )

    profile_filler_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_networking, pattern=f'^{NETWORKING}$'),
            CallbackQueryHandler(forward_message_to_guest)
        ],
        states={
            LASTNAME:[MessageHandler(filters=Filters.text, callback=get_first_name)],
            FIRSTNAME:[MessageHandler(filters=Filters.text, callback=get_email)],
            EMAIL:[MessageHandler(filters=Filters.text, callback=get_company_name)],
            COMPANY:[MessageHandler(filters=Filters.text, callback=get_phone)],
            PHONE:[MessageHandler(filters=Filters.contact, callback=finish_profile)],
        },
        fallbacks=[CommandHandler('start', start)],
        allow_reentry=True
    )
    updater.dispatcher.add_handler(main_conv_handler)
    updater.dispatcher.add_handler(profile_filler_handler)


    #updater.dispatcher.add_handler(answer_button_handler)
    #updater.dispatcher.add_handler(CallbackQueryHandler(get_donation_amount, pattern='make_donation'))
    #updater.dispatcher.add_handler(CallbackQueryHandler(cancel_payments, pattern='cancel_donation'))
    #updater.dispatcher.add_handler(CallbackQueryHandler(forward_message_to_guest, pattern=f'^{SEND_MESSAGE}$'))
    updater.dispatcher.add_handler(PreCheckoutQueryHandler(confirm_payment))
    updater.dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
