# -*- encoding: utf-8 -*
from django.conf.urls import url

from app.concepto import views

urlpatterns = [
    url(r'^$', views.ConceptoListView.as_view(), name='list'),
    url(r'^(?P<pk>[\d]+)$', views.ConceptoListView.as_view(), name='list'),
]
