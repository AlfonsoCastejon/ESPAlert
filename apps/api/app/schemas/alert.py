import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import AlertSeverity, AlertSource, AlertStatus, AlertType


class AlertCreate(BaseModel):
    external_id: str | None = None
    source: AlertSource
    alert_type: AlertType
    severity: AlertSeverity = Field(default=AlertSeverity.UNKNOWN)
    status: AlertStatus = Field(default=AlertStatus.ACTUAL)
    headline: str
    description: str | None = None
    area_description: str | None = None
    geometry: Any | None = None
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    raw_data: dict[str, Any] | None = None


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
    geometry: Any | None = Field(default=None, description="Raw geometry")
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    fetched_at: datetime
    created_at: datetime


class AlertGeoJSON(AlertResponse):
    """Schema para devolver una alerta con su geometría pre-serializada en GeoJSON."""
    
    @model_validator(mode="after")
    def _serialize_geometry(self) -> "AlertGeoJSON":
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
    items: list[AlertGeoJSON]
    limit: int
    offset: int
