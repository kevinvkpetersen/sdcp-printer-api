import socket
import logging
import sys

BROADCAST_PORT = 3000

logger = logging.getLogger(__name__)


def discover_devices():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    with sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(b'M99999', ('<broadcast>', BROADCAST_PORT))

        raw_data, address = sock.recvfrom(1024)
        logger.debug(f'Reply from {address[0]}: {raw_data.decode()}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    discover_devices()
