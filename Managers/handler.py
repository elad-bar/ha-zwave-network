import json
import logging

from http.server import SimpleHTTPRequestHandler

from .data_manager import HAZWaveManager
from models.consts import *

_LOGGER = logging.getLogger(__name__)


class ZWaveNetworkHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        manager = HAZWaveManager()

        current_path = self.path

        if current_path in SUPPORTED_CUSTOM_ENDPOINTS:
            response = None

            if current_path == STATES_ENDPOINT:
                response = manager.get_states()

            elif current_path == ZWAVE_ENDPOINT:
                response = manager.get_zwave_states()

            elif current_path == NODES_ENDPOINT:
                response = manager.get_zwave_nodes_json()

            status = 500 if response is None else 200

            self.send_response(status)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            if status == 200:
                self.wfile.write(str(json.dumps(response, indent=4)).encode("utf-8"))

        else:
            super().do_GET()
