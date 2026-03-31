"""Tests del parser XML: CAP (AEMET/MeteoAlarm) y DATEX2 (DGT)."""
from app.utils.xml_parser import parse_cap_xml, parse_datex2_xml


def test_cap_incluye_effective_y_expires():
    """Los campos <effective> y <expires> del <info> deben estar en el dict."""
    cap = b"""<?xml version="1.0" encoding="UTF-8"?>
    <alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
      <identifier>CAP-001</identifier>
      <sent>2024-03-26T10:00:00+01:00</sent>
      <info>
        <severity>Severe</severity>
        <headline>Test</headline>
        <effective>2024-03-26T12:00:00+01:00</effective>
        <expires>2024-03-27T12:00:00+01:00</expires>
        <area>
          <areaDesc>Zona test</areaDesc>
          <polygon>40.0,-4.0 40.5,-4.0 40.5,-3.5 40.0,-3.5 40.0,-4.0</polygon>
        </area>
      </info>
    </alert>"""

    result = parse_cap_xml(cap)

    assert len(result) == 1
    assert result[0]["expires"] == "2024-03-27T12:00:00+01:00"
    assert result[0]["effective"] == "2024-03-26T12:00:00+01:00"


def test_cap_sin_expires_devuelve_none():
    """Si no hay <expires> en el XML, el campo debe ser None."""
    cap = b"""<?xml version="1.0" encoding="UTF-8"?>
    <alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
      <identifier>CAP-002</identifier>
      <sent>2024-03-26T10:00:00Z</sent>
      <info>
        <severity>Minor</severity>
        <headline>Sin expirar</headline>
        <area>
          <areaDesc>Zona</areaDesc>
          <polygon>40.0,-4.0 40.5,-4.0 40.5,-3.5 40.0,-3.5 40.0,-4.0</polygon>
        </area>
      </info>
    </alert>"""

    result = parse_cap_xml(cap)
    assert result[0]["expires"] is None
    assert result[0]["effective"] is None


def test_cap_contenido_vacio_devuelve_lista_vacia():
    assert parse_cap_xml(b"") == []
    assert parse_cap_xml("") == []


def test_datex2_extrae_ubicacion_como_geojson_point():
    """El parser debe devolver location como GeoJSON Point con [lon, lat]."""
    datex2 = b"""<?xml version="1.0" encoding="UTF-8"?>
    <d2LogicalModel xmlns="http://datex2.eu/schema/2/2_0">
      <payloadPublication>
        <situation>
          <situationRecord id="SR-001">
            <situationRecordCreationTime>2024-03-26T10:00:00+00:00</situationRecordCreationTime>
            <severity>high</severity>
            <groupOfLocations>
              <locationForDisplay>
                <latitude>40.4</latitude>
                <longitude>-3.7</longitude>
              </locationForDisplay>
            </groupOfLocations>
          </situationRecord>
        </situation>
      </payloadPublication>
    </d2LogicalModel>"""

    result = parse_datex2_xml(datex2)

    assert len(result) == 1
    assert result[0]["id"] == "SR-001"
    assert result[0]["location"]["coordinates"] == [-3.7, 40.4]
