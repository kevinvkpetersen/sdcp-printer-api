"""Classes to handle messages received from the printer."""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


class SDCPMessage:
    def __init__(self, message_json: dict):
        self.topic = message_json["Topic"].split("/")[1]

    @staticmethod
    def parse(message: str) -> SDCPMessage:
        """Parses a message from the printer."""
        logger.debug(f"Message: {message}")
        message_json = json.loads(message)

        topic = message_json["Topic"].split("/")[1]
        logger.debug(f"Topic: {topic}")
        match topic:
            case "response":
                return SDCPResponseMessage(message_json)
            case "status":
                return SDCPStatusMessage(message_json)
            case _:
                logger.warning(f"Unknown topic: {topic}")
                return SDCPMessage(message_json)


class SDCPResponseMessage(SDCPMessage):
    def __init__(self, message_json: dict):
        super().__init__(message_json)
        self.ack = message_json["Data"]["Data"]["Ack"]

    @property
    def is_success(self) -> bool:
        """Returns True if the response was successful."""
        return self.ack == 0

    @property
    def error_message(self) -> str | None:
        """Returns the error message if the response was not successful."""
        match self.ack:
            case 0:
                return None
            case _:
                return f"Unknown error for ACK value: {self.ack}"


class SDCPStatusMessage(SDCPMessage):
    def __init__(self, message_json: dict):
        super().__init__(message_json)
        self.status = message_json["Status"]["CurrentStatus"]
