# Generated by Django 4.0.6 on 2022-08-03 12:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0003_load_test_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='event',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='questions', to='telegram_bot.event', verbose_name='Event'),
        ),
    ]
