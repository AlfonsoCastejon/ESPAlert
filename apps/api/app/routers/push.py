from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.push_subscription import PushSubscription
from app.schemas.push_subscripion import (
    PushSubscribeRequest,
    PushSubscribeResponse,
    PushUnsubscribeRequest,
)

router = APIRouter(prefix="/push", tags=["push"])


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
        201: {"description": "Suscripción registrada correctamente"},
        422: {"description": "Payload inválido"},
    },
)
async def subscribe(
    body: PushSubscribeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PushSubscribeResponse:
    existing = await db.scalar(
        select(PushSubscription).where(PushSubscription.endpoint == body.endpoint)
    )

    if existing:
        existing.p256dh = body.p256dh
        existing.auth = body.auth
        await db.flush()
        return PushSubscribeResponse(ok=True, message="Suscripción actualizada")

    db.add(
        PushSubscription(
            endpoint=body.endpoint,
            p256dh=body.p256dh,
            auth=body.auth,
        )
    )
    await db.flush()
    return PushSubscribeResponse(ok=True, message="Suscripción registrada")


@router.delete(
    "/subscribe",
    response_model=PushSubscribeResponse,
    summary="Eliminar suscripción push",
    description="Elimina la suscripción push asociada al endpoint proporcionado.",
    responses={
        200: {"description": "Suscripción eliminada correctamente"},
        404: {"description": "Suscripción no encontrada"},
        422: {"description": "Payload inválido"},
    },
)
async def unsubscribe(
    body: PushUnsubscribeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PushSubscribeResponse:
    result = await db.execute(
        delete(PushSubscription).where(PushSubscription.endpoint == body.endpoint)
    )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe ninguna suscripción para ese endpoint",
        )

    return PushSubscribeResponse(ok=True, message="Suscripción eliminada")
