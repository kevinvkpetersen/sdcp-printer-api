"""Classes to handle requests sent to the printer."""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

from .enum import SDCPCommand, SDCPFrom

if TYPE_CHECKING:
    from . import SDCPPrinter


class SDCPRequest:
    """Base class for requests to the printer."""

    @staticmethod
    def build(
        printer: SDCPPrinter,
        command: SDCPCommand,
        data: dict,
        sdcp_from: SDCPFrom = SDCPFrom.PC,
    ) -> dict:
        """Builds a request to be sent to the printer."""
        return {
            "Id": printer.uuid,
            "Data": {
                "Cmd": command.value,
                "Data": data,
                "RequestID": os.urandom(8).hex(),
                "MainboardID": printer.mainboard_id,
                "TimeStamp": int(time.time()),
                "From": sdcp_from.value,
            },
            "Topic": f"sdcp/request/{printer.mainboard_id}",
        }


class SDCPStatusRequest(SDCPRequest):
    """Class to build a request to get the printer's status."""

    @staticmethod
    def build(printer: SDCPPrinter, sdcp_from: SDCPFrom = SDCPFrom.PC) -> dict:
        """Builds a request to get the printer's status."""
        return SDCPRequest.build(printer, SDCPCommand.STATUS, {}, sdcp_from)
