import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Canal WebSocket de actualizaciones en tiempo real.

    El servidor emite objetos JSON con el siguiente esquema::

        {
            "event": "alert.new" | "alert.updated" | "alert.expired" | "ping",
            "data": <WsAlertPayload> | null,
            "timestamp": "<ISO 8601 UTC>"
        }

    Tipos de evento:
    - ``alert.new``     — nueva alerta insertada.
    - ``alert.updated`` — alerta modificada.
    - ``alert.expired`` — alerta expirada o eliminada.
    - ``ping``          — latido periódico (data=null).

    Códigos de cierre WebSocket:
    - ``1000`` — cierre normal iniciado por el cliente.
    - ``1011`` — error interno del servidor.
    """
    await ws_manager.connect(websocket)
    logger.info("Nueva conexión WS — activas: %d", ws_manager.active_count)
    try:
        while True:
            # Mantiene la conexión viva esperando mensajes del cliente
            # (el cliente no necesita enviar nada; los pings los gestiona el servidor)
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Conexión WS cerrada por el cliente")
    finally:
        await ws_manager.disconnect(websocket)
