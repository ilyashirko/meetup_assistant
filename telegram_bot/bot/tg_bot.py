import telegram
from telegram.ext import Updater, MessageHandler, CallbackContext
from telegram.ext.filters import Filters
import traceback
import sys


class Bot():

    def __init__(self, token):
        if not token:
            raise(ValueError('Токен не указан!'))
        self.token = token
        self.bot = telegram.Bot(token=token)
        self.updater = Updater(self.token, use_context=True)
        self.job_queue = self.updater.job_queue
        self.dispatcher = self.updater.dispatcher
    
    def message_handler(self, update: telegram.Update, context: CallbackContext):
        update.message.reply_text(text='Я получил ваше сообщение')
    
    def send_message(self, chat_id, message):
        return self.bot.send_message(chat_id=chat_id, text=message).message_id
    
    def update_message(self, chat_id, message_id, new_message):
        self.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=new_message)
    
    def reply_on_message(self, callback, *args, **kwargs):
        if not callable(callback):
            raise TypeError('Ожидаем функцию на вход')
        if args:
            raise TypeError(f"reply_on_message() takes 1 positional argument but {len(args) + 1} were given")

        def handle_text(update, context):
            users_reply = update.message.text
            chat_id = update.message.chat_id
            callback(chat_id, users_reply, **kwargs)

        self.dispatcher.add_handler(MessageHandler(Filters.text, handle_text))
    
    def run_bot(self):
        def error_handler(update, context):
            error = context.error
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr, limit=-3)

        self.dispatcher.add_error_handler(error_handler)
        self.dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=self.message_handler))
        self.updater.start_polling()
        self.updater.idle()
