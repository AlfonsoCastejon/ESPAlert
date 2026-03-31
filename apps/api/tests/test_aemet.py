"""Tests del conector AEMET: severidad, fechas, expires_at y geometria."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.connectors.aemet import AemetConnector
from app.models.enums import AlertSeverity, AlertSource


FAKE_CAP_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>AEMET-TEST-001</identifier>
  <sender>w-nws.webmaster@noaa.gov</sender>
  <sent>2024-03-26T10:00:00+01:00</sent>
  <info>
    <language>es</language>
    <category>Met</category>
    <event>Lluvias</event>
    <severity>Severe</severity>
    <headline>Aviso naranja por lluvias</headline>
    <description>Lluvias intensas previstas</description>
    <effective>2024-03-26T10:00:00+01:00</effective>
    <expires>2024-03-27T10:00:00+01:00</expires>
    <area>
      <areaDesc>Madrid</areaDesc>
      <polygon>40.0,-4.0 40.5,-4.0 40.5,-3.5 40.0,-3.5 40.0,-4.0</polygon>
    </area>
  </info>
</alert>"""


def _mock_aemet_client(cap_content):
    """Prepara un mock de httpx que simula la doble peticion de AEMET (API + datos)."""
    mock_api = MagicMock()
    mock_api.raise_for_status = MagicMock()
    mock_api.json.return_value = {"estado": 200, "datos": "http://fake/data.xml"}

    mock_cap = MagicMock()
    mock_cap.raise_for_status = MagicMock()
    mock_cap.content = cap_content

    client = AsyncMock()
    client.get.side_effect = [mock_api, mock_cap]
    return client


@pytest.mark.asyncio
async def test_aemet_extrae_expires_at_del_cap():
    """El campo <expires> del CAP debe llegar como expires_at en la alerta."""
    connector = AemetConnector()
    mock_client = _mock_aemet_client(FAKE_CAP_XML)

    with patch.object(connector, "get_client", return_value=mock_client):
        alerts = await connector._fetch()

    assert len(alerts) == 1
    assert alerts[0].expires_at is not None
    assert alerts[0].expires_at.year == 2024
    assert alerts[0].expires_at.day == 27


@pytest.mark.asyncio
async def test_aemet_severity_extreme_mapea_a_rojo():
    """severity=Extreme en CAP -> AlertSeverity.EXTREME."""
    connector = AemetConnector()
    cap_extreme = FAKE_CAP_XML.replace(b"Severe", b"Extreme")
    mock_client = _mock_aemet_client(cap_extreme)

    with patch.object(connector, "get_client", return_value=mock_client):
        alerts = await connector._fetch()

    assert alerts[0].severity == AlertSeverity.EXTREME
    assert alerts[0].source == AlertSource.AEMET


@pytest.mark.asyncio
async def test_aemet_sin_poligono_descarta_area():
    """Areas sin <polygon> ni <circle> no deben generar alerta."""
    connector = AemetConnector()

    cap_sin_geo = b"""<?xml version="1.0" encoding="UTF-8"?>
    <alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
      <identifier>AEMET-TEST-002</identifier>
      <sent>2024-03-26T10:00:00+01:00</sent>
      <info>
        <severity>Moderate</severity>
        <headline>Sin geometria</headline>
        <area><areaDesc>Zona sin poligono</areaDesc></area>
      </info>
    </alert>"""

    mock_client = _mock_aemet_client(cap_sin_geo)

    with patch.object(connector, "get_client", return_value=mock_client):
        alerts = await connector._fetch()

    assert len(alerts) == 0


@pytest.mark.asyncio
async def test_aemet_fechas_con_z_tienen_timezone():
    """Fechas con sufijo 'Z' deben parsearse con tzinfo UTC, no como naive."""
    connector = AemetConnector()

    cap_z = FAKE_CAP_XML.replace(
        b"2024-03-26T10:00:00+01:00", b"2024-03-26T10:00:00Z"
    ).replace(
        b"2024-03-27T10:00:00+01:00", b"2024-03-27T10:00:00Z"
    )
    mock_client = _mock_aemet_client(cap_z)

    with patch.object(connector, "get_client", return_value=mock_client):
        alerts = await connector._fetch()

    assert alerts[0].effective_at.tzinfo is not None
    assert alerts[0].expires_at.tzinfo is not None
