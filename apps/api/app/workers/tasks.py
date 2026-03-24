import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import update

from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.alert import Alert
from app.models.enums import AlertStatus

try:
    from app.connectors.aemet import AEMETConnector
except ImportError:
    AEMETConnector = None

try:
    from app.connectors.ign import IGNConnector
except ImportError:
    IGNConnector = None

try:
    from app.connectors.dgt import DGTConnector
except ImportError:
    DGTConnector = None

try:
    from app.connectors.meteoalarm import MeteoalarmConnector
except ImportError:
    MeteoalarmConnector = None

logger = logging.getLogger(__name__)

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def async_fetch_aemet():
    async with AsyncSessionLocal() as db:
        if AEMETConnector is not None:
            connector = AEMETConnector(db)
            await connector.fetch()

async def async_fetch_ign():
    async with AsyncSessionLocal() as db:
        if IGNConnector is not None:
            connector = IGNConnector(db)
            await connector.fetch()

async def async_fetch_dgt():
    async with AsyncSessionLocal() as db:
        if DGTConnector is not None:
            connector = DGTConnector(db)
            await connector.fetch()

async def async_fetch_meteoalarm():
    async with AsyncSessionLocal() as db:
        if MeteoalarmConnector is not None:
            connector = MeteoalarmConnector(db)
            await connector.fetch()

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
        logger.info(f"Alertas expiradas automáticamentes: {result.rowcount}")

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

@celery_app.task(name="app.workers.tasks.expire_alerts_task", ignore_result=True)
def expire_alerts_task():
    try:
        run_async(async_expire_alerts())
    except Exception as e:
        logger.error(f"Error expiracion: {e}")
