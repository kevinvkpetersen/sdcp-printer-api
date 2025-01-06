"""Constants used in the project"""

from enum import Enum, IntEnum


class SDCPCommand(Enum):
    """Values for the Cmd field."""

    UNKNOWN = None
    STATUS = 0


class SDCPFrom(IntEnum):
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


class SDCPMachineStatus(IntEnum):
    """Values for the CurrentStatus and PreviousStatus fields in the status message."""

    IDLE = 0  # Idle
    PRINTING = 1  # Executing print task
    FILE_TRANSFER = 2  # File transfer in progress
    EXPOSURE_TEST = 3  # Exposure test in progress
    DEVICE_TEST = 4  # Device self-check in progress


class SDCPPrintStatus(Enum):
    """Values for the Status field in the PrintInfo section of the status message."""

    UNKNOWN = None
    IDLE = 0  # Idle
    HOMING = 1  # Resetting
    DROPPING = 2  # Descending
    EXPOSING = 3  # Exposing
    LIFTING = 4  # Lifting
    PAUSING = 5  # Executing Pause Action
    PAUSED = 6  # Suspended
    STOPPING = 7  # Executing Stop Action
    STOPPED = 8  # Stopped
    COMPLETE = 9  # Print Completed
    FILE_CHECKING = 10  # File Checking in Progress


class SDCPPrintError(Enum):
    """Values for the ErrorNumber field in the PrintInfo section of the status message."""

    UNKNOWN = None
    NONE = 0  # Normal
    MD5_CHECK = 1  # File MD5 Check Failed
    FILE_IO = 2  # File Read Failed
    INVALID_RESOLUTION = 3  # Resolution Mismatch
    UNKNOWN_FORMAT = 4  # Format Mismatch
    UNKNOWN_MODEL = 5  # Machine Model Mismatch
