from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.mesh_message import MeshMessage
from app.schemas.mesh_message import MeshMessageListResponse, MeshMessageResponse

router = APIRouter(prefix="/mesh", tags=["mesh"])


@router.get(
    "/messages",
    response_model=MeshMessageListResponse,
    summary="Mensajes de la red mesh",
    description=(
        "Devuelve los mensajes recibidos desde nodos Meshtastic LoRa. "
        "Se pueden filtrar por identificador de nodo y paginar con limit/offset."
    ),
    responses={
        200: {"description": "Lista de mensajes mesh"},
        422: {"description": "Parámetros de consulta inválidos"},
    },
)
async def get_mesh_messages(
    db: Annotated[AsyncSession, Depends(get_db)],
    node_id: Annotated[
        str | None,
        Query(description="Filtrar por identificador hexadecimal del nodo emisor"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=200, description="Número máximo de resultados")] = 50,
    offset: Annotated[int, Query(ge=0, description="Desplazamiento para paginación")] = 0,
) -> MeshMessageListResponse:
    stmt = select(MeshMessage)

    if node_id:
        stmt = stmt.where(MeshMessage.node_id == node_id)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = await db.scalars(
        stmt.order_by(MeshMessage.received_at.desc()).limit(limit).offset(offset)
    )
    items = [MeshMessageResponse.model_validate(r) for r in rows.all()]

    return MeshMessageListResponse(total=total or 0, items=items, limit=limit, offset=offset)
