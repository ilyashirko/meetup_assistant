from django.contrib import admin

from telegram_bot.models import Person, Event, Lecture, Question

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    pass

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    pass

@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    pass

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    pass
