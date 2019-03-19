# -*- encoding: utf-8 -*-
import datetime
import decimal
import json

import math
from django.db import transaction
from django.db.models import Sum
from django.forms.models import model_to_dict
from django.http import HttpResponse
from rest_framework.views import APIView

from algoritmos import M97Q
from models import Contribuyente, Concepto, SalarioMinimo, SolicitudPago, ReferenciaPago

MUNICIPIOS_VALIDOS = {
    '00': 'Otro',
    '01': 'Cozumel',
    '02': 'Felipe Carrillo Puerto',
    '03': 'Isla Mujeres',
    '04': 'Othón P. Blanco',
    '05': 'Benito Juárez',
    '06': 'José María Morelos',
    '07': 'Lázaro Cárdenas',
    '08': 'Solidaridad',
    '09': 'Tulum',
    '10': 'Bacalar',
    '11': 'Puerto Morelos'
}


def serializar_solicitud(solicitud_pago):
    response_dict = {
        'id':              solicitud_pago.id,
        'concepto':        {
            'clave':       solicitud_pago.concepto.clave,
            'descripcion': solicitud_pago.concepto.descripcion
        },
        'cantidad':        solicitud_pago.cantidad,
        'salario_minimo':  str(solicitud_pago.salario_minimo.monto),
        'referencia_pago': {
            'referencia': solicitud_pago.referencia_pago.referencia,
            'vigencia':   str(solicitud_pago.referencia_pago.vigencia)
        },
        'fecha_solicitud': str(solicitud_pago.fecha_solicitud),
        'monto':           str(solicitud_pago.monto),
        'total':           str(solicitud_pago.total),
        'descuento':       str(solicitud_pago.descuento),
        'contribuyente':   model_to_dict(solicitud_pago.contribuyente, exclude='id'),
        'deposito':        None
    }
    if solicitud_pago.deposito is not None:
        response_dict['deposito'] = {
            'fecha': str(solicitud_pago.deposito.fecha),
            'abono': str(solicitud_pago.deposito.abono),
            'banco': solicitud_pago.deposito.reporte_deposito.banco.referencia
        }
    return json.dumps(response_dict, indent=4)


