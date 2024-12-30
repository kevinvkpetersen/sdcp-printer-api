"""Module for discovering SDCP printers on the network."""

import json
import logging
import socket

from . import DISCOVERY_PORT, MESSAGE_ENCODING, SDCPPrinter
from .message import SDCPDiscoveryMessage

_logger = logging.getLogger(__name__)


def discover_devices(timeout: int = 1) -> list[SDCPPrinter]:
    """Broadcasts a discovery message to all devices on the network and waits for responses."""
    printers: list[SDCPPrinter] = []

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, timeout)
        sock.sendto(b"M99999", ("<broadcast>", DISCOVERY_PORT))

        _logger.info("Starting scan")
        while True:
            try:
                device_response, address = sock.recvfrom(8192)
                _logger.debug(
                    f"Reply from {address[0]}: {device_response.decode(MESSAGE_ENCODING)}"
                )
                discovery_message = SDCPDiscoveryMessage.parse(
                    device_response.decode(MESSAGE_ENCODING)
                )
                printers.append(
                    SDCPPrinter(
                        discovery_message.id,
                        discovery_message.ip_address,
                        discovery_message.mainboard_id,
                        discovery_message,
                    )
                )
            except socket.timeout:
                _logger.info("Done scanning")
                break
            except json.JSONDecodeError:
                _logger.error(f"Invalid JSON from {address[0]}")

    return printers
