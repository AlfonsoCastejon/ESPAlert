"""Tests del router de suscripciones push."""
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _payload():
    return {
        "endpoint": "https://fcm.googleapis.com/fcm/send/abc123",
        "p256dh": "BNbwK3pub",
        "auth": "authSecret",
    }


def test_subscribe_devuelve_201_al_registrar(build_app, override_deps, mock_db_session):
    app = build_app(include_push=True)
    override_deps(app, db=mock_db_session)

    with patch("app.routers.push.push_service") as svc:
        svc.subscribe = AsyncMock()

        client = TestClient(app)
        res = client.post("/api/push/subscribe", json=_payload())

    assert res.status_code == 201
    assert res.json()["ok"] is True


def test_subscribe_con_payload_invalido_devuelve_422(build_app, override_deps, mock_db_session):
    app = build_app(include_push=True)
    override_deps(app, db=mock_db_session)

    client = TestClient(app)
    res = client.post("/api/push/subscribe", json={"endpoint": "falta-todo"})

    assert res.status_code == 422


def test_unsubscribe_existente_devuelve_200(build_app, override_deps, mock_db_session):
    app = build_app(include_push=True)
    override_deps(app, db=mock_db_session)

    with patch("app.routers.push.push_service") as svc:
        svc.unsubscribe = AsyncMock(return_value=True)

        client = TestClient(app)
        res = client.request(
            "DELETE",
            "/api/push/subscribe",
            json={"endpoint": "https://fcm.googleapis.com/fcm/send/abc"},
        )

    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_unsubscribe_inexistente_devuelve_404(build_app, override_deps, mock_db_session):
    app = build_app(include_push=True)
    override_deps(app, db=mock_db_session)

    with patch("app.routers.push.push_service") as svc:
        svc.unsubscribe = AsyncMock(return_value=False)

        client = TestClient(app)
        res = client.request(
            "DELETE",
            "/api/push/subscribe",
            json={"endpoint": "https://fcm.googleapis.com/fcm/send/nope"},
        )

    assert res.status_code == 404
