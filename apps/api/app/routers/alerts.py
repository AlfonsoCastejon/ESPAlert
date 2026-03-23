import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DBSessionDep
from app.models.alert import Alert
from app.models.enums import AlertSeverity, AlertSource, AlertStatus, AlertType
from app.schemas.alerts import AlertListResponse, AlertResponse

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
    limit: Annotated[int, Query(ge=1, le=200, description="Número máximo de resultados")] = 50,
    offset: Annotated[int, Query(ge=0, description="Desplazamiento para paginación")] = 0,
) -> AlertListResponse:
    stmt = select(Alert).where(
        Alert.status == AlertStatus.ACTUAL,
        (Alert.expires_at.is_(None)) | (Alert.expires_at > datetime.now(UTC)),
    )
    stmt = _apply_common_filters(stmt, source, alert_type, severity, bbox)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = await db.scalars(stmt.order_by(Alert.created_at.desc()).limit(limit).offset(offset))
    items = [AlertResponse.model_validate(r) for r in rows.all()]

    return AlertListResponse(total=total or 0, items=items, limit=limit, offset=offset)


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
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AlertListResponse:
    stmt = select(Alert)
    stmt = _apply_common_filters(stmt, source, alert_type, severity, bbox)

    if date_from:
        stmt = stmt.where(Alert.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Alert.created_at <= date_to)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = await db.scalars(stmt.order_by(Alert.created_at.desc()).limit(limit).offset(offset))
    items = [AlertResponse.model_validate(r) for r in rows.all()]

    return AlertListResponse(total=total or 0, items=items, limit=limit, offset=offset)


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Detalle de una alerta",
    responses={
        200: {"description": "Alerta encontrada"},
        404: {"description": "Alerta no encontrada"},
    },
)
async def get_alert_by_id(
    alert_id: uuid.UUID,
    db: DBSessionDep,
) -> AlertResponse:
    row = await db.get(Alert, alert_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta no encontrada")
    return AlertResponse.model_validate(row)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_common_filters(
    stmt,
    source: AlertSource | None,
    alert_type: AlertType | None,
    severity: AlertSeverity | None,
    bbox: str | None,
):
    if source:
        stmt = stmt.where(Alert.source == source)
    if alert_type:
        stmt = stmt.where(Alert.alert_type == alert_type)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    if bbox:
        try:
            min_lon, min_lat, max_lon, max_lat = (float(v) for v in bbox.split(","))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="bbox debe tener el formato: minLon,minLat,maxLon,maxLat",
            ) from exc
        envelope = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        stmt = stmt.where(ST_Intersects(Alert.geometry, envelope))
    return stmt
