import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import AlertSeverity, AlertSource, AlertStatus, AlertType


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_id: str | None = None
    source: AlertSource
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    headline: str
    description: str | None = None
    area_description: str | None = None
    geometry: Any | None = Field(default=None, description="GeoJSON geometry object")
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    fetched_at: datetime
    created_at: datetime

    @model_validator(mode="after")
    def _serialize_geometry(self) -> "AlertResponse":
        """Convierte WKBElement de GeoAlchemy2 a GeoJSON dict."""
        geom = self.geometry
        if geom is not None and hasattr(geom, "data"):
            try:
                from geoalchemy2.shape import to_shape
                from shapely.geometry import mapping

                self.geometry = mapping(to_shape(geom))
            except Exception:
                self.geometry = None
        return self


class AlertListResponse(BaseModel):
    total: int
    items: list[AlertResponse]
    limit: int
    offset: int
