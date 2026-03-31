"""Tests de la pipeline fetch + persistencia de Celery tasks."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.enums import AlertSource, AlertType, AlertSeverity, AlertStatus
from app.schemas.alert import AlertCreate


def _make_alert(**overrides) -> AlertCreate:
    defaults = {
        "external_id": "test-001",
        "source": AlertSource.AEMET,
        "alert_type": AlertType.METEOROLOGICAL,
        "severity": AlertSeverity.MODERATE,
        "status": AlertStatus.ACTUAL,
        "headline": "Alerta de prueba",
    }
    defaults.update(overrides)
    return AlertCreate(**defaults)


@pytest.mark.asyncio
async def test_fetch_and_persist_guarda_todas_las_alertas():
    """Cada alerta devuelta por el conector debe pasar por upsert_alert."""
    from app.workers.tasks import _fetch_and_persist

    alertas = [_make_alert(external_id=f"id-{i}") for i in range(3)]

    mock_connector_cls = MagicMock()
    mock_connector_cls.return_value.fetch = AsyncMock(return_value=alertas)

    mock_upsert = AsyncMock()
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.workers.tasks.upsert_alert", mock_upsert), \
         patch("app.workers.tasks.AsyncSessionLocal", return_value=mock_session):
        await _fetch_and_persist(mock_connector_cls, "TEST")

    assert mock_upsert.await_count == 3
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_and_persist_lista_vacia_no_toca_bd():
    """Si no hay alertas nuevas, ni siquiera se abre sesion de BD."""
    from app.workers.tasks import _fetch_and_persist

    mock_connector_cls = MagicMock()
    mock_connector_cls.return_value.fetch = AsyncMock(return_value=[])

    mock_session_local = MagicMock()

    with patch("app.workers.tasks.AsyncSessionLocal", mock_session_local):
        await _fetch_and_persist(mock_connector_cls, "TEST")

    mock_session_local.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_and_persist_conector_none_es_noop():
    """Cuando el import del conector fallo (None), no se ejecuta nada."""
    from app.workers.tasks import _fetch_and_persist

    mock_session_local = MagicMock()

    with patch("app.workers.tasks.AsyncSessionLocal", mock_session_local):
        await _fetch_and_persist(None, "INEXISTENTE")

    mock_session_local.assert_not_called()
