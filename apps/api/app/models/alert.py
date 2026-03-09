import uuid
from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import Enum, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import AlertSeverity, AlertSource, AlertStatus, AlertType


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="Identificador original en la fuente externa",
    )
    source: Mapped[AlertSource] = mapped_column(
        Enum(AlertSource, name="alert_source", create_type=True),
        nullable=False,
        index=True,
    )
    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, name="alert_type", create_type=True),
        nullable=False,
        index=True,
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alert_severity", create_type=True),
        nullable=False,
        default=AlertSeverity.UNKNOWN,
        index=True,
    )
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, name="alert_status", create_type=True),
        nullable=False,
        default=AlertStatus.ACTUAL,
    )
    headline: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    area_description: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    geometry: Mapped[Any | None] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, nullable=True),
        nullable=True,
        comment="Geometría del área de la alerta (punto, polígono o multipolígono) en WGS84",
    )
    effective_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        index=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        index=True,
    )
    fetched_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Payload original sin procesar de la fuente",
    )

    __table_args__ = (
        Index("ix_alerts_geometry", "geometry", postgresql_using="gist"),
        Index("ix_alerts_source_severity", "source", "severity"),
        Index("ix_alerts_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<Alert id={self.id} source={self.source} severity={self.severity}>"
