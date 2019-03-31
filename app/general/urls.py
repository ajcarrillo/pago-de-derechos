# -*- encoding: utf-8 -*
from django.conf.urls import url

from app.general.views import RootRedirectView, check_service_on_line

urlpatterns = [
    url(r'^$', RootRedirectView.as_view(), name='redirect_to_admin'),
    url(r'^check-service-on-line/$', check_service_on_line),
]
