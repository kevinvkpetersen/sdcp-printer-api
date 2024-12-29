"""Main module for the SDCP Printer API."""

from __future__ import annotations

import json
import logging
import socket
import threading
import time
from contextlib import closing

import websocket

from .message import SDCPMessage, SDCPResponseMessage, SDCPStatusMessage
from .request import SDCPStatusRequest

PRINTER_PORT = 3030
DISCOVERY_PORT = 3000

MESSAGE_ENCODING = "utf-8"

logger = logging.getLogger(__package__)


class SDCPPrinter:
    """Class to represent a printer discovered on the network."""

    _connection = None
    _is_connected = False

    _status = None

    def __init__(self, discovery_json: dict):
        """Constructor."""
        self._id: str = discovery_json["Id"]
        self._ip_address: str = discovery_json["Data"]["MainboardIP"]
        self._mainboard_id: str = discovery_json["Data"]["MainboardID"]

    @property
    def id(self) -> str:
        """ID of the printer."""
        return self._id

    @property
    def ip_address(self) -> str:
        """IP address of the printer."""
        return self._ip_address

    @property
    def mainboard_id(self) -> str:
        """Mainboard ID of the printer."""
        return self._mainboard_id

    @property
    def _websocket_url(self) -> str:
        """URL for the printer's websocket connection."""
        return f"ws://{self._ip_address}:{PRINTER_PORT}/websocket"

    @property
    def status(self) -> dict:
        """The printer's status details."""
        return self._status

    @staticmethod
    def get_printer_info(ip_address: str, timeout: int = 1) -> SDCPPrinter:
        """Gets information about a printer given its IP address."""
        logger.info(f"Getting printer info for {ip_address}")

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            sock.sendto(b"M99999", (ip_address, DISCOVERY_PORT))

            try:
                device_response = sock.recv(8192)
                logger.debug(
                    f"Reply from {ip_address}: {device_response.decode(MESSAGE_ENCODING)}"
                )
                printer_json = json.loads(device_response.decode(MESSAGE_ENCODING))
                return SDCPPrinter(printer_json)
            except socket.timeout:
                raise TimeoutError(f"Timed out waiting for response from {ip_address}")
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON from {ip_address}")

    def start_listening(self, timeout: int = 1) -> None:
        """Opens a persistent connection to the printer to listen for messages."""
        self._connection = websocket.WebSocketApp(
            self._websocket_url,
            on_open=self._on_open,
            on_close=self._on_close,
            on_message=self._on_message,
        )

        logger.info(f"{self._ip_address}: Opening connection")
        threading.Thread(target=self._connection.run_forever).start()

        start_time = time.time()
        while not self._is_connected:
            if timeout > 0 and time.time() - start_time > timeout:
                raise TimeoutError("Connection timed out")
            time.sleep(0.1)

        logger.info(f"{self._ip_address}: Persistent connection established")

    def stop_listening(self) -> None:
        """Closes the connection to the printer."""
        # TODO: Make sure this is more reliably called. Ideally in __exit__ using the with statement.
        self._connection and self._connection.close()

    def _on_open(self, ws) -> None:
        """Callback for when the connection is opened."""
        logger.info(f"{self._ip_address}: Connection opened")
        self._is_connected = True

    def _on_close(self, ws, close_status_code, close_msg) -> None:
        """Callback for when the connection is closed."""
        logger.info(f"{self._ip_address}: Connection closed")
        self._is_connected = False

    def _on_message(self, ws, message: str) -> SDCPMessage:
        """Callback for when a message is received."""
        logger.debug(f"{self._ip_address}: Message received: {message}")
        parsed_message = SDCPMessage.parse(message)

        match parsed_message.topic:
            case "response":
                pass
            case "status":
                self._update_status(parsed_message)
            case _:
                logger.warning(f"{self._ip_address}: Unknown message topic")

        return parsed_message

    def refresh_status(self) -> None:
        """Sends a request to the printer to report its status."""
        logger.info(f"{self._ip_address}: Requesting status")

        payload = SDCPStatusRequest.build(self)

        self._send_request(payload)

    def _send_request(
        self,
        payload: dict,
        connection: websocket = None,
        receive_message: bool = True,
        expect_response: bool = True,
    ) -> SDCPMessage:
        """Sends a request to the printer."""
        if connection is None:
            if self._connection is not None and self._is_connected:
                return self._send_request(
                    payload, self._connection, receive_message=False
                )
            else:
                with closing(websocket.create_connection(self._websocket_url)) as ws:
                    return self._send_request(
                        payload,
                        ws,
                        receive_message=True,
                        expect_response=expect_response,
                    )

        logger.debug(f"{self._ip_address}: Sending request with payload: {payload}")
        connection.send(json.dumps(payload))

        # TODO: Add timeout
        if receive_message:
            if expect_response:
                response: SDCPResponseMessage = self._on_message(
                    connection, connection.recv()
                )
                if not response.is_success:
                    raise AssertionError(f"Request failed: {response.error_message}")
            return self._on_message(connection, connection.recv())

    def _update_status(self, message: SDCPStatusMessage) -> None:
        """Updates the printer's status fields."""
        self._status = message.status
        logger.info(f"{self._ip_address}: Status updated: {self._status}")
