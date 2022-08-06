import os

import requests
from django.contrib import admin
from django.db import models
from django.forms import CheckboxSelectMultiple

from telegram_bot.models import (AdminMessage, Donate, Event, Lecture, Person,
                                 Question)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'first_name', 'last_name', 'phone_number', 'company')
    list_filter = ('company',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    model = Event
    list_display = ('title', 'organizer', 'start', 'finish')
    raw_id_fields = ('participants',)
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    


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
        for message in queryset:
            users = message.users.all() or Person.objects.all()
            for user in users:
                requests.get(
                    f'https://api.telegram.org/bot{os.getenv("TG_BOT_TOKEN")}/sendMessage',
                    params={
                        'chat_id': user.telegram_id,
                        'text': message.message
                    }
                )
            message.was_sent = True
            message.save()
    send_message.short_description = "Send message(-s)"

    list_display = ('message', 'was_sent')
    raw_id_fields = ('users', )
    actions = [send_message]
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    
