from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings, settings
from app.database import get_db
from app.models.user import User
from app.services import auth_service
from app.services.websocket_manager import WebSocketManager, ws_manager

# Alias de tipos para una inyección más limpia en los routers
DBSessionDep = Annotated[AsyncSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

# Getter simple para el gestor de WebSocket que permite su inyección
def get_ws_manager() -> WebSocketManager:
    return ws_manager

WebSocketManagerDep = Annotated[WebSocketManager, Depends(get_ws_manager)]


async def get_current_user(
    db: DBSessionDep,
    espalert_session: Annotated[str | None, Cookie(alias=settings.SESSION_COOKIE_NAME)] = None,
) -> User:
    if not espalert_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
        )
    user_id = auth_service.decode_access_token(espalert_session)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida",
        )
    user = await auth_service.get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    return user


async def get_current_user_optional(
    db: DBSessionDep,
    espalert_session: Annotated[str | None, Cookie(alias=settings.SESSION_COOKIE_NAME)] = None,
) -> User | None:
    if not espalert_session:
        return None
    user_id = auth_service.decode_access_token(espalert_session)
    if user_id is None:
        return None
    return await auth_service.get_user_by_id(db, user_id)


CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentUserOptionalDep = Annotated[User | None, Depends(get_current_user_optional)]
