"""Main module for the SDCP Printer API."""

from __future__ import annotations

import asyncio
import json
import logging

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from .async_udp import AsyncUDPConnection
from .enum import SDCPFrom, SDCPMachineStatus, SDCPPrintError, SDCPPrintStatus
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

DEFAULT_TIMEOUT = 5

_logger = logging.getLogger(__package__)


class SDCPPrinter:
    """Class to represent a printer discovered on the network."""

    _connection: ClientConnection = None
    _is_connected: bool = False
    _callbacks: list[callable] = []
    _requests: dict[str, callable] = {}

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
    def get_printer(ip_address: str, timeout: int = DEFAULT_TIMEOUT) -> SDCPPrinter:
        """Gets information about a printer given its IP address."""

        return asyncio.run(SDCPPrinter.get_printer_async(ip_address, timeout))

    @staticmethod
    async def get_printer_async(ip_address: str, timeout: float = None) -> SDCPPrinter:
        """Gets information about a printer given its IP address."""
        _logger.info(f"Getting printer info for {ip_address}")

        try:
            async with asyncio.timeout(timeout):
                async with AsyncUDPConnection(
                    ip_address, DISCOVERY_PORT, timeout
                ) as conn:
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
    def name(self) -> str:
        """The printer's name."""
        return self._discovery_message and self._discovery_message.name

    @property
    def manufacturer(self) -> str:
        """The printer's manufacturer."""
        return self._discovery_message and self._discovery_message.manufacturer

    @property
    def model(self) -> str:
        """The printer's model."""
        return self._discovery_message and self._discovery_message.model

    @property
    def firmware_version(self) -> str:
        """The printer's firmware version."""
        return self._discovery_message and self._discovery_message.firmware_version

    @property
    def current_status(self) -> list[SDCPMachineStatus]:
        """The printer's current status."""
        return self._status_message and self._status_message.current_status

    @property
    def uv_led_temperature(self) -> float:
        """The printer's UV LED temperature in degrees Celsius."""
        return self._status_message and self._status_message.uv_led_temperature

    @property
    def screen_usage(self) -> float:
        """The printer's screen usage in seconds."""
        return self._status_message and self._status_message.screen_usage

    @property
    def film_usage(self) -> int:
        """The number of layers printed on the current film."""
        return self._status_message and self._status_message.film_usage

    @property
    def is_printing(self) -> bool:
        """Returns True if the printer is currently printing."""
        return (
            self._status_message and SDCPMachineStatus.PRINTING in self.current_status
        )

    @property
    def print_status(self) -> SDCPPrintStatus:
        """Returns the status of the print job."""
        return self._status_message and self._status_message.print_status

    @property
    def print_error(self) -> SDCPPrintError:
        """Returns the ErrorNumber field of the PrintInfo section."""
        return self._status_message and self._status_message.print_error

    @property
    def current_layer(self) -> int:
        """Returns the current layer number."""
        return self._status_message and self._status_message.current_layer

    @property
    def total_layers(self) -> int:
        """Returns the total number of layers in this print job."""
        return self._status_message and self._status_message.total_layers

    @property
    def current_time(self) -> int:
        """Returns the current print time in milliseconds."""
        return self._status_message and self._status_message.current_time

    @property
    def total_time(self) -> int:
        """Returns the total print time in milliseconds."""
        return self._status_message and self._status_message.total_time

    @property
    def file_name(self) -> str:
        """Returns the name of the file being printed."""
        return self._status_message and self._status_message.file_name

    # endregion

    def start_listening(
        self, timeout: float = DEFAULT_TIMEOUT, sleep_interval: float = 0
    ) -> None:
        """Opens a persistent connection to the printer to listen for messages."""
        asyncio.create_task(self.start_listening_async())
        asyncio.run(self.wait_for_connection_async(timeout, sleep_interval))

    async def start_listening_async(self) -> None:
        """Opens a persistent connection to the printer to listen for messages."""
        _logger.info(f"{self._ip_address}: Opening connection")

        async for ws in connect(self._websocket_url):
            try:
                self._connection = ws
                self._on_open()

                while True:
                    message = await self._connection.recv()
                    self._on_message(message)
            except ConnectionClosedError:
                _logger.warning(f"{self._ip_address}: Connection lost, retrying")
                self._is_connected = False
            except ConnectionClosedOK:
                break

        self._on_close()

    async def wait_for_connection_async(
        self, timeout: float = None, sleep_interval: float = 0
    ) -> None:
        """Waits for the connection to be established."""
        async with asyncio.timeout(timeout):
            while not self._is_connected:
                await asyncio.sleep(sleep_interval)

    def stop_listening(self) -> None:
        """Closes the connection to the printer."""
        asyncio.run(self.stop_listening_async())

    async def stop_listening_async(self) -> None:
        """Closes the connection to the printer."""
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
                self._handle_response(parsed_message)
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

    def _handle_response(self, response: SDCPResponseMessage) -> None:
        try:
            request_id = response._message_json["Data"]["RequestID"]
        except:
            return  # invalid response, no RequestID

        if request_id in self._requests:
            _logger.debug(
                f"{self._ip_address}: Handling response for request ID {request_id}"
            )
            callback = self._requests[request_id]
            del self._requests[request_id]
            callback(response)
        else:
            _logger.debug(
                f"{self._ip_address}: No callback found for request ID {request_id};"
                f"cmd: {response._message_json.get('Data',{}).get('Cmd', 'UNKNOWN')}"
            )

    def _fire_callbacks(self) -> None:
        """Calls all registered callbacks."""
        for callback in self._callbacks:
            callback(self)

    def _send_request(
        self,
        payload: dict,
        connection: ClientConnection = None,
        receive_message: bool = True,
        expect_response: bool = True,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> SDCPMessage:
        """Sends a request to the printer."""
        asyncio.run(
            self._send_request_async(
                payload,
                connection,
                receive_message,
                expect_response,
                timeout,
            )
        )

    async def send_request_async(
        self,
        payload: dict,
        timeout: float = None,
    ) -> SDCPMessage:
        """Sends a request to the printer, waiting for a matching response"""
        if self._connection is None:
            raise Exception("No connection established")

        # Expect a request id, throw on key error if we don't have oen
        request_id = payload["Data"]["RequestID"]
        resp: asyncio.Future[SDCPMessage] = asyncio.Future()
        def on_message(message: SDCPMessage) -> None:
            resp.set_result(message)
        self._requests[request_id] = on_message

        _logger.debug(f"{self._ip_address}: Sending request with payload: {payload}")
        try:
            async with asyncio.timeout(timeout):
                await self._connection.send(json.dumps(payload))
                return await resp
        finally:
            self._requests.pop(request_id, None)

    async def _send_request_async(
        self,
        payload: dict,
        connection: ClientConnection = None,
        receive_message: bool = True,
        expect_response: bool = True,
        timeout: float = None,
    ) -> SDCPMessage:
        """Sends a request to the printer."""
        if connection is None:
            if self._connection is not None and self._is_connected:
                return await self._send_request_async(
                    payload,
                    self._connection,
                    receive_message=False,
                    timeout=timeout,
                )
            else:
                async with connect(self._websocket_url) as ws:
                    return await self._send_request_async(
                        payload,
                        ws,
                        receive_message=True,
                        expect_response=expect_response,
                        timeout=timeout,
                    )

        _logger.debug(f"{self._ip_address}: Sending request with payload: {payload}")
        async with asyncio.timeout(timeout):
            await connection.send(json.dumps(payload))

            if receive_message:
                if expect_response:
                    response: SDCPResponseMessage = self._on_message(
                        await connection.recv()
                    )
                    if not response.is_success:
                        raise AssertionError(
                            f"Request failed: {response.error_message}"
                        )
                return self._on_message(await connection.recv())

    def refresh_status(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        sdcp_from: SDCPFrom = SDCPFrom.PC,
    ) -> None:
        """Sends a request to the printer to report its status."""
        asyncio.run(self.refresh_status_async(timeout, sdcp_from))

    async def refresh_status_async(
        self,
        timeout: float = None,
        sdcp_from: SDCPFrom = SDCPFrom.PC,
    ) -> None:
        """Sends a request to the printer to report its status."""
        _logger.info(f"{self._ip_address}: Requesting status")

        payload = SDCPStatusRequest.build(self, sdcp_from)

        await self._send_request_async(payload, timeout=timeout)

    def _update_status(self, status_message: SDCPStatusMessage) -> None:
        """Updates the printer's status fields."""
        self._status_message = status_message
        _logger.info(f"{self._ip_address}: Status updated: {self._status_message}")
