import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.connectors.ign import IGNConnector
from app.connectors.meteoalarm import MeteoAlarmConnector
from app.models.enums import AlertSeverity, AlertType, AlertSource

@pytest.mark.asyncio
async def test_ign_connector_parsing():
    """
    Prueba que el conector IGN del Instituto Geográfico Nacional
    parsea correctamente el formato de texto FDSN devuelto por su API
    y mapea las magnitudes a severidades.
    """
    connector = IGNConnector()
    
    # Fake CSV text similar to IGN output
    fake_text = (
        "EventID|Time|Latitude|Longitude|Depth/km|Magnitude|EventLocationName\n"
        "ign2024abcd|2024-03-26T10:00:00Z|36.5|-4.5|10.0|4.2|Mar de Alborán\n"
        "ign2024efgh|2024-03-26T12:00:00Z|37.0|-5.0|5.0|2.1|Granada\n"
    )
    
    # Mocking httpx Response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.text = fake_text
    
    # Mocking httpx AsyncClient
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    
    with patch.object(connector, 'get_client', return_value=mock_client):
        alerts = await connector._fetch()
        
        assert len(alerts) == 2
        
        # Comprobar el primer sismo (Magnitud 4.2 -> Naranja/Severe)
        assert alerts[0].external_id == "ign2024abcd"
        assert alerts[0].severity == AlertSeverity.SEVERE
        assert alerts[0].area_description == "Mar de Alborán"
        assert alerts[0].geometry["coordinates"] == [-4.5, 36.5] # GeoJSON obliga Lon, Lat
        assert alerts[0].alert_type == AlertType.SEISMIC
        assert alerts[0].source == AlertSource.IGN
        
        # Comprobar el segundo sismo (Magnitud 2.1 -> Verde/Minor)
        assert alerts[1].external_id == "ign2024efgh"
        assert alerts[1].severity == AlertSeverity.MINOR

@pytest.mark.asyncio
async def test_meteoalarm_connector_parsing():
    """
    Prueba que el conector de MeteoAlarm parsea correctamente los
    avisos en GeoJSON, evita colisiones de Area, y extrae correctamente
    los niveles de seguridad (awareness_level).
    """
    connector = MeteoAlarmConnector()
    
    # Fake GeoJSON FeatureCollection
    fake_json = {
        "features": [
            {
                "properties": {
                    "identifier": "CAP-12345",
                    "areaDesc": "Madrid",
                    "awareness_level": "3; orange; Severe",
                    "headline": "Lluvia intensa"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0,0], [0,1], [1,1], [0,0]]]
                }
            }
        ]
    }
    
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = fake_json
    
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    
    with patch.object(connector, 'get_client', return_value=mock_client):
        alerts = await connector._fetch()
        
        assert len(alerts) == 1
        # Comprobar unicidad para DB: identifier_areaDesc
        assert alerts[0].external_id == "CAP-12345_Madrid"
        # Naranja 3 mapea a SEVERE
        assert alerts[0].severity == AlertSeverity.SEVERE
        assert alerts[0].headline == "Lluvia intensa"
        assert alerts[0].source == AlertSource.METEOALARM
        assert alerts[0].geometry["type"] == "Polygon"
