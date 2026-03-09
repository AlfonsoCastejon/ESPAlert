import uuid
from datetime import datetime

from sqlalchemy import Text, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    endpoint: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        index=True,
        comment="URL del endpoint del servicio push del navegador",
    )
    p256dh: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Clave pública del cliente para cifrado ECDH",
    )
    auth: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Secreto de autenticación del cliente",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<PushSubscription id={self.id} endpoint={self.endpoint[:40]}...>"
