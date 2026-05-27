import asyncio
import logging
import time
from typing import Optional

from backend.app.core.config import get_settings
from backend.app.db.repository import storage_repository
from backend.app.services.coreiot_service import coreiot_service


logger = logging.getLogger(__name__)

_task: Optional[asyncio.Task] = None


async def _sampler_loop(interval_seconds: int) -> None:
    while True:
        try:
            snapshot = await asyncio.to_thread(coreiot_service.get_latest_snapshot)
            collected_at_ms = int(time.time() * 1000)
            await asyncio.to_thread(
                storage_repository.save_telemetry_snapshot,
                snapshot,
                collected_at_ms,
            )
        except Exception:
            logger.warning("Telemetry sampler tick failed", exc_info=True)

        await asyncio.sleep(interval_seconds)


def start_telemetry_sampler() -> None:
    global _task

    settings = get_settings()
    if not settings.database_enabled or not settings.database_telemetry_sampler_enabled:
        return
    if _task is not None and not _task.done():
        return

    interval = max(1, settings.database_telemetry_interval_seconds)
    _task = asyncio.create_task(_sampler_loop(interval))
    logger.info("Telemetry sampler started (every %ss)", interval)


async def stop_telemetry_sampler() -> None:
    global _task

    if _task is None:
        return

    _task.cancel()
    try:
        await _task
    except asyncio.CancelledError:
        pass
    _task = None
