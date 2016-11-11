from django.http import JsonResponse


class AjaxResponse(JsonResponse):
    def __init__(self, result, message, errors=[]):
        self.response['result'] = result
        self.response['message'] = message
        self.response['errors'] = errors
        super(AjaxResponse, self).__init__(self.response)
