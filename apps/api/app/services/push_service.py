"""Servicio de notificaciones push vía Web Push Protocol (VAPID)."""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict

from pywebpush import webpush, WebPushException
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.alert import Alert
from app.models.enums import AlertSeverity
from app.models.push_subscription import PushSubscription
from app.schemas.push_subscription import SubscriptionCreate


logger = logging.getLogger(__name__)


async def subscribe(
    db: AsyncSession,
    data: SubscriptionCreate,
    user_id: uuid.UUID | None = None,
) -> PushSubscription:
    """
    Guarda o actualiza una suscripción de notificaciones push en la base de datos.
    Se utiliza un upsert para actualizar las claves en caso de que el endpoint ya exista.
    """
    valores = {
        "endpoint": data.endpoint,
        "p256dh": data.p256dh,
        "auth": data.auth,
    }
    if user_id is not None:
        valores["user_id"] = user_id

    set_dict = {"p256dh": data.p256dh, "auth": data.auth}
    if user_id is not None:
        set_dict["user_id"] = user_id

    stmt = insert(PushSubscription).values(**valores).on_conflict_do_update(
        index_elements=["endpoint"],
        set_=set_dict,
    ).returning(PushSubscription)

    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()


async def unsubscribe(db: AsyncSession, endpoint: str) -> bool:
    """
    Elimina una suscripción de notificaciones push utilizando su endpoint.
    """
    stmt = delete(PushSubscription).where(PushSubscription.endpoint == endpoint)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


def _send_push_sync(subscription: PushSubscription, payload: str, vapid_private_key: str) -> bool:
    """
    Envía de manera síncrona la notificación push usando pywebpush.
    Retorna True si fue exitoso, y False si el endpoint expiró (404/410).
    """
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth
                }
            },
            data=payload,
            vapid_private_key=vapid_private_key,
            vapid_claims={
                "sub": "mailto:contacto@espalert.es"
            }
        )
        return True
    except WebPushException as ex:
        # Los códigos 404 y 410 indican que la suscripción ha expirado/es inválida
        if ex.response is not None and ex.response.status_code in (404, 410):
            logger.warning(f"Suscripción push inactiva o expirada: {subscription.endpoint}")
            return False
        
        logger.error(f"Error al enviar push a {subscription.endpoint}: {ex}")
        return True
    except Exception as e:
        logger.error(f"Error desconocido enviando push a {subscription.endpoint}: {e}")
        return True


async def send_notification(subscription: PushSubscription, payload: Dict[str, Any]) -> bool:
    """
    Envía una notificación push de forma asíncrona.
    """
    settings = get_settings()
    vapid_key = settings.VAPID_PRIVATE_KEY
    if hasattr(vapid_key, "get_secret_value"):
        vapid_key = vapid_key.get_secret_value()

    data_str = json.dumps(payload)
    success = await asyncio.to_thread(_send_push_sync, subscription, data_str, vapid_key)
    return success


_NOMBRE_FUENTE = {
    "aemet": "AEMET",
    "ign": "IGN",
    "dgt": "DGT",
    "meteoalarm": "MeteoAlarm",
    "meshtastic": "Meshtastic",
}

_NOMBRE_SEVERIDAD = {
    "severe": "severa",
    "extreme": "extrema",
}

_NOMBRE_REGION = {
    "andalucia": "Andalucía", "aragon": "Aragón", "asturias": "Asturias",
    "baleares": "Baleares", "canarias": "Canarias", "cantabria": "Cantabria",
    "castilla-la-mancha": "Castilla-La Mancha", "castilla-y-leon": "Castilla y León",
    "cataluna": "Cataluña", "ceuta": "Ceuta", "extremadura": "Extremadura",
    "galicia": "Galicia", "la-rioja": "La Rioja", "madrid": "Madrid",
    "melilla": "Melilla", "murcia": "Murcia", "navarra": "Navarra",
    "pais-vasco": "País Vasco", "valencia": "Comunidad Valenciana",
}


