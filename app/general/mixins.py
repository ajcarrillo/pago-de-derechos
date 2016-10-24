# -*- encoding: utf-8 -*
from django.http import JsonResponse


class JsonResponseMixin(object):
    def dispatch(self, request, *args, **kwargs):
        try:
            return super(JsonResponseMixin, self).dispatch(request, *args, **kwargs)
        except Exception as e:
            data = {'status': 400, 'debug_message': e.message, 'message': 'Bad request'}
            return JsonResponse(data, safe=False)

    def response_handler(self):
        return self.json_to_response()

    def json_to_response(self):
        data = self.get_data()
        return JsonResponse(data, safe=False)
