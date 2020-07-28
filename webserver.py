import logging

from Managers.data_manager import HAZWaveManager
from Managers.server import HAZWaveViewerServer

_LOGGER = logging.getLogger(__name__)


manager = HAZWaveManager()

server = HAZWaveViewerServer()
server.initialize(manager)
