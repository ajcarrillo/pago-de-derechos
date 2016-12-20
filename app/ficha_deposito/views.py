from django.http import HttpResponse
from django.views import generic

from app.general.PentahoReport.NativePentahoReport import NativePentahoReport
from app.solicitud_pago.models import SolicitudPago


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
        except:
            return HttpResponse(status = 404)
