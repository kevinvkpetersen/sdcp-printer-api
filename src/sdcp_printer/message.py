"""Classes to handle messages received from the printer."""

from __future__ import annotations

import json
import logging

_logger = logging.getLogger(__name__)


class SDCPDiscoveryMessage:
    """Message received as a reply to the broadcast message."""

    def __init__(self, message_json: dict):
        self._message_json = message_json

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

    @staticmethod
    def parse(message: str) -> SDCPDiscoveryMessage:
        """Parses a discovery message from the printer."""
        _logger.debug("Discovery message: %s", message)
        return SDCPDiscoveryMessage(json.loads(message))


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
                return SDCPResponseMessage(message_json)
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
        self.ack = message_json["Data"]["Data"]["Ack"]

    @property
    def is_success(self) -> bool:
        """Returns True if the request was successful."""
        return self.ack == 0

    @property
    def error_message(self) -> str | None:
        """Returns the error message if the request was unsuccessful."""
        match self.ack:
            case 0:
                return None
            case _:
                return f"Unknown error for ACK value: {self.ack}"


class SDCPStatusMessage(SDCPMessage):
    """Message received with the status details of the printer."""

    def __init__(self, message_json: dict):
        """Constructor."""
        super().__init__(message_json)

    @property
    def current_status(self) -> str:
        """Returns the CurrentStatus field of the message."""
        return self._message_json["Status"]["CurrentStatus"]
