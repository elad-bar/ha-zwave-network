import json
import logging

from http.server import SimpleHTTPRequestHandler

from .data_manager import HAZWaveManager
from models.consts import *

_LOGGER = logging.getLogger(__name__)


class ZWaveNetworkHandler(SimpleHTTPRequestHandler):
    @staticmethod
    def default_serializer(obj):
        return obj.__dict__

    def get_content(self, data):
        json_data = json.dumps(data, indent=4, default=self.default_serializer)
        content = str(json_data).encode("utf-8")

        return content

    def do_GET(self):
        current_path = self.path

        if "/external/" in current_path:
            manager = HAZWaveManager()
            response = manager.get_external_nodes_json(current_path)
            content = self.get_content(response)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            self.wfile.write(content)

        elif current_path in SUPPORTED_CUSTOM_ENDPOINTS:
            response = None

            manager = HAZWaveManager()
            manager.load_data()

            if current_path == NODES_ENDPOINT:
                response = manager.get_nodes()

            content = self.get_content(response)

            status = 500 if response is None else 200

            self.send_response(status)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            if status == 200:
                self.wfile.write(content)

        else:
            super().do_GET()
