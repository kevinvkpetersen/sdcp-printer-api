import logging
import socket

BROADCAST_PORT = 3000

logger = logging.getLogger(__name__)


def discover_devices():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(b'M99999', ('<broadcast>', BROADCAST_PORT))

        raw_data, address = sock.recvfrom(8192)
        logger.debug(f'Reply from {address[0]}: {raw_data.decode()}')
