# -*- encoding: utf-8 -*
from django.conf.urls import url

from app.banco import views

# **************************************
#
#   url: /bancos/
#   namespace: bancos
#
# **************************************

urlpatterns = [
    url(r'^$', views.BancoListView.as_view(), name='list'),
    url(r'^(?P<pk>[\d]+)$', views.BancoListView.as_view(), name='list'),
    url(r'^bugsnag/$', views.TestBugsnagReport.as_view(), name='test_bugsnag'),
]
