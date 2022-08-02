from django.core.management.base import BaseCommand
from environs import Env


class Command(BaseCommand):
    help = "Telegram bot"

    def handle(self, *args, **kwargs):
        env = Env()
        env.read_env()

        # write here