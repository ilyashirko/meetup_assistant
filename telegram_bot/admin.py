import os
from django.contrib import admin

from telegram_bot.models import AdminMessage, Person, Event, Lecture, Question, Donate


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'telegram_id', 'phone_number', 'company')
    list_filter = ('company',)
    list_select_related = ('lectures',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'start', 'finish')
    raw_id_fields = ('participants',)


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ('event', 'title', 'speaker', 'start', 'end')
    list_filter = ('event',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_filter = ('event', 'speaker', 'processed',)


@admin.register(Donate)
class DonateAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'event', 'user', 'summ', 'confirmed')


@admin.register(AdminMessage)
class AdminMessageAdmin(admin.ModelAdmin):
    
    def send_message(self, request, queryset):
        import requests
        requests.get(f'https://api.telegram.org/bot{os.getenv("TG_BOT_TOKEN")}/sendMessage?chat_id=434137786&text={queryset}')
    send_message.short_description = "Send message(-s)"

    actions = [send_message]

    
