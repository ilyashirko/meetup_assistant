# Generated by Django 4.0.6 on 2022-08-08 11:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0008_adminmessage_was_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='donate',
            name='paid_at',
            field=models.DateTimeField(auto_now=True, blank=True, verbose_name='Paid at'),
        ),
    ]
