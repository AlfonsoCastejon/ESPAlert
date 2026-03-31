import logging
from datetime import datetime

from app.config import settings
from app.connectors.base import BaseConnector
from app.schemas.alert import AlertCreate
from app.models.enums import AlertSource, AlertType, AlertSeverity, AlertStatus
from app.utils.xml_parser import parse_cap_xml

logger = logging.getLogger(__name__)

class AemetConnector(BaseConnector):
    """
    Conector para extraer alertas meteorológicas de AEMET (formato CAP/XML).
    Requiere una API key preconfigurada.
    """
    
    BASE_URL = "https://opendata.aemet.es/opendata/api/avisos_cap/ultimoelaborado/todasareas/"

    async def _fetch(self) -> list[AlertCreate]:
        client = self.get_client()
        api_key = settings.AEMET_API_KEY.get_secret_value()
        
        # 1. Petición inicial para obtener la URL real de los datos
        headers = {
            "api_key": api_key,
            "Accept": "application/json"
        }
        
        response = await client.get(self.BASE_URL, headers=headers)
        response.raise_for_status()
        
        data_json = response.json()
        
        if data_json.get("estado") != 200:
            logger.error(f"Error en AEMET API: {data_json.get('descripcion')}")
            return []
            
        data_url = data_json.get("datos")
        if not data_url:
            logger.error("AEMET no devolvió una URL de datos válida en el payload.")
            return []
            
        # 2. Descargar el archivo CAP/XML desde la URL proporcionada
        cap_response = await client.get(data_url)
        cap_response.raise_for_status()
        
        xml_content = cap_response.content
        
        # 3. Parsear el XML usando la utilidad general
        parsed_alerts = parse_cap_xml(xml_content)
        
        # 4. Normalizar y mapear al schema de la base de datos
        normalized_alerts = []
        for alert_dict in parsed_alerts:
            # Parsear niveles de severidad
            # AEMET utiliza niveles amarillo, naranja y rojo que se mapean al estándar CAP
            severity_str = str(alert_dict.get("severity", "")).lower()
            if severity_str == "extreme":
                severity = AlertSeverity.EXTREME   # Rojo
            elif severity_str == "severe":
                severity = AlertSeverity.SEVERE    # Naranja
            elif severity_str == "moderate":
                severity = AlertSeverity.MODERATE  # Amarillo
            elif severity_str == "minor":
                severity = AlertSeverity.MINOR
            else:
                severity = AlertSeverity.UNKNOWN

            # Parsing de fechas
            sent_str = alert_dict.get("sent")
            effective_at = None
            if sent_str:
                try:
                    effective_at = datetime.fromisoformat(sent_str.replace("Z", "+00:00"))
                except ValueError:
                    logger.debug(f"Fecha en formato no reconocido AEMET: {sent_str}")

            expires_str = alert_dict.get("expires")
            expires_at = None
            if expires_str:
                try:
                    expires_at = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                except ValueError:
                    logger.debug(f"Fecha expires en formato no reconocido AEMET: {expires_str}")

            # Generamos un AlertCreate por cada área afectada devuelta
            for area in alert_dict.get("areas", []):
                geometry = area.get("geometry")
                
                # Descartar si no hay polígono u área significativa y preferimos polígonos validos
                if not geometry:
                    continue
                    
                alert = AlertCreate(
                    external_id=alert_dict.get("identifier"),
                    source=AlertSource.AEMET,
                    alert_type=AlertType.METEOROLOGICAL,
                    severity=severity,
                    status=AlertStatus.ACTUAL,
                    headline=alert_dict.get("headline", "Alerta Meteorológica AEMET"),
                    description=alert_dict.get("description"),
                    area_description=area.get("areaDesc"),
                    geometry=geometry,
                    effective_at=effective_at,
                    expires_at=expires_at,
                    raw_data=alert_dict
                )
                normalized_alerts.append(alert)
                
        logger.info(f"AEMET: Procesadas {len(normalized_alerts)} alertas/áreas correctamente.")
        return normalized_alerts
