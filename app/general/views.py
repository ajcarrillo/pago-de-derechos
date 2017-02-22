from django.views import generic


class RootRedirectView(generic.RedirectView):
    url = '/admin'
