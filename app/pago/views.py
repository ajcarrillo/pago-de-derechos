# -*- encoding: utf-8 -*
import datetime
import decimal
import hashlib
import json
import logging
import time
from unicodedata import normalize

from django.core import serializers
from django.db import transaction
from django.db.models import Sum
from django.forms import model_to_dict
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from app.pago.models import ReporteDeposito, Deposito
from app.solicitud_pago.models import ReferenciaPago, SolicitudPago, Banco

logger = logging.getLogger('carga_de_pagos')
module = 'app/pago/views.py'


class ReporteDepositoView(generic.View):
    pagos_reportados = 0  # el total de pagos que envía el reporte
    pagos_realizados = 0  # número de pagos correctamente realizados
    contenido_invalido = None  # texto que contiene la estructura original de los pagos invalidos
    reporte_procesado = None

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(ReporteDepositoView, self).dispatch(*args, **kwargs)

    def post(self, request):
        transaction.set_autocommit(False)
        try:
            if not request.FILES.get('archivo'):
                raise Exception('No se envió ningún archivo')
            peso_maximo = 1024 * 1024 * 3
            uploaded_file = request.FILES['archivo']
            if uploaded_file.size > peso_maximo:
                raise Exception('El archivo excede el tamaño máximo de 3MB')
            id_banco = request.POST.get('banco')
            if not id_banco:
                raise Exception('No se indicó el banco al cual pertenece el reporte')
            banco = Banco.objects.get(pk=id_banco)
            contenido_archivo = uploaded_file.read()

            reporte = ReporteDeposito()
            reporte.banco = banco
            reporte.depositos_reportados = 0
            reporte.depositos_procesados = 0
            reporte.nombre_original = uploaded_file.name
            reporte.fecha_carga = datetime.date.today()
            reporte.ip_cliente = request.META['REMOTE_ADDR']
            sha1_hash = hashlib.sha1()
            sha1_hash.update(contenido_archivo)
            if ReporteDeposito.objects.filter(hash_contenido=sha1_hash.hexdigest()).exists():
                raise Exception('Un reporte con el mismo contenido ya ha sido cargado')
            reporte.hash_contenido = sha1_hash.hexdigest()
            reporte.contenido_original = ''
            self.reporte_procesado = reporte
            self.reporte_procesado.save()

            if banco.referencia == 'BBVA BANCOMER':
                self.procesar_reporte_bancomer(contenido_archivo)
            elif banco.referencia == 'SANTANDER':
                self.procesar_reporte_santander(contenido_archivo)
            elif banco.referencia == 'HSBC':
                self.procesar_reporte_hsbc(contenido_archivo)
            else:
                raise Exception('Aun no está soportado el proceso de reportes de {0}'.format(banco.referencia))

            if self.pagos_realizados == 0:
                raise Exception('No se pudo procesar exitosamente ningún depósito')
            self.reporte_procesado.depositos_reportados = self.pagos_reportados
            self.reporte_procesado.depositos_procesados = self.pagos_realizados
            # logger.warning(contenido_archivo)
            self.reporte_procesado.contenido_original = str(contenido_archivo.decode("utf8", "ignore"))
            self.reporte_procesado.contenido_fallido = self.contenido_invalido
            self.reporte_procesado.save()
            transaction.commit()
            msg = "Reporte: {0}, Reportados: {1}, Procesados: {2}, Contenido Fallido: {3}" \
                .format(self.reporte_procesado.id, self.reporte_procesado.depositos_reportados,
                        self.reporte_procesado.depositos_procesados, self.reporte_procesado.contenido_fallido)
            return HttpResponse(msg, status=200)
        except Exception as e:
            logger.warning(str(e))
            transaction.rollback()
            return HttpResponse(e, status=400)

    def get(self, request):
        return HttpResponse('No se permite obtener la lista de reportes', status=404)

    def procesar_reporte_bancomer(self, contenido):
        pipe_separated = str(contenido).split('|')
        registros_por_deposito = 6
        self.pagos_reportados = len(pipe_separated) // registros_por_deposito
        registros_counter = 0
        campos_pagos_invalidos = []
        for n in range(0, self.pagos_reportados):
            fecha = pipe_separated[registros_counter]
            f1 = pipe_separated[registros_counter + 1]
            f2 = pipe_separated[registros_counter + 2]
            referencia = pipe_separated[registros_counter + 3]
            final_referencia = pipe_separated[registros_counter + 4]
            abono = pipe_separated[registros_counter + 5]
            registros_counter += registros_por_deposito
            deposito = Deposito()
            deposito.abono = decimal.Decimal(abono)
            deposito.saldo = 0
            deposito.reporte_deposito = self.reporte_procesado
            try:
                # validación de la referencia de pago
                referencia_original = '{0}{1}'.format(referencia, final_referencia)
                deposito.referencia = '{0}|{1}'.format(referencia, final_referencia)
                if len(referencia_original) < 20:
                    raise Exception('La referencia no cumple con los dígitos mínimos')
                referencia_original = '{0}-{1}'.format(referencia_original[-20:-2], referencia_original[-2:])
                if len(referencia_original) != 21:
                    raise Exception('El campo de referencia no cumple con la longitud mínima')
                # referencia_pago = ReferenciaPago.objects.get(referencia = referencia_original)
                # validación de fecha
                if len(fecha) < 5 or len(fecha) > 6 or not fecha.isdigit():
                    raise Exception('El campo de fecha no cumple con la longitud requerida')
                deposito.fecha = datetime.date(2000 + int(fecha[-2:]), int(fecha[-4:-2]), int(fecha[:-4]))
                deposito.abono = decimal.Decimal(abono)
                deposito.save()
                # asignación del pago a la solicitud correspondiente
                solicitud_pago = self.asignar_pago_solicitud(referencia_original, deposito)
                if solicitud_pago.total != deposito.abono:
                    raise Exception('El depósito que reporta el banco no concuerda')
                self.pagos_realizados += 1
            except Exception as e:
                logger.warning(e)
                campos_pagos_invalidos += [fecha, f1, f2, referencia, final_referencia, abono]
        if len(campos_pagos_invalidos) > 0:
            self.contenido_invalido = '|'.join(campos_pagos_invalidos)

    def procesar_reporte_santander(self, contenido_archivo):
        contenido_archivo = contenido_archivo.split('\n')
        self.pagos_reportados = 0
        pagos_invalidos = []
        for line in contenido_archivo:
            try:
                splits = line.split()
                if len(splits) == 0: continue  # para evitar el error de 'list index out of range'
                timestamp = splits[1]
                linea_captura = splits[len(splits) - 1]
                if linea_captura[:1] != '+': continue
                self.pagos_reportados += 1
                fecha = time.strptime(timestamp[:8], '%d%m%Y')

                '''
                FIX PROCESO 2015: Aparecieron pagos a referencias de 19 dígitos y se aprobaron debido a que el banco acepta
                referencias de 18, 19 y 20 dígitos. Únicamente se leen los primeros 18 dígitos de derecha a izquiera como
                referencia. Si los primeros dos dígitos de esta referencia son 26, asumimos que es una referencia correcta
                de pago, le agregamos los dos ceros a la izquierda y continuamos el proceso
                '''

                referencia = linea_captura[-18:]
                if referencia[0:2] != '26':
                    raise Exception('Referencia no valida')
                else:
                    referencia = '00' + referencia
                self.guardar_deposito(fecha, referencia)
            except Exception as e:
                pagos_invalidos.append(str(e))
        if len(pagos_invalidos) > 0:
            self.contenido_invalido = '<br>'.join(pagos_invalidos)

    def procesar_reporte_hsbc(self, contenido_archivo):
        contenido_archivo = contenido_archivo.split('\n')
        pagos_invalidos = []
        self.pagos_reportados = 0
        for line in contenido_archivo:
            if line == '':
                break
            try:
                splits = line.split()
                if splits[0] == 'Nombre':
                    continue
                self.pagos_reportados += 1

                referencia = splits[10]
                fecha = time.strptime(splits[14], '%d/%m/%Y')
                self.guardar_deposito(fecha, referencia)
            except Exception as e:
                logger.warning(e)
                pagos_invalidos.append(str(e))
        if len(pagos_invalidos) > 0:
            self.contenido_invalido = '<br>'.join(pagos_invalidos)

    def se_asignara(self, referencia):
        """
        Función para saber si se asignará o no el deposito a la solicitud de pago.
        Esto sirve para siempre asignar el primer deposito a la solicitud de pago.
        """
        deposito = Deposito.objects.filter(referencia=referencia)

        if len(deposito) == 0:
            return True
        else:
            return False

    def asignar_pago_solicitud(self, referencia, deposito):
        referencia_pago = ReferenciaPago.objects.filter(referencia=referencia)
        if referencia_pago.exists():
            referencia_pago = referencia_pago.get()
        else:
            raise Exception('No existe la referencia de pago {0}'.format(referencia))
        solicitud_pago = SolicitudPago.objects.filter(referencia_pago=referencia_pago)
        if solicitud_pago.exists():
            solicitud_pago = solicitud_pago.get()
            solicitud_pago.deposito = deposito
            solicitud_pago.save()
            return solicitud_pago
        else:
            raise Exception('No existe una solicitud de pago con referencia {0}'.format(referencia))

    def guardar_deposito(self, fecha, referencia):
        try:
            asignar = self.se_asignara(referencia)
            deposito = Deposito()
            deposito.fecha = datetime.date(fecha.tm_year, fecha.tm_mon, fecha.tm_mday)
            deposito.referencia = referencia
            deposito.abono = decimal.Decimal('0')
            deposito.saldo = decimal.Decimal('0')
            deposito.reporte_deposito = self.reporte_procesado
            deposito.save()
            if asignar is True:
                solicitud_pago = self.asignar_pago_solicitud(referencia, deposito)
                deposito.abono = solicitud_pago.total
            deposito.save()
            self.pagos_realizados += 1
        except Exception as e:
            message = '{0} - {1} - {2}'.format(module, 'line 240', e.message)
            logger.warning(message)
            raise Exception(e.message)

    def remover_acentos(txt, codif='utf-8'):
        return normalize('NFKD', txt.decode(codif)).encode('ASCII', 'ignore')


