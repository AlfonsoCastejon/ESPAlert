import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'apps/api')))

import uuid
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

os.environ['ENV'] = 'development'
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://user:pass@localhost/db'
os.environ['REDIS_URL'] = 'redis'
os.environ['AEMET_API_KEY'] = 'key'
os.environ['ALLOWED_ORIGINS'] = 'http://localhost'
os.environ['VAPID_PUBLIC_KEY'] = 'pub'
os.environ['VAPID_PRIVATE_KEY'] = 'priv'
os.environ['MQTT_BROKER_URL'] = 'mqtt'

from app.main import app
from app.database import get_db
from app.models.enums import AlertSource

# Mock dependency
app.dependency_overrides[get_db] = lambda: AsyncMock()

with TestClient(app, raise_server_exceptions=False) as client:
    print("--------------------------------------------------")
    print("🔬 TESTEANDO ROUTERS ESPALERT API...")
    print("--------------------------------------------------\n")

    print("[ALERTS]")
    with patch('app.routers.alerts.alert_service.get_active_alerts', new_callable=AsyncMock) as m:
        m.return_value = (0, [])
        res = client.get("/api/alerts")
        print(f"  GET /api/alerts: HTTP {res.status_code} (Esperado: 200)")

    with patch('app.routers.alerts.alert_service.get_active_alerts', new_callable=AsyncMock) as m:
        m.side_effect = ValueError("Invalid bbox")
        res = client.get("/api/alerts?bbox=1,2")
        print(f"  GET /api/alerts?bbox=inválido: HTTP {res.status_code} (Esperado: 422)")
        
    res = client.get("/api/alerts?limit=-10")
    print(f"  GET /api/alerts?limit=-10 (Pydantic < 1): HTTP {res.status_code} (Esperado: 422)")

    with patch('app.routers.alerts.alert_service.get_alert_by_id', new_callable=AsyncMock) as m:
        m.return_value = None
        test_uuid = str(uuid.uuid4())
        res = client.get(f"/api/alerts/{test_uuid}")
        print(f"  GET /api/alerts/id (No existe): HTTP {res.status_code} (Esperado: 404)")

    print("\n[PUSH]")
    res = client.post("/api/push/subscribe", json={})
    print(f"  POST /api/push/subscribe (Datos Vacíos): HTTP {res.status_code} (Esperado: 422)")

    with patch('app.routers.push.push_service.subscribe', new_callable=AsyncMock):
        res = client.post("/api/push/subscribe", json={"endpoint": "http://a.com", "p256dh": "key", "auth": "key"})
        print(f"  POST /api/push/subscribe (Valida): HTTP {res.status_code} (Esperado: 201)")

    with patch('app.routers.push.push_service.unsubscribe', new_callable=AsyncMock) as m:
        m.return_value = False
        res = client.request("DELETE", "/api/push/subscribe", json={"endpoint": "http://a.com"})
        print(f"  DELETE /api/push/subscribe (No existe): HTTP {res.status_code} (Esperado: 404)")

    print("\n[MESH]")
    with patch('app.routers.mesh.mesh_service.get_mesh_messages_count', new_callable=AsyncMock) as mc, \
         patch('app.routers.mesh.mesh_service.get_mesh_messages', new_callable=AsyncMock) as mm:
        mc.return_value = 0
        mm.return_value = []
        res = client.get("/api/mesh/messages?limit=100")
        print(f"  GET /api/mesh/messages: HTTP {res.status_code} (Esperado: 200)")

    res = client.get("/api/mesh/messages?limit=50000")
    print(f"  GET /api/mesh/messages?limit=50000 (Pydantic max=200): HTTP {res.status_code} (Esperado: 422)")

    print("\n[HEALTH]")
    with patch('sqlalchemy.ext.asyncio.AsyncSession.scalar', new_callable=AsyncMock) as ds:
        ds.return_value = None
        res = client.get("/api/health")
        print(f"  GET /api/health: HTTP {res.status_code} (Esperado: 200)")

    print("\n[WEBSOCKETS]")
    try:
        with client.websocket_connect("/ws") as websocket:
            print("  WS /ws: Conexión Establecida (Esperado: Upgrade Correcto)")
    except Exception as e:
        print("  WS /ws Falló:", e)