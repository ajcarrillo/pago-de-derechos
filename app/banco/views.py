from django.views import generic

from app.general.mixins import JsonResponseMixin
from app.solicitud_pago.models import Banco


class BancoListView(JsonResponseMixin, generic.ListView):
    model = Banco

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        return self.response_handler()

    def get_data(self):
        data = [{
                    'pk':          banco.pk,
                    'referencia':  banco.referencia,
                    'descripcion': banco.descripcion,
                } for banco in self.object_list]

        return data

    def get_queryset(self):
        if self.kwargs.get('name'):
            queryset = self.model.objects.filter(referencia__contains=self.kwargs['name'])
        elif self.kwargs.get('pk'):
            queryset = self.model.objects.get(pk=self.kwargs['pk'])
        else:
            queryset = super(BancoListView, self).get_queryset()

        return queryset