class ProblemasPagoView(generic.View):
    def get(self, request, referencia):
        try:
            # Obtenemos los depositos hechos con esa referencia
            depositos = Deposito.objects.all().filter(referencia=referencia)
            if depositos.exists():
                response = {}
                response['depositos'] = list()
                cant_depositos = 0
                cant_solicitudes = 0
                depositos_list = list()
                for deposito in depositos:
                    # Obtenemos las solicitudes de pago relacionadas a ese deposito
                    try:
                        solicitud_pago = SolicitudPago.objects.get(deposito=deposito.id)
                        cant_solicitudes = cant_solicitudes + 1
                    except SolicitudPago.DoesNotExist:
                        solicitud_pago = None
                        datasp = None

                    if solicitud_pago is not None:
                        solicitud_pago.fecha_solicitud = solicitud_pago.fecha_solicitud.isoformat()
                        solicitud_pago.monto = str(solicitud_pago.monto)
                        solicitud_pago.descuento = str(solicitud_pago.descuento)
                        solicitud_pago.total = str(solicitud_pago.total)
                        datasp = model_to_dict(solicitud_pago)

                    deposito.fecha = deposito.fecha.isoformat()
                    deposito.abono = str(deposito.abono)
                    deposito.saldo = str(deposito.saldo)

                    data = model_to_dict(deposito)
                    response['depositos'].append(data)

                    d = list()
                    data['solicitud_pago'] = datasp
                    d.append(data)
                    depositos_list.append(d)
                    cant_depositos = cant_depositos + 1
                response['resumen'] = {
                    'cant_depositos':   cant_depositos,
                    'cant_solicitudes': cant_solicitudes
                }
                return HttpResponse(json.dumps(response, indent=4), content_type='application/json; charset=UTF-8')
            else:
                raise Exception('No se encuentra la referencia de pago  ')

        except Exception as e:
            return HttpResponse(e, status=404)


