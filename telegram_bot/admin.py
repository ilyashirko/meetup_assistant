from django.contrib import admin

from telegram_bot.models import Person, Event, Lecture, Question


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'telegram_id', 'phone_number', 'company')
    list_filter = ('company',)


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
