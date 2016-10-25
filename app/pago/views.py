import datetime
import decimal
import hashlib
import json
from unicodedata import normalize

from django.db import transaction
from django.forms import model_to_dict
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from app.pago.models import ReporteDeposito, Deposito
from app.solicitud_pago.models import ReferenciaPago, SolicitudPago, Banco


class ReporteDepositoView(generic.View):
    pagos_reportados = 0  # el total de pagos que envía el reporte
    pagos_realizados = 0  # número de pagos correctamente realizados
    contenido_invalido = None  # texto que contiene la estructura original de los pagos invalidos
    reporte_procesado = None

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(ReporteDepositoAPI, self).dispatch(*args, **kwargs)

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
            print '*' * 50
            print contenido_archivo
            print '*' * 50
            self.reporte_procesado.contenido_original = str(contenido_archivo.decode("utf8", "ignore"))
            self.reporte_procesado.contenido_fallido = self.contenido_invalido
            self.reporte_procesado.save()
            transaction.commit()
            msg = "Reporte: {0}, Reportados: {1}, Procesados: {2}, Contenido Fallido: {3}" \
                .format(self.reporte_procesado.id, self.reporte_procesado.depositos_reportados,
                        self.reporte_procesado.depositos_procesados, self.reporte_procesado.contenido_fallido)
            return HttpResponse(msg, status=400)
        except Exception as e:
            print e
            transaction.rollback()
            return HttpResponse(e, status=400)

    def get(self, request):
        return HttpResponse('No se permite obtener la lista de reportes', status=404)

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
                print e
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
                fecha = datetime.time.strptime(timestamp[:8], '%d%m%Y')
                """
					FIX PROCESO 2015: Aparecieron pagos a referencias de 19 dígitos y se aprobaron debido a que el banco acepta
					referencias de 18, 19 y 20 dígitos. Únicamente se leen los primeros 18 dígitos de derecha a izquiera como
					referencia. Si los primeros dos dígitos de esta referencia son 26, asumimos que es una referencia correcta
					de pago, le agregamos los dos ceros a la izquierda y continuamos el proceso
				"""
                referencia = linea_captura[-18:]
                if referencia[0:2] != '26':
                    raise Exception('Referencia no valida')
                else:
                    referencia = '00' + referencia
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
                print str(e)
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
                asignar = self.se_asignara(referencia)
                fecha = datetime.time.strptime(splits[14], '%d/%m/%Y')

                deposito = Deposito()
                deposito.fecha = datetime.date(fecha.tm_year, fecha.tm_mon, fecha.tm_mday)
                deposito.referencia = referencia
                deposito.saldo = decimal.Decimal('0')
                deposito.abono = decimal.Decimal('0')
                deposito.reporte_deposito = self.reporte_procesado
                deposito.save()
                referencia = deposito.referencia
                if asignar is True:
                    solicitud_pago = self.asignar_pago_solicitud(referencia, deposito)
                    deposito.abono = solicitud_pago.total
                deposito.save()
                self.pagos_realizados += 1
            except Exception as e:
                print e
                pagos_invalidos.append(str(e))
        if len(pagos_invalidos) > 0:
            self.contenido_invalido = '<br>'.join(pagos_invalidos)

    """
		Función para saber si se asignará o no el deposito a la solicitud de pago.
		Esto sirve para siempre asignar el primer deposito a la solicitud de pago.
	"""

    def se_asignara(self, referencia):
        deposito = Deposito.objects.filter(referencia=referencia)

        if len(deposito) == 0:
            return True
        else:
            return False

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

            # Here comes the assignation!

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
            return HttpResponse(e, status=404)
