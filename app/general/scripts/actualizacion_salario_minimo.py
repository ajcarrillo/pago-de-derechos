# -*- encoding: utf-8 -*-
import datetime
import decimal

from app.solicitud_pago.models import SalarioMinimo

for salario_minimo in SalarioMinimo.objects.all():
	if salario_minimo.activo:
		salario_minimo.fecha_baja = datetime.date.today()
		salario_minimo.activo = False
		salario_minimo.save()

#salario minimo
nuevo_salario_minimo = SalarioMinimo()
nuevo_salario_minimo.monto = decimal.Decimal('61.38')
nuevo_salario_minimo.activo = True
nuevo_salario_minimo.fecha_alta = datetime.date.today()
nuevo_salario_minimo.save()

print 'actualización de salario mínimo terminada\n'
