import logging
import ssl

from http.server import HTTPServer
from typing import Optional

from .handler import ZWaveNetworkHandler
from .data_manager import HAZWaveManager
from models.consts import *

_LOGGER = logging.getLogger(__name__)


class HAZWaveViewerServer:
    httpd: Optional[HTTPServer]

    def __init__(self):
        self.httpd = None

    def initialize(self, manager: HAZWaveManager):
        self.httpd = HTTPServer((SERVER_BIND, SERVER_PORT), ZWaveNetworkHandler)

        if manager.is_ssl:
            self.httpd.socket = ssl.wrap_socket(self.httpd.socket,
                                                keyfile=manager.ssl_key,
                                                certfile=manager.ssl_certificate,
                                                server_side=True)

        self.httpd.serve_forever()
