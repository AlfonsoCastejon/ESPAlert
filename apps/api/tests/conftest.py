import os
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
