"""Endpoints de suscripciones push: alta, baja y clave pública VAPID."""

from fastapi import APIRouter, HTTPException, status
from app.config import get_settings
from app.dependencies import CurrentUserDep, DBSessionDep
from app.schemas.push_subscription import (
    SubscriptionCreate,
    PushSubscribeResponse,
    PushUnsubscribeRequest,
)
from app.services import push_service

router = APIRouter(prefix="/push", tags=["push"])


@router.get(
    "/vapid-key",
    summary="Clave pública VAPID",
    description="Devuelve la clave pública VAPID que el navegador necesita para suscribirse.",
)
async def get_vapid_public_key() -> dict[str, str]:
    return {"public_key": get_settings().VAPID_PUBLIC_KEY}

@router.post(
    "/subscribe",
    response_model=PushSubscribeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar suscripción push",
    description=(
        "Registra el endpoint y las claves criptográficas del navegador para recibir "
        "notificaciones push cuando se detecten alertas críticas. "
        "Si el endpoint ya existe se actualiza sin crear un duplicado."
    ),
    responses={
        201: {"description": "Suscripción registrada o actualizada correctamente"},
        422: {"description": "Payload inválido"},
    }
)
async def subscribe(
    body: SubscriptionCreate,
    db: DBSessionDep,
    user: CurrentUserDep,
) -> PushSubscribeResponse:
    await push_service.subscribe(db, body, user_id=user.id)
    return PushSubscribeResponse(ok=True, message="Suscripción registrada o actualizada correctamente")

@router.delete(
    "/subscribe",
    response_model=PushSubscribeResponse,
    summary="Eliminar suscripción push",
    description="Elimina la suscripción push asociada al endpoint proporcionado.",
    responses={
        200: {"description": "Suscripción eliminada correctamente"},
        404: {"description": "Suscripción no encontrada"},
        422: {"description": "Payload inválido"},
    }
)
async def unsubscribe(
    body: PushUnsubscribeRequest,
    db: DBSessionDep,
) -> PushSubscribeResponse:
    eliminado = await push_service.unsubscribe(db, body.endpoint)
    
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe ninguna suscripción para ese endpoint"
        )

    return PushSubscribeResponse(ok=True, message="Suscripción eliminada correctamente")
