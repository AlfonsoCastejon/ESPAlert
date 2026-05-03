# 7. Pruebas

## Metodología

Estrategia híbrida: TDD parcial en los routers críticos (auth, alerts, admin) y pruebas manuales para la interfaz. La regla práctica fue escribir test antes del código solo cuando el contrato (entrada/salida HTTP) estaba claro; en componentes UI con iteración visual rápida, los tests se añadieron después de estabilizar la pantalla.

Las pruebas se ejecutan localmente y en CI (GitHub Actions, workflow `ci.yml`) en cada pull request y en cada push a `main`. Si fallan, el merge se bloquea.

## Tipos de prueba

### Unitarias y de integración del backend

- Framework: `pytest` con `pytest-asyncio` (modo `auto`).
- Mocking: la sesión async de SQLAlchemy se sustituye por `AsyncMock` en `tests/conftest.py`. Cada test recibe una sesión limpia y se evita tocar la base de datos real.
- Cliente HTTP: `httpx.AsyncClient` con la app FastAPI montada en memoria (`ASGITransport`).

Ficheros (`apps/api/tests/`):

- `test_auth.py` — registro, login, logout, `me`, cambio de contraseña, validación de fortaleza, rate limit.
- `test_alerts.py` — listado, filtros, paginación, detalle, histórico.
- `test_admin.py` — protección por rol, cambio de rol, eliminación de alertas, gestión mesh.
- `test_user.py` — favoritos y preferencias.
- `test_push.py` — alta y baja de suscripción VAPID.
- `test_aemet.py` — cliente AEMET con mocks de HTTPX.
- `test_dgt.py` — parseo del feed DGT.
- `test_xml_parser.py` — CAP multi-idioma con XMLs reales abreviados.
- `test_connectors.py` — base común de conectores.
- `test_health.py` — endpoint de salud.
- `test_tasks.py` — tareas Celery (sin broker real, llamada directa a la función).
- `test_ws.py` — autenticación previa al `accept()` en el WebSocket.
- `test_config.py` — carga de variables de entorno.

Total: 65 tests verdes.

### Frontend

- Framework: Vitest sobre `jsdom`, con `@testing-library/react` y `@testing-library/user-event`.
- Cobertura: componentes (`AlertCard`, `AlertBadge`, `Filters`, `CookieBanner`, `Header`), hooks de fetch y reductores de estado.
- Total: 59 tests verdes.

### Cobertura

Reportada con `pytest-cov`:

```bash
cd apps/api && pytest --cov
```

Cobertura actual: 66 por ciento de líneas en `app/`. Las áreas con menor cobertura son los workers Celery (difíciles de medir por su naturaleza asíncrona externa) y el cliente MQTT (depende de un broker).

### Pruebas manuales E2E

Flujo completo verificado a mano antes de cada release:

1. Registrar nueva cuenta.
2. Iniciar sesión y comprobar la cookie `espalert_session`.
3. Buscar municipio en `/prediccion`, ver predicción.
4. Marcar una alerta como favorita.
5. Activar permisos de notificación, suscribirse a push.
6. Forzar una alerta de prueba en BD y comprobar que llega push y aparece en el mapa por WebSocket.

### Verificaciones extra

- Accesibilidad: WAVE sobre `/`, `/alertas`, `/registro` y `/perfil`. Cero errores, cero contrastes insuficientes.
- Lighthouse: desktop 93, móvil 66 (recogido en `06-desarrollo.md`).
- Headers de seguridad: `curl -I https://espalert.app` debe mostrar `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` y `Permissions-Policy`.
- Rate limit: ráfagas con `for i in {1..20}; do curl -X POST .../auth/login; done` deben empezar a devolver 429 a partir de la 11ª llamada.

## Cómo ejecutar las pruebas

Backend:

```bash
cd apps/api
pytest                     # todos los tests
pytest --cov               # con cobertura
pytest tests/test_auth.py  # un fichero
```

Frontend:

```bash
cd apps/web
pnpm test                  # ejecución única
pnpm test --watch          # modo desarrollo
```
