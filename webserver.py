import json
import logging
import os
import requests
import ssl

from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Optional

_LOGGER = logging.getLogger(__name__)

SERVER_PORT = 6123
SERVER_BIND = "0.0.0.0"


class HAZWaveViewerServer:
    token: str
    url: str
    ssl_key: Optional[str]
    ssl_certificate: Optional[str]
    httpd: Optional[HTTPServer]

    def __init__(self):
        self.url = os.environ.get('HA_URL')
        self.token = os.environ.get('HA_TOKEN')
        self.ssl_key = os.environ.get('SSL_KEY')
        self.ssl_certificate = os.environ.get('SSL_CERTIFICATE')

        if self.ssl_key == "":
            self.ssl_key = None

        if self.ssl_certificate == "":
            self.ssl_certificate = None

        self.is_ssl = self.ssl_key is not None and self.ssl_certificate is not None
        self.httpd = None

    def initialize(self):
        if self.url is None:
            _LOGGER.fatal("Environment variable HA_URL is empty, cannot initialize server")
            return

        if self.token is None:
            _LOGGER.fatal("Environment variable HA_URL is empty, cannot initialize server")
            return

        _LOGGER.info(f"Initializing server {SERVER_BIND}:{SERVER_PORT}, SSL: {self.is_ssl}")

        self.httpd = HTTPServer((SERVER_BIND, SERVER_PORT), SimpleHTTPRequestHandlerX)

        if self.is_ssl:
            self.httpd.socket = ssl.wrap_socket(self.httpd.socket,
                                                keyfile=self.ssl_key,
                                                certfile=self.ssl_certificate,
                                                server_side=True)

        self.httpd.serve_forever()

    def get_states(self):
        try:
            headers = {
                'Authorization': 'Bearer ' + self.token
            }

            verify = False if "https://" in self.url else None

            response = requests.get(f"{self.url}/api/states", headers=headers, verify=verify)

            return response.json()

        except Exception as ex:
            _LOGGER.error(f"Failed to retrieve states from HA, error: {ex}")

            return None


class SimpleHTTPRequestHandlerX(SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/states.json":
            states = server.get_states()
            status = 500 if states is None else 200

            self.send_response(status)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            if states is not None:
                self.wfile.write(str(json.dumps(states)).encode("utf-8"))

        else:
            super().do_GET()


server = HAZWaveViewerServer()
server.initialize()
