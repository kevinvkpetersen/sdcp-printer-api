import json
import logging
import socket

from const import BROADCAST_PORT, MESSAGE_ENCODING
from printer import SDCPPrinter

logger = logging.getLogger(__name__)


def discover_devices():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(b'M99999', ('<broadcast>', BROADCAST_PORT))

        raw_data, address = sock.recvfrom(8192)
        logger.debug(
            f'Reply from {address[0]}: {raw_data.decode(MESSAGE_ENCODING)}')
        printer_json = json.loads(raw_data.decode(MESSAGE_ENCODING))
        printer_object = SDCPPrinter(printer_json)
        logger.info(f'Found printer: {printer_object}')

    return printer_object
