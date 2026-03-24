"""Connector for IGN (Instituto Geográfico Nacional) seismic alerts."""

from datetime import UTC, datetime

import httpx

from app.connectors.base import BaseConnector
from app.models.enums import AlertSeverity, AlertSource, AlertStatus, AlertType
from app.schemas.alert import AlertCreate
from app.services import alert_service

# IGN real-time earthquake catalogue (last ~30 days, GeoJSON)
_IGN_URL = "https://www.ign.es/web/resources/sismologia/tproximos/terremotos.geojson"

# Richter/Mw magnitude thresholds → severity levels
_MAGNITUDE_SEVERITY: list[tuple[float, AlertSeverity]] = [
    (6.0, AlertSeverity.EXTREME),
    (5.0, AlertSeverity.SEVERE),
    (4.0, AlertSeverity.MODERATE),
    (2.5, AlertSeverity.MINOR),
]


def _magnitude_to_severity(magnitude: float | None) -> AlertSeverity:
    if magnitude is None:
        return AlertSeverity.UNKNOWN
    for threshold, severity in _MAGNITUDE_SEVERITY:
        if magnitude >= threshold:
            return severity
    return AlertSeverity.MINOR


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class IGNConnector(BaseConnector):
    """Fetches recent seismic events from the IGN GeoJSON catalogue."""

    source = AlertSource.IGN

    async def _fetch(self) -> tuple[int, int]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(_IGN_URL)
            resp.raise_for_status()
            geojson = resp.json()

        features: list[dict] = geojson.get("features", [])
        alerts_fetched = len(features)
        alerts_new = 0

        for feature in features:
            props: dict = feature.get("properties", {})
            geometry_raw: dict | None = feature.get("geometry")

            event_id = str(props.get("cod") or props.get("id") or "")
            magnitude: float | None = props.get("mag")
            if magnitude is not None:
                try:
                    magnitude = float(magnitude)
                except (TypeError, ValueError):
                    magnitude = None

            mag_str = f"M{magnitude}" if magnitude is not None else ""
            location = props.get("prov") or props.get("lugar") or ""
            headline = f"Terremoto {mag_str} – {location}".strip(" –")

            data = AlertCreate(
                external_id=f"ign-{event_id}" if event_id else None,
                source=AlertSource.IGN,
                alert_type=AlertType.SEISMIC,
                severity=_magnitude_to_severity(magnitude),
                status=AlertStatus.ACTUAL,
                headline=headline or "Evento sísmico detectado",
                description=props.get("info"),
                area_description=location or None,
                geometry=geometry_raw,
                effective_at=_parse_dt(props.get("hora") or props.get("time")),
                expires_at=None,
                raw_data=props,
            )

            result = await alert_service.upsert_alert(self.db, data)
            if result is not None:
                alerts_new += 1

        return alerts_fetched, alerts_new
