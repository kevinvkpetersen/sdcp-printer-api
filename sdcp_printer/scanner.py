import json
import logging
import socket
import sys

from const import BROADCAST_PORT, MESSAGE_ENCODING
from printer import Printer

logger = logging.getLogger(__name__)


def discover_devices():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    with sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(b'M99999', ('<broadcast>', BROADCAST_PORT))

        raw_data, address = sock.recvfrom(8192)
        logger.debug(
            f'Reply from {address[0]}: {raw_data.decode(MESSAGE_ENCODING)}')
        printer_data = json.loads(raw_data.decode(MESSAGE_ENCODING))
        printer_object = Printer(printer_data)
        logger.info(f'Found printer: {printer_object}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    discover_devices()
