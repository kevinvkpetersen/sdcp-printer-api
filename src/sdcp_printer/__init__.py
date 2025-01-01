"""Main module for the SDCP Printer API."""

from __future__ import annotations

import asyncio
import json
import logging

import websocket
from websockets.asyncio.client import ClientConnection, connect

from .async_udp import AsyncUDPConnection
from .message import (
    SDCPDiscoveryMessage,
    SDCPMessage,
    SDCPResponseMessage,
    SDCPStatusMessage,
)
from .request import SDCPStatusRequest

PRINTER_PORT = 3030
DISCOVERY_PORT = 3000

MESSAGE_ENCODING = "utf-8"

_logger = logging.getLogger(__package__)


class SDCPPrinter:
    """Class to represent a printer discovered on the network."""

    _connection: ClientConnection = None
    _is_connected: bool = False
    _callbacks: list[callable] = []

    _discovery_message: SDCPDiscoveryMessage = None
    _status_message: SDCPStatusMessage = None

    def __init__(
        self,
        uuid: str,
        ip_address: str,
        mainboard_id: str,
        discovery_message: SDCPDiscoveryMessage | None = None,
    ):
        """Constructor."""
        self._uuid = uuid
        self._ip_address = ip_address
        self._mainboard_id = mainboard_id
        self._discovery_message = discovery_message

    @staticmethod
    def get_printer(ip_address: str, timeout: int = 1) -> SDCPPrinter:
        """Gets information about a printer given its IP address."""

        return asyncio.run(SDCPPrinter.get_printer_async(ip_address, timeout))

    @staticmethod
    async def get_printer_async(ip_address: str, timeout: int = None) -> SDCPPrinter:
        """Gets information about a printer given its IP address."""
        _logger.info(f"Getting printer info for {ip_address}")

        try:
            async with AsyncUDPConnection(ip_address, DISCOVERY_PORT, timeout) as conn:
                await conn.send(b"M99999", timeout)

                device_response = await conn.receive(timeout)
                _logger.debug(
                    f"Reply from {ip_address}: {device_response.decode(MESSAGE_ENCODING)}"
                )
                discovery_message = SDCPDiscoveryMessage.parse(
                    device_response.decode(MESSAGE_ENCODING)
                )

                return SDCPPrinter(
                    discovery_message.id,
                    discovery_message.ip_address,
                    discovery_message.mainboard_id,
                    discovery_message,
                )
        except TimeoutError as e:
            raise TimeoutError(
                f"Timed out waiting for response from {ip_address}"
            ) from e
        except AttributeError as e:
            raise AttributeError(f"Invalid JSON from {ip_address}") from e

    # region Properties
    @property
    def uuid(self) -> str:
        """ID of the printer."""
        return self._uuid

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
        return f"ws://{self.ip_address}:{PRINTER_PORT}/websocket"

    @property
    def current_status(self) -> dict:
        """The printer's status details."""
        return self._status_message and self._status_message.current_status

    # endregion

    # TODO: Timeout
    def start_listening(self) -> None:
        """Opens a persistent connection to the printer to listen for messages."""
        asyncio.create_task(self.start_listening_async())
        asyncio.run(self.wait_for_connection_async())

    # TODO: Timeout
    async def start_listening_async(self) -> None:
        """Opens a persistent connection to the printer to listen for messages."""
        _logger.info(f"{self._ip_address}: Opening connection")

        async with connect(self._websocket_url) as ws:
            self._connection = ws
            # TODO: Add connection recvovery
            self._on_open()

            while True:
                message = await self._connection.recv()
                self._on_message(message)

        self._on_close()

    # TODO: Timeout; Sleep Interval
    async def wait_for_connection_async(self) -> None:
        """Waits for the connection to be established."""
        while not self._is_connected:
            await asyncio.sleep(0)

    def stop_listening(self) -> None:
        """Closes the connection to the printer."""
        asyncio.run(self.stop_listening_async())

    async def stop_listening_async(self) -> None:
        """Closes the connection to the printer."""
        # TODO: Make sure this is more reliably called. Ideally in __exit__ using the with statement.
        self._connection and await self._connection.close()

    def _on_open(self) -> None:
        """Callback for when the connection is opened."""
        _logger.info(f"{self._ip_address}: Connection established")
        self._is_connected = True

    def _on_close(self) -> None:
        """Callback for when the connection is closed."""
        _logger.info(f"{self._ip_address}: Connection closed")
        self._is_connected = False

    def _on_message(self, message: str) -> SDCPMessage:
        """Callback for when a message is received."""
        _logger.debug(f"{self._ip_address}: Message received: {message}")
        parsed_message = SDCPMessage.parse(message)

        match parsed_message.topic:
            case "response":
                pass
            case "status":
                self._update_status(parsed_message)
                self._fire_callbacks()
            case _:
                _logger.warning(f"{self._ip_address}: Unknown message topic")

        return parsed_message

    def register_callback(self, callback: callable) -> None:
        """Registers a callback function to be called when a message is received."""
        if callback in self._callbacks:
            _logger.debug(f"{self._ip_address}: Callback already registered")
            return

        self._callbacks.append(callback)
        _logger.info(f"{self._ip_address}: Callback registered")

    def _fire_callbacks(self) -> None:
        """Calls all registered callbacks."""
        for callback in self._callbacks:
            callback(self)

    # TODO: Add timeout
    def _send_request(
        self,
        payload: dict,
        connection: websocket = None,
        receive_message: bool = True,
        expect_response: bool = True,
    ) -> SDCPMessage:
        """Sends a request to the printer."""
        asyncio.run(
            self._send_request_async(
                payload, connection, receive_message, expect_response
            )
        )

    # TODO: Add timeout
    async def _send_request_async(
        self,
        payload: dict,
        connection: ClientConnection = None,
        receive_message: bool = True,
        expect_response: bool = True,
    ) -> SDCPMessage:
        """Sends a request to the printer."""
        if connection is None:
            if self._connection is not None and self._is_connected:
                return await self._send_request_async(
                    payload, self._connection, receive_message=False
                )
            else:
                async with connect(self._websocket_url) as ws:
                    return await self._send_request_async(
                        payload,
                        ws,
                        receive_message=True,
                        expect_response=expect_response,
                    )

        _logger.debug(f"{self._ip_address}: Sending request with payload: {payload}")
        await connection.send(json.dumps(payload))

        if receive_message:
            if expect_response:
                response: SDCPResponseMessage = self._on_message(
                    await connection.recv()
                )
                if not response.is_success:
                    raise AssertionError(f"Request failed: {response.error_message}")
            return self._on_message(await connection.recv())

    # TODO: Add timeout
    def refresh_status(self) -> None:
        """Sends a request to the printer to report its status."""
        asyncio.run(self.refresh_status_async())

    # TODO: Add timeout
    async def refresh_status_async(self) -> None:
        """Sends a request to the printer to report its status."""
        _logger.info(f"{self._ip_address}: Requesting status")

        payload = SDCPStatusRequest.build(self)

        await self._send_request_async(payload)

    def _update_status(self, message: SDCPStatusMessage) -> None:
        """Updates the printer's status fields."""
        self._status_message = message
        _logger.info(f"{self._ip_address}: Status updated: {self._status_message}")
