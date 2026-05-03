# 6. Desarrollo

## Secuencia de desarrollo

El proyecto se construyó por capas, desde la infraestructura hacia la interfaz, en sprints de dos semanas:

1. **Andamiaje y stack** (sprint 1). Estructura monorepo con `apps/api` y `apps/web`. Dockerfiles base, `docker-compose.yml`, integración Postgres + PostGIS, Redis, FastAPI minimal y Next 16 vacío.
2. **Modelo y migraciones** (sprint 1). Modelos SQLAlchemy 2.0 con async, alembic para migraciones, primeras tablas (`users`, `alerts`).
3. **Conector AEMET** (sprint 2). Cliente HTTPX, parseo CAP XML multi-idioma, tarea Celery `fetch_aemet_task`, persistencia con upsert por `external_id`.
4. **Router de alertas y frontend listado** (sprint 2). Endpoint `/api/alerts` con paginación y filtros, página `/alertas` con tabla, badges de severidad y filtros.
5. **Mapa MapLibre** (sprint 3). Tiles OpenFreeMap, capas GeoJSON de comunidades autónomas y provincias, leyenda, marcadores con color por severidad, popup al clic.
6. **Auth con JWT en cookie** (sprint 3). Registro, login, logout, dependencia `get_current_user`, hashing bcrypt con passlib, validación Pydantic, formularios en cliente.
7. **Favoritos y preferencias** (sprint 4). Tablas `user_favorites` y `user_preferences`, endpoints REST, integración en el listado.
8. **Conectores adicionales** (sprint 4). IGN (sismicidad), DGT (incidencias) y MeteoAlarm (paraguas europeo). Cada conector hereda de una clase base.
9. **Meshtastic vía MQTT** (sprint 5). Cliente paho-mqtt, suscripción al broker Mosquitto propio (servicio Docker), persistencia de mensajes en `mesh_messages`, retransmisión de alertas severas hacia la red LoRa a través de un nodo Meshtastic gateway que se autentica contra el broker, panel admin para revisar y purgar.
10. **Push web** (sprint 5). Generación VAPID, service worker, suscripción desde el frontend, envío con `pywebpush` desde un worker Celery.
11. **Panel admin** (sprint 6). Roles (`user`/`admin`), dependencia `get_current_admin`, CRUD limitado.
12. **CI/CD** (sprint 6). GitHub Actions con `ci.yml` (typecheck + tests + build) y `deploy.yml` (push a ghcr.io + SSH al droplet).
13. **Optimización Lighthouse** (sprint 7). Simplificación GeoJSON con mapshaper, defer del init MapLibre con `requestIdleCallback`, resultado: 64 → 93 desktop y 45 → 66 móvil.
14. **Endurecimiento de seguridad** (sprint 7). Rate limit con slowapi en endpoints de auth, headers de seguridad en Caddy, autenticación previa en `/ws`, restricción de CORS, lock en cache de municipios.
15. **Accesibilidad y SEO** (sprint 7). Skip-link, focus-visible global, sitemap dinámico, manifest, OpenGraph y Twitter Card, robots con sitemap.

## Arquitectura MVC en el backend

El backend respeta una separación estricta en cuatro capas inspirada en MVC, con una capa adicional de validación tomada de FastAPI:

- **Modelo** (`app/models/`): clases SQLAlchemy 2.0 que definen las tablas (`User`, `Alert`, `UserFavorite`, `UserPreferences`, `PushSubscription`, `MeshMessage`). Aquí viven las relaciones y los tipos de columna, incluida la geometría PostGIS.
- **Schemas** (`app/schemas/`): clases Pydantic que validan entrada y serializan salida. Funcionan como el contrato público de la API y permiten generar OpenAPI automáticamente.
- **Servicios** (`app/services/`): lógica de negocio. `AuthService` se encarga del hash bcrypt y de la emisión y verificación de JWT; `AlertService` orquesta filtros, paginación y consultas espaciales; `PushService` envía notificaciones; `MeshService` persiste mensajes MQTT. Los servicios reciben la sesión de BD por inyección, nunca la abren directamente.
- **Controladores** (`app/routers/`): cada router agrupa endpoints por dominio (`auth.py`, `alerts.py`, `admin.py`, `user.py`, `forecast.py`, `push.py`, `mesh.py`, `ws.py`). Solo orquestan: validan con el schema, delegan en el servicio y devuelven el modelo serializado. Cero lógica de negocio en los routers.

Esta separación se traduce literalmente en el sistema de carpetas, lo que facilita encontrar dónde tocar al añadir o modificar funcionalidades. Los tests siguen la misma división: `test_alerts.py` cubre el router, los servicios se cubren a través de los tests del router con la sesión mockeada.

### Autorización por rol

La columna `role` de `users` admite `user` o `admin`. Dos dependencias de FastAPI controlan el acceso:

- `get_current_user`: extrae la cookie `espalert_session`, decodifica el JWT, carga al usuario y verifica `is_active=True`. Si falla, `401`.
- `get_current_admin`: encadena `get_current_user` y comprueba `role == "admin"`. Si falla, `403`.

Los routers la aplican declarativamente:

