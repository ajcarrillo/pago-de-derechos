"""billy URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^bancos/', include('app.banco.urls', namespace='bancos')),
    url(r'^conceptos/', include('app.concepto.urls', namespace='conceptos')),
    url(r'^fichas-deposito/', include('app.ficha_deposito.urls', namespace='fichas_deposito')),
    url(r'^solicitud-pago/', include('app.solicitud_pago.urls', namespace='solicitud_pago')),
    url(r'^pagos/', include('app.pago.urls', namespace='pagos')),
    url(r'^', include('app.general.urls', namespace='general')),
]