class SolicitudPagoResource(APIView):
    def get(self, request, pk=None):
        try:
            if pk is None:
                raise Exception('Solicitud de pago no encontrada')
            solicitud_pago = SolicitudPago.objects.get(pk=pk)
            return HttpResponse(serializar_solicitud(solicitud_pago), content_type='application/json; charset=UTF-8')
        except Exception as e:
            return HttpResponse(e, status=404)

    def post(self, request):
        transaction.set_autocommit(False)
        try:
            '''parámetros obligatorios: concepto, cantidad, contribuyente[nombre_completo, municipio]'''

            data = json.loads(request.body)
            self.clean_dict(data)
            # concepto de pago (obligatorio)
            concepto = Concepto.objects.filter(clave=data.get('concepto'))
            concepto = concepto[0] if concepto.exists() else None
            if concepto == None:
                raise Exception('Concepto no encontrado')
            # salario mínimo activo (obligatoria la existencia de exactamente uno activo)
            salario_minimo = SalarioMinimo.objects.filter(activo=True)
            if len(salario_minimo) != 1:
                raise Exception('Debe haber exactamente un salario mínimo activo')
            salario_minimo = salario_minimo[0]
            # descuento
            descuento = data['descuento'] if data.get('descuento') is not None else decimal.Decimal('0')

            if 'contribuyente' not in data:
                raise Exception('Los datos del contributente son obligatorios')
            self.clean_dict(data['contribuyente'])

            nombre_completo = data['contribuyente'].get('nombre_completo')
            if nombre_completo is None:
                raise Exception('El nombre del contribuyente es obligatorio')
            curp = data['contribuyente'].get('curp')

            # Validacion para los extranjeros: estos siempre tendran la misma CURP
            if curp == '000000000000000000' or curp is None:
                # Buscamos por nombre
                try:
                    contribuyente = Contribuyente.objects.filter(nombre_completo=nombre_completo)[:1].get()
                except Contribuyente.DoesNotExist:
                    contribuyente = None
            else:
                # Buscamos al contribuyente por CURP
                try:
                    contribuyente = Contribuyente.objects.filter(curp=curp)[:1].get()
                except Contribuyente.DoesNotExist:
                    # Buscamos por nombre
                    try:
                        contribuyente = Contribuyente.objects.filter(nombre_completo=nombre_completo)[:1].get()
                    except Contribuyente.DoesNotExist:
                        contribuyente = None

            if contribuyente is None:
                # Creamos un contribuyente
                contribuyente = Contribuyente()
            else:
                # TODO Transaformar a minusculas o mayusculas para evitar errores al comparar los mismos nombres pero ingresados en may o min
                if nombre_completo != contribuyente.nombre_completo:
                    raise Exception('Tus datos no coinciden. ¿Corresponde tu CURP con tu Nombre?')

            contribuyente.nombre_completo = data['contribuyente'].get('nombre_completo')
            if contribuyente.nombre_completo is None:
                raise Exception('El nombre del contribuyente es obligatorio')
            if data['contribuyente'].get('municipio') not in MUNICIPIOS_VALIDOS:
                raise Exception('Municipio inválido')
            contribuyente.municipio = MUNICIPIOS_VALIDOS[data['contribuyente']['municipio']]
            contribuyente.rfc = data['contribuyente'].get('rfc')
            if contribuyente.rfc is not None and len(contribuyente.rfc) != 13:
                raise Exception('RFC del contribuyente inválido')
            contribuyente.curp = data['contribuyente'].get('curp')
            """
            Dado que el registro automatico de siem jala los datos de siceeb alguna CURP no contienen los 18 caracteres
            if contribuyente.curp is not None and len(contribuyente.curp) != 18:
                raise Exception('CURP del contribuyente inválida')
            """
            contribuyente.entidad_federativa = 'Quintana Roo'
            contribuyente.localidad = data['contribuyente'].get('localidad')
            contribuyente.colonia = data['contribuyente'].get('colonia')
            contribuyente.calle = data['contribuyente'].get('calle')
            contribuyente.codigo_postal = data['contribuyente'].get('codigo_postal')
            contribuyente.numero = data['contribuyente'].get('numero')
            contribuyente.save()
            # referencia de pago
            referencia_pago = ReferenciaPago()
            # calculo de fecha de vigencia
            if data.get('vigencia') is None:
                referencia_pago.vigencia = datetime.date.today() + datetime.timedelta(days=15)
            else:
                try:
                    vigencia = data['vigencia'].split('-')
                    referencia_pago.vigencia = datetime.date(int(vigencia[0]), int(vigencia[1]), int(vigencia[2]))
                except:
                    raise Exception('Formato inválido de vigencia, se necesita aaaa/mm/dd')
                if referencia_pago.vigencia < datetime.date.today():
                    raise Exception('No puedo generar una referencia de pago con la vigencia vencida')
                elif referencia_pago.vigencia == datetime.date.today():
                    referencia_pago.vigencia = datetime.date.today() + datetime.timedelta(days=2)
                elif (referencia_pago.vigencia - datetime.timedelta(days=1) == datetime.date.today()):
                    referencia_pago.vigencia = datetime.date.today() + datetime.timedelta(days=2)
            referencia_pago.fecha_generacion = datetime.date.today()
            referencia_pago.save()
            # solicitud de pago
            solicitud_pago = SolicitudPago()
            solicitud_pago.contribuyente = contribuyente
            solicitud_pago.concepto = concepto
            if data.get('cantidad') is None:
                raise Exception('Cantidad del concepto a solicitar requerida')
            solicitud_pago.cantidad = int(data.get('cantidad'))
            solicitud_pago.salario_minimo = salario_minimo
            solicitud_pago.referencia_pago = referencia_pago
            solicitud_pago.fecha_solicitud = datetime.date.today()
            solicitud_pago.monto = concepto.salarios_minimos * salario_minimo.monto * solicitud_pago.cantidad
            # redondeo del monto, no se cobran centavos
            solicitud_pago.monto = solicitud_pago.monto.quantize(decimal.Decimal('0'), rounding=decimal.ROUND_HALF_UP)
            solicitud_pago.descuento = decimal.Decimal(descuento).quantize(decimal.Decimal('0'), rounding=decimal.ROUND_HALF_UP)
            t = solicitud_pago.monto - (solicitud_pago.monto * (solicitud_pago.descuento/100))
            solicitud_pago.total = decimal.Decimal(math.ceil(t)).quantize(decimal.Decimal('0'), rounding=decimal.ROUND_HALF_UP)
            if solicitud_pago.total < 0:
                raise Exception('El descuento excede el monto total a pagar')

            # generando referencia en base al monto de la solicitud de pago
            consecutivo_hexadecimal = hex(referencia_pago.id).replace('0x', '').replace('L', '').upper().zfill(7)
            # referencia_contribuyente = '%s%s%s' % (concepto.clave, data['contribuyente']['municipio'], consecutivo_hexadecimal)
            '''
				Proceso 2015: Se agregó un cero mas a la izquierda debido a los requisitos de los bancos HSBC y Santander
			'''
            referencia_contribuyente = '%s%s%s' % ('0026', data['contribuyente']['municipio'], consecutivo_hexadecimal)
            algoritmo = M97Q(referencia_contribuyente, solicitud_pago.total, referencia_pago.vigencia)
            referencia_pago.referencia = algoritmo.generar()
            referencia_pago.save()
            # se termina la solicitud de pago
            solicitud_pago.save()
            # preparando la respuesta
            http_response = HttpResponse(status=201)
            http_response['Location'] = '/solicitud-pago/%s' % solicitud_pago.id
            print ('*' * 50)
            print (http_response)
            print ('*' * 50)
            transaction.commit()
            return http_response
        except Exception as e:
            transaction.rollback()
            return HttpResponse(e, status=400)

    def clean_dict(self, dict):
        for item in dict:
            if dict[item] is None or unicode(dict[item]).strip() == '':
                dict[item] = None


