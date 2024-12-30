"""A module for async UDP connections."""

from __future__ import annotations

import asyncio_dgram


class AsyncUDPConnection:
    """A context manager for an async UDP connection."""

    _connection: asyncio_dgram.DatagramClient

    def __init__(self, host: str, port: int | str):
        """Constructor."""
        self.host = host
        self.port = port

    async def __aenter__(self):
        """Open the connection."""
        self._connection = await asyncio_dgram.connect((self.host, self.port))

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Close the connection."""
        self._connection.close()

    async def send(self, data: bytes):
        """Send data to the connection."""
        await self._connection.send(data)

    async def receive(self, buffer_size: int = 8192) -> bytes:
        """Receive data from the connection."""
        data, _ = await self._connection.recv()
        return data
