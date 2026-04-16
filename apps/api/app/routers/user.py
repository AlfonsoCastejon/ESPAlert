"""Endpoints de usuario: favoritos, preferencias y perfil."""

import uuid

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import delete, func, select

from app.dependencies import CurrentUserDep, DBSessionDep
from app.models.alert import Alert
from app.models.user_favorite import UserFavorite
from app.models.user_preferences import UserPreferences
from app.schemas.alert import AlertResponse

router = APIRouter(tags=["user"])


# ──────────────────── Favoritos ────────────────────


@router.get("/favorites", summary="Listar alertas favoritas del usuario")
async def listar_favoritos(
    user: CurrentUserDep,
    db: DBSessionDep,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    total_q = await db.execute(
        select(func.count(UserFavorite.id)).where(UserFavorite.user_id == user.id)
    )
    total = total_q.scalar() or 0

    q = (
        select(Alert)
        .join(UserFavorite, UserFavorite.alert_id == Alert.id)
        .where(UserFavorite.user_id == user.id)
        .order_by(UserFavorite.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(q)
    alerts = result.scalars().all()

    return {
        "total": total,
        "items": [AlertResponse.model_validate(a) for a in alerts],
    }


@router.post(
    "/favorites/{alert_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Marcar alerta como favorita",
)
async def agregar_favorito(
    alert_id: uuid.UUID,
    user: CurrentUserDep,
    db: DBSessionDep,
):
    alert_q = await db.execute(select(Alert.id).where(Alert.id == alert_id))
    if not alert_q.scalar():
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    existe = await db.execute(
        select(UserFavorite.id).where(
            UserFavorite.user_id == user.id,
            UserFavorite.alert_id == alert_id,
        )
    )
    if existe.scalar():
        raise HTTPException(status_code=409, detail="Ya es favorita")

    fav = UserFavorite(user_id=user.id, alert_id=alert_id)
    db.add(fav)
    await db.commit()
    return {"detail": "Favorito agregado"}


@router.delete(
    "/favorites/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Quitar alerta de favoritos",
)
async def quitar_favorito(
    alert_id: uuid.UUID,
    user: CurrentUserDep,
    db: DBSessionDep,
):
    result = await db.execute(
        delete(UserFavorite).where(
            UserFavorite.user_id == user.id,
            UserFavorite.alert_id == alert_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Favorito no encontrado")
    await db.commit()


# ──────────────────── Preferencias ────────────────────


class PreferenciasInput(BaseModel):
    region: str | None = None
    filters: dict | None = None
    theme: str | None = None


@router.get("/preferences", summary="Obtener preferencias del usuario")
async def obtener_preferencias(
    user: CurrentUserDep,
    db: DBSessionDep,
):
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user.id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        return {"region": None, "filters": None, "theme": None}

    return {
        "region": prefs.region,
        "filters": prefs.filters,
        "theme": prefs.theme,
    }


@router.put("/preferences", summary="Guardar preferencias del usuario")
async def guardar_preferencias(
    data: PreferenciasInput,
    user: CurrentUserDep,
    db: DBSessionDep,
):
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user.id)
    )
    prefs = result.scalar_one_or_none()

    if prefs:
        if data.region is not None:
            prefs.region = data.region
        if data.filters is not None:
            prefs.filters = data.filters
        if data.theme is not None:
            prefs.theme = data.theme
    else:
        prefs = UserPreferences(
            user_id=user.id,
            region=data.region,
            filters=data.filters,
            theme=data.theme,
        )
        db.add(prefs)

    await db.commit()
    return {"detail": "Preferencias guardadas"}
