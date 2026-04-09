"""Endpoint de health check para monitorización y despliegue."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DBSessionDep
from app.models.enums import AlertSource, FetchStatus
from app.models.fetch_log import FetchLog
from app.schemas.fetch_log import HealthResponse, SourceHealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Estado de la API y fuentes de datos",
    description=(
        "Devuelve el estado general de la API y el resultado del último "
        "ciclo de ingesta para cada fuente de datos configurada."
    ),
    responses={
        200: {"description": "Estado actual de la API y de cada fuente"},
    },
)
async def get_health(
    db: DBSessionDep,
) -> HealthResponse:
    sources_health: list[SourceHealthResponse] = []

    for source in AlertSource:
        # Obtener el registro de fetch más reciente para esta fuente
        latest = await db.scalar(
            select(FetchLog)
            .where(FetchLog.source == source)
            .order_by(FetchLog.started_at.desc())
            .limit(1)
        )

        if latest:
            sources_health.append(
                SourceHealthResponse(
                    source=source,
                    status=latest.status,
                    last_run=latest.started_at,
                    alerts_new=latest.alerts_new,
                    error_message=latest.error_message,
                )
            )
        else:
            sources_health.append(
                SourceHealthResponse(
                    source=source,
                    status=FetchStatus.RUNNING,
                    last_run=None,
                    alerts_new=0,
                    error_message=None,
                )
            )

    return HealthResponse(api="ok", sources=sources_health)
