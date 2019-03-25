# -*- encoding: utf-8 -*
from django.conf.urls import url

from app.pago import views

# **************************************
#
#   url: /pagos/
#   namespace: pagos
#
# **************************************

urlpatterns = [
    url(r'^deposito/reporte/$', views.ReporteDepositoView.as_view()),
    url(r'^deposito/referencia/(.*)/$', views.ProblemasPagoView.as_view()),
    url(r'^asignar-deposito/$', views.AsignarPagoView.as_view()),

    url(r'^nuevo-deposito/$', views.CreateDeposito.as_view()),
    url(r'^referencia/(.*)/$', views.PaymentIssue.as_view()),
    url(r'^decrease/$', views.DecreaseMultiplePayments.as_view()),

    url(r'^stats/payments/$', views.PaymentStatistics.as_view()),
    url(r'^reporte-pagos/$', views.ReportesBancariosView.as_view()),
]
