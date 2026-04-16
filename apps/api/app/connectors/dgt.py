"""Conector DGT: parsea incidencias de tráfico desde DATEX2 v3.6 del NAP."""

from datetime import datetime
import logging

from app.connectors.base import BaseConnector
from app.models.enums import AlertSeverity, AlertSource, AlertStatus, AlertType
from app.schemas.alert import AlertCreate
from app.utils.xml_parser import parse_datex2_xml

logger = logging.getLogger(__name__)


class DgtConnector(BaseConnector):
    """Conector para el feed NAP de la DGT (formato DATEX2/XML)."""
    
    DATEX2_URL = "https://nap.dgt.es/datex2/v3/dgt/SituationPublication/datex2_v36.xml"

    def _map_severity(self, severity_str: str | None) -> AlertSeverity:
        if not severity_str:
            return AlertSeverity.MINOR
            
        sev = severity_str.lower()
        if sev in ("highest", "severe", "critical", "extreme"):
            return AlertSeverity.EXTREME
        elif sev in ("high", "major"):
            return AlertSeverity.SEVERE
        elif sev in ("medium", "moderate"):
            return AlertSeverity.MODERATE
        elif sev in ("low", "minor"):
            return AlertSeverity.MINOR
            
        return AlertSeverity.UNKNOWN

    async def _fetch(self) -> list[AlertCreate]:
        client = self.get_client()
        response = await client.get(self.DATEX2_URL)
        response.raise_for_status()

        situations = parse_datex2_xml(response.content)
        alerts = []

        for sit in situations:
            try:
                if not sit.get("location"):
                    continue

                severity = self._map_severity(sit.get("severity"))
                summary = sit.get("summary") or "Incidencia de tráfico DGT"

                alert_dict = {
                    "external_id": sit.get("id"),
                    "source": AlertSource.DGT,
                    "alert_type": AlertType.TRAFFIC,
                    "severity": severity,
                    "headline": summary,
                    "description": summary,
                    "geometry": sit.get("location"),
                    "status": AlertStatus.ACTUAL,
                    "raw_data": sit
                }

                time_str = sit.get("versionTime") or sit.get("creationTime")
                if time_str:
                    try:
                        effective_at = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                        alert_dict["effective_at"] = effective_at
                    except ValueError:
                        logger.debug(f"Fecha en formato no reconocido DGT: {time_str}")

                alerts.append(AlertCreate(**alert_dict))
                
            except Exception as e:
                logger.warning(f"Error procesando situación DATEX2 {sit.get('id', 'Unknown')}: {e}")

        logger.info(f"DGT DATEX2: {len(alerts)} incidencias mapeadas.")
        return alerts
