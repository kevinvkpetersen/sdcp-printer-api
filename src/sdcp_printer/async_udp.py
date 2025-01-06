"""A module for async UDP connections."""

from __future__ import annotations

import asyncio

import asyncio_dgram


class AsyncUDPConnection:
    """A context manager for an async UDP connection."""

    _connection: asyncio_dgram.DatagramClient

    def __init__(self, host: str, port: int | str, timeout: float = None):
        """Constructor."""
        self.host = host
        self.port = port
        self.timeout = timeout

    async def __aenter__(self):
        """Open the connection."""
        async with asyncio.timeout(self.timeout):
            self._connection = await asyncio_dgram.connect((self.host, self.port))
            return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Close the connection."""
        self._connection.close()

    async def send(self, data: bytes, timeout: float = None):
        """Send data to the connection."""
        async with asyncio.timeout(timeout):
            await self._connection.send(data)

    async def receive(self, timeout: float = None) -> bytes:
        """Receive data from the connection."""
        async with asyncio.timeout(timeout):
            data, _ = await self._connection.recv()
            return data
