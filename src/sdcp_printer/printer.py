from __future__ import annotations

import json
import logging
import websocket

from contextlib import closing

from const import PRINTER_PORT
from message import SDCPMessage, SDCPResponseMessage, SDCPStatusMessage
from request import SDCPStatusRequest

logger = logging.getLogger(__name__)


class SDCPPrinter:
    def __init__(self, discovery_json: dict):
        self._id: str = discovery_json['Id']
        self._ip_address: str = discovery_json['Data']['MainboardIP']
        self._mainboard_id: str = discovery_json['Data']['MainboardID']
        self._status = None

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

        status_message: SDCPStatusMessage = self.send_request(payload)
        self._status = status_message.status

    def send_request(self, payload: dict, expect_response: bool = True) -> SDCPMessage:
        '''Sends a request to the printer.'''
        logger.debug(
            f'{self._ip_address}: Sending request with payload: {payload}')
        with closing(websocket.create_connection(f'ws://{self._ip_address}:{PRINTER_PORT}/websocket')) as ws:
            ws.send(json.dumps(payload))

            if expect_response:
                response: SDCPResponseMessage = SDCPMessage.parse(ws.recv())
                if not response.is_success():
                    raise Exception('Request failed')

            return SDCPMessage.parse(ws.recv())
