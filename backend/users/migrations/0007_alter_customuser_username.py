# Generated by Django 3.2.16 on 2024-03-01 09:44

import api.validators
import django.contrib.auth.validators
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20240222_1336'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(default='username', max_length=149, unique=True, validators=[django.core.validators.RegexValidator(regex='^[\\w.@+-]+\\Z'), django.contrib.auth.validators.UnicodeUsernameValidator(), api.validators.validate_username], verbose_name='Псевдоним'),
        ),
    ]
