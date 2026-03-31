"""Tests de Settings: parseo de ALLOWED_ORIGINS desde variable de entorno."""
from app.config import Settings


_BASE = dict(
    ENV="development",
    DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
    REDIS_URL="redis://localhost:6379/0",
    AEMET_API_KEY="key",
    VAPID_PUBLIC_KEY="pub",
    VAPID_PRIVATE_KEY="priv",
    MQTT_BROKER_URL="mqtt://localhost:1883",
)


def test_origins_separados_por_comas():
    """'http://a,http://b' -> ['http://a', 'http://b']"""
    s = Settings(**_BASE, ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8000")
    assert s.allowed_origins_list == ["http://localhost:3000", "http://localhost:8000"]


def test_origins_wildcard():
    """'*' -> ['*']"""
    s = Settings(**_BASE, ALLOWED_ORIGINS="*")
    assert s.allowed_origins_list == ["*"]


def test_origins_con_espacios_se_limpian():
    """' http://a , http://b ' -> ['http://a', 'http://b']"""
    s = Settings(**_BASE, ALLOWED_ORIGINS=" http://a.com , http://b.com ")
    assert s.allowed_origins_list == ["http://a.com", "http://b.com"]
