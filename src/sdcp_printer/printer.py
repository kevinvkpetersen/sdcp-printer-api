import json
import logging
import os
import time
import websocket

from contextlib import closing

from const import PRINTER_PORT

logger = logging.getLogger(__name__)


class SDCPPrinter:
    def __init__(self, discovery_data):
        self.id = discovery_data['Id']
        self.ip_address = discovery_data['Data']['MainboardIP']
        self.mainboard_id = discovery_data['Data']['MainboardID']

    def refresh_status(self):
        '''Sends a request to the printer to report its status.'''
        logger.info(f'{self.ip_address}: Requesting status')

        payload = {
            'Id': self.id,
            'Data': {
                'Cmd': 0,
                'Data': {},
                'RequestID': os.urandom(8).hex(),
                'MainboardID': self.mainboard_id,
                'TimeStamp': int(time.time()),
                'From': 0,
            },
            'Topic': f'sdcp/request/{self.mainboard_id}'
        }
        logger.debug(f'{self.ip_address}: Payload: {payload}')

        with closing(websocket.create_connection(f'ws://{self.ip_address}:{PRINTER_PORT}/websocket')) as ws:
            ws.send(json.dumps(payload))
            response = ws.recv()
            logger.debug(f'{self.ip_address}: Response: {response}')
            status = ws.recv()
            logger.debug(f'{self.ip_address}: Response: {status}')
            return json.loads(status)