class SolicitudPagoReferencia(APIView):
    def get(self, request, referencia):
        try:
            referencia_pago = ReferenciaPago.objects.filter(referencia=referencia)
            if referencia_pago.exists():
                referencia_pago = referencia_pago.get()
                solicitud_pago = SolicitudPago.objects.get(referencia_pago=referencia_pago)
                return HttpResponse(serializar_solicitud(solicitud_pago), content_type='application/json; charset=UTF-8')
            else:
                raise Exception('No se encuentra la referencia de pago')
        except Exception as e:
            return HttpResponse(e, status=404)


class StatusSolicitudPago(APIView):
    def get(self, request):
        try:
            concepto = request.GET.get('concepto')
            resumen = None
            if concepto:
                resumen = self.resumen_concepto(Concepto.objects.get(clave=concepto))
            else:
                resumen = self.resumen_general()
            return HttpResponse(json.dumps(resumen, indent=4), content_type='application/json; charset=UTF-8')
        except Exception as e:
            return HttpResponse(e, status=404)

    def resumen_concepto(self, concepto):
        resumen = dict()
        solicitudes_concepto = SolicitudPago.objects.filter(concepto=concepto)
        resumen['solicitudes_generadas'] = solicitudes_concepto.count()
        resumen['solicitudes_pagadas'] = solicitudes_concepto.exclude(deposito__isnull=True).count()
        resumen['monto_total_pagado'] = str(solicitudes_concepto.exclude(deposito__isnull=True).aggregate(Sum('total'))['total__sum'])
        return resumen

    def resumen_general(self):
        solicitudes_concepto = SolicitudPago.objects.all()
        resumen = dict()
        resumen['solicitudes_generadas'] = solicitudes_concepto.count()
        resumen['solicitudes_pagadas'] = solicitudes_concepto.exclude(deposito__isnull=True).count()
        resumen['monto_total_pagado'] = str(solicitudes_concepto.exclude(deposito__isnull=True).aggregate(Sum('total'))['total__sum'])
        return resumen
