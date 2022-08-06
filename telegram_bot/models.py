from textwrap import dedent
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
            f'{self.last_name if self.last_name else "User"} '
            f'{self.first_name if self.first_name else self.telegram_id}'
        )

    def is_speaker(self, event):
        lectures = Lecture.objects.filter(event=event)
        speakers = [lecture.speaker for lecture in lectures]
        return self in speakers


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
        related_name='organized_events',
        on_delete=models.PROTECT
    )
    participants = models.ManyToManyField(
        'Person',
        verbose_name='Participants',
        related_name='took_parts_in',
    )
    start = models.DateTimeField('Start')
    finish = models.DateTimeField('Finish')

    def in_process(self):
        return self.start < datetime.now() < self.finish

    def _convert_time(self, date_time):
        hour = date_time.hour
        minute = date_time.minute
        if 10 > hour >= 0:
            hour = f'0{hour}'
        if minute < 10:
            minute = f'0{minute}'
        return f'{hour}:{minute}'
        
    def get_programm(self):
        lectures = self.lectures.all().order_by('start')
        programm = (
            f'{self.title}\n\n'

            f'Время начала: {self.start}\n'
            f'Время завершения: {self.finish}\n'
        )
        for lecture in lectures:
            programm += (
                f'\n{self._convert_time(lecture.start)} - '
                f'{lecture.title} ({lecture.speaker})'
            )
        return programm



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
    event = models.ForeignKey(
        'Event',
        verbose_name='Event',
        related_name='questions',
        on_delete=models.PROTECT,
        default=None,
        null=True
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

    question = models.TextField('Question', blank=True)
    answer = models.TextField('Answer', blank=True)

    # Оставляет право не отвечать на вопрос если он не по делу
    processed = models.BooleanField('Processed', default=False)

    def __str__(self):
        return f'{self.question[:100]}{"..." if len(self.question) < 100 else ""}'




class Donate(models.Model):
    payment_id = models.CharField(
        "id",
        unique=True,
        default=uuid.uuid1,
        max_length=36,
        validators=[MinLengthValidator(36)],
        primary_key=True,
        editable=False
    )
    event = models.ForeignKey(
        'Event',
        verbose_name='Event',
        related_name='donations',
        on_delete=models.PROTECT,
        blank=True
    )
    user = models.ForeignKey(
        'Person',
        verbose_name='Guest',
        related_name='donations',
        on_delete=models.PROTECT
    )
    summ = models.IntegerField('Amount', null=True)
    confirmed = models.BooleanField('Payment confirmed', default=False)


class AdminMessage(models.Model):
    message = models.TextField('Message', max_length=3000) # max length because of Telegram API limits
    users = models.ManyToManyField(
        'Person',
        verbose_name='Users (if blank, will send to everyone in database)',
        related_name='got_admin_messages',
        blank=True
    )
