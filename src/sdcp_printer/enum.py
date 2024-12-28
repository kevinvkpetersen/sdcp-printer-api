"""Constants used in the project"""

from enum import Enum


class SDCPCommand(Enum):
    """Values for the Cmd field."""

    STATUS = 0
    ATTRIBUTE = 1
    START_PRINT = 128
    PAUSE_PRINT = 129
    STOP_PRINT = 130
    CONTINUE_PRINT = 131
    STOP_FEEDING_MATERIAL = 132
    SKIP_PREHEAT = 133
    CHANGE_PRINTER_NAME = 192
    TERMINATE_FILE_TRANSFER = 255
    RETRIEVE_FILE_LIST = 258
    BATCH_DELETE_FILES = 259
    RETRIEVE_HISTORICAL_TASKS = 320
    RETRIEVE_TASK_DETAILS = 321
    ENABLE_DISABLE_VIDEO_STREAM = 386
    ENABLE_DISABLE_TIME_LAPSE = 387


class SDCPFrom(Enum):
    """Values for the From field."""

    PC = 0  # Local PC Software Local Area Network
    WEB_PC = 1  # PC Software via WEB
    WEB = 2  # Web Client
    APP = 3  # App
    SERVER = 4  # Server


class SDCPAck(Enum):
    """Values for the Ack field in the response message."""

    OK = 0


class SDCPStartPrintAck(SDCPAck):
    """Values for the Ack field in the start print response message."""

    BUSY = 1  # The printer is busy
    NOT_FOUND = 2  # File not found
    MD5_FAILED = 3  # MD5 verification failed
    FILEIO_FAILED = 4  # File read failed
    INVALID_RESOLUTION = 5  # Resolution mismatch
    UNKNOWN_FORMAT = 6  # Unrecognized file format
    UNKNOWN_MODEL = 7  # Machine model mismatch


class SDCPFileTransferAck(SDCPAck):
    """Values for the Ack field in the file transfer response message."""

    SUCCESS = 0  # Success
    NOT_TRANSFER = 1  # The printer is not currently transferring files.
    CHECKING = 2  # The printer is already in the file verification phase.
    NOT_FOUND = 3  # File not found


class SDCPMachineStatus(Enum):
    """Values for the CurrentStatus and PreviousStatus fields in the status message."""

    IDLE = 0  # Idle
    PRINTING = 1  # Executing print task
    FILE_TRANSFER = 2  # File transfer in progress
    EXPOSURE_TEST = 3  # Exposure test in progress
    DEVICE_TEST = 4  # Device self-check in progress


class SDCPPrintStatus(Enum):
    """Values for the PrintInfo > Status field in the status message."""

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
    """Values for the PrintInfo > Error field in the status message."""

    NONE = 0  # Normal
    MD5_CHECK = 1  # File MD5 Check Failed
    FILE_IO = 2  # File Read Failed
    INVALID_RESOLUTION = 3  # Resolution Mismatch
    UNKNOWN_FORMAT = 4  # Format Mismatch
    UNKNOWN_MODEL = 5  # Machine Model Mismatch
