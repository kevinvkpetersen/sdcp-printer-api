"""A module for async UDP connections."""

from __future__ import annotations

import asyncio

import asyncio_dgram


class AsyncUDPConnection:
    """A context manager for an async UDP connection."""

    _connection: asyncio_dgram.DatagramClient

    def __init__(self, host: str, port: int | str, timeout: int = None):
        """Constructor."""
        self.host = host
        self.port = port
        self.timeout = timeout

    async def __aenter__(self):
        """Open the connection."""
        self._connection = await asyncio.wait_for(
            asyncio_dgram.connect((self.host, self.port)),
            timeout=self.timeout,
        )

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Close the connection."""
        self._connection.close()

    async def send(self, data: bytes, timeout: int = None):
        """Send data to the connection."""
        await asyncio.wait_for(self._connection.send(data), timeout=timeout)

    async def receive(self, timeout: int = None) -> bytes:
        """Receive data from the connection."""
        data, _ = await asyncio.wait_for(self._connection.recv(), timeout=timeout)
        return data
