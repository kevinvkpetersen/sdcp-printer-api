"""Classes to handle messages received from the printer."""

from __future__ import annotations

import json
import logging

from .enum import SDCPAck, SDCPCommand, SDCPMachineStatus

_logger = logging.getLogger(__name__)


class SDCPDiscoveryMessage:
    """Message received as a reply to the broadcast message."""

    def __init__(self, message_json: dict):
        self._message_json = message_json

    @staticmethod
    def parse(message: str) -> SDCPDiscoveryMessage:
        """Parses a discovery message from the printer."""
        _logger.debug("Discovery message: %s", message)
        return SDCPDiscoveryMessage(json.loads(message))

    # Required properties
    @property
    def id(self) -> str:
        """Returns the ID of the printer."""
        return self._message_json["Id"]

    @property
    def ip_address(self) -> str:
        """Returns the IP address of the printer."""
        return self._message_json["Data"]["MainboardIP"]

    @property
    def mainboard_id(self) -> str:
        """Returns the mainboard ID of the printer."""
        return self._message_json["Data"]["MainboardID"]

    # Optional properties
    @property
    def name(self) -> str:
        """Returns the name of the printer."""
        return self._message_json.get("Data", {}).get("Name")

    @property
    def manufacturer(self) -> str:
        """Returns the manufacturer of the printer."""
        return self._message_json.get("Data", {}).get("BrandName")

    @property
    def model(self) -> str:
        """Returns the model of the printer."""
        return self._message_json.get("Data", {}).get("MachineName")

    @property
    def firmware_version(self) -> str:
        """Returns the firmware version of the printer."""
        return self._message_json.get("Data", {}).get("FirmwareVersion")


class SDCPMessage:
    """Base class to represent a message received from the printer."""

    def __init__(self, message_json: dict):
        """Constructor."""
        self.topic = message_json["Topic"].split("/")[1]
        self._message_json = message_json

    @staticmethod
    def parse(message: str) -> SDCPMessage:
        """Parses a message from the printer."""
        _logger.debug(f"Message: {message}")
        message_json = json.loads(message)

        topic = message_json["Topic"].split("/")[1]
        _logger.debug(f"Topic: {topic}")
        match topic:
            case "response":
                return SDCPResponseMessage.parse(message_json)
            case "status":
                return SDCPStatusMessage(message_json)
            case _:
                _logger.warning(f"Unknown topic: {topic}")
                return SDCPMessage(message_json)


class SDCPResponseMessage(SDCPMessage):
    """Message received as a direct response to a request."""

    def __init__(self, message_json: dict):
        """Constructor."""
        super().__init__(message_json)
        try:
            ack_value = message_json["Data"]["Data"]["Ack"]
            self.ack = SDCPAck(ack_value)
        except ValueError:
            _logger.warning(f"Unknown Ack value: {ack_value}")
            self.ack = SDCPAck.UNKNOWN

    @staticmethod
    def parse(message_json: dict) -> SDCPResponseMessage:
        """Parses a response message from the printer."""
        try:
            cmd_value = message_json["Data"]["Cmd"]
            command = SDCPCommand(cmd_value)
        except ValueError:
            _logger.warning(f"Unknown command: {cmd_value}")
            command = SDCPCommand.UNKNOWN

        match command:
            case _:
                return SDCPResponseMessage(message_json)

    @property
    def is_success(self) -> bool:
        """Returns True if the request was successful."""
        return self.ack == SDCPAck.SUCCESS

    @property
    def error_message(self) -> str | None:
        """Returns the error message if the request was unsuccessful."""
        match self.ack:
            case SDCPAck.SUCCESS:
                return None
            case _:
                return f"Unknown error for ACK value: {self._message_json['Data']['Data']['Ack']}"


class SDCPStatusMessage(SDCPMessage):
    """Message received with the status details of the printer."""

    _current_status: list[SDCPMachineStatus] = None

    def __init__(self, message_json: dict):
        """Constructor."""
        super().__init__(message_json)
        self._current_status = [
            SDCPMachineStatus(value)
            for value in message_json["Status"]["CurrentStatus"]
        ]

    @property
    def current_status(self) -> list[SDCPMachineStatus]:
        """Returns the CurrentStatus field of the message."""
        return self._current_status

    @property
    def uv_led_temperature(self) -> float:
        """Returns the UV LED temperature in degrees Celsius."""
        return self._message_json["Status"].get("TempOfUVLED")
