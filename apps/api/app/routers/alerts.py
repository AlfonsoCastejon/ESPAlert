"""Endpoints REST de alertas: listado activo, historial y detalle."""

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import DBSessionDep
from app.models.alert import Alert
from app.models.enums import AlertSeverity, AlertSource, AlertStatus, AlertType
from app.schemas.alert import AlertListResponse, AlertResponse, AlertGeoJSON
from app.services import alert_service
from app.utils.regions import Region

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get(
    "",
    response_model=AlertListResponse,
    summary="Alertas activas",
    description=(
        "Devuelve las alertas actuales con filtros opcionales. "
        "Por defecto solo incluye alertas en estado ACTUAL cuyo `expires_at` no ha pasado."
    ),
    responses={
        200: {"description": "Lista de alertas filtrada"},
        422: {"description": "Parámetros de consulta inválidos"},
    },
)
async def get_active_alerts(
    db: DBSessionDep,
    source: Annotated[AlertSource | None, Query(description="Fuente de datos")] = None,
    alert_type: Annotated[AlertType | None, Query(description="Tipo de alerta")] = None,
    severity: Annotated[AlertSeverity | None, Query(description="Nivel de severidad")] = None,
    bbox: Annotated[
        str | None,
        Query(
            description="Bounding box geográfica: minLon,minLat,maxLon,maxLat (WGS84)",
            examples=["minLon,minLat,maxLon,maxLat"],
        ),
    ] = None,
    region: Annotated[
        Region | None,
        Query(description="Comunidad autónoma (aplica su bounding box)"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=200, description="Número máximo de resultados")] = 50,
    offset: Annotated[int, Query(ge=0, description="Desplazamiento para paginación")] = 0,
) -> AlertListResponse:
    filters = {
        "source": source,
        "alert_type": alert_type,
        "severity": severity,
        "bbox": bbox,
        "region": region,
    }
    
    try:
        total, rows = await alert_service.get_active_alerts(db, filters, limit, offset)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="bbox debe tener el formato: minLon,minLat,maxLon,maxLat",
        ) from exc

    items = [AlertGeoJSON.model_validate(r) for r in rows]

    return AlertListResponse(total=total, items=items, limit=limit, offset=offset)


@router.get(
    "/history",
    response_model=AlertListResponse,
    summary="Historial de alertas",
    description="Devuelve todas las alertas sin filtrar por estado de expiración.",
    responses={
        200: {"description": "Lista histórica de alertas"},
        422: {"description": "Parámetros de consulta inválidos"},
    },
)
async def get_alert_history(
    db: DBSessionDep,
    source: Annotated[AlertSource | None, Query(description="Fuente de datos")] = None,
    alert_type: Annotated[AlertType | None, Query(description="Tipo de alerta")] = None,
    severity: Annotated[AlertSeverity | None, Query(description="Nivel de severidad")] = None,
    date_from: Annotated[
        datetime | None, Query(description="Inicio del rango temporal (ISO 8601)")
    ] = None,
    date_to: Annotated[
        datetime | None, Query(description="Fin del rango temporal (ISO 8601)")
    ] = None,
    bbox: Annotated[str | None, Query(description="Bounding box: minLon,minLat,maxLon,maxLat")] = None,
    region: Annotated[
        Region | None,
        Query(description="Comunidad autónoma (aplica su bounding box)"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AlertListResponse:
    filters = {
        "source": source,
        "alert_type": alert_type,
        "severity": severity,
        "bbox": bbox,
        "region": region,
        "date_from": date_from,
        "date_to": date_to,
    }

    try:
        total, rows = await alert_service.get_alert_history(db, filters, limit, offset)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="bbox debe tener el formato: minLon,minLat,maxLon,maxLat",
        ) from exc

    items = [AlertGeoJSON.model_validate(r) for r in rows]

    return AlertListResponse(total=total, items=items, limit=limit, offset=offset)


@router.get(
    "/{alert_id}",
    response_model=AlertGeoJSON,
    summary="Detalle de una alerta",
    responses={
        200: {"description": "Alerta encontrada"},
        404: {"description": "Alerta no encontrada"},
    },
)
async def get_alert_by_id(
    alert_id: uuid.UUID,
    db: DBSessionDep,
) -> AlertGeoJSON:
    row = await alert_service.get_alert_by_id(db, alert_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta no encontrada")
    return AlertGeoJSON.model_validate(row)
