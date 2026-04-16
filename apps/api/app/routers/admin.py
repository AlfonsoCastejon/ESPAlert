"""Endpoints de administración: gestión de usuarios, alertas y mensajes mesh."""

import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select, delete

from app.dependencies import CurrentAdminDep, DBSessionDep
from app.models.alert import Alert
from app.models.mesh_message import MeshMessage
from app.models.user import User, UserRole

router = APIRouter(tags=["admin"])


# ──────────────────── Usuarios ────────────────────


@router.get(
    "/users",
    summary="Listar usuarios registrados",
    responses={403: {"description": "No autorizado"}},
)
async def listar_usuarios(
    _admin: CurrentAdminDep,
    db: DBSessionDep,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    total_q = await db.execute(select(func.count(User.id)))
    total = total_q.scalar() or 0

    q = (
        select(User)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(q)
    users = result.scalars().all()

    return {
        "total": total,
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
    }


@router.patch(
    "/users/{user_id}/role",
    summary="Cambiar rol de un usuario",
    responses={404: {"description": "Usuario no encontrado"}},
)
async def cambiar_rol(
    user_id: uuid.UUID,
    role: UserRole,
    _admin: CurrentAdminDep,
    db: DBSessionDep,
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.role = role
    await db.commit()
    return {"id": str(user.id), "email": user.email, "role": user.role.value}


# ──────────────────── Alertas ────────────────────


@router.delete(
    "/alerts/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una alerta",
    responses={404: {"description": "Alerta no encontrada"}},
)
async def eliminar_alerta(
    alert_id: uuid.UUID,
    _admin: CurrentAdminDep,
    db: DBSessionDep,
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alerta = result.scalar_one_or_none()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    await db.delete(alerta)
    await db.commit()


# ──────────────────── Mensajes Mesh ────────────────────


@router.delete(
    "/mesh/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un mensaje mesh",
    responses={404: {"description": "Mensaje no encontrado"}},
)
async def eliminar_mensaje_mesh(
    message_id: uuid.UUID,
    _admin: CurrentAdminDep,
    db: DBSessionDep,
):
    result = await db.execute(select(MeshMessage).where(MeshMessage.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Mensaje mesh no encontrado")

    await db.delete(msg)
    await db.commit()


@router.delete(
    "/mesh",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar todos los mensajes mesh",
)
async def eliminar_todos_mesh(
    _admin: CurrentAdminDep,
    db: DBSessionDep,
):
    await db.execute(delete(MeshMessage))
    await db.commit()
