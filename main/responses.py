from django.http import JsonResponse


class AjaxResponse(JsonResponse):
    def __init__(self, result, message, errors=[]):
        self.resp = {'result': result,
                     'message': message,
                     'errors': errors}
        super(AjaxResponse, self).__init__(self.resp)


