"""Base connector class shared by all data-source connectors."""

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AlertSource, FetchStatus
from app.models.fetch_log import FetchLog


class BaseConnector(ABC):
    """Abstract base connector that manages FetchLog lifecycle around data ingestion."""

    source: AlertSource

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    async def fetch(self) -> None:
        """Run a full fetch cycle, wrapping results in a FetchLog entry."""
        log = FetchLog(
            source=self.source,
            status=FetchStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
        self.db.add(log)
        await self.db.flush()

        start_time = datetime.now(UTC)
        alerts_fetched = 0
        alerts_new = 0
        error_message = None

        try:
            alerts_fetched, alerts_new = await self._fetch()
            log.status = FetchStatus.SUCCESS
        except Exception as exc:
            self.logger.error("Error fetching from %s: %s", self.source.value, exc)
            log.status = FetchStatus.FAILURE
            error_message = str(exc)

        duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        log.finished_at = datetime.now(UTC)
        log.alerts_fetched = alerts_fetched
        log.alerts_new = alerts_new
        log.duration_ms = duration_ms
        log.error_message = error_message
        await self.db.commit()

    @abstractmethod
    async def _fetch(self) -> tuple[int, int]:
        """Perform the actual data fetch.

        Returns
        -------
        tuple[int, int]
            A tuple of (alerts_fetched, alerts_new).
        """

