"""Conector IGN: consulta sismos recientes vía FDSNWS (QuakeML)."""

import logging
from datetime import datetime, timedelta, timezone

from app.connectors.base import BaseConnector
from app.schemas.alert import AlertCreate
from app.models.enums import AlertSource, AlertType, AlertSeverity, AlertStatus

logger = logging.getLogger(__name__)

class IGNConnector(BaseConnector):
    """
    Conector para extraer sismos del Instituto Geográfico Nacional (IGN).
    Utiliza el servicio FDSNWS Event.
    """
    
    BASE_URL = "https://fdsnws.sismologia.ign.es/fdsnws/event/1/query"

    async def _fetch(self) -> list[AlertCreate]:
        client = self.get_client()
        
        # Calcular ventana de tiempo (últimas 24h)
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=24)
        
        params = {
            "starttime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "minmag": 2.0,
            "format": "text"  # El formato de texto de FDSNWS devuelve valores separados por '|'
        }
        
        response = await client.get(self.BASE_URL, params=params)
        if response.status_code == 404:
            logger.info("IGN: Sin sismos en las últimas 24h (FDSNWS 404 = sin resultados).")
            return []
        response.raise_for_status()
        
        text_data = response.text
        lines = text_data.strip().split('\n')
        
        normalized_alerts = []
        
        if not lines:
            return []
            
        # Parsear cabeceras dinámicamente para mayor robustez
        headers = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('EventID') or 'Latitude' in line:
                headers = line.split('|')
                break
                
        if not headers:
            logger.error("IGN: No se encontraron cabeceras válidas en el formato FDSN.")
            return []
            
        try:
            time_idx = headers.index('Time')
            lat_idx = headers.index('Latitude')
            lon_idx = headers.index('Longitude')
            depth_idx = headers.index('Depth/km')
            mag_idx = headers.index('Magnitude')
            loc_idx = headers.index('EventLocationName')
        except ValueError as e:
            logger.error(f"IGN: Faltan columnas esperadas en el CSV: {e}")
            return []

        for line in lines:
            line = line.strip()
            # Ignorar líneas vacías y encabezados de archivo
            if not line or line.startswith('#') or line.startswith('EventID') or 'Latitude' in line:
                continue
                
            row = line.split('|')
            if len(row) <= max(mag_idx, loc_idx, lat_idx, lon_idx):
                continue
                
            try:
                event_id = row[0]
                time_str = row[time_idx]
                lat = float(row[lat_idx])
                lon = float(row[lon_idx])
                depth = float(row[depth_idx]) if row[depth_idx] else 0.0
                mag = float(row[mag_idx])
                location_name = row[loc_idx] if row[loc_idx] else "Desconocido"
                
                # Convertir magnitud a severidad según los criterios requeridos
                if mag < 3.0:
                    severity = AlertSeverity.MINOR      # Verde (Menos de 3.0)
                elif 3.0 <= mag < 4.0:
                    severity = AlertSeverity.MODERATE   # Amarillo (3.0 - 3.9)
                elif 4.0 <= mag < 5.0:
                    severity = AlertSeverity.SEVERE     # Naranja (4.0 - 4.9)
                else:
                    severity = AlertSeverity.EXTREME    # Rojo (5.0 o más)
                    
                # Parsear fecha
                try:
                    # Maneja posibles sufijos 'Z' como UTC explícito
                    effective_at = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                except ValueError:
                    effective_at = None
                    
                # Guardar coordenadas como punto geográfico (GeoJSON: [lon, lat])
                geometry = {
                    "type": "Point",
                    "coordinates": [lon, lat]
                }
                
                alert = AlertCreate(
                    external_id=event_id,
                    source=AlertSource.IGN,
                    alert_type=AlertType.SEISMIC,
                    severity=severity,
                    status=AlertStatus.ACTUAL,
                    headline=f"Terremoto mag {mag} en {location_name}",
                    description=f"Sismo de magnitud {mag} a {depth} km de profundidad.",
                    area_description=location_name,
                    geometry=geometry,
                    effective_at=effective_at,
                    raw_data={
                        "event_id": event_id,
                        "time": time_str,
                        "lat": lat,
                        "lon": lon,
                        "depth": depth,
                        "mag": mag,
                        "location": location_name
                    }
                )
                normalized_alerts.append(alert)
                
            except (ValueError, IndexError) as e:
                logger.warning(f"IGN: Error parseando fila de texto: {row} - {e}")
                continue
                
        logger.info(f"IGN: Procesados {len(normalized_alerts)} sismos correctamente.")
        return normalized_alerts