```python
@router.delete("/admin/alerts/{alert_id}")
async def delete_alert(
    alert_id: UUID,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Response:
    ...
```

Esto evita duplicar checks y permite añadir roles nuevos cambiando una sola dependencia.

## Frontend: sintaxis moderna y comunicación asíncrona

El frontend está escrito íntegramente en TypeScript estricto (ES2022) sobre React 18 con Next.js 16. Características modernas usadas de forma sistemática:

- `async/await` en toda llamada a la API.
- *Optional chaining* y *nullish coalescing* (`?.`, `??`) para acceder a estructuras opcionales sin condicionales anidados.
- Desestructuración con valores por defecto en props y respuestas de API.
- *Template literals* para construir URLs (`/api/alerts?source=${source}`).
- Módulos ES nativos con imports relativos resueltos por TypeScript.

### Estructuras definidas por el usuario

El frontend define los siguientes tipos propios:

- **Interfaces TypeScript** en `src/types/` (`Alert`, `User`, `UserPreferences`, `MeshMessage`, `ForecastDay`) que tipan tanto la respuesta de la API como las props de los componentes.
- **Tipos unión literal** para enums: `type Severity = "minor" | "moderate" | "severe" | "extreme"`.
- **Componentes funcionales** como funciones tipadas: `function AlertCard({ alert }: AlertCardProps): JSX.Element`.
- **Custom hooks** que encapsulan lógica reutilizable: `useAlerts`, `useAlertsWebSocket`, `useTheme`, `useDebounce`, `usePushSubscription`.
- **Contextos React** (`ThemeContext`, `AuthContext`) implementados con clases lógicas (provider + consumer) para inyección dependencias sin prop-drilling.
- **Servicios cliente** en `src/lib/api.ts` y `src/lib/auth.ts` que actúan como capa de acceso a la API.

### Librerías de actualización dinámica incorporadas

- **MapLibre GL JS** para renderizado vectorial del mapa con animaciones (`flyTo`, `easeTo`), capas dinámicas y eventos sobre features.
- **Lucide React** para iconografía SVG inline con tree-shaking.
- **Sass (Dart Sass)** como preprocesador CSS.
- **`pywebpush`** y **`web-push`** (CLI) en backend para Push API con cifrado VAPID.

Para fetch y estado de la API se usan las APIs nativas del navegador (`fetch`, `WebSocket`, `Cache API` vía Service Worker), evitando dependencias innecesarias en el bundle. La actualización en vivo combina polling con `setInterval` y push por WebSocket, ambas mecanismos asíncronos del propio navegador.

### Manejo de eventos y validación de formularios

Aunque React abstrae `addEventListener`, el manejo de eventos sigue exactamente el modelo del DOM: `onClick`, `onSubmit`, `onChange`, `onKeyDown`. El `CookieBanner` cierra al pulsar `Escape` mediante `addEventListener` directo en `useEffect`, evidenciando el uso del modelo de eventos del navegador.

La validación de formularios (registro, login, cambio de contraseña) se hace en dos niveles:

1. **Cliente**: validación en tiempo real con regex (`/[A-Z]/`, `/[a-z]/`, `/[0-9]/`) y longitud mínima. El indicador de fortaleza se actualiza con cada `onChange`.
2. **Servidor**: validación con Pydantic (`@field_validator`) que rechaza con `422` si el cliente se ha saltado las reglas.

### Comunicación asíncrona

Tres mecanismos coexisten:

- **`fetch`** con `credentials: "include"` para todas las llamadas REST. Devuelve JSON tipado contra interfaces TypeScript declaradas en `src/types/`.
- **WebSocket nativo** (`new WebSocket(url)`) en `useAlertsWebSocket`. Reconecta con backoff exponencial al cerrar.
- **Service Worker + Push API** para notificaciones, registrado en `public/sw.js` y suscrito vía `navigator.serviceWorker.ready` y `pushManager.subscribe`.

### Manipulación del DOM y objetos predefinidos

React reconcilia el DOM internamente, pero hay puntos en los que se accede directamente:

- `document.documentElement.setAttribute('data-theme', tema)` en el toggle de tema.
- `window.localStorage` para persistir preferencias (`espalert_theme`).
- `window.matchMedia('(prefers-color-scheme: dark)')` para detectar preferencia inicial.
- `window.requestIdleCallback` para diferir la inicialización de MapLibre y reducir el TBT.
- `navigator.serviceWorker` para el Push API.

## Decisiones técnicas

### FastAPI vs Django REST

FastAPI: tipado fuerte con Pydantic, async nativo, OpenAPI generado automáticamente. Con cuatro APIs externas que se consultan por polling, el modelo async ahorra threads. Django habría exigido más configuración para el mismo resultado.

### Next.js 16 con App Router

App Router permite mezclar componentes servidor (SEO, metadata) y cliente (mapa, formularios) en el mismo árbol. La metadata por ruta vía `layout.tsx` aporta directamente puntos de SEO en la rúbrica. La contrapartida es que Next 16 es muy reciente: hubo que sortear cambios respecto a Next 15 (eliminación de `next lint`, requisitos nuevos en `metadata`).

