# -*- encoding: utf-8 -*-
from app.solicitud_pago.models import Convenio, Banco, Concepto, ConvenioPagoConcepto

bancomer = Banco()
bancomer.referencia = 'BBVA BANCOMER'
bancomer.descripcion = 'Banco de Comercio'
bancomer.save()

convenios_bancomer = ['1148966', '1148915']
for numero_convenio in convenios_bancomer:
	convenio = Convenio()
	convenio.banco = bancomer
	convenio.referencia = numero_convenio
	convenio.save()
	if numero_convenio == '1148966':
		convenio_pago_concepto = ConvenioPagoConcepto()
		convenio_pago_concepto.convenio = convenio
		convenio_pago_concepto.concepto = Concepto.objects.get(clave = '026')
		convenio_pago_concepto.save()
	else:
		for concepto in Concepto.objects.exclude(clave = '026'):
			convenio_pago_concepto = ConvenioPagoConcepto()
			convenio_pago_concepto.convenio = convenio
			convenio_pago_concepto.concepto = concepto
			convenio_pago_concepto.save()

santander = Banco()
santander.referencia = 'SANTANDER'
santander.descripcion = 'Banco Santander S.A.'
santander.save()

convenios_santander = ['3776']
for numero_convenio in convenios_santander:
	convenio = Convenio()
	convenio.banco = santander
	convenio.referencia = numero_convenio
	convenio.save()
	for concepto in Concepto.objects.all():
		convenio_pago_concepto = ConvenioPagoConcepto()
		convenio_pago_concepto.convenio = convenio
		convenio_pago_concepto.concepto = concepto
		convenio_pago_concepto.save()

print 'carga de bancos, convenios, y asginación de convenios terminada'
