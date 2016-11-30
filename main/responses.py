from django.http import JsonResponse

RESULT_OK = 'ok'
RESULT_ERROR = 'error'


class AjaxResponse(JsonResponse):
    def __init__(self, result, message, errors=[], data={}):
        self.resp = {'result': result,
                     'message': message,
                     'data': data,
                     'errors': errors}
        super(AjaxResponse, self).__init__(self.resp)


