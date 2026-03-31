"""Tests del conector DGT: filtro 24h, severidad DATEX2 y descarte sin ubicacion."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.connectors.dgt import DgtConnector
from app.models.enums import AlertSeverity, AlertSource


DATEX2_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<d2LogicalModel xmlns="http://datex2.eu/schema/2/2_0">
  <payloadPublication>
    <situation>
      <situationRecord id="{sit_id}">
        <situationRecordCreationTime>{time}</situationRecordCreationTime>
        <severity>{severity}</severity>
        <generalPublicComment>
          <comment><values><value>{summary}</value></values></comment>
        </generalPublicComment>
        <groupOfLocations>
          <locationForDisplay>
            <latitude>{lat}</latitude>
            <longitude>{lon}</longitude>
          </locationForDisplay>
        </groupOfLocations>
      </situationRecord>
    </situation>
  </payloadPublication>
</d2LogicalModel>"""


def _make_datex2(sit_id="DGT-001", time=None, severity="high",
                 lat="40.4", lon="-3.7", summary="Corte de trafico"):
    if time is None:
        time = datetime.now(timezone.utc).isoformat()
    return DATEX2_TEMPLATE.format(
        sit_id=sit_id, time=time, severity=severity,
        lat=lat, lon=lon, summary=summary
    ).encode()


def _mock_dgt_client(xml_content):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.content = xml_content
    client = AsyncMock()
    client.get.return_value = mock_response
    return client


@pytest.mark.asyncio
async def test_dgt_incidencia_de_hace_48h_se_descarta():
    """Las incidencias con mas de 24h de antiguedad no deben aparecer."""
    connector = DgtConnector()
    t = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    client = _mock_dgt_client(_make_datex2(time=t))

    with patch.object(connector, "get_client", return_value=client):
        alerts = await connector._fetch()

    assert len(alerts) == 0


@pytest.mark.asyncio
async def test_dgt_incidencia_reciente_se_procesa():
    """Una incidencia de hace 1h debe aparecer con source=DGT y coordenadas."""
    connector = DgtConnector()
    t = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    client = _mock_dgt_client(_make_datex2(time=t))

    with patch.object(connector, "get_client", return_value=client):
        alerts = await connector._fetch()

    assert len(alerts) == 1
    assert alerts[0].source == AlertSource.DGT
    assert alerts[0].geometry["coordinates"] == [-3.7, 40.4]


@pytest.mark.asyncio
async def test_dgt_mapeo_severidades():
    """Comprobar que cada nivel DATEX2 se traduce al AlertSeverity correcto."""
    c = DgtConnector()
    assert c._map_severity("highest") == AlertSeverity.EXTREME
    assert c._map_severity("severe") == AlertSeverity.EXTREME
    assert c._map_severity("high") == AlertSeverity.SEVERE
    assert c._map_severity("medium") == AlertSeverity.MODERATE
    assert c._map_severity("low") == AlertSeverity.MINOR
    assert c._map_severity(None) == AlertSeverity.UNKNOWN
    assert c._map_severity("desconocido") == AlertSeverity.UNKNOWN


@pytest.mark.asyncio
async def test_dgt_sin_coordenadas_no_genera_alerta():
    """Registros DATEX2 sin locationForDisplay se saltan."""
    connector = DgtConnector()

    xml_sin_loc = b"""<?xml version="1.0" encoding="UTF-8"?>
    <d2LogicalModel xmlns="http://datex2.eu/schema/2/2_0">
      <payloadPublication>
        <situation>
          <situationRecord id="DGT-SIN-LOC">
            <situationRecordCreationTime>2024-03-26T10:00:00+00:00</situationRecordCreationTime>
            <severity>high</severity>
          </situationRecord>
        </situation>
      </payloadPublication>
    </d2LogicalModel>"""

    client = _mock_dgt_client(xml_sin_loc)

    with patch.object(connector, "get_client", return_value=client):
        alerts = await connector._fetch()

    assert len(alerts) == 0
