"""Constants used in the project"""

from enum import Enum


class SDCPCommand(Enum):
    """Values for the Cmd field."""

    UNKNOWN = None
    STATUS = 0


class SDCPFrom(Enum):
    """Values for the From field."""

    PC = 0  # Local PC Software Local Area Network
    WEB_PC = 1  # PC Software via WEB
    WEB = 2  # Web Client
    APP = 3  # App
    SERVER = 4  # Server


class SDCPAck(Enum):
    """Values for the Ack field in the response message."""

    UNKNOWN = None  # Unknown error
    SUCCESS = 0  # Success


class SDCPMachineStatus(Enum):
    """Values for the CurrentStatus and PreviousStatus fields in the status message."""

    IDLE = 0  # Idle
    PRINTING = 1  # Executing print task
    FILE_TRANSFER = 2  # File transfer in progress
    EXPOSURE_TEST = 3  # Exposure test in progress
    DEVICE_TEST = 4  # Device self-check in progress
