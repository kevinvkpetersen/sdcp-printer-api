from __future__ import annotations

import json
import logging
import threading
import time
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

        self._connection = None
        self._is_connected = False

        self._status = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def mainboard_id(self) -> str:
        return self._mainboard_id

    @property
    def _websocket_url(self) -> str:
        return f'ws://{self._ip_address}:{PRINTER_PORT}/websocket'

    def start_listening(self) -> None:
        '''Opens a persistent connection to the printer to listen for messages.'''
        self._connection = websocket.WebSocketApp(
            self._websocket_url,
            on_open=self._on_open,
            on_close=self._on_close,
            on_message=self._on_message,
        )
        threading.Thread(target=self._connection.run_forever).start()
        while not self._is_connected:
            time.sleep(0.1)

    def stop_listening(self) -> None:
        '''Closes the connection to the printer.'''
        self._connection.close()

    def _on_open(self, ws) -> None:
        logger.info(f'{self._ip_address}: Connection opened')
        self._is_connected = True

    def _on_close(self, ws, close_status_code, close_msg) -> None:
        logger.info(f'{self._ip_address}: Connection closed')
        self._is_connected = False

    def _on_message(self, ws, message: str) -> SDCPMessage:
        logger.debug(f'{self._ip_address}: Message received: {message}')
        parsed_message = SDCPMessage.parse(message)

        match parsed_message.topic:
            case 'response':
                pass
            case 'status':
                self._update_status(parsed_message)
            case _:
                logger.warning(f'{self._ip_address}: Unknown message topic')

        return parsed_message

    def refresh_status(self) -> None:
        '''Sends a request to the printer to report its status.'''
        logger.info(f'{self._ip_address}: Requesting status')

        payload = SDCPStatusRequest.build(self)

        self._send_request(payload)

    def _send_request(
            self,
            payload: dict,
            connection: websocket = None,
            receive_message: bool = True,
            expect_response: bool = True
    ) -> SDCPMessage:
        '''Sends a request to the printer.'''
        if connection is None:
            if self._connection is not None and self._is_connected:
                return self._send_request(payload, self._connection, receive_message=False)
            else:
                with closing(websocket.create_connection(self._websocket_url)) as ws:
                    return self._send_request(payload, ws, receive_message=True, expect_response=expect_response)

        logger.debug(
            f'{self._ip_address}: Sending request with payload: {payload}')
        connection.send(json.dumps(payload))

        if receive_message:
            if expect_response:
                response: SDCPResponseMessage = self._on_message(
                    connection.recv())
                if not response.is_success():
                    raise Exception('Request failed')
            return self._on_message(connection.recv())

    def _update_status(self, message: SDCPStatusMessage) -> None:
        '''Updates the printer's status fields.'''
        self._status = message.status
        logger.info(f'{self._ip_address}: Status updated: {self._status}')
