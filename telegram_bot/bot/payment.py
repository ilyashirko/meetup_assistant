import os

from telegram import LabeledPrice
from telegram_bot.bot.bot_main import get_keyboard
from telegram_bot.models import Donate, Event, Person


def get_donation_amount(update, context):
    
    try:
        _, event_uuid = update.callback_query.data.split(':')
        event = Event.objects.get(uuid=event_uuid)      
    except (ValueError, Event.DoesNotExist):
        event = Event.objects.first()

    user = Person.objects.get(telegram_id=update.effective_chat.id)

    payment, _ = Donate.objects.get_or_create(event=event, user=user, summ=None)
    
    os.environ.setdefault(f'{update.effective_chat.id}', '')
    os.environ[f'{update.effective_chat.id}'] = f'donation:{payment.payment_id}'
    
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Какую сумму вы хотели бы задонатить?'
    )


def make_payment(update, context, payment_id, amount):
    payment = Donate.objects.get(payment_id=payment_id)
    payment.summ = amount
    payment.save()
    context.bot.sendInvoice(
        chat_id=update.effective_chat.id,
        title='Help the organizers',
        description=payment.event.title,
        payload=payment.payment_id,
        provider_token=os.getenv('YOOKASSA_TOKEN'),
        currency='RUB',
        prices=[LabeledPrice('Руб', amount*100)]
    )
    

def confirm_payment(update, context):
    context.bot.answerPreCheckoutQuery(update.pre_checkout_query.id, True)
    
    donate = Donate.objects.get(payment_id=update.pre_checkout_query.invoice_payload)
    donate.confirmed = True
    donate.save()
    print(os.getenv(f'{donate.user.telegram_id}'))
    os.environ.pop(f'{donate.user.telegram_id}', 'empty')


def cancel_payments(update, context):
    _, payment_uuid = os.getenv(f'{update.effective_chat.id}').split(':')
    try:
        Donate.objects.get(payment_id=payment_uuid).delete()
    except Donate.DoesNotExist:
        pass
    os.environ.pop(f'{update.effective_chat.id}', 'empty')
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Донат отменен',
        reply_markup=get_keyboard
    )