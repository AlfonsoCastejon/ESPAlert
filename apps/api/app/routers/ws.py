"""WebSocket para recibir alertas y mensajes mesh en tiempo real."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.config import settings
from app.database import AsyncSessionLocal
from app.dependencies import WebSocketManagerDep
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, ws_manager: WebSocketManagerDep) -> None:
    # Auth previa al accept(): exigimos cookie de sesión válida para evitar
    # que cualquiera abra conexiones (vector de DoS).
    cookie = websocket.cookies.get(settings.SESSION_COOKIE_NAME)
    user_id = auth_service.decode_access_token(cookie) if cookie else None
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    async with AsyncSessionLocal() as db:
        user = await auth_service.get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(websocket)
    logger.info("Nueva conexión WS (user=%s) — activas: %d", user.id, ws_manager.active_count)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Conexión WS cerrada por el cliente")
    finally:
        await ws_manager.disconnect(websocket)
