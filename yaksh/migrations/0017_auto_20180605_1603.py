# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-06-05 16:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('yaksh', '0016_auto_20180605_0838'),
    ]

    operations = [
        migrations.AlterField(
            model_name='easystandardtestcase',
            name='operator',
            field=models.CharField(choices=[(1, '=='), (2, '!='), (3, '>='), (4, '<='), (5, '>'), (6, '<')], max_length=24, null=True),
        ),
    ]
