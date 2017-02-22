# -*- encoding: utf-8 -*
from django.conf.urls import url

from app.general.views import RootRedirectView

urlpatterns = [
    url(r'^$', RootRedirectView.as_view(), name='redirect_to_admin'),
]