class AsignarPagoView(generic.View):
    def get(self, request):
        try:
            id_deposito = request.GET.get('id_deposito')
            id_solicitud_pago = request.GET.get('id_solicitud_pago')

            if id_deposito is None or id_solicitud_pago is None:
                raise Exception('El déposito y la solicitud de pago son requeridos')

            try:
                solicitud_pago = SolicitudPago.objects.get(pk=id_solicitud_pago)
                deposito = Deposito.objects.get(pk=id_deposito)
                deposito.abono = solicitud_pago.total
                deposito.save()
                solicitud_pago.deposito = deposito
                solicitud_pago.save()
                response = {
                    'exito': 'true'
                }
            except Exception as e:
                response = {
                    'exito': e
                }
            return HttpResponse(json.dumps(response, indent=4), content_type='application/json; charset=UTF-8')
        except Exception as e:
            return HttpResponse(e, status=400)


class JsonResponseUtils(object):
    fillable = []
    invalid_fields = []
    invalid_content = None
    response = None
    status_code = 200
    is_valid = True
    msg = None
    errors = None

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        self._get_response()
        return super(JsonResponseUtils, self).dispatch(request, *args, **kwargs)

    def _validate_fill_fields(self):
        for field in self.fillable:
            if field not in self.request.POST:
                self.invalid_fields.append(field)
        if len(self.invalid_fields) > 0:
            return False
        return True

    def _get_response(self):
        self.response = {'errors': self.errors}

    def validate_fillable_fields(self):
        if not self._validate_fill_fields():
            self.invalid_content = ', '.join(self.invalid_fields)
            raise Exception('missing field: ' + self.invalid_content)
        return True


