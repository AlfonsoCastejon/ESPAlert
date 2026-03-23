from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db
from app.services.websocket_manager import WebSocketManager, ws_manager

# Alias de tipos para una inyección más limpia en los routers
DBSessionDep = Annotated[AsyncSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

# Getter simple para el gestor de WebSocket que permite su inyección
def get_ws_manager() -> WebSocketManager:
    return ws_manager

WebSocketManagerDep = Annotated[WebSocketManager, Depends(get_ws_manager)]
