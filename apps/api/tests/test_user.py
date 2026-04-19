"""Tests del router de usuario: favoritos y preferencias."""
import uuid
from unittest.mock import MagicMock, AsyncMock

from fastapi.testclient import TestClient


def _result_with_scalar(value):
    """Crea un resultado simulado de SQLAlchemy donde .scalar() devuelve value."""
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


def _result_with_rowcount(n):
    r = MagicMock()
    r.rowcount = n
    return r


# ──────────────────── Favoritos ────────────────────


def test_listar_favoritos_vacio(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_user=True)
    override_deps(app, db=mock_db_session, user=fake_user)

    mock_db_session.execute = AsyncMock(side_effect=[
        _result_with_scalar(0),
        _result_with_scalars_all([]),
    ])

    client = TestClient(app)
    res = client.get("/api/user/favorites")

    assert res.status_code == 200
    assert res.json() == {"total": 0, "items": []}


def test_agregar_favorito_alerta_inexistente_devuelve_404(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_user=True)
    override_deps(app, db=mock_db_session, user=fake_user)

    mock_db_session.execute = AsyncMock(return_value=_result_with_scalar(None))

    client = TestClient(app)
    res = client.post(f"/api/user/favorites/{uuid.uuid4()}")

    assert res.status_code == 404


def test_agregar_favorito_duplicado_devuelve_409(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_user=True)
    override_deps(app, db=mock_db_session, user=fake_user)

    alert_id = uuid.uuid4()
    fav_id = uuid.uuid4()
    mock_db_session.execute = AsyncMock(side_effect=[
        _result_with_scalar(alert_id),
        _result_with_scalar(fav_id),
    ])

    client = TestClient(app)
    res = client.post(f"/api/user/favorites/{alert_id}")

    assert res.status_code == 409


def test_agregar_favorito_exitoso_devuelve_201(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_user=True)
    override_deps(app, db=mock_db_session, user=fake_user)

    alert_id = uuid.uuid4()
    mock_db_session.execute = AsyncMock(side_effect=[
        _result_with_scalar(alert_id),
        _result_with_scalar(None),
    ])

    client = TestClient(app)
    res = client.post(f"/api/user/favorites/{alert_id}")

    assert res.status_code == 201
    assert mock_db_session.commit.await_count == 1


def test_quitar_favorito_inexistente_devuelve_404(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_user=True)
    override_deps(app, db=mock_db_session, user=fake_user)

    mock_db_session.execute = AsyncMock(return_value=_result_with_rowcount(0))

    client = TestClient(app)
    res = client.delete(f"/api/user/favorites/{uuid.uuid4()}")

    assert res.status_code == 404


def test_quitar_favorito_exitoso_devuelve_204(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_user=True)
    override_deps(app, db=mock_db_session, user=fake_user)

    mock_db_session.execute = AsyncMock(return_value=_result_with_rowcount(1))

    client = TestClient(app)
    res = client.delete(f"/api/user/favorites/{uuid.uuid4()}")

    assert res.status_code == 204


# ──────────────────── Preferencias ────────────────────


def test_obtener_preferencias_sin_guardar_devuelve_valores_nulos(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_user=True)
    override_deps(app, db=mock_db_session, user=fake_user)

    mock_db_session.execute = AsyncMock(return_value=_result_with_scalar_one(None))

    client = TestClient(app)
    res = client.get("/api/user/preferences")

    assert res.status_code == 200
    assert res.json() == {"region": None, "filters": None, "theme": None}


def test_obtener_preferencias_guardadas(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_user=True)
    override_deps(app, db=mock_db_session, user=fake_user)

    prefs = MagicMock()
    prefs.region = "madrid"
    prefs.filters = {"severidades": {"extreme": True}}
    prefs.theme = "dark"
    mock_db_session.execute = AsyncMock(return_value=_result_with_scalar_one(prefs))

    client = TestClient(app)
    res = client.get("/api/user/preferences")

    assert res.status_code == 200
    assert res.json()["region"] == "madrid"
    assert res.json()["theme"] == "dark"


def test_guardar_preferencias_crea_registro_nuevo(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_user=True)
    override_deps(app, db=mock_db_session, user=fake_user)

    mock_db_session.execute = AsyncMock(return_value=_result_with_scalar_one(None))

    client = TestClient(app)
    res = client.put("/api/user/preferences", json={
        "region": "andalucia",
        "filters": {"severidades": {"extreme": True}},
    })

    assert res.status_code == 200
    assert mock_db_session.commit.await_count == 1


def test_guardar_preferencias_actualiza_registro_existente(build_app, override_deps, mock_db_session, fake_user):
    app = build_app(include_user=True)
    override_deps(app, db=mock_db_session, user=fake_user)

    prefs = MagicMock()
    prefs.region = "madrid"
    prefs.filters = None
    prefs.theme = None
    mock_db_session.execute = AsyncMock(return_value=_result_with_scalar_one(prefs))

    client = TestClient(app)
    res = client.put("/api/user/preferences", json={
        "region": "galicia",
    })

    assert res.status_code == 200
    assert prefs.region == "galicia"


def test_endpoints_sin_sesion_devuelven_401(build_app):
    app = build_app(include_user=True)
    client = TestClient(app)

    assert client.get("/api/user/favorites").status_code == 401
    assert client.get("/api/user/preferences").status_code == 401
    assert client.put("/api/user/preferences", json={}).status_code == 401
