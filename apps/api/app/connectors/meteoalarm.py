"""Connector for MeteoAlarm CAP alerts (Spain feed)."""

import xml.etree.ElementTree as ET
from datetime import UTC, datetime

import httpx

from app.connectors.base import BaseConnector
from app.models.enums import AlertSeverity, AlertSource, AlertStatus, AlertType
from app.schemas.alert import AlertCreate
from app.services import alert_service
from app.utils.xml_parser import extract_geometry_from_cap

# MeteoAlarm Atom/CAP feed for Spain
_METEOALARM_URL = "https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-spain"

_SEVERITY_MAP: dict[str, AlertSeverity] = {
    "minor": AlertSeverity.MINOR,
    "moderate": AlertSeverity.MODERATE,
    "severe": AlertSeverity.SEVERE,
    "extreme": AlertSeverity.EXTREME,
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


def _get_text(element: ET.Element, xpath: str) -> str | None:
    el = element.find(xpath)
    return el.text.strip() if el is not None and el.text else None


def _parse_meteoalarm_feed(content: bytes) -> list[dict]:
    """Parse MeteoAlarm Atom feed; each entry may embed a CAP <alert> block."""
    alerts: list[dict] = []
    if not content:
        return alerts

    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return alerts

    ns_atom = "{http://www.w3.org/2005/Atom}"
    ns_cap = "{urn:oasis:names:tc:emergency:cap:1.2}"

    for entry in root.findall(f"{ns_atom}entry"):
        entry_id = _get_text(entry, f"{ns_atom}id")

        # Locate the embedded CAP <info> block (may be in a <content> element)
        cap_alert = entry.find(f".//{ns_cap}alert") or entry.find(".//{*}alert")
        if cap_alert is None:
            # Treat the Atom entry itself as a minimal alert record
            title = _get_text(entry, f"{ns_atom}title")
            updated = _get_text(entry, f"{ns_atom}updated")
            alerts.append(
                {
                    "identifier": entry_id,
                    "headline": title,
                    "severity": None,
                    "sent": updated,
                    "expires": None,
                    "areas": [],
                }
            )
            continue

        identifier = _get_text(cap_alert, f".//{ns_cap}identifier") or entry_id
        sent = _get_text(cap_alert, f".//{ns_cap}sent")

        infos = cap_alert.findall(f".//{ns_cap}info")
        if not infos:
            infos = cap_alert.findall(".//{*}info")

        for info in infos:
            lang = _get_text(info, f".//{ns_cap}language") or _get_text(
                info, ".//{*}language"
            )
            # Prefer Spanish content when available
            if lang and not lang.lower().startswith("es") and len(infos) > 1:
                continue

            severity_raw = _get_text(info, f".//{ns_cap}severity") or _get_text(
                info, ".//{*}severity"
            )
            headline = _get_text(info, f".//{ns_cap}headline") or _get_text(
                info, ".//{*}headline"
            )
            description = _get_text(info, f".//{ns_cap}description") or _get_text(
                info, ".//{*}description"
            )
            expires = _get_text(info, f".//{ns_cap}expires") or _get_text(
                info, ".//{*}expires"
            )

            areas: list[dict] = []
            area_nodes = info.findall(f".//{ns_cap}area") or info.findall(".//{*}area")
            for area in area_nodes:
                area_desc = _get_text(area, f".//{ns_cap}areaDesc") or _get_text(
                    area, ".//{*}areaDesc"
                )
                geometry = extract_geometry_from_cap(area)
                areas.append({"areaDesc": area_desc, "geometry": geometry})

            alerts.append(
                {
                    "identifier": identifier,
                    "headline": headline,
                    "description": description,
                    "severity": severity_raw,
                    "sent": sent,
                    "expires": expires,
                    "areas": areas,
                }
            )
            break  # Only process one info block per entry

    return alerts


class MeteoalarmConnector(BaseConnector):
    """Fetches current meteorological warnings from the MeteoAlarm Spain CAP feed."""

    source = AlertSource.METEOALARM

    async def _fetch(self) -> tuple[int, int]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(_METEOALARM_URL)
            resp.raise_for_status()
            content = resp.content

        alerts_raw = _parse_meteoalarm_feed(content)
        alerts_fetched = len(alerts_raw)
        alerts_new = 0

        for raw in alerts_raw:
            areas: list[dict] = raw.get("areas", [])
            area_description = areas[0].get("areaDesc") if areas else None
            geometry = next(
                (a.get("geometry") for a in areas if a.get("geometry")), None
            )

            data = AlertCreate(
                external_id=raw.get("identifier"),
                source=AlertSource.METEOALARM,
                alert_type=AlertType.METEOROLOGICAL,
                severity=_map_severity(raw.get("severity")),
                status=AlertStatus.ACTUAL,
                headline=raw.get("headline") or "Aviso meteorológico MeteoAlarm",
                description=raw.get("description"),
                area_description=area_description,
                geometry=geometry,
                effective_at=_parse_dt(raw.get("sent")),
                expires_at=_parse_dt(raw.get("expires")),
                raw_data=raw,
            )

            result = await alert_service.upsert_alert(self.db, data)
            if result is not None:
                alerts_new += 1

        return alerts_fetched, alerts_new
