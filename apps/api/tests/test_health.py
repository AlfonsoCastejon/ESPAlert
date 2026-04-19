"""Tests del endpoint /health."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient


def test_health_sin_logs_devuelve_running_para_cada_fuente(build_app, override_deps, mock_db_session):
    app = build_app(include_health=True)
    override_deps(app, db=mock_db_session)

    mock_db_session.scalar = AsyncMock(return_value=None)

    client = TestClient(app)
    res = client.get("/api/health")

    assert res.status_code == 200
    data = res.json()
    assert data["api"] == "ok"
    # Debe haber una entrada por cada fuente declarada en AlertSource
    from app.models.enums import AlertSource
    assert len(data["sources"]) == len(list(AlertSource))
    for s in data["sources"]:
        assert s["status"] == "running"
        assert s["last_run"] is None


def test_health_con_log_exitoso_devuelve_success(build_app, override_deps, mock_db_session):
    app = build_app(include_health=True)
    override_deps(app, db=mock_db_session)

    from app.models.enums import AlertSource, FetchStatus

    fake_log = MagicMock()
    fake_log.status = FetchStatus.SUCCESS
    fake_log.started_at = datetime.now(timezone.utc)
    fake_log.alerts_new = 5
    fake_log.error_message = None

    async def _scalar(q):
        return fake_log

    mock_db_session.scalar = AsyncMock(side_effect=_scalar)

    client = TestClient(app)
    res = client.get("/api/health")

    assert res.status_code == 200
    data = res.json()
    assert data["api"] == "ok"
    assert all(s["status"] == "success" for s in data["sources"])
    assert all(s["alerts_new"] == 5 for s in data["sources"])
