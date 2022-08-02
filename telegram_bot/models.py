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
    first_name = models.CharField('First name', max_length=50, blank=True)
    last_name = models.CharField('Last name', max_length=50, blank=True)
    patronymic = models.CharField('Patronymic', max_length=50, blank=True)

    phone_number = PhoneNumberField('Phone number', blank=True)
    email = models.EmailField('E-mail', blank=True)

    company = models.CharField('Company', max_length=100, blank=True)

    telegram_id = models.SmallIntegerField('Telegram ID')

    def __str__(self):
        return (
            f'{self.second_name if self.second_name else "User"} '
            f'{self.first_name if self.first_name else ""} ({self.telegram_id})'
        )


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
    organizer = models.ForeignKey(
        'Person',
        verbose_name='Organizer',
        related_name='events',
        on_delete=models.PROTECT
    )
    start = models.DateTimeField('Start')
    finish = models.DateTimeField('Finish')

    def in_process(self):
        return self.start < datetime.now() < self.finish

    def __str__(self):
        return self.title


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
        'Person',
        verbose_name='Event',
        related_name='lectures',
        on_delete=models.PROTECT
    )
    start = models.DateTimeField('Start')
    end = models.DateTimeField('Schedule end')

    def __str__(self):
        return f'{self.title} ({self.speaker})'


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
        'Person',
        verbose_name='Guest',
        related_name='questions_from',
        on_delete=models.PROTECT
    )

    speaker = models.ForeignKey(
        'Person',
        verbose_name='Speaker',
        related_name='questions_to',
        on_delete=models.PROTECT
    )

    question = models.TextField('Question')
    answer = models.TextField('Answer', blank=True)

    # Оставляет право не отвечать на вопрос если он не по делу
    processed = models.BooleanField('Processed', default=True)

    def __str__(self):
        return f'{self.question[:100]}{"..." if len(self.question) < 100 else ""}'
    