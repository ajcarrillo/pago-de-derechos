from django.shortcuts import render

# Create your views here.
from django.views import generic

from app.general.mixins import JsonResponseMixin
from app.solicitud_pago.models import Concepto


class ConceptoListView(JsonResponseMixin, generic.ListView):
    model = Concepto

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        return self.response_handler()

    def get_data(self):
        data = [{
                    'pk':          concepto.pk,
                    'clave':       concepto.clave,
                    'descripcion': concepto.descripcion,
                } for concepto in self.object_list]

        return data

    def get_queryset(self):
        queryset = self.model.objects.exclude(clave='026')
        if self.kwargs.get('pk'):
            return queryset.filter(pk__exact=self.kwargs['pk'])
        else:
            return queryset
