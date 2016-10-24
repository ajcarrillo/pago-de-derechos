from django.http import HttpResponse
from django.views import generic

from app.general.libseq.reporting import PentahoReport
from app.solicitud_pago.models import SolicitudPago


class FichaDepositoView(generic.View):
    def get(self, request, pk = None):
        try:
            solicitud_pago = SolicitudPago.objects.get(pk = pk)
            report = PentahoReport()
            report.name = 'ficha_deposito'
            report.project = 'billy'
            report.set('solicitud_pago', str(solicitud_pago.id))
            print report
            response = HttpResponse(report.fetch())
            response['Content-Type'] = 'application/pdf'
            response['Content-Disposition'] = 'attachment; filename = "%s.pdf"' % solicitud_pago.referencia_pago.referencia
            return response
        except:
            return HttpResponse(status = 404)
