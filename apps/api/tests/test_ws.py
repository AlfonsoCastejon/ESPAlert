"""Tests del endpoint WebSocket /ws (auth por cookie)."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


def test_ws_sin_cookie_se_rechaza(build_app):
    app = build_app(include_ws=True)
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws"):
            pass
    assert exc.value.code == 1008


def test_ws_cookie_invalida_se_rechaza(build_app):
    app = build_app(include_ws=True)
    client = TestClient(app)
    client.cookies.set("espalert_session", "token-no-valido")
    with patch("app.routers.ws.auth_service") as svc:
        svc.decode_access_token = lambda _t: None
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect("/ws"):
                pass
    assert exc.value.code == 1008


def test_ws_usuario_inactivo_se_rechaza(build_app, fake_user):
    fake_user.is_active = False
    app = build_app(include_ws=True)
    client = TestClient(app)
    client.cookies.set("espalert_session", "token-valido")
    with patch("app.routers.ws.auth_service") as svc, \
         patch("app.routers.ws.AsyncSessionLocal") as session_local:
        svc.decode_access_token = lambda _t: fake_user.id
        svc.get_user_by_id = AsyncMock(return_value=fake_user)
        session_local.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
        session_local.return_value.__aexit__ = AsyncMock(return_value=None)
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect("/ws"):
                pass
    assert exc.value.code == 1008
