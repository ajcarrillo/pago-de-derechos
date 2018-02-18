# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-03-22 10:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pago', '0006_remove_deposito_multiples_pagos'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reportedeposito',
            name='hash_contenido',
            field=models.CharField(db_column='hash_contenido', db_index=True, max_length=40, unique=True),
        ),
    ]
