"""Connector for AEMET (Agencia Estatal de Meteorología) CAP XML alerts."""

import re
from datetime import UTC, datetime
from typing import Any

import httpx

from app.config import get_settings
from app.connectors.base import BaseConnector
from app.models.enums import AlertSeverity, AlertSource, AlertStatus, AlertType
from app.schemas.alert import AlertCreate
from app.services import alert_service
from app.utils.xml_parser import parse_cap_xml

# AEMET OpenData API – returns a JSON envelope whose "datos" field holds the CAP URL
_BASE_URL = "https://opendata.aemet.es/openapi/api/avisos_cap/ultimoelaborado/todasestaciones"

_SEVERITY_MAP: dict[str, AlertSeverity] = {
    "minor": AlertSeverity.MINOR,
    "moderate": AlertSeverity.MODERATE,
    "severe": AlertSeverity.SEVERE,
    "extreme": AlertSeverity.EXTREME,
    "amarillo": AlertSeverity.MINOR,
    "naranja": AlertSeverity.MODERATE,
    "rojo": AlertSeverity.SEVERE,
    "yellow": AlertSeverity.MINOR,
    "orange": AlertSeverity.MODERATE,
    "red": AlertSeverity.SEVERE,
}

_ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # Normalise offset-naive strings to UTC
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _map_severity(raw: str | None) -> AlertSeverity:
    if not raw:
        return AlertSeverity.UNKNOWN
    return _SEVERITY_MAP.get(raw.lower().strip(), AlertSeverity.UNKNOWN)


def _extract_geometry(areas: list[dict[str, Any]]) -> Any | None:
    for area in areas:
        geom = area.get("geometry")
        if geom:
            return geom
    return None


class AEMETConnector(BaseConnector):
    """Fetches current CAP meteorological alerts from AEMET OpenData."""

    source = AlertSource.AEMET

    async def _fetch(self) -> tuple[int, int]:
        settings = get_settings()
        api_key = settings.AEMET_API_KEY.get_secret_value()

        async with httpx.AsyncClient(timeout=30) as client:
            # Step 1 – get the envelope with the actual data URL
            envelope_resp = await client.get(
                _BASE_URL,
                headers={"api_key": api_key},
            )
            envelope_resp.raise_for_status()
            envelope = envelope_resp.json()

            data_url: str | None = envelope.get("datos")
            if not data_url:
                self.logger.info("AEMET returned no 'datos' URL – nothing to import")
                return 0, 0

            # Step 2 – download the CAP XML
            cap_resp = await client.get(data_url, headers={"api_key": api_key})
            cap_resp.raise_for_status()
            cap_content = cap_resp.content

        alerts_raw = parse_cap_xml(cap_content)
        alerts_fetched = len(alerts_raw)
        alerts_new = 0

        for raw in alerts_raw:
            external_id = raw.get("identifier")
            areas: list[dict[str, Any]] = raw.get("areas", [])
            area_description = areas[0].get("areaDesc") if areas else None
            geometry = _extract_geometry(areas)

            data = AlertCreate(
                external_id=external_id,
                source=AlertSource.AEMET,
                alert_type=AlertType.METEOROLOGICAL,
                severity=_map_severity(raw.get("severity")),
                status=AlertStatus.ACTUAL,
                headline=raw.get("headline") or raw.get("event") or "Aviso meteorológico AEMET",
                description=raw.get("description"),
                area_description=area_description,
                geometry=geometry,
                effective_at=_parse_dt(raw.get("sent")),
                expires_at=None,
                raw_data=raw,
            )

            result = await alert_service.upsert_alert(self.db, data)
            if result is not None:
                alerts_new += 1

        return alerts_fetched, alerts_new
