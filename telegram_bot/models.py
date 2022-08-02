from django.db import models
from datetime import datetime
import uuid
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinLengthValidator


class Person(models.Model):
    uuid = models.CharField(
        "id",
        unique=True,
        default=uuid.uuid1,
        max_length=36,
        validators=[MinLengthValidator(36)],
        primary_key=True,
        editable=False
    )
    first_name = models.CharField('First name', max_length=50)
    last_name = models.CharField('Last name', max_length=50)
    patronymic = models.CharField('Patronymic', max_length=50, blank=True)

    phone_number = PhoneNumberField('Phone number')

    telegram_id = models.SmallIntegerField('Telegram ID')

class Guest(Person):
    specializations = models.ManyToManyField(
        'Specialization',
        verbose_name='Specializations',
        related_name='guests',
    )

    GRADES = [
    ('BG', 'beginner'),
    ('JN', 'junior'),
    ('MD', 'middle'),
    ('SR', 'senior'),
    ('TL', 'team lead'),
    ('PM', 'project manager')
]
    grade = models.CharField('grade', max_length=50, choices=GRADES)

    def __str__(self):
        return f'{self.second_name} {self.first_name} ({self.grade})'


class Speaker(Person):
    pass

class Organizer(Person):
    pass


class Specialization(models.Model):
    title = models.CharField('Specialization', max_length=100)


class Event(models.Model):
    uuid = models.CharField(
        "id",
        unique=True,
        default=uuid.uuid1,
        max_length=36,
        validators=[MinLengthValidator(36)],
        primary_key=True,
        editable=False
    )
    title = models.CharField('Event title', max_length=200)
    description = models.TextField('Description', blank=True)
    start = models.DateTimeField('Start')
    finish = models.DateTimeField('Finish')

    def in_process(self):
        return self.start < datetime.now() < self.finish


class Lecture(models.Model):
    uuid = models.CharField(
        "id",
        unique=True,
        default=uuid.uuid1,
        max_length=36,
        validators=[MinLengthValidator(36)],
        primary_key=True,
        editable=False
    )
    title = models.CharField('Lecture title', max_length=200)
    description = models.TextField('Description', blank=True)
    event = models.ForeignKey(
        'Event',
        verbose_name='Event',
        related_name='lectures',
        on_delete=models.PROTECT
    )
    speaker = models.ForeignKey(
        'Speaker',
        verbose_name='Event',
        related_name='lectures',
        on_delete=models.PROTECT
    )
    schedule_start = models.DateTimeField('Schedule start')
    schedule_end = models.DateTimeField('Schedule end')

    fact_start = models.DateTimeField('Fact start', blank=True)
    fact_end = models.DateTimeField('Fact end', blank=True)


class Question(models.Model):
    uuid = models.CharField(
        "id",
        unique=True,
        default=uuid.uuid1,
        max_length=36,
        validators=[MinLengthValidator(36)],
        primary_key=True,
        editable=False
    )
    guest = models.ForeignKey(
        'Guest',
        verbose_name='Guest',
        related_name='questions',
        on_delete=models.PROTECT
    )

    speaker = models.ForeignKey(
        'Speaker',
        verbose_name='Speaker',
        related_name='questions',
        on_delete=models.PROTECT
    )

    question = models.TextField('Question')
    answer = models.TextField('Answer', blank=True)

    # Оставляет право не отвечать на вопрос если он не по делу
    processed = models.BooleanField('Processed', default=True)
    