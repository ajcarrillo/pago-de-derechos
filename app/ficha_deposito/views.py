import logging

from django.http import HttpResponse
from django.views import generic

from app.general.PentahoReport.NativePentahoReport import NativePentahoReport
from app.solicitud_pago.models import SolicitudPago

logger = logging.getLogger('carga_de_pagos')
module = 'app/ficha_deposito/views.py'

class FichaDepositoView(generic.View):
    def get(self, request, pk = None):
        try:
            solicitud_pago = SolicitudPago.objects.get(pk = pk)
            reporte = NativePentahoReport()
            reporte.project = 'cricalde'  # billy
            reporte.report = 'ficha_deposito'  # name = solicitud_pago.referencia_pago.referencia
            reporte.format = 'pdf'  # 'xls'
            reporte.set('solicitud_pago', str(solicitud_pago.id))
            return reporte.download()
        except Exception as e:
            message = '{0} - {1} - {2}'.format(module, 'line 14', e.message)
            logger.warning(message)
            return HttpResponse(status = 404)
