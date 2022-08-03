from django.core.management.base import BaseCommand
from environs import Env

from telegram_bot.bot import bot_main


class Command(BaseCommand):
    help = "Telegram bot"

    def handle(self, *args, **kwargs):
        env = Env()
        env.read_env()

        # write here
        bot_main.main()