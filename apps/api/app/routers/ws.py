"""WebSocket para recibir alertas y mensajes mesh en tiempo real."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.dependencies import WebSocketManagerDep

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, ws_manager: WebSocketManagerDep) -> None:
    await ws_manager.connect(websocket)
    logger.info("Nueva conexión WS — activas: %d", ws_manager.active_count)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Conexión WS cerrada por el cliente")
    finally:
        await ws_manager.disconnect(websocket)
