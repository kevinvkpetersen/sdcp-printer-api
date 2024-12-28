"""Classes to handle messages received from the printer."""

from __future__ import annotations

import json
import logging

from .enum import SDCPCommand, SDCPAck, SDCPMachineStatus

logger = logging.getLogger(__name__)


class SDCPMessage:
    def __init__(self, message_json: dict):
        self._topic = message_json["Topic"].split("/")[1]

    @property
    def topic(self) -> str:
        """Returns the topic of the message."""
        return self._topic

    @staticmethod
    def parse(message: str) -> SDCPMessage:
        """Parses a message from the printer."""
        logger.debug(f"Message: {message}")
        message_json = json.loads(message)

        topic = message_json["Topic"].split("/")[1]
        logger.debug(f"Topic: {topic}")
        match topic:
            case "response":
                return SDCPResponseMessage.parse(message_json)
            case "status":
                return SDCPStatusMessage(message_json)
            case _:
                logger.warning(f"Unknown topic: {topic}")
                return SDCPMessage(message_json)


class SDCPResponseMessage(SDCPMessage):
    def __init__(self, message_json: dict):
        super().__init__(message_json)
        self._ack = SDCPAck(message_json["Data"]["Data"]["Ack"])

    @property
    def ack(self) -> SDCPAck:
        """Returns the Ack value of the response."""
        return self._ack

    @property
    def is_success(self) -> bool:
        """Returns True if the response was successful."""
        return self._ack == SDCPAck.OK

    @property
    def error_message(self) -> str | None:
        """Returns the error message if the response was not successful."""
        match self._ack:
            case SDCPAck.OK:
                return None
            case _:
                return f"Unknown error for ACK value: {self.ack}"

    @staticmethod
    def parse(message_json: dict) -> SDCPResponseMessage:
        """Parses a response message from the printer."""
        command = SDCPCommand(message_json["Data"]["Cmd"])
        match command:
            case _:
                return SDCPResponseMessage(message_json)


class SDCPStatusMessage(SDCPMessage):
    def __init__(self, message_json: dict):
        super().__init__(message_json)
        self._current_status = [
            SDCPMachineStatus(status_code)
            for status_code in message_json["Status"]["CurrentStatus"]
        ]

    @property
    def current_status(self) -> list[SDCPMachineStatus]:
        """Returns the CurrentStatus of the printer."""
        return self._current_status
