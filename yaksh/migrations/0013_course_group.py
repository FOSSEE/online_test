# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-07-05 12:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('yaksh', '0012_auto_20180628_0922'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='group',
            field=models.CharField(choices=[('Self', 'Self'), ('Instructor', 'Instructor')], default='Unknown', max_length=32),
        ),
    ]
