"""Endpoints de mensajes Meshtastic: listado y envío."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import DBSessionDep
from app.schemas.mesh_message import MeshMessageListResponse, MeshMessageResponse
from app.services import mesh_service

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
    db: DBSessionDep,
    node_id: Annotated[
        str | None,
        Query(description="Filtrar por identificador hexadecimal del nodo emisor")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=200, description="Número máximo de resultados")] = 50,
    offset: Annotated[int, Query(ge=0, description="Desplazamiento para paginación")] = 0,
) -> MeshMessageListResponse:
    
    total = await mesh_service.get_mesh_messages_count(db, node_id=node_id)
    rows = await mesh_service.get_mesh_messages(db, limit=limit, offset=offset, node_id=node_id)
    
    items = [MeshMessageResponse.model_validate(r) for r in rows]

    return MeshMessageListResponse(total=total, items=items, limit=limit, offset=offset)