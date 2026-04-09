"""Conector MeteoAlarm: obtiene avisos meteorológicos europeos vía API REST."""

import logging
from datetime import datetime
import hashlib

from app.connectors.base import BaseConnector
from app.schemas.alert import AlertCreate
from app.models.enums import AlertSource, AlertType, AlertSeverity, AlertStatus

logger = logging.getLogger(__name__)

class MeteoAlarmConnector(BaseConnector):
    """
    Conector para extraer avisos meteorológicos de MeteoAlarm (formato GeoJSON).
    Fuente: https://feeds.meteoalarm.org/api/v1/warnings/feeds-spain
    """
    
    BASE_URL = "https://feeds.meteoalarm.org/api/v1/warnings/feeds-spain"

    async def _fetch(self) -> list[AlertCreate]:
        client = self.get_client()
        
        response = await client.get(self.BASE_URL)
        response.raise_for_status()
        
        data_json = response.json()
        features = data_json.get("features", [])
        
        normalized_alerts = []
        seen_identifiers = set()
        
        if not features:
            return []
            
        for feature in features:
            try:
                properties = feature.get("properties", {})
                geometry = feature.get("geometry")
                
                if not properties or not geometry:
                    continue
                    
                # Extraer propiedades del formato CAP mapeado en JSON
                # A menudo MeteoAlarm expone los mismos avisos que AEMET.
                # Para evitar duplicados en la base de datos (y luego en frontend),
                # la external_id debería ser manejada para detectarlo, pero para estar
                # seguros de no duplicar entre AEMET y MeteoAlarm, generaremos
                # un ID compuesto o usaremos el mismo identificador CAP si existe.
                identifier = properties.get("identifier", "")
                if not identifier:
                    identifier = properties.get("id", "")
                    
                area_description = properties.get("areaDesc", properties.get("area", "España"))
                unique_key = f"{identifier}_{area_description}"
                if unique_key in seen_identifiers:
                    continue
                seen_identifiers.add(unique_key)
                external_id = unique_key
                
                # Parsear la gravedad ("awareness_level")
                # El awareness_level suele venir en formato "2; yellow; Moderate", etc.
                awareness_level = properties.get("awareness_level", "").lower()
                severity = AlertSeverity.UNKNOWN
                
                if "red" in awareness_level or "extreme" in awareness_level or "4" in awareness_level:
                    severity = AlertSeverity.EXTREME
                elif "orange" in awareness_level or "severe" in awareness_level or "3" in awareness_level:
                    severity = AlertSeverity.SEVERE
                elif "yellow" in awareness_level or "moderate" in awareness_level or "2" in awareness_level:
                    severity = AlertSeverity.MODERATE
                elif "green" in awareness_level or "minor" in awareness_level or "1" in awareness_level:
                    severity = AlertSeverity.MINOR
                    
                # Parsing de fechas
                onset = properties.get("onset") or properties.get("effective") or properties.get("sent")
                effective_at = None
                if onset:
                    try:
                        effective_at = datetime.fromisoformat(onset.replace('Z', '+00:00'))
                    except ValueError:
                        pass
                        
                expires = properties.get("expires")
                expires_at = None
                if expires:
                    try:
                        expires_at = datetime.fromisoformat(expires.replace('Z', '+00:00'))
                    except ValueError:
                        pass

                # Campos de texto
                headline = properties.get("headline")
                description = properties.get("description")
                instruction = properties.get("instruction")
                
                # Fallback para headline si no existe: combinar tipo y severidad
                if not headline:
                    event_type = properties.get("awareness_type", properties.get("event", "Alerta meteorológica"))
                    headline = f"{event_type.capitalize()} en {area_description}"
                
                # Combinar descripciones si están vacías, para asegurar contexto
                full_desc = description
                if not description and instruction:
                    full_desc = instruction

                # En GeoAlchemy2/PostGIS el campo de geometría recibe dicts con "type" y "coordinates"
                # que es exactamente lo que viene en 'geometry' de GeoJSON.
                # Validar la estructura basica de GeoJSON antes de insertar.
                geom_type = geometry.get("type")
                geom_coords = geometry.get("coordinates")
                
                if not geom_type or not geom_coords:
                    continue

                alert = AlertCreate(
                    external_id=external_id,
                    source=AlertSource.METEOALARM,
                    alert_type=AlertType.METEOROLOGICAL,
                    severity=severity,
                    status=AlertStatus.ACTUAL,
                    headline=headline,
                    description=full_desc,
                    area_description=area_description,
                    geometry=geometry,
                    effective_at=effective_at,
                    expires_at=expires_at,
                    raw_data=properties
                )
                normalized_alerts.append(alert)
                
            except Exception as e:
                logger.warning(f"MeteoAlarm: Error parseando feature [{feature.get('id', 'N/A')}]: {e}")
                continue
                
        logger.info(f"MeteoAlarm: Procesados {len(normalized_alerts)} avisos correctamente.")
        return normalized_alerts
