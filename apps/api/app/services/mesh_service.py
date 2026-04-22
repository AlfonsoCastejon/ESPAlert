"""Servicio Meshtastic: persistencia de mensajes y difusión por WebSocket."""

import asyncio
import logging
from typing import Sequence
from urllib.parse import urlparse

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.alert import Alert
from app.models.enums import AlertSeverity
from app.models.mesh_message import MeshMessage
from app.schemas.mesh_message import MeshMessageCreate

logger = logging.getLogger(__name__)


async def save_mesh_message(db: AsyncSession, data: MeshMessageCreate) -> MeshMessage:
    """
    Guarda un mensaje originado en la red mesh en la base de datos.
    """
    message = MeshMessage(
        node_id=data.node_id,
        channel=data.channel,
        packet_id=data.packet_id,
        message=data.message,
        latitude=data.latitude,
        longitude=data.longitude,
        altitude=data.altitude,
        snr=data.snr,
        rssi=data.rssi,
        raw_payload=data.raw_payload,
        alert_id=data.alert_id
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    logger.info(f"Mensaje mesh guardado correctamente: {message.id}")
    return message


async def get_mesh_messages(db: AsyncSession, limit: int = 50, offset: int = 0, node_id: str | None = None) -> Sequence[MeshMessage]:
    """
    Devuelve los mensajes de la red mesh de forma paginada y ordenados por el más reciente.
    """
    stmt = select(MeshMessage)
    if node_id:
        stmt = stmt.where(MeshMessage.node_id == node_id)
        
    result = await db.execute(
        stmt.order_by(MeshMessage.received_at.desc()).limit(limit).offset(offset)
    )
    return result.scalars().all()

async def get_last_known_position(db: AsyncSession, node_id: str) -> tuple[float, float] | None:
    """Devuelve (lat, lon) del último mensaje con coordenadas del nodo, o None."""
    stmt = (
        select(MeshMessage.latitude, MeshMessage.longitude)
        .where(MeshMessage.node_id == node_id)
        .where(MeshMessage.latitude.is_not(None))
        .where(MeshMessage.longitude.is_not(None))
        .order_by(MeshMessage.received_at.desc())
        .limit(1)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        return None
    return float(row[0]), float(row[1])


async def get_mesh_messages_count(db: AsyncSession, node_id: str | None = None) -> int:
    """Devuelve el total de mensajes para paginación"""
    stmt = select(func.count(MeshMessage.id))
    if node_id:
        stmt = stmt.where(MeshMessage.node_id == node_id)
    return await db.scalar(stmt) or 0


def _publish_mqtt_sync(broker_url: str, topic: str, payload: str) -> bool:
    """
    Publica un mensaje síncrono vía MQTT estándar a la red Mesh.
    Utiliza asyncio.to_thread para no bloquear FastAPI.
    """
    try:
        url = urlparse(broker_url)
        host = url.hostname or "localhost"
        port = url.port or 1883

        client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        
        # Soportar autenticación si la URL la incluye (e.g. mqtt://usuario:pass@broker)
        if url.username and url.password:
            client.username_pw_set(url.username, url.password)

        client.connect(host, port, 60)
        client.loop_start()
        
        # QoS 1 para asegurar la entrega
        info = client.publish(topic, payload, qos=1)
        info.wait_for_publish()
        
        client.loop_stop()
        client.disconnect()
        return True
    except Exception as e:
        logger.error(f"Error publicando alerta a mesh vía MQTT ({broker_url}): {e}")
        return False


async def publish_alert_to_mesh(alert: Alert) -> bool:
    """
    Publica una alerta crítica en la red mesh vía MQTT.
    Solo alerta si la severidad es 'orange' (SEVERE) o 'red' (EXTREME).
    """
    if alert.severity not in (AlertSeverity.SEVERE, AlertSeverity.EXTREME):
        logger.info(f"Omitiendo publicación mesh para alerta {alert.id}; no es de severidad crítica.")
        return False

    settings = get_settings()
    
    # Formatear el contenido en texto plano y corto dado las limitaciones por radio (LoRa/Mesh)
    headline = alert.headline[:150] if alert.headline else "Nueva alerta de riesgo detectada."
    payload = f"ALERTA {alert.severity.value.upper()}: {headline}"
    
    # Topic estándar del sistema mesh para difundir
    topic = "msh/espalert/alerts"

    logger.info(f"Publicando alerta crítica en Mesh: {payload}")
    
    success = await asyncio.to_thread(_publish_mqtt_sync, settings.MQTT_BROKER_URL, topic, payload)
    return success
