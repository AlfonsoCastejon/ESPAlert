import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AlertSource, FetchStatus


class FetchLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: AlertSource
    status: FetchStatus
    started_at: datetime
    finished_at: datetime | None = None
    alerts_fetched: int
    alerts_new: int
    duration_ms: int | None = None
    error_message: str | None = None


class SourceHealthResponse(BaseModel):
    source: AlertSource
    status: FetchStatus
    last_run: datetime | None = None
    alerts_new: int
    error_message: str | None = None


class HealthResponse(BaseModel):
    api: str
    sources: list[SourceHealthResponse]
