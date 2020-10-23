SERVER_PORT = 6123
SERVER_BIND = "0.0.0.0"

DOMAIN_ZWAVE = "zwave"
DOMAIN_OZW = "ozw"
SUPPORTED_DOMAINS = [DOMAIN_ZWAVE, DOMAIN_OZW]

DEBUG_DIR = "/debug"
LOG_FILE = f"{DEBUG_DIR}/ha-zwave-network.log"

WEBSITE_INDEX = "index.html"

WEB_SOCKET_STATUS_DISCONNECTED = "disconnected"
WEB_SOCKET_STATUS_CONNECTED = "connected"
WEB_SOCKET_STATUS_AUTHORIZED = "authorized"

WEB_SOCKET_ERRORS = {
    "1": "A non-increasing identifier has been supplied",
    "2": "Received message is not in expected format",
    "3": "Requested item cannot be found",
    "id_reuse": "A non-increasing identifier has been supplied"
}

WS_MAIN_DETAILS = {
    "Devices": "config/device_registry/list",
    "Entities": "config/entity_registry/list",
    "States": "get_states"
}
