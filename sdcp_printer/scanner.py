import json
import logging
import socket
import sys

from const import BROADCAST_PORT, MESSAGE_ENCODING
from printer import Printer

logger = logging.getLogger(__name__)


def discover_devices(timeout: int = 1):
    printers: list[Printer] = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    with sock:
        sock.settimeout(timeout)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, timeout)
        sock.sendto(b'M99999', ('<broadcast>', BROADCAST_PORT))

        logger.info('Starting scan')
        while True:
            try:
                raw_data, address = sock.recvfrom(8192)
                logger.debug(
                    f'Reply from {address[0]}: {raw_data.decode(MESSAGE_ENCODING)}')
                printer_data = json.loads(raw_data.decode(MESSAGE_ENCODING))
                printers.append(Printer(printer_data))
            except socket.timeout:
                logger.info('Done scanning')
                break
            except json.JSONDecodeError:
                logger.error(f'Invalid JSON from {address[0]}')

    return printers


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(levelname)8s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG,
        stream=sys.stdout
    )

    discover_devices()
