from __future__ import annotations

import json
import logging
import websocket

from contextlib import closing

from const import PRINTER_PORT
from request import SDCPStatusRequest

logger = logging.getLogger(__name__)


class SDCPPrinter:
    def __init__(self, discovery_json: dict):
        self._id: str = discovery_json['Id']
        self._ip_address: str = discovery_json['Data']['MainboardIP']
        self._mainboard_id: str = discovery_json['Data']['MainboardID']
        self.status = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def mainboard_id(self) -> str:
        return self._mainboard_id

    def refresh_status(self) -> None:
        '''Sends a request to the printer to report its status.'''
        logger.info(f'{self._ip_address}: Requesting status')

        payload = SDCPStatusRequest.build(self)
        logger.debug(f'{self._ip_address}: Payload: {payload}')

        with closing(websocket.create_connection(f'ws://{self._ip_address}:{PRINTER_PORT}/websocket')) as ws:
            ws.send(json.dumps(payload))

            response = ws.recv()
            logger.debug(f'{self._ip_address}: Response: {response}')

            if self.handle_message(response):
                status = ws.recv()
                logger.debug(f'{self._ip_address}: Response: {status}')
                self.handle_message(status)

    def handle_message(self, message: str):
        '''Handles incoming messages from the printer.'''
        logger.debug(f'{self._ip_address}: Message: {message}')

        message_json = json.loads(message)
        topic = message_json['Topic'].split('/')[1]
        logger.debug(f'{self._ip_address}: Topic: {topic}')

        match topic:
            case 'response':
                ack = message_json['Data']['Data']['Ack']
                logger.debug(f'{self._ip_address}: Ack: {ack}')
                return ack == 0
            case 'status':
                self.update_status(message_json['Status'])
            case _:
                logger.warning(
                    f'{self._ip_address}: Unknown topic: {topic}')

    def update_status(self, status_json: dict) -> None:
        '''Updates the printer's status values.'''
        self.status = status_json['CurrentStatus']
