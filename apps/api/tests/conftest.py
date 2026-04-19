import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

# Configurar variables de entorno dummy MÍNIMAS requeridas por pydantic-settings
# antes de que las partes de FastAPI intenten importarlas y fallen en CI.
os.environ["ENV"] = "development"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost:5432/espalert"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["AEMET_API_KEY"] = "fake_test_key"
os.environ["ALLOWED_ORIGINS"] = "*"
os.environ["VAPID_PUBLIC_KEY"] = "fake_pub_key"
os.environ["VAPID_PRIVATE_KEY"] = "fake_priv_key"
os.environ["MQTT_BROKER_URL"] = "mqtt://localhost:1883"
os.environ["JWT_SECRET"] = "fake_jwt_secret_for_tests"


@pytest.fixture(autouse=True)
def env_setup():
    pass


@pytest.fixture
def mock_db_session():
    """Sesión de BD fake (AsyncMock) lista para inyectar en dependencias."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.add = lambda obj: None
    return session


@pytest.fixture
def fake_user():
    """Usuario normal (rol 'user') de prueba."""
    from app.models.user import User, UserRole

    u = User()
    u.id = uuid.uuid4()
    u.email = "user@test.com"
    u.password_hash = "$2b$12$fakehash"
    u.role = UserRole.user
    u.is_active = True
    u.created_at = datetime.now(timezone.utc)
    u.updated_at = datetime.now(timezone.utc)
    return u


@pytest.fixture
def fake_admin():
    """Usuario admin de prueba."""
    from app.models.user import User, UserRole

    u = User()
    u.id = uuid.uuid4()
    u.email = "admin@test.com"
    u.password_hash = "$2b$12$fakehash"
    u.role = UserRole.admin
    u.is_active = True
    u.created_at = datetime.now(timezone.utc)
    u.updated_at = datetime.now(timezone.utc)
    return u


def _build_test_app(include_auth=False, include_user=False, include_admin=False,
                    include_push=False, include_health=False):
    """Construye una app FastAPI mínima (sin lifespan) con los routers solicitados."""
    from fastapi import FastAPI

    app = FastAPI()
    if include_auth:
        from app.routers import auth
        app.include_router(auth.router, prefix="/api")
    if include_user:
        from app.routers import user
        app.include_router(user.router, prefix="/api/user")
    if include_admin:
        from app.routers import admin
        app.include_router(admin.router, prefix="/api/admin")
    if include_push:
        from app.routers import push
        app.include_router(push.router, prefix="/api")
    if include_health:
        from app.routers import health
        app.include_router(health.router, prefix="/api")
    return app


@pytest.fixture
def build_app():
    """Factory que devuelve una app de test configurable."""
    return _build_test_app


@pytest.fixture
def override_deps():
    """Helper para registrar overrides de dependencias en una app."""

    def _override(app, *, db=None, user=None, admin=None):
        from app.dependencies import get_current_admin, get_current_user, get_db

        if db is not None:
            async def _get_db():
                yield db
            app.dependency_overrides[get_db] = _get_db
        if user is not None:
            async def _get_user():
                return user
            app.dependency_overrides[get_current_user] = _get_user
        if admin is not None:
            async def _get_admin():
                return admin
            app.dependency_overrides[get_current_admin] = _get_admin

    return _override
