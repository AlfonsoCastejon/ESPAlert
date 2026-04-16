"""Punto de entrada de la API FastAPI: lifespan, CORS y routers."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, alerts, auth, forecast, health, mesh, push, user, ws
from app.services.websocket_manager import ws_manager
from app.connectors.meshtastic import meshtastic_connector

is_debug = settings.ENV == "development"
logging.basicConfig(level=logging.DEBUG if is_debug else logging.INFO)
logger = logging.getLogger(__name__)

_PING_INTERVAL_SECONDS = 30    
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("Iniciando ESPAlert API y servicios...")
    
    # Arrancar conector Meshtastic
    await meshtastic_connector.start()
    
    # Arrancar latido del WebSocket manager
    async def _ping_loop() -> None:
        try:
            while True:
                await asyncio.sleep(_PING_INTERVAL_SECONDS)
                if ws_manager.active_count:
                    await ws_manager.broadcast_ping()
        except asyncio.CancelledError:
            logger.debug("WS ping loop cancelado")
            
    ping_task = asyncio.create_task(_ping_loop())

    yield

    # --- Shutdown ---
    logger.info("Deteniendo ESPAlert API y servicios...")
    
    # Parar latido del WebSocket manager
    ping_task.cancel()
    try:
        await ping_task
    except asyncio.CancelledError:
        pass
        
    # Parar conector Meshtastic
    await meshtastic_connector.stop()


app = FastAPI(
    title="ESPAlert API",
    description=(
        "API REST y WebSocket para el sistema de alertas multi-riesgo ESPAlert. "
        "Agrega alertas de AEMET, IGN, DGT, MeteoAlarm y la red mesh Meshtastic."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api"

app.include_router(alerts.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(push.router, prefix=API_PREFIX)
app.include_router(mesh.router, prefix=API_PREFIX)
app.include_router(forecast.router, prefix=API_PREFIX)
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(user.router, prefix=f"{API_PREFIX}/user")
app.include_router(admin.router, prefix=f"{API_PREFIX}/admin")

app.include_router(ws.router)
