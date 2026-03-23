import asyncio
import json
import logging
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


async def subscribe(db: AsyncSession, data: SubscriptionCreate) -> PushSubscription:
    """
    Guarda o actualiza una suscripción de notificaciones push en la base de datos.
    Se utiliza un upsert para actualizar las claves en caso de que el endpoint ya exista.
    """
    stmt = insert(PushSubscription).values(
        endpoint=data.endpoint,
        p256dh=data.p256dh,
        auth=data.auth
    ).on_conflict_do_update(
        index_elements=["endpoint"],
        set_={
            "p256dh": data.p256dh,
            "auth": data.auth
        }
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


async def broadcast_critical_alert(db: AsyncSession, alert: Alert) -> None:
    """
    Filtra y envía notificaciones automáticas a todos los suscriptores.
    IMPORTANTE: Solo notifica sobre alertas catalogadas como graves o extremas.
    Limpia automáticamente los endpoints que rechacen con 404 o 410.
    """
    if alert.severity not in (AlertSeverity.SEVERE, AlertSeverity.EXTREME):
        return

    result = await db.execute(select(PushSubscription))
    subscriptions = result.scalars().all()

    if not subscriptions:
        return

    payload = {
        "title": f"¡Alerta {alert.severity.value.upper()} reportada!",
        "body": alert.headline if alert.headline else "Nueva alerta de riesgo detectada.",
        "url": f"/alerts/{alert.id}",
        "icon": "/logo192.png", 
        "badge": "/badge.png"
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
