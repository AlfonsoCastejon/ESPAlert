# 3. Instalación y preparación

Esta guía explica cómo levantar ESPAlert en local con Docker. La opción nativa (Python y Node directamente en la máquina) está documentada al final como alternativa para desarrollo.

## Requisitos previos

- Docker Desktop 24 o superior (incluye Docker Compose v2).
- Git.
- Cuenta y clave en AEMET OpenData (gratuita): [https://opendata.aemet.es](https://opendata.aemet.es).
- Opcional para desarrollo nativo: Node.js 20 LTS, pnpm 9, Python 3.12.

## Pasos de instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/alfonsocastejon/ESPAlert.git
cd ESPAlert
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` y completa al menos:

- `AEMET_API_KEY`: clave personal de AEMET OpenData.
- `JWT_SECRET`: secreto largo y aleatorio. Genéralo con `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
- `VAPID_PUBLIC_KEY` y `VAPID_PRIVATE_KEY`: claves VAPID para Web Push. Genéralas con `npx web-push generate-vapid-keys`.
- `VAPID_CLAIMS_EMAIL`: tu correo de contacto.
- `POSTGRES_PASSWORD`: contraseña de la base de datos local.

El resto de variables (`POSTGRES_DB`, `REDIS_URL`, `CELERY_BROKER_URL`, etc.) ya tienen valores por defecto que funcionan en compose.

### 3. Levantar los servicios

```bash
docker compose up -d
```

Compose arranca seis servicios: PostgreSQL con PostGIS, Redis, la API FastAPI, los workers Celery (worker y beat) y el frontend Next.js.

### 4. Aplicar migraciones de base de datos

```bash
docker compose exec api alembic upgrade head
```

Esto crea las tablas y la extensión PostGIS necesarias.

### 5. Verificar que todo arranca

```bash
curl http://localhost:8000/api/health
```

Debe responder con `{"status": "ok"}`. Abre el frontend en [http://localhost:3000](http://localhost:3000) y comprueba que se carga el mapa.

La documentación interactiva de la API está disponible en [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI) y [http://localhost:8000/redoc](http://localhost:8000/redoc).

## Variables de entorno

- `ENV`: `development` o `production`. Activa logs de debug y desactiva la cookie segura en desarrollo.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: credenciales de la base de datos.
- `DATABASE_URL`: URL completa SQLAlchemy. En compose se construye automáticamente; solo define esta variable si ejecutas la API fuera de Docker.
- `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`: conexión a Redis.
- `ALLOWED_ORIGINS`: lista CSV de orígenes permitidos para CORS (`http://localhost:3000` en local).
- `MQTT_BROKER_URL`: broker MQTT para Meshtastic. En producción se usa un Mosquitto propio levantado como servicio Docker (`mqtt://mqtt:1883` dentro de la red interna). En local funciona con cualquier broker MQTT.
- `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_CLAIMS_EMAIL`: claves Web Push.
- `AEMET_API_KEY`: clave personal de AEMET OpenData.
- `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_DAYS`: configuración del token de sesión.
- `CADDY_DOMAIN`: dominio que usará Caddy en producción para emitir certificados.
- `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`: URLs públicas que el frontend usará para hablar con la API.

## Detener y limpiar

```bash
docker compose down            # detiene y elimina contenedores
docker compose down -v         # incluye volúmenes (borra base de datos)
```

## Desarrollo nativo (alternativa sin Docker)

Para iterar más rápido sin reconstruir contenedores:

### Backend

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate           # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd apps/web
pnpm install
pnpm dev
```

Recuerda tener un Postgres y un Redis accesibles, ya sea por Docker o instalados en el sistema.

## Troubleshooting habitual

- `docker compose up` falla con "port already in use": para procesos que usen 3000, 5432, 6379 u 8000.
- Migraciones fallan con "extension postgis not found": la imagen `postgis/postgis` ya la incluye; reconstruye con `docker compose build --no-cache db`.
- Las claves VAPID se ven inválidas: regenéralas con `npx web-push generate-vapid-keys` y reinicia la API (`docker compose restart api`).
