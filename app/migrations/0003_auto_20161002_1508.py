# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-10-02 15:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20161002_1502'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='trader',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.Trader'),
        ),
    ]
