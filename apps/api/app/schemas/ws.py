import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.enums import AlertSeverity, AlertSource, AlertType


class WsAlertPayload(BaseModel):
    """Payload incluido en eventos de tipo alert.*"""

    id: uuid.UUID
    source: AlertSource
    alert_type: AlertType
    severity: AlertSeverity
    headline: str
    area_description: str | None = None


class WsEvent(BaseModel):
    """Mensaje emitido por el servidor a través del WebSocket.

    Tipos de evento:
    - ``alert.new``     — nueva alerta insertada en la base de datos.
    - ``alert.updated`` — alerta existente modificada.
    - ``alert.expired`` — alerta marcada como expirada.
    - ``ping``          — latido periódico del servidor (sin data).
    """

    event: Literal["alert.new", "alert.updated", "alert.expired", "ping"] = Field(
        ...,
        description="Tipo de evento WebSocket",
    )
    data: Any | None = Field(
        default=None,
        description="Payload del evento; estructura depende del tipo de evento",
    )
    timestamp: datetime = Field(
        ...,
        description="Instante UTC en que el servidor generó el evento",
    )
