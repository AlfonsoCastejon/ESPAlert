"""Tareas periódicas de Celery: recolección de alertas y expiración."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, update

from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.alert import Alert
from app.models.enums import AlertStatus
from app.services.alert_service import upsert_alert

try:
    from app.connectors.aemet import AemetConnector
except ImportError:
    AemetConnector = None

try:
    from app.connectors.ign import IGNConnector
except ImportError:
    IGNConnector = None

try:
    from app.connectors.dgt import DgtConnector
except ImportError:
    DgtConnector = None

try:
    from app.connectors.meteoalarm import MeteoAlarmConnector
except ImportError:
    MeteoAlarmConnector = None

logger = logging.getLogger(__name__)

def run_async(coro):
    """Ejecuta una corutina en un event loop nuevo (Celery no tiene uno propio)."""
    from app.database import engine
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        # Libera el pool para que las conexiones no queden atadas al loop cerrado
        try:
            loop.run_until_complete(engine.dispose())
        except Exception:
            pass
        loop.close()

async def _fetch_and_persist(connector_cls, name: str):
    """Descarga alertas del conector indicado y las persiste en BD."""
    if connector_cls is None:
        return
    connector = connector_cls()
    alerts = await connector.fetch()
    if not alerts:
        return
    async with AsyncSessionLocal() as db:
        for alert_data in alerts:
            await upsert_alert(db, alert_data)
        await db.commit()
    logger.info(f"{name}: {len(alerts)} alertas persistidas.")

async def async_fetch_aemet():
    await _fetch_and_persist(AemetConnector, "AEMET")

async def async_fetch_ign():
    await _fetch_and_persist(IGNConnector, "IGN")

async def async_fetch_dgt():
    await _fetch_and_persist(DgtConnector, "DGT")

async def async_fetch_meteoalarm():
    await _fetch_and_persist(MeteoAlarmConnector, "MeteoAlarm")

async def async_expire_alerts():
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        stmt = (
            update(Alert)
            .where(Alert.expires_at < now)
            .where(Alert.status != AlertStatus.EXPIRED)
            .values(status=AlertStatus.EXPIRED)
        )
        result = await db.execute(stmt)
        await db.commit()
        logger.info(f"Alertas expiradas automáticamente: {result.rowcount}")

@celery_app.task(name="app.workers.tasks.fetch_aemet_task", ignore_result=True)
def fetch_aemet_task():
    try:
        run_async(async_fetch_aemet())
    except Exception as e:
        logger.error(f"Error AEMET: {e}")

@celery_app.task(name="app.workers.tasks.fetch_ign_task", ignore_result=True)
def fetch_ign_task():
    try:
        run_async(async_fetch_ign())
    except Exception as e:
        logger.error(f"Error IGN: {e}")

@celery_app.task(name="app.workers.tasks.fetch_dgt_task", ignore_result=True)
def fetch_dgt_task():
    try:
        run_async(async_fetch_dgt())
    except Exception as e:
        logger.error(f"Error DGT: {e}")

@celery_app.task(name="app.workers.tasks.fetch_meteoalarm_task", ignore_result=True)
def fetch_meteoalarm_task():
    try:
        run_async(async_fetch_meteoalarm())
    except Exception as e:
        logger.error(f"Error Meteoalarm: {e}")

async def async_purge_old_alerts():
    """Elimina alertas cuyo created_at tiene más de 14 días."""
    async with AsyncSessionLocal() as db:
        limite = datetime.now(timezone.utc) - timedelta(days=14)
        stmt = delete(Alert).where(Alert.created_at < limite)
        result = await db.execute(stmt)
        await db.commit()
        logger.info(f"Alertas purgadas (>21 días): {result.rowcount}")


@celery_app.task(name="app.workers.tasks.expire_alerts_task", ignore_result=True)
def expire_alerts_task():
    try:
        run_async(async_expire_alerts())
    except Exception as e:
        logger.error(f"Error expiracion: {e}")


@celery_app.task(name="app.workers.tasks.purge_old_alerts_task", ignore_result=True)
def purge_old_alerts_task():
    try:
        run_async(async_purge_old_alerts())
    except Exception as e:
        logger.error(f"Error purgando alertas antiguas: {e}")