### PostgreSQL + PostGIS frente a SQLite

PostGIS aporta tipos `geometry` y operadores espaciales (`ST_Intersects`, índices GIST). El mapa filtra por bounding box mediante una consulta con índice, lo que escala mucho mejor que cargar todas las alertas y filtrar en memoria.

### JWT en cookie httpOnly frente a localStorage

`localStorage` es accesible desde JavaScript y por tanto vulnerable a XSS. La cookie httpOnly con `SameSite=Lax` y `Secure=true` en producción no se expone al script y mitiga la fuga del token. La contrapartida es que toda llamada a la API debe ir con `credentials: "include"`.

### MapLibre GL frente a Mapbox

MapLibre es el fork OSS de Mapbox tras su cambio de licencia. Mismos tiles vector, mismos estilos, gratuito, sin token. Combinado con OpenFreeMap como proveedor de tiles, el coste operativo del mapa es cero.

### SCSS con ITCSS frente a Tailwind

El TFG está vinculado al módulo DIW que valora explícitamente el uso de preprocesadores. ITCSS aporta una arquitectura por capas que se entiende y defiende mejor que clases utilitarias. Permite reutilizar tokens (variables, mixins) y mantener BEM consistente.

### Celery con Beat frente a APScheduler in-process

Celery separa la API del polling. Si AEMET tarda 30 segundos en responder, el endpoint público no se bloquea. Beat aporta el cron de tareas periódicas (cada 2-5 minutos por conector). Redis sirve a la vez de broker y backend de resultados.

## Dificultades encontradas y cómo se superaron

### Parseo CAP XML multi-idioma

Los avisos de AEMET y MeteoAlarm vienen en formato CAP, un XML con varios bloques `<info>` (uno por idioma). El parser inicial cogía siempre el primero, lo que daba títulos en inglés. Solución: priorizar el bloque con `<language>es</language>` o el genérico `und`. Tests dedicados (`test_xml_parser.py`) cubren los formatos reales descargados.

### Lighthouse en el mapa

La home arrancaba con TBT (Total Blocking Time) altísimo: 3 segundos en móvil. El culpable era la inicialización síncrona de MapLibre y la descarga del GeoJSON de provincias (11.6 MB). Soluciones aplicadas:

- Simplificación con `mapshaper` al 5 por ciento manteniendo formas (`-simplify 5% keep-shapes -o precision=0.0001`). De 11.6 MB a 400 KB.
- Diferir la creación del mapa con `requestIdleCallback` para no bloquear el hilo principal durante el TTI.
- Diferir la carga de capas adicionales tras la primera interacción.

Resultado: Lighthouse desktop 64 → 93, móvil 45 → 66.

### Race en cache de municipios

El cache global de municipios de AEMET (`_cache_municipios`) se inicializaba sin sincronización. En arranques con múltiples requests concurrentes, dos coroutines podían dispararse a descargar a la vez. Se añadió un `asyncio.Lock` con doble comprobación.

### Autenticación del WebSocket

El endpoint `/ws` aceptaba cualquier conexión sin validar la cookie. Vector de DoS y exposición de eventos a anónimos. Se introdujo validación previa al `accept()` con extracción de cookie, decode de JWT y comprobación del usuario activo en BD. Si falla, se cierra con código 1008 (policy violation).

## Control de versiones

- Repositorio en GitHub: ramas `feature/*` que se mergean a `main` por pull request.
- Convención de mensajes: `feat:`, `fix:`, `perf:`, `chore:`, `docs:` (commits convencionales).
- Branch `main` siempre desplegable. CI obligatoria antes del merge.
- GitHub Projects con tablero kanban: campos Estado, Sprint, Prioridad, Estimación, Categoría.
- Sprint Review cada dos semanas con vídeo demo de menos de cinco minutos.

## Fragmentos de código relevantes

### Lock con doble comprobación en cache de municipios

```python
async def _obtener_municipios() -> list[dict]:
    global _cache_municipios
    if _cache_municipios is not None:
        return _cache_municipios

    async with _cache_lock:
        if _cache_municipios is not None:
            return _cache_municipios
        # ... descarga y persiste el cache
        _cache_municipios = municipios
        return municipios
```

El doble `if` evita que dos coroutines en cola descarguen el dato dos veces tras adquirir el lock.

### Auth previa al accept en WebSocket

```python
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, ws_manager: WebSocketManagerDep) -> None:
    cookie = websocket.cookies.get(settings.SESSION_COOKIE_NAME)
    user_id = auth_service.decode_access_token(cookie) if cookie else None
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    # ...
```

Cerrar antes de `accept()` evita siquiera abrir el handshake con conexiones no autorizadas.

### Diferir el init del mapa al idle del navegador

```typescript
const enIdle = (cb: () => void) => {
  if ("requestIdleCallback" in window) {
    requestIdleCallback(cb, { timeout: 1500 });
  } else {
    setTimeout(cb, 200);
  }
};

useEffect(() => {
  enIdle(() => {
    mapRef.current = new maplibregl.Map({ /* ... */ });
  });
}, []);
```

Saca la creación del mapa de la ruta crítica de Time To Interactive.
