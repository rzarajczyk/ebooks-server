import logging

from actions_server import Action, Response, StaticResourceResponse, ErrorResponse


class FilesStorageResources(Action):
    def __init__(self, url_path_prefix, storage):
        self._url_prefix = url_path_prefix
        self._storage = storage
        if not self._url_prefix.endswith('/'):
            self._url_prefix += '/'

    def can_handle(self, method, path, params, payload):
        return method == 'GET' and path.startswith(self._url_prefix) and '/' not in path[len(self._url_prefix):]

    def handle(self, method, path, params, payload) -> Response:
        path = path[len(self._url_prefix):]
        filename = path
        if filename in self._storage:
            mime, encoding = self._storage.guess_mime_type(filename)
            with self._storage.open(filename, 'rb') as f:
                data = f.read()
            return StaticResourceResponse(mime, data)
        else:
            logging.getLogger('web').info("Static resource %s not found" % filename)
            return ErrorResponse(404, "File not found: %s" % path)
