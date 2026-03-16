import logging

logger = logging.getLogger(__name__)

class MeshtasticConnector:
    def __init__(self):
        self.is_running = False

    async def start(self):
        self.is_running = True
        logger.info('Meshtastic connector started')

    async def stop(self):
        self.is_running = False
        logger.info('Meshtastic connector stopped')

meshtastic_connector = MeshtasticConnector()