class PaymentIssue(JsonResponseUtils, generic.View):
    def get(self, request, referencia):
        try:
            depositos = Deposito.objects.prefetch_related(
                'solicitud_de_pago_related', 'solicitud_de_pago_related__contribuyente', 'solicitud_de_pago_related__referencia_pago').select_related(
                'reporte_deposito', 'reporte_deposito__banco').filter(referencia__exact=referencia)

            if not depositos.exists():
                self.status_code = 404
                raise Exception("La referencia no existe")

            data = []
            solicitudes_de_pago = 0
            payment = {}
            payment['reporte'] = {}
            payment['solicitud_pago'] = {}
            for deposito in depositos:
                payment = {
                    'id':             deposito.id,
                    'fecha':          deposito.fecha.isoformat(),
                    'abono':          deposito.abono,
                    'saldo':          deposito.saldo,
                    'cargo':          deposito.cargo,
                    'reporte':        [],
                    'referencia':     deposito.referencia,
                    'solicitud_pago': [],
                }

                if deposito.reporte_deposito is not None:
                    reporte = {
                        'banco':       deposito.reporte_deposito.banco.referencia,
                        'nombre':      deposito.reporte_deposito.nombre_original,
                        'fecha_carga': deposito.reporte_deposito.fecha_carga.isoformat(),
                    }
                    payment['reporte'] = reporte

                solicitud_pago = None if not hasattr(deposito, 'solicitud_de_pago_related') else deposito.solicitud_de_pago_related

                if solicitud_pago is None:
                    payment['solicitud_pago'] = None
                else:
                    solicitud = {
                        'id':              solicitud_pago.id,
                        'contribuyente':   solicitud_pago.contribuyente.nombre_completo,
                        'referencia':      solicitud_pago.referencia_pago.referencia,
                        'cantidad':        solicitud_pago.cantidad,
                        'fecha_solicitud': solicitud_pago.fecha_solicitud,
                        'monto':           str(solicitud_pago.monto),
                        'descuento':       str(solicitud_pago.descuento),
                        'total':           str(solicitud_pago.total)
                    }
                    payment['solicitud_pago'] = solicitud
                    solicitudes_de_pago += 1
                data.append(payment)
            self.response.update({'depositos': data, 'resumen': {
                'cant_depositos':   depositos.count(),
                'cant_solicitudes': solicitudes_de_pago
            }})
            self.status_code = 200
            self.response['is_valid'] = True
        except Exception as e:
            self.response['msg'] = e.message

        return JsonResponse(self.response, safe=True, status=self.status_code)


