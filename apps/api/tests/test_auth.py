"""Tests del router de autenticación: register, login, logout, /me."""
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _mk_user_response(user, email="user@test.com"):
    """Devuelve un objeto parecido al ORM que pasa model_validate de pydantic."""
    from app.schemas.auth import UserResponse
    return UserResponse.model_validate(user)


def test_register_usuario_nuevo_devuelve_201(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_auth=True)
    override_deps(app, db=mock_db_session)

    with patch("app.routers.auth.auth_service") as svc:
        svc.get_user_by_email = AsyncMock(return_value=None)
        svc.create_user = AsyncMock(return_value=fake_user)
        svc.create_access_token = lambda uid: ("fake-token", None)

        client = TestClient(app)
        res = client.post("/api/auth/register", json={
            "email": "nuevo@test.com",
            "password": "Password1",
        })

    assert res.status_code == 201
    assert res.json()["email"] == fake_user.email
    assert "espalert_session" in res.cookies


def test_register_email_ya_existente_devuelve_409(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_auth=True)
    override_deps(app, db=mock_db_session)

    with patch("app.routers.auth.auth_service") as svc:
        svc.get_user_by_email = AsyncMock(return_value=fake_user)

        client = TestClient(app)
        res = client.post("/api/auth/register", json={
            "email": "user@test.com",
            "password": "Password1",
        })

    assert res.status_code == 409


def test_register_password_debil_devuelve_422(build_app, override_deps, mock_db_session):
    app = build_app(include_auth=True)
    override_deps(app, db=mock_db_session)

    client = TestClient(app)
    res = client.post("/api/auth/register", json={
        "email": "a@b.com",
        "password": "abc123",
    })
    assert res.status_code == 422


def test_login_credenciales_correctas_devuelve_usuario(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_auth=True)
    override_deps(app, db=mock_db_session)

    with patch("app.routers.auth.auth_service") as svc:
        svc.authenticate = AsyncMock(return_value=fake_user)
        svc.create_access_token = lambda uid: ("fake-token", None)

        client = TestClient(app)
        res = client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "Password1",
        })

    assert res.status_code == 200
    assert res.json()["email"] == fake_user.email


def test_login_credenciales_invalidas_devuelve_401(build_app, override_deps, mock_db_session):
    app = build_app(include_auth=True)
    override_deps(app, db=mock_db_session)

    with patch("app.routers.auth.auth_service") as svc:
        svc.authenticate = AsyncMock(return_value=None)

        client = TestClient(app)
        res = client.post("/api/auth/login", json={
            "email": "bad@test.com",
            "password": "wrongpass",
        })

    assert res.status_code == 401


def test_logout_devuelve_204_y_borra_cookie(build_app):
    app = build_app(include_auth=True)
    client = TestClient(app)
    res = client.post("/api/auth/logout")
    assert res.status_code == 204


def test_me_devuelve_usuario_autenticado(build_app, override_deps, fake_user):
    app = build_app(include_auth=True)
    override_deps(app, user=fake_user)

    client = TestClient(app)
    res = client.get("/api/auth/me")

    assert res.status_code == 200
    assert res.json()["email"] == fake_user.email
    assert res.json()["role"] == "user"


def test_me_sin_sesion_devuelve_401(build_app):
    app = build_app(include_auth=True)
    client = TestClient(app)
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_change_password_con_actual_correcta_devuelve_204(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_auth=True)
    override_deps(app, db=mock_db_session, user=fake_user)

    with patch("app.routers.auth.auth_service") as svc:
        svc.verify_password = lambda plain, hashed: True
        svc.hash_password = lambda p: "nuevohash"

        client = TestClient(app)
        res = client.patch("/api/auth/password", json={
            "current_password": "Oldpass1",
            "new_password": "Newpass1",
        })

    assert res.status_code == 204
    assert fake_user.password_hash == "nuevohash"


def test_change_password_con_actual_incorrecta_devuelve_401(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_auth=True)
    override_deps(app, db=mock_db_session, user=fake_user)

    with patch("app.routers.auth.auth_service") as svc:
        svc.verify_password = lambda plain, hashed: False

        client = TestClient(app)
        res = client.patch("/api/auth/password", json={
            "current_password": "Wrongpass1",
            "new_password": "Newpass1",
        })

    assert res.status_code == 401


def test_change_password_nueva_debil_devuelve_422(build_app, override_deps, fake_user):
    app = build_app(include_auth=True)
    override_deps(app, user=fake_user)

    client = TestClient(app)
    res = client.patch("/api/auth/password", json={
        "current_password": "Oldpass1",
        "new_password": "abc",
    })
    assert res.status_code == 422


def test_change_password_sin_sesion_devuelve_401(build_app):
    app = build_app(include_auth=True)
    client = TestClient(app)
    res = client.patch("/api/auth/password", json={
        "current_password": "x",
        "new_password": "Newpass1",
    })
    assert res.status_code == 401
