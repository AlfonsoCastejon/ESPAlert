import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MeshMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    node_id: str
    channel: str | None = None
    packet_id: int | None = None
    message: str
    latitude: float | None = None
    longitude: float | None = None
    altitude: int | None = None
    snr: float | None = None
    rssi: int | None = None
    received_at: datetime
    alert_id: uuid.UUID | None = None


class MeshMessageListResponse(BaseModel):
    total: int
    items: list[MeshMessageResponse]
    limit: int = Field(default=50)
    offset: int = Field(default=0)
