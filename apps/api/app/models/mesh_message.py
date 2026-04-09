"""Modelo de mensaje recibido por la red Meshtastic vía MQTT."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Float, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.alert import Alert


class MeshMessage(Base):
    __tablename__ = "mesh_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    alert_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Alerta asociada si el mensaje ha generado o está vinculado a una alerta",
    )
    node_id: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="Identificador hexadecimal del nodo Meshtastic emisor",
    )
    channel: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="Canal del nodo en la red mesh",
    )
    packet_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="ID de paquete asignado por el protocolo Meshtastic",
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Contenido del mensaje recibido",
    )
    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Latitud del nodo emisor en WGS84",
    )
    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Longitud del nodo emisor en WGS84",
    )
    altitude: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Altitud del nodo emisor en metros",
    )
    snr: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Relación señal/ruido (dB) en el momento de la recepción",
    )
    rssi: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Intensidad de señal recibida (dBm)",
    )
    received_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        index=True,
    )
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Payload MQTT completo sin procesar",
    )

    alert: Mapped[Alert | None] = relationship(
        "Alert",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<MeshMessage id={self.id} node_id={self.node_id}>"
