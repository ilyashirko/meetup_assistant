from django.contrib import admin

from telegram_bot.models import Guest

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    pass
