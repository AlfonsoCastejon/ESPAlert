"""Connector for DGT (Dirección General de Tráfico) DATEX2 traffic incidents."""

from datetime import UTC, datetime

import httpx

from app.connectors.base import BaseConnector
from app.models.enums import AlertSeverity, AlertSource, AlertStatus, AlertType
from app.schemas.alert import AlertCreate
from app.services import alert_service
from app.utils.xml_parser import parse_datex2_xml

_DGT_URL = "https://infocar.dgt.es/datex2/dgt/SituationPublication/all/content.xml"

_SEVERITY_MAP: dict[str, AlertSeverity] = {
    "lowest": AlertSeverity.MINOR,
    "low": AlertSeverity.MINOR,
    "medium": AlertSeverity.MODERATE,
    "high": AlertSeverity.SEVERE,
    "highest": AlertSeverity.EXTREME,
    "unknown": AlertSeverity.UNKNOWN,
}


def _map_severity(raw: str | None) -> AlertSeverity:
    if not raw:
        return AlertSeverity.UNKNOWN
    return _SEVERITY_MAP.get(raw.lower().strip(), AlertSeverity.UNKNOWN)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class DGTConnector(BaseConnector):
    """Fetches current traffic incidents from DGT in DATEX2 format."""

    source = AlertSource.DGT

    async def _fetch(self) -> tuple[int, int]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(_DGT_URL)
            resp.raise_for_status()
            xml_content = resp.content

        situations = parse_datex2_xml(xml_content)
        alerts_fetched = len(situations)
        alerts_new = 0

        for sit in situations:
            external_id = sit.get("id") or None
            summary = sit.get("summary") or "Incidencia de tráfico DGT"
            geometry = sit.get("location")

            data = AlertCreate(
                external_id=f"dgt-{external_id}" if external_id else None,
                source=AlertSource.DGT,
                alert_type=AlertType.TRAFFIC,
                severity=_map_severity(sit.get("severity")),
                status=AlertStatus.ACTUAL,
                headline=summary,
                description=None,
                area_description=None,
                geometry=geometry,
                effective_at=_parse_dt(sit.get("creationTime")),
                expires_at=None,
                raw_data=sit,
            )

            result = await alert_service.upsert_alert(self.db, data)
            if result is not None:
                alerts_new += 1

        return alerts_fetched, alerts_new