class PaymentStatistics(JsonResponseUtils, generic.View):
    def get(self, request):
        depositos = Deposito.objects.all().count()
        monto_pagado = Deposito.objects.all().aggregate(Sum('abono'))

        solicitudes = SolicitudPago.objects.all().count()
        solicitudes_pagadas = SolicitudPago.objects.exclude(deposito=None).count()
        solicitudes_pagadas_monto = SolicitudPago.objects.exclude(deposito=None).aggregate(Sum('total'))
        solicitudes_por_pagar = SolicitudPago.objects.filter(deposito=None).count()
        solicitudes_por_pagar_monto = SolicitudPago.objects.filter(deposito=None).aggregate(Sum('total'))

        self.response.update({'stats': {
            'depositos':    {
                'total': depositos,
                'monto_pagado': str(monto_pagado['abono__sum']),
            },
            'solicitudes': {
                'total':     solicitudes,
                'pagadas':   solicitudes_pagadas,
                'por_pagar': solicitudes_por_pagar,
                'solicitudes_pagadas_monto': solicitudes_pagadas_monto['total__sum'],
                'solicitudes_por_pagar_monto': solicitudes_por_pagar_monto['total__sum']
            }
        }})

        return JsonResponse(self.response, safe=True, status=self.status_code)


class DecreaseMultiplePayments(JsonResponseUtils, generic.View):
    fillable = ['referencia']

    def post(self, request):
        try:
            self.validate_fillable_fields()
            deposito = Deposito.get_by_referencia(request.POST.get('referencia'))
            if deposito.multiples_pagos == 1:
                raise Exception("La referencia {0} no tiene multiples pagos".format(deposito.referencia))
            deposito.multiples_pagos -= 1
            deposito.save()
            self.response.update({'errors': ''})
        except Deposito.DoesNotExist as e:
            self.response.update({'errors': e.message})
            self.status_code = 404
        except Exception as e:
            self.response.update({'errors': e.message})

        return JsonResponse(self.response, safe=True, status=self.status_code)


class CreateDeposito(JsonResponseUtils, generic.View):
    fillable = ['referencia', 'abono', 'reporte_deposito']

    def validate_fields(self):
        for field in self.fill:
            if field not in self.request.POST:
                self.invalid_fields.append(field)
        if len(self.invalid_fields) > 0:
            return False
        return True

    @staticmethod
    def validate_referencia(referencia):
        if not ReferenciaPago.objects.filter(referencia__exact=referencia).exists():
            return False
        return True

    @staticmethod
    def create_deposito(fecha=None, abono=None, referencia=None, reporte_deposito=None):
        try:
            deposito = Deposito.objects.get(referencia=referencia)
            deposito.multiples_pagos += 1
            deposito.save()
            return deposito
        except Deposito.DoesNotExist:
            try:
                deposito = Deposito()
                deposito.fecha = fecha
                deposito.referencia = referencia
                deposito.abono = abono
                deposito.saldo = decimal.Decimal('0')
                deposito.cargo = decimal.Decimal('0')
                deposito.reporte_deposito = None if reporte_deposito == '0' else reporte_deposito
                deposito.save()
                return deposito
            except Exception as e:
                raise

    def get(self, request):
        return HttpResponseBadRequest("Bad request!")

    def post(self, request):
        try:
            if not self.validate_fields():
                self.invalid_content = ', '.join(self.invalid_fields)
                self.response.update({'errors': 'missing field: ' + self.invalid_content})
                raise Exception

            fecha = datetime.datetime.today()
            abono = request.POST.get('abono')
            referencia = request.POST.get('referencia')
            reporte_deposito = request.POST.get('reporte_deposito')

            if not self.validate_referencia(referencia):
                self.invalid_content = 'la referencia {0} no existe'.format(referencia)
                self.response.update({'errors': self.invalid_content})
                raise Exception

            deposito = self.create_deposito(fecha, abono, referencia, reporte_deposito)
            data = {
                'id':              deposito.id,
                'fecha':           deposito.fecha,
                'referencia':      deposito.referencia,
                'abono':           deposito.abono,
                'saldo':           deposito.saldo,
                'cargo':           deposito.cargo,
                'multiples_pagos': deposito.multiples_pagos,
            }
            self.response.update({'deposito': data})
            self.status_code = 200
            self.response['is_valid'] = True
        except Exception as e:
            pass

        return JsonResponse(self.response, safe=True, status=self.status_code)
