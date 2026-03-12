import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import alerts, health, mesh, push, ws
from app.services.websocket_manager import ws_manager

logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger(__name__)

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
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api"

app.include_router(alerts.router, prefix=API_PREFIX)
app.include_router(push.router, prefix=API_PREFIX)
app.include_router(mesh.router, prefix=API_PREFIX)
app.include_router(health.router, prefix=API_PREFIX)

app.include_router(ws.router)

_PING_INTERVAL_SECONDS = 30


@app.on_event("startup")
async def _start_ws_ping() -> None:
    async def _ping_loop() -> None:
        while True:
            await asyncio.sleep(_PING_INTERVAL_SECONDS)
            if ws_manager.active_count:
                await ws_manager.broadcast_ping()

    asyncio.create_task(_ping_loop())
    logger.info("ESPAlert API iniciada")
