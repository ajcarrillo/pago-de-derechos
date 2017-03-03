from __future__ import unicode_literals

from django.db import models


class ReporteDeposito(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    banco = models.ForeignKey('solicitud_pago.Banco', db_column='banco')
    depositos_reportados = models.IntegerField(db_column='depositos_reportados')
    depositos_procesados = models.IntegerField(db_column='depositos_procesados')
    nombre_original = models.CharField(db_column='nombre_reporte', max_length=255)
    fecha_carga = models.DateField(db_column='fecha_carga')
    ip_cliente = models.CharField(db_column='ip_cliente', max_length=15)
    hash_contenido = models.CharField(db_column='hash_contenido', max_length=40, db_index=True)
    contenido_original = models.TextField(db_column='contenido_original')
    contenido_fallido = models.TextField(db_column='contenido_fallido', null=True)

    class Meta:
        db_table = 'reporte_deposito'

    def __unicode__(self):
        return self.nombre_original


class Deposito(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    fecha = models.DateField(db_column='fecha')
    referencia = models.CharField(db_column='referencia', max_length=255)
    abono = models.DecimalField(db_column='abono', max_digits=8, decimal_places=2)
    saldo = models.DecimalField(db_column='saldo', max_digits=8, decimal_places=2)
    cargo = models.DecimalField(db_column='cargo', max_digits=8, decimal_places=2, null=True)
    reporte_deposito = models.ForeignKey(ReporteDeposito, db_column='reporte_deposito')
    multiples_pagos = models.IntegerField(db_column='multiples_pagos', default=1)

    class Meta:
        db_table = 'deposito'

    def __unicode__(self):
        return "%s - %s" % (self.id, self.referencia)
