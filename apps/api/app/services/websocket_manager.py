"""Gestor de conexiones WebSocket activas.

Permite suscribir/desuscribir clientes y difundir eventos a todos ellos.
"""

import asyncio
import logging
from datetime import UTC, datetime

from fastapi import WebSocket

from app.schemas.ws import WsEvent

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Mantiene el conjunto de conexiones WebSocket activas y gestiona el broadcast."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.debug("WS connect — activas: %d", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        logger.debug("WS disconnect — activas: %d", len(self._connections))

    async def broadcast(self, event: WsEvent) -> None:
        """Envía el evento a todas las conexiones activas."""
        payload = event.model_dump_json()
        dead: list[WebSocket] = []

        async with self._lock:
            targets = list(self._connections)

        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:
                logger.debug("WS send fallido — marcando para eliminar")
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)

    async def broadcast_ping(self) -> None:
        """Latido periódico para mantener conexiones vivas."""
        await self.broadcast(
            WsEvent(event="ping", data=None, timestamp=datetime.now(UTC))
        )

    @property
    def active_count(self) -> int:
        return len(self._connections)


# Instancia global compartida
ws_manager = WebSocketManager()
