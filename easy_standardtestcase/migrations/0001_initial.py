# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-05-30 05:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='easy_standardtestcase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('function', models.TextField()),
                ('inputVals', models.CharField(max_length=200)),
                ('output', models.IntegerField()),
                ('final_standardtestcase', models.TextField()),
            ],
        ),
    ]
