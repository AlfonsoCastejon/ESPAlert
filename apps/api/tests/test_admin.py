"""Tests del router de administración: gestión de usuarios, alertas y mesh."""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

from fastapi.testclient import TestClient


def _result_with_scalar(value):
    r = MagicMock()
    r.scalar = MagicMock(return_value=value)
    return r


def _result_with_scalar_one(value):
    r = MagicMock()
    r.scalar_one_or_none = MagicMock(return_value=value)
    return r


def _result_with_scalars_all(items):
    r = MagicMock()
    scalars = MagicMock()
    scalars.all = MagicMock(return_value=items)
    r.scalars = MagicMock(return_value=scalars)
    return r


def _mk_user(email="u@test.com", role_value="user"):
    from app.models.user import UserRole
    u = MagicMock()
    u.id = uuid.uuid4()
    u.email = email
    u.role = UserRole.user if role_value == "user" else UserRole.admin
    u.is_active = True
    u.created_at = datetime.now(timezone.utc)
    return u


# ──────────────────── Usuarios ────────────────────


def test_listar_usuarios_como_admin(build_app, override_deps, mock_db_session, fake_admin):
    app = build_app(include_admin=True)
    override_deps(app, db=mock_db_session, admin=fake_admin)

    users = [_mk_user(), _mk_user(email="otro@test.com")]
    mock_db_session.execute = AsyncMock(side_effect=[
        _result_with_scalar(2),
        _result_with_scalars_all(users),
    ])

    client = TestClient(app)
    res = client.get("/api/admin/users")

    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["role"] == "user"


def test_listar_usuarios_sin_sesion_devuelve_401(build_app):
    app = build_app(include_admin=True)
    client = TestClient(app)
    res = client.get("/api/admin/users")
    assert res.status_code == 401


def test_listar_usuarios_como_user_normal_devuelve_403(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_admin=True)
    override_deps(app, db=mock_db_session, user=fake_user)

    client = TestClient(app)
    res = client.get("/api/admin/users")

    assert res.status_code == 403


def test_cambiar_rol_usuario_inexistente_devuelve_404(build_app, override_deps, mock_db_session, fake_admin):
    app = build_app(include_admin=True)
    override_deps(app, db=mock_db_session, admin=fake_admin)

    mock_db_session.execute = AsyncMock(return_value=_result_with_scalar_one(None))

    client = TestClient(app)
    res = client.patch(f"/api/admin/users/{uuid.uuid4()}/role?role=admin")

    assert res.status_code == 404


def test_cambiar_rol_exitoso(build_app, override_deps, mock_db_session, fake_admin):
    app = build_app(include_admin=True)
    override_deps(app, db=mock_db_session, admin=fake_admin)

    target = _mk_user()
    mock_db_session.execute = AsyncMock(return_value=_result_with_scalar_one(target))

    client = TestClient(app)
    res = client.patch(f"/api/admin/users/{target.id}/role?role=admin")

    assert res.status_code == 200
    from app.models.user import UserRole
    assert target.role == UserRole.admin


# ──────────────────── Alertas ────────────────────


def test_eliminar_alerta_inexistente_devuelve_404(build_app, override_deps, mock_db_session, fake_admin):
    app = build_app(include_admin=True)
    override_deps(app, db=mock_db_session, admin=fake_admin)

    mock_db_session.execute = AsyncMock(return_value=_result_with_scalar_one(None))

    client = TestClient(app)
    res = client.delete(f"/api/admin/alerts/{uuid.uuid4()}")

    assert res.status_code == 404


def test_eliminar_alerta_existente_devuelve_204(build_app, override_deps, mock_db_session, fake_admin):
    app = build_app(include_admin=True)
    override_deps(app, db=mock_db_session, admin=fake_admin)

    alerta = MagicMock()
    mock_db_session.execute = AsyncMock(return_value=_result_with_scalar_one(alerta))

    client = TestClient(app)
    res = client.delete(f"/api/admin/alerts/{uuid.uuid4()}")

    assert res.status_code == 204
    mock_db_session.delete.assert_awaited_once_with(alerta)


# ──────────────────── Mensajes Mesh ────────────────────


def test_listar_mensajes_mesh_como_admin(build_app, override_deps, mock_db_session, fake_admin):
    app = build_app(include_admin=True)
    override_deps(app, db=mock_db_session, admin=fake_admin)

    msg = MagicMock()
    msg.id = uuid.uuid4()
    msg.node_id = "abcd1234"
    msg.channel = "LongFast"
    msg.message = "Hola mundo"
    msg.latitude = 40.4
    msg.longitude = -3.7
    msg.snr = 5.0
    msg.rssi = -90
    msg.received_at = datetime.now(timezone.utc)

    mock_db_session.execute = AsyncMock(side_effect=[
        _result_with_scalar(1),
        _result_with_scalars_all([msg]),
    ])

    client = TestClient(app)
    res = client.get("/api/admin/mesh")

    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["node_id"] == "abcd1234"


def test_listar_mensajes_mesh_sin_sesion_devuelve_401(build_app):
    app = build_app(include_admin=True)
    client = TestClient(app)
    res = client.get("/api/admin/mesh")
    assert res.status_code == 401


def test_eliminar_mensaje_mesh_inexistente_devuelve_404(build_app, override_deps, mock_db_session, fake_admin):
    app = build_app(include_admin=True)
    override_deps(app, db=mock_db_session, admin=fake_admin)

    mock_db_session.execute = AsyncMock(return_value=_result_with_scalar_one(None))

    client = TestClient(app)
    res = client.delete(f"/api/admin/mesh/{uuid.uuid4()}")

    assert res.status_code == 404


def test_eliminar_mensaje_mesh_existente_devuelve_204(build_app, override_deps, mock_db_session, fake_admin):
    app = build_app(include_admin=True)
    override_deps(app, db=mock_db_session, admin=fake_admin)

    msg = MagicMock()
    mock_db_session.execute = AsyncMock(return_value=_result_with_scalar_one(msg))

    client = TestClient(app)
    res = client.delete(f"/api/admin/mesh/{uuid.uuid4()}")

    assert res.status_code == 204


def test_eliminar_todos_los_mensajes_mesh_devuelve_204(build_app, override_deps, mock_db_session, fake_admin):
    app = build_app(include_admin=True)
    override_deps(app, db=mock_db_session, admin=fake_admin)

    mock_db_session.execute = AsyncMock(return_value=MagicMock())

    client = TestClient(app)
    res = client.delete("/api/admin/mesh")

    assert res.status_code == 204
    assert mock_db_session.commit.await_count == 1