async def _describir_zona(db: AsyncSession, alert: Alert) -> str:
    """Devuelve una descripción de la zona de la alerta: el área que indica la
    fuente si existe, o la comunidad autónoma deducida del centroide.
    """
    if alert.area_description:
        return alert.area_description

    if alert.geometry is None:
        return "España"

    from sqlalchemy import func
    from app.utils.regions import REGION_BBOX

    try:
        punto = await db.scalar(func.ST_AsText(func.ST_Centroid(alert.geometry)))
        # Formato "POINT(lon lat)"
        coords = punto.replace("POINT(", "").replace(")", "").split()
        lon, lat = float(coords[0]), float(coords[1])
        for region, (min_lon, min_lat, max_lon, max_lat) in REGION_BBOX.items():
            if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
                return _NOMBRE_REGION.get(region.value, region.value)
    except Exception:
        pass
    return "España"


async def broadcast_critical_alert(db: AsyncSession, alert: Alert) -> None:
    """
    Envía notificaciones a las suscripciones cuyo usuario tenga la severidad y la
    región solicitadas. Las suscripciones sin usuario asociado (legacy) reciben
    todas las alertas severas o extremas. Limpia endpoints caducados (404/410).
    """
    if alert.severity not in (AlertSeverity.SEVERE, AlertSeverity.EXTREME):
        return

    from app.models.user_preferences import UserPreferences
    from app.utils.regions import REGION_BBOX, Region
    from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope
    from sqlalchemy.orm import selectinload

    stmt = select(PushSubscription).options(
        selectinload(PushSubscription.user).selectinload("preferences"),
    ) if False else select(PushSubscription)

    result = await db.execute(stmt)
    todas = result.scalars().all()
    if not todas:
        return

    # Cargar preferencias de los usuarios afectados (los que tienen user_id).
    user_ids = [s.user_id for s in todas if s.user_id is not None]
    prefs_por_usuario: dict = {}
    if user_ids:
        pref_rows = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id.in_(user_ids))
        )
        for p in pref_rows.scalars().all():
            prefs_por_usuario[p.user_id] = p

    # Decide a qué suscripciones notificar.
    severidad_actual = alert.severity.value
    subscriptions = []
    for sub in todas:
        if sub.user_id is None:
            # Suscripción legacy sin usuario: comportamiento previo, recibe.
            subscriptions.append(sub)
            continue
        prefs = prefs_por_usuario.get(sub.user_id)
        if prefs is None:
            subscriptions.append(sub)
            continue

        # Filtro de severidades del usuario (si está definido).
        sevs = (prefs.filters or {}).get("severidades")
        if isinstance(sevs, dict):
            permitido = bool(sevs.get(severidad_actual, False))
            if not permitido:
                continue

        # Filtro de región: si el usuario eligió región, la alerta debe intersectar su bbox.
        if prefs.region:
            try:
                region = Region(prefs.region)
                min_lon, min_lat, max_lon, max_lat = REGION_BBOX[region]
                envelope = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
                intersecta = await db.scalar(
                    select(ST_Intersects(alert.geometry, envelope))
                )
                if not intersecta:
                    continue
            except (ValueError, KeyError):
                pass  # Región desconocida: no filtrar por región.

        subscriptions.append(sub)

    if not subscriptions:
        return

    zona = await _describir_zona(db, alert)
    fuente = _NOMBRE_FUENTE.get(alert.source.value, alert.source.value.upper()) if alert.source else "Fuente desconocida"
    severidad = _NOMBRE_SEVERIDAD.get(alert.severity.value, alert.severity.value)

    payload = {
        "titulo": f"Nueva alerta {severidad}",
        "cuerpo": f"{zona} - {fuente}: {alert.headline}" if alert.headline else f"{zona} - {fuente}",
        "url": "/alertas",
        "icon": "/icon.png",
        "badge": "/icon.png",
    }

    # Enviar notificaciones de forma concurrente para mayor escalabilidad
    tasks = [send_notification(sub, payload) for sub in subscriptions]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    expired_endpoints = []
    for sub, success in zip(subscriptions, results):
        if success is False: # False indica que la suscripción expiró (404/410)
            expired_endpoints.append(sub.endpoint)
        elif isinstance(success, Exception):
            logger.error(f"Error no controlado en la tarea push para {sub.endpoint}: {success}")

    if expired_endpoints:
        del_stmt = delete(PushSubscription).where(PushSubscription.endpoint.in_(expired_endpoints))
        await db.execute(del_stmt)
        await db.commit()
        logger.info(f"Limpieza de notificaciones: {len(expired_endpoints)} endpoints caducados han sido eliminados.")
