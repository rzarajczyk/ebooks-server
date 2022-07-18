from actions_server import Action, Response, StaticResourceResponse, ErrorResponse


class FileUpload(Action):
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def can_handle(self, method, path, params, payload):
        return method == 'POST' and path == self.endpoint

    def handle(self, method, path, params, payload) -> Response:
        return None
