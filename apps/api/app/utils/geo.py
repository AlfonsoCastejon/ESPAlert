"""Utilidades geográficas: conversión de geometrías y validación de coordenadas."""

import logging
import re
from typing import Dict, Any, Union, Tuple, List

logger = logging.getLogger(__name__)

def wkt_to_geojson(wkt_str: str) -> Union[Dict[str, Any], None]:
    """
    Convierte WKT de PostGIS a un diccionario GeoJSON asumiendo EPSG:4326.
    Soporta POINT y POLYGON basico.
    """
    if not wkt_str or not isinstance(wkt_str, str):
        return None

    try:
        wkt_str = wkt_str.upper().strip()
        if wkt_str.startswith('SRID='):
            parts = wkt_str.split(';')
            if len(parts) > 1:
                wkt_str = parts[1]

        if wkt_str.startswith('POINT'):
            coords_match = re.search(r'\(([^)]+)\)', wkt_str)
            if not coords_match:
                return None
            parts = coords_match.group(1).split()
            if len(parts) < 2:
                return None
            return {"type": "Point", "coordinates": [float(parts[0]), float(parts[1])]}
            
        elif wkt_str.startswith('POLYGON'):
            # Buscar anillos individuales
            rings = []
            for ring_match in re.findall(r'\(([^()]+)\)', wkt_str):
                points = []
                for pt in ring_match.split(','):
                    parts = pt.strip().split()
                    if len(parts) >= 2:
                        points.append([float(parts[0]), float(parts[1])])
                if points:
                    rings.append(points)
            if rings:
                return {"type": "Polygon", "coordinates": rings}
                
    except Exception as e:
        logger.warning(f"Error parseando WKT a GeoJSON: {wkt_str} - {e}")
        
    return None

def coords_to_point(lat: float, lon: float) -> Union[str, None]:
    """
    Crea un punto geográfico postgis-compatible (WKT) en EPSG:4326.
    Notese el orden POINT(lon lat).
    """
    try:
        lat = float(lat)
        lon = float(lon)
        return f"SRID=4326;POINT({lon} {lat})"
    except (ValueError, TypeError):
        logger.warning(f"Coordenadas inválidas para coords_to_point: lat={lat}, lon={lon}")
        return None

def bbox_to_polygon(bbox: Union[List, Tuple]) -> Union[str, None]:
    """
    Convierte un bounding box [min_lon, min_lat, max_lon, max_lat] 
    a un polígono WKT usando EPSG:4326.
    """
    if not bbox or len(bbox) != 4:
        return None
    try:
        min_lon, min_lat, max_lon, max_lat = map(float, bbox)
        poly = f"SRID=4326;POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
        return poly
    except (ValueError, TypeError):
        logger.warning(f"Bounding box inválido: {bbox}")
        return None
