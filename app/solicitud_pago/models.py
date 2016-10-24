from __future__ import unicode_literals

from django.db import models


class ReferenciaPago(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    referencia = models.CharField(db_column='referencia', max_length=22, unique=True, null=True)
    vigencia = models.DateField(db_column='vigencia')
    fecha_generacion = models.DateField(db_column='fecha_generacion')

    class Meta:
        db_table = 'referencia_pago'


class Contribuyente(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    nombre_completo = models.CharField(db_column='nombre_completo', max_length=255)
    rfc = models.CharField(db_column='rfc', max_length=13, null=True)
    curp = models.CharField(db_column='curp', max_length=18, null=True)
    entidad_federativa = models.CharField(db_column='entidad_federativa', max_length=50, null=True)
    municipio = models.CharField(db_column='municipio', max_length=80, null=True)
    localidad = models.CharField(db_column='localidad', max_length=100, null=True)
    codigo_postal = models.CharField(db_column='codigo_postal', max_length=5, null=True)
    colonia = models.CharField(db_column='colonia', max_length=255, null=True)
    calle = models.CharField(db_column='calle', max_length=255, null=True)
    numero = models.CharField(db_column='numero', max_length=8, null=True)

    class Meta:
        db_table = 'contribuyente'


class Banco(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    referencia = models.CharField(db_column='referencia', max_length=50)
    descripcion = models.CharField(db_column='descripcion', max_length=255, null=True)

    class Meta:
        db_table = 'banco'


class Convenio(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    banco = models.ForeignKey(Banco, db_column='banco', related_name='convenios')
    referencia = models.CharField(db_column='referencia', max_length=20)
    descripcion = models.CharField(db_column='descripcion', max_length=255, null=True)

    class Meta:
        db_table = 'convenio'


class Concepto(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    clave = models.CharField(db_column='clave', max_length=3, unique=True)
    descripcion = models.CharField(db_column='descripcion', max_length=500)
    salarios_minimos = models.DecimalField(db_column='salarios_minimos', max_digits=8, decimal_places=2)
    convenios = models.ManyToManyField(Convenio, through='ConvenioPagoConcepto')

    class Meta:
        db_table = 'concepto'


class ConvenioPagoConcepto(models.Model):
    convenio = models.ForeignKey(Convenio, db_column='convenio')
    concepto = models.ForeignKey(Concepto, db_column='concepto')

    class Meta:
        db_table = 'convenio_pago_concepto'


class SalarioMinimo(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    monto = models.DecimalField(db_column='monto', max_digits=8, decimal_places=2)
    activo = models.BooleanField(db_column='activo')
    fecha_alta = models.DateField(db_column='fecha_alta')
    fecha_baja = models.DateField(db_column='fecha_baja', null=True)

    class Meta:
        db_table = 'salario_minimo'


class SolicitudPago(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    contribuyente = models.ForeignKey(Contribuyente, db_column='contribuyente')
    concepto = models.ForeignKey(Concepto, db_column='concepto')
    cantidad = models.IntegerField(db_column='cantidad')
    salario_minimo = models.ForeignKey(SalarioMinimo, db_column='salario_minimo')
    referencia_pago = models.ForeignKey(ReferenciaPago, db_column='referencia_pago')
    fecha_solicitud = models.DateField(db_column='fecha_solicitud')
    monto = models.DecimalField(db_column='monto', max_digits=8, decimal_places=2)
    descuento = models.DecimalField(db_column='descuento', max_digits=8, decimal_places=2)
    deposito = models.ForeignKey('pago.Deposito', db_column='deposito', on_delete=models.DO_NOTHING, unique=True, null=True)
    total = models.DecimalField(db_column='total', max_digits=8, decimal_places=2)

    class Meta:
        db_table = 'solicitud_pago'
