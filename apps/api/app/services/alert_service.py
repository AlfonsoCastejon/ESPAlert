"""Servicio de alertas: consultas, upsert y expiración automática."""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope
from sqlalchemy import case, func, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.enums import AlertSeverity, AlertSource, AlertStatus, AlertType
from app.schemas.alert import AlertCreate
from app.utils.regions import REGION_BBOX, Region


def _geojson_to_wke(geom: Any) -> Any:
    """Convierte un dict GeoJSON a una expresión SQL ST_GeomFromGeoJSON."""
    if isinstance(geom, dict):
        return func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps(geom)), 4326)
    return geom

_ORDEN_SEVERIDAD = case(
    {
        AlertSeverity.EXTREME: 0,
        AlertSeverity.SEVERE: 1,
        AlertSeverity.MODERATE: 2,
        AlertSeverity.MINOR: 3,
    },
    value=Alert.severity,
    else_=4,
)


def _aplicar_orden(stmt, order_by: str | None):
    """Aplica el criterio de ordenación. 'severity' usa un CASE y desempata por fecha."""
    if order_by == "severity":
        return stmt.order_by(_ORDEN_SEVERIDAD.asc(), Alert.created_at.desc())
    return stmt.order_by(Alert.created_at.desc())


async def get_active_alerts(
    db: AsyncSession,
    filters: dict[str, Any],
    limit: int = 50,
    offset: int = 0,
    order_by: str | None = None,
) -> tuple[int, list[Alert]]:
    """Devuelve alertas activas (no expiradas) aplicando los filtros recibidos."""
    stmt = select(Alert).where(
        Alert.status == AlertStatus.ACTUAL,
        (Alert.expires_at.is_(None)) | (Alert.expires_at > datetime.now(UTC)),
    )
    stmt = _apply_common_filters(stmt, filters)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    total = total or 0

    stmt = _aplicar_orden(stmt, order_by).limit(limit).offset(offset)
    rows = await db.scalars(stmt)
    return total, list(rows.all())

async def get_alert_history(
    db: AsyncSession,
    filters: dict[str, Any],
    limit: int = 50,
    offset: int = 0,
    order_by: str | None = None,
) -> tuple[int, list[Alert]]:
    """Devuelve el historial completo de alertas, sin filtrar por estado."""
    stmt = select(Alert)
    stmt = _apply_common_filters(stmt, filters)

    date_from = filters.get("date_from")
    if date_from:
        stmt = stmt.where(Alert.created_at >= date_from)

    date_to = filters.get("date_to")
    if date_to:
        stmt = stmt.where(Alert.created_at <= date_to)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    total = total or 0

    stmt = _aplicar_orden(stmt, order_by).limit(limit).offset(offset)
    rows = await db.scalars(stmt)
    return total, list(rows.all())

async def get_alert_by_id(db: AsyncSession, alert_id: uuid.UUID) -> Alert | None:
    """Busca una alerta por su UUID. Devuelve None si no existe."""
    return await db.get(Alert, alert_id)

async def upsert_alert(db: AsyncSession, alert_data: AlertCreate) -> Alert:
    """Inserta una alerta o la actualiza automáticamente si el external_id ya existe."""
    data_dict = alert_data.model_dump(exclude_unset=True)

    if "geometry" in data_dict and data_dict["geometry"] is not None:
        data_dict["geometry"] = _geojson_to_wke(data_dict["geometry"])

    if not data_dict.get("external_id"):
        alert = Alert(**data_dict)
        db.add(alert)
        await db.flush()
        return alert

    stmt = insert(Alert).values(**data_dict)
    
    # Excluimos la id y la fecha de creación en caso de que sea un update
    update_dict = {
        c.name: c
        for c in stmt.excluded
        if c.name not in ["id", "created_at", "external_id"]
    }
    
    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=["external_id"],
        set_=update_dict
    ).returning(Alert)
    
    result = await db.scalar(upsert_stmt)
    await db.flush()
    return result

async def expire_old_alerts(db: AsyncSession) -> int:
    """Marca como expiradas aquellas alertas que ya pasaron su fecha natural
    o están activas indefinidamente y pasaron de un umbral de obsolescencia.
    """
    now = datetime.now(UTC)
    stmt = (
        update(Alert)
        .where(
            Alert.status == AlertStatus.ACTUAL,
            Alert.expires_at < now
        )
        .values(status=AlertStatus.EXPIRED) 
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount

def _apply_common_filters(stmt, filters: dict[str, Any]):
    """Aplica filtros de fuente, tipo, severidad y zona geográfica al query."""
    if source := filters.get("source"):
        stmt = stmt.where(Alert.source == source)
    if alert_type := filters.get("alert_type"):
        stmt = stmt.where(Alert.alert_type == alert_type)
    if severity := filters.get("severity"):
        stmt = stmt.where(Alert.severity == severity)
    if bbox := filters.get("bbox"):
        # Se asume que el input ha sido validado (por ej. en el router o schema)
        # o que lanzará ValueError si no son 4 floats válidos.
        min_lon, min_lat, max_lon, max_lat = (float(v) for v in bbox.split(","))
        envelope = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        stmt = stmt.where(ST_Intersects(Alert.geometry, envelope))
    # Si nos pasan una CCAA y no hay bbox explícito, usamos su bounding box.
    # El bbox explícito tiene prioridad porque permite zooms más finos.
    elif region := filters.get("region"):
        if isinstance(region, str):
            region = Region(region)
        min_lon, min_lat, max_lon, max_lat = REGION_BBOX[region]
        envelope = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        stmt = stmt.where(ST_Intersects(Alert.geometry, envelope))
    return stmt
