import os
import logging

from typing import Optional

from models.consts import *

_LOGGER = logging.getLogger(__name__)


class ConfigurationManager:
    home_assistant_url: Optional[str]
    home_assistant_web_socket_url: Optional[str]
    home_assistant_token: Optional[str]
    ssl_key: Optional[str]
    ssl_certificate: Optional[str]
    is_ssl: Optional[bool]
    is_debug: Optional[bool]
    is_local: Optional[bool]
    server_port: Optional[int]
    ssl_context: Optional

    def __init__(self):
        self.home_assistant_url = os.environ.get('HA_URL')
        self.home_assistant_token = os.environ.get('HA_TOKEN')
        self.ssl_key = os.environ.get('SSL_KEY')
        self.ssl_certificate = os.environ.get('SSL_CERTIFICATE')
        self.is_debug = bool(os.environ.get('DEBUG', "false").lower() == "true")
        self.is_local = bool(os.environ.get('LOCAL', "false").lower() == "true")
        self.server_port = int(os.environ.get('SERVER_PORT', SERVER_PORT))

        self.home_assistant_web_socket_url = self.home_assistant_url.replace("http", "ws")

        self.is_ssl = self._has_valid_content(self.ssl_key) and self._has_valid_content(self.ssl_certificate)
        self.ssl_context = None

    @staticmethod
    def _has_valid_content(data):
        return data is not None and data != ""

    def initialize(self):
        if os.path.exists(DEBUG_DIR):
            for f in os.listdir(DEBUG_DIR):
                if self.is_local and f.endswith(".json"):
                    continue

                os.remove(f"{DEBUG_DIR}/{f}")

        log_level = logging.DEBUG if self.is_debug else logging.INFO

        logging.basicConfig(filename=LOG_FILE, level=log_level)

        if self.home_assistant_url is None:
            raise Exception("Environment variable HA_URL is empty, cannot initialize server")

        if self.home_assistant_token is None:
            raise Exception("Environment variable HA_URL is empty, cannot initialize server")

        if self.is_ssl:
            self.ssl_context = (self.ssl_certificate, self.ssl_key)

        _LOGGER.info(f"Configuration is valid, data: {self}")

    def __repr__(self):
        return f"{self.__dict__}"
