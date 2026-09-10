import asyncio
import json
from typing import Set

import websockets


class TelemetryServer:
    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port
        self._clients: Set = set()

    async def _handle_connection(self, connection) -> None:
        self._clients.add(connection)
        try:
            # Never read or act on client frames: the boat must not accept
            # commands from shore, even accidental ones from a browser tab.
            async for _ in connection:
                pass
        finally:
            self._clients.discard(connection)

    def broadcast(self, message: dict) -> None:
        if self._clients:
            websockets.broadcast(self._clients, json.dumps(message))

    async def run_forever(self) -> None:
        async with websockets.serve(self._handle_connection, self._host, self._port):
            await asyncio.Future()
