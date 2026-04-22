"""Conector Meshtastic: suscripción MQTT para mensajes de la red mesh."""

import json
import logging
import asyncio
import ssl
from typing import Any, Dict
from urllib.parse import urlparse, unquote

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.enums import AlertSource, AlertType, AlertSeverity, AlertStatus
from app.schemas.alert import AlertCreate
from app.schemas.mesh_message import MeshMessageCreate
from app.services.alert_service import upsert_alert
from app.services.mesh_service import save_mesh_message

logger = logging.getLogger(__name__)

class MeshtasticConnector:
    """
    Conector bidireccional MQTT para la red Meshtastic.
    """
    def __init__(self):
        # Utiliza la URL de configuración, con fallback al broker público
        self.broker_url = settings.MQTT_BROKER_URL if settings.MQTT_BROKER_URL else "mqtt://mqtt.meshtastic.org:1883"
        
        # Suscribimos a JSON general de meshes
        self.topic_subscribe = "msh/+/+/json/#"
        self.topic_publish = "msh/espalert/json"
        
        # Instancia del cliente paho-mqtt
        self.client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Para llamar corrutinas desde el hilo de paho-mqtt
        self.loop = None
        self.is_running = False

    async def start(self):
        """
        Inicia la conexión MQTT y lanza un hilo en background.
        paho-mqtt maneja las reconexiones automáticamente.
        Soporta esquemas mqtt:// (plano) y mqtts:// (TLS).
        """
        self.loop = asyncio.get_running_loop()

        url = urlparse(self.broker_url)
        host = url.hostname or "mqtt.meshtastic.org"
        use_tls = url.scheme == "mqtts"
        port = url.port or (8883 if use_tls else 1883)

        if url.username and url.password:
            self.client.username_pw_set(unquote(url.username), unquote(url.password))

        if use_tls:
            self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)

        logger.info(f"MeshtasticConnector: Conectando a broker MQTT en {host}:{port} (TLS={use_tls})...")
        self.client.connect(host, port, keepalive=60)
        
        # Inicia el loop en un thread aparte interno de PAHO
        # Reconectará automáticamente (auto-reconnect está en True por defecto)
        self.client.loop_start()
        self.is_running = True

    async def stop(self):
        """Detiene el cliente MQTT."""
        self.client.loop_stop()
        self.client.disconnect()
        self.is_running = False

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logger.error(f"MeshtasticConnector: Conexión fallida. Código: {reason_code}")
        else:
            logger.info(f"MeshtasticConnector: Conectado. Suscribiendo a {self.topic_subscribe}")
            client.subscribe(self.topic_subscribe, qos=1)

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        logger.warning(f"MeshtasticConnector: Desconectado. Código: {reason_code}. Intentará reconectar...")

    def on_message(self, client, userdata, msg):
        """Callback invocado por paho-mqtt desde su hilo en background."""
        try:
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)
            
            # Se usa run_coroutine_threadsafe porque esto es un thread separado
            if self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(self.process_and_save_message(data), self.loop)

        except json.JSONDecodeError:
            pass  # Ignoramos topics que no devuelvan JSON válido
        except Exception as e:
            logger.error(f"MeshtasticConnector: Excepción en on_message: {e}")

    async def process_and_save_message(self, data: Dict[str, Any]):
        """Parsea el formato del mensaje Meshtastic y lo guarda en BD."""
        try:
            # Extraer payload anidado del frame
            payload = data.get("payload", {})
            message_text = payload.get("text", "")
            
            lat = payload.get("latitude_i")
            if lat is not None:
                lat = lat / 1e7
                
            lon = payload.get("longitude_i")
            if lon is not None:
                lon = lon / 1e7
                
            alt = payload.get("altitude")

            # Solo guardar si hay mensaje de texto o son coordenadas puras
            if not message_text and lat is None:
                return

            mesh_val = MeshMessageCreate(
                node_id=str(data.get("sender", "unknown")),
                channel=str(data.get("channel", "0")),
                packet_id=data.get("id"),
                message=message_text if message_text else "Posición/Señal actualizada",
                latitude=lat,
                longitude=lon,
                altitude=alt,
                snr=data.get("rxSnr"),
                rssi=data.get("rxRssi"),
                raw_payload=data
            )
            
            # Apertura de sesión efímera para guardar el registro asíncronamente
            async with AsyncSessionLocal() as db:
                await save_mesh_message(db, mesh_val)

                # Si el mensaje incluye texto, tambien se crea una Alert para
                # que aparezca en el feed principal con source=meshtastic.
                if message_text:
                    geometry = None
                    if lat is not None and lon is not None:
                        geometry = {"type": "Point", "coordinates": [lon, lat]}

                    alert = AlertCreate(
                        external_id=f"mesh-{data.get('sender', 'unknown')}-{data.get('id', '')}",
                        source=AlertSource.MESHTASTIC,
                        alert_type=AlertType.MESH,
                        severity=AlertSeverity.UNKNOWN,
                        status=AlertStatus.ACTUAL,
                        headline=message_text[:200],
                        description=message_text,
                        area_description=f"Nodo {data.get('sender', 'desconocido')}",
                        geometry=geometry,
                        raw_data=data,
                    )
                    await upsert_alert(db, alert)

                await db.commit()

        except Exception as e:
            logger.error(f"MeshtasticConnector: Fallo al persistir mensaje: {e}")

    def publish_to_mesh(self, message: str) -> bool:
        """
        Publica un mensaje a la red mesh mediante el broker MQTT.
        """
        try:
            payload_json = json.dumps({
                "payload": {"text": message},
                "type": "text"
            })
            info = self.client.publish(self.topic_publish, payload_json, qos=1)
            info.wait_for_publish()
            logger.info(f"MeshtasticConnector: Mensaje publicado en mesh: {message}")
            return True
        except Exception as e:
            logger.error(f"MeshtasticConnector: Error publicando: {e}")
            return False

meshtastic_connector = MeshtasticConnector()
