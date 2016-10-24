# -*- encoding: utf-8 -*
from django.conf.urls import url

from app.ficha_deposito import views

# **************************************
#
#   url: /fichas-deposito/
#   namespace: fichas_deposito
#
# **************************************

urlpatterns = [
    url(r'^(?P<pk>[\d]+)$', views.FichaDepositoView.as_view(), name='list'),
]
