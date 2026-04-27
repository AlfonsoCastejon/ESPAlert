"""Parsers de XML: CAP (AEMET/MeteoAlarm), QuakeML (IGN) y DATEX2 (DGT)."""

import xml.etree.ElementTree as ET
import logging
from typing import Any, Union

logger = logging.getLogger(__name__)

def _get_text(element: ET.Element, xpath: str) -> Union[str, None]:
    if element is None:
        return None
    el = element.find(xpath)
    return el.text.strip() if el is not None and el.text else None

def extract_geometry_from_cap(element: ET.Element) -> Union[dict[str, Any], None]:
    """
    Extrae un polígono o círculo en formato GeoJSON-compatible a partir de un elemento area en un CAP XML.
    """
    if element is None:
        return None
        
    try:
        # Polígonos
        polygon = element.find('.//{*}polygon')
        if polygon is not None and polygon.text:
            points_str = polygon.text.strip().split()
            coords = []
            for p in points_str:
                parts = p.split(',')
                if len(parts) >= 2:
                    lat, lon = parts[0], parts[1]
                    coords.append([float(lon), float(lat)]) # GeoJSON es [lon, lat]
            # Validar que cierre el anillo
            if coords and coords[0] != coords[-1]:
                coords.append(coords[0])
            if coords:
                return {
                    "type": "Polygon",
                    "coordinates": [coords]
                }
            
        # Círculos
        circle = element.find('.//{*}circle')
        if circle is not None and circle.text:
            parts = circle.text.strip().split()
            if len(parts) >= 2:
                lat_lon = parts[0].split(',')
                if len(lat_lon) >= 2:
                    lat, lon = lat_lon[0], lat_lon[1]
                    return {
                        "type": "Point",
                        "coordinates": [float(lon), float(lat)],
                        "radius_km": float(parts[1])
                    }
    except Exception as e:
        logger.warning(f"Error extrayendo geometría CAP: {e}")
        
    return None

def parse_cap_xml(content: Union[str, bytes]) -> list[dict[str, Any]]:
    """
    Parsea contenido XML en formato CAP (Common Alerting Protocol).
    Usado por AEMET y MeteoAlarm. Devuelve lista de diccionarios de alertas.
    """
    alerts = []
    if not content:
        return alerts

    try:
        if isinstance(content, bytes):
            content = content.decode('utf-8')
            
        # Manejo básico robusto y wildcard para namespaces
        root = ET.fromstring(content)
        
        # En CAP la raíz a veces es la alerta (<alert>) o un listado global
        alert_nodes = [root] if 'alert' in root.tag.lower() else root.findall('.//{*}alert')
        if not alert_nodes and 'alert' in root.tag.lower():
             alert_nodes = [root]
             
        for alert_node in alert_nodes:
            identifier = _get_text(alert_node, './/{*}identifier')
            sender = _get_text(alert_node, './/{*}sender')
            sent = _get_text(alert_node, './/{*}sent')
            
            infos = alert_node.findall('.//{*}info')
            # CAP suele incluir un <info> por idioma (es-ES, en-GB, ...). Si hay
            # bloques en español, descartamos los demás para evitar duplicados
            # y textos en inglés colándose en la UI.
            infos_es = [
                i for i in infos
                if (_get_text(i, './/{*}language') or "es").lower().startswith("es")
            ]
            if infos_es:
                infos = infos_es
            for info in infos:
                alert_dict = {
                    "identifier": identifier,
                    "sender": sender,
                    "sent": sent,
                    "language": _get_text(info, './/{*}language'),
                    "category": _get_text(info, './/{*}category'),
                    "event": _get_text(info, './/{*}event'),
                    "urgency": _get_text(info, './/{*}urgency'),
                    "severity": _get_text(info, './/{*}severity'),
                    "certainty": _get_text(info, './/{*}certainty'),
                    "headline": _get_text(info, './/{*}headline'),
                    "description": _get_text(info, './/{*}description'),
                    "instruction": _get_text(info, './/{*}instruction'),
                    "effective": _get_text(info, './/{*}effective'),
                    "expires": _get_text(info, './/{*}expires'),
                    "areas": []
                }
                
                areas = info.findall('.//{*}area')
                for area in areas:
                    area_dict = {
                        "areaDesc": _get_text(area, './/{*}areaDesc'),
                        "geometry": extract_geometry_from_cap(area)
                    }
                    alert_dict["areas"].append(area_dict)
                    
                alerts.append(alert_dict)
                
    except ET.ParseError as e:
        logger.warning(f"Error parseando CAP XML (Malformed/ParseError): {e}")
    except Exception as e:
        logger.warning(f"Error inesperado parseando CAP XML: {e}")
        
    return alerts

def parse_datex2_xml(content: Union[str, bytes]) -> list[dict[str, Any]]:
    """
    Parsea XML en formato DATEX2 (DGT).
    """
    situations = []
    if not content:
        return situations
        
    try:
        if isinstance(content, bytes):
            content = content.decode('utf-8')
            
        root = ET.fromstring(content)
        
        situation_records = root.findall('.//{*}situationRecord')
        for record in situation_records:
            # Intentamos sacar nombre de la carretera / descripción de la ubicación
            road_number = _get_text(record, './/{*}roadNumber')
            area_name = (
                _get_text(record, './/{*}supplementaryPositionalDescription/{*}locationDescriptor/{*}values/{*}value')
                or _get_text(record, './/{*}supplementaryPositionalDescription/{*}roadName/{*}values/{*}value')
                or _get_text(record, './/{*}roadName/{*}values/{*}value')
                or _get_text(record, './/{*}areaName/{*}values/{*}value')
            )
            partes = [p for p in (road_number, area_name) if p]
            area_description = " · ".join(partes) if partes else None

            sit = {
                "id": record.attrib.get('id', ''),
                "creationTime": _get_text(record, './/{*}situationRecordCreationTime'),
                "versionTime": _get_text(record, './/{*}situationRecordVersionTime'),
                "probabilityOfOccurrence": _get_text(record, './/{*}probabilityOfOccurrence'),
                "severity": _get_text(record, './/{*}severity'),
                "summary": _get_text(record, './/{*}nonGeneralPublicComment/{*}comment/{*}values/{*}value') or _get_text(record, './/{*}generalPublicComment/{*}comment/{*}values/{*}value'),
                "area_description": area_description,
                "location": None
            }
            
            point = record.find('.//{*}pointByCoordinates/{*}pointCoordinates')
            if point is None:
                point = record.find('.//{*}locationForDisplay')
            if point is None:
                point = record.find('.//{*}pointCoordinates')

            if point is not None:
                lat = _get_text(point, './/{*}latitude')
                lon = _get_text(point, './/{*}longitude')
                if lat and lon:
                    sit["location"] = {"type": "Point", "coordinates": [float(lon), float(lat)]}
                    
            situations.append(sit)
            
    except ET.ParseError as e:
        logger.warning(f"Error parseando DATEX2 XML (Malformed/ParseError): {e}")
    except Exception as e:
        logger.warning(f"Error inesperado parseando DATEX2 XML: {e}")
        
    return situations
