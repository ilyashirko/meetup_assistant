# Generated by Django 4.0.6 on 2022-08-08 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0012_add_test_questions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donate',
            name='paid_at',
            field=models.DateTimeField(blank=True, verbose_name='Created or Paid at'),
        ),
    ]
