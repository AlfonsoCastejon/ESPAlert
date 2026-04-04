import uuid
from datetime import datetime

from sqlalchemy import Enum, Integer, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import AlertSource, FetchStatus


class FetchLog(Base):
    __tablename__ = "fetch_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    source: Mapped[AlertSource] = mapped_column(
        Enum(AlertSource, name="alert_source", create_type=False,
             values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        index=True,
        comment="Fuente de datos consultada",
    )
    status: Mapped[FetchStatus] = mapped_column(
        Enum(FetchStatus, name="fetch_status", create_type=True,
             values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=FetchStatus.RUNNING,
    )
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        index=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    alerts_fetched: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Total de alertas obtenidas de la fuente",
    )
    alerts_new: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Alertas nuevas insertadas en esta ejecución",
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Duración total de la consulta en milisegundos",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Mensaje de error si el estado es FAILURE o PARTIAL",
    )

    def __repr__(self) -> str:
        return f"<FetchLog id={self.id} source={self.source} status={self.status}>"
