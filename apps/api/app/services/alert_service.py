"""Servicio de alertas: consultas, upsert y expiración automática."""

import json
import logging
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

logger = logging.getLogger(__name__)

_MESH_SEVERIDADES = {AlertSeverity.SEVERE, AlertSeverity.EXTREME}


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


def _construir_select_listado():
    # ST_AsGeoJSON en SQL evita serializar WKB en Python por cada fila.
    cols = [c for c in Alert.__table__.columns if c.name != "geometry"]
    return select(*cols, func.ST_AsGeoJSON(Alert.geometry).label("geometry_json"))


async def _materializar_filas(db: AsyncSession, stmt) -> list[dict[str, Any]]:
    result = await db.execute(stmt)
    filas: list[dict[str, Any]] = []
    for fila in result.mappings().all():
        d = dict(fila)
        gj = d.pop("geometry_json", None)
        d["geometry"] = json.loads(gj) if gj else None
        filas.append(d)
    return filas


async def get_active_alerts(
    db: AsyncSession,
    filters: dict[str, Any],
    limit: int = 50,
    offset: int = 0,
    order_by: str | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    """Devuelve alertas activas (no expiradas) aplicando los filtros recibidos."""
    base = select(Alert).where(
        Alert.status == AlertStatus.ACTUAL,
        (Alert.expires_at.is_(None)) | (Alert.expires_at > datetime.now(UTC)),
    )
    base = _apply_common_filters(base, filters)

    total = await db.scalar(select(func.count()).select_from(base.subquery())) or 0

    listado = _construir_select_listado().where(
        Alert.status == AlertStatus.ACTUAL,
        (Alert.expires_at.is_(None)) | (Alert.expires_at > datetime.now(UTC)),
    )
    listado = _apply_common_filters(listado, filters)
    listado = _aplicar_orden(listado, order_by).limit(limit).offset(offset)
    return total, await _materializar_filas(db, listado)


async def get_alert_history(
    db: AsyncSession,
    filters: dict[str, Any],
    limit: int = 50,
    offset: int = 0,
    order_by: str | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    """Devuelve el historial completo de alertas, sin filtrar por estado."""
    base = _apply_common_filters(select(Alert), filters)

    date_from = filters.get("date_from")
    if date_from:
        base = base.where(Alert.created_at >= date_from)
    date_to = filters.get("date_to")
    if date_to:
        base = base.where(Alert.created_at <= date_to)

    total = await db.scalar(select(func.count()).select_from(base.subquery())) or 0

    listado = _apply_common_filters(_construir_select_listado(), filters)
    if date_from:
        listado = listado.where(Alert.created_at >= date_from)
    if date_to:
        listado = listado.where(Alert.created_at <= date_to)
    listado = _aplicar_orden(listado, order_by).limit(limit).offset(offset)
    return total, await _materializar_filas(db, listado)

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
        _notificar_mesh_si_procede(alert, es_nueva=True)
        await _notificar_push_si_procede(db, alert)
        return alert

    existente = await db.scalar(
        select(Alert).where(Alert.external_id == data_dict["external_id"])
    )
    es_nueva = existente is None
    severidad_previa = existente.severity if existente is not None else None

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

    if result is not None:
        escalada = (
            not es_nueva
            and severidad_previa not in _MESH_SEVERIDADES
            and result.severity in _MESH_SEVERIDADES
        )
        if es_nueva or escalada:
            _notificar_mesh_si_procede(result, es_nueva=es_nueva)
            await _notificar_push_si_procede(db, result)

    return result


async def _notificar_push_si_procede(db: AsyncSession, alert: Alert) -> None:
    # Envía push web a los suscriptores. broadcast_critical_alert filtra por
    # severidad y preferencias. Falla en silencio para no romper el upsert.
    try:
        from app.services import push_service

        await push_service.broadcast_critical_alert(db, alert)
    except Exception as exc:
        logger.warning(f"No se pudieron enviar notificaciones push: {exc}")


def _notificar_mesh_si_procede(alert: Alert, *, es_nueva: bool) -> None:
    # Difusión solo en alertas nuevas o escaladas, y nunca si la fuente es mesh.
    if alert.source == AlertSource.MESHTASTIC:
        return
    if alert.severity not in _MESH_SEVERIDADES:
        return
    try:
        from app.connectors.meshtastic import meshtastic_connector

        nivel = "EXTREMO" if alert.severity == AlertSeverity.EXTREME else "SEVERO"
        fuente = alert.source.value.upper() if alert.source else "ALERTA"
        prefijo = "NUEVA" if es_nueva else "ESCALADA"
        titulo = (alert.headline or "Alerta")[:120]
        meshtastic_connector.publish_to_mesh(f"[{prefijo} {nivel}] {fuente}: {titulo}")
    except Exception as exc:
        logger.warning(f"No se pudo notificar a la red mesh: {exc}")

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
