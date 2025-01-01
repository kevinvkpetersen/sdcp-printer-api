"""Constants used in the project"""

from enum import Enum


class SDCPCommand(Enum):
    """Values for the Cmd field."""

    STATUS = 0


class SDCPFrom(Enum):
    """Values for the From field."""

    PC = 0  # Local PC Software Local Area Network


class SDCPStatus(Enum):
    """Values for the CurrentStatus and PreviousStatus fields."""

    IDLE = 0  # Idle
    PRINTING = 1  # Executing print task
    TRANSFERRING = 2  # File transfer in progress
    EXPOSURE_TESTING = 3  # Exposure test in progress
    DEVICES_TESTING = 4  # Device self-check in progress
