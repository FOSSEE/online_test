# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-06-25 10:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('yaksh', '0019_easystandardtestcase_weight'),
    ]

    operations = [
        migrations.AlterField(
            model_name='easystandardtestcase',
            name='operator',
            field=models.CharField(choices=[('!=', '!='), ('==', '==')], max_length=24),
        ),
    ]
