# Generated by Django 3.2.16 on 2024-02-21 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_subscribed',
            field=models.BooleanField(blank=True, default=False, verbose_name='Подписаться на автора'),
        ),
    ]
