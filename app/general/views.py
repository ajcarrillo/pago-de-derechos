from django.http import JsonResponse
from django.views import generic


class RootRedirectView(generic.RedirectView):
    url = '/admin'


def check_service_on_line(request):
    response = JsonResponse({'foo': 'bar'})
    return response
