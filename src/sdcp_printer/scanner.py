import json
import logging
import socket

from const import BROADCAST_PORT, MESSAGE_ENCODING
from printer import SDCPPrinter

logger = logging.getLogger(__name__)


def discover_devices(timeout: int = 1) -> list[SDCPPrinter]:
    '''Broadcasts a discovery message to all devices on the network and waits for responses.'''
    printers: list[SDCPPrinter] = []

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, timeout)
        sock.sendto(b'M99999', ('<broadcast>', BROADCAST_PORT))

        logger.info('Starting scan')
        while True:
            try:
                raw_data, address = sock.recvfrom(8192)
                logger.debug(
                    f'Reply from {address[0]}: {raw_data.decode(MESSAGE_ENCODING)}')
                printer_json = json.loads(raw_data.decode(MESSAGE_ENCODING))
                printers.append(SDCPPrinter(printer_json))
            except socket.timeout:
                logger.info('Done scanning')
                break
            except json.JSONDecodeError:
                logger.error(f'Invalid JSON from {address[0]}')

    return printers
