# -*- encoding: utf-8 -*
from django.conf.urls import url

from app.solicitud_pago import views

urlpatterns = [
    url(r'^$', views.SolicitudPagoResource.as_view()),
    url(r'^(\d+)$', views.SolicitudPagoResource.as_view()),
    url(r'^status/$', views.StatusSolicitudPago.as_view()),
    url(r'^referencia/(.*)/$', views.SolicitudPagoReferencia.as_view())
]
