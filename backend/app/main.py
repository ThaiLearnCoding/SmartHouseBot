from pathlib import Path

import asyncio
import logging

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.core.security import apply_security
from backend.app.db.database import init_db
from backend.app.middleware.request_context import RequestContextMiddleware
from backend.app.routers import audit, devices, health, telemetry, voice
from backend.app.services.telemetry_sampler import start_telemetry_sampler, stop_telemetry_sampler
from backend.app.services.tts_service import tts_service
from backend.app.services.whisper_service import whisper_service


configure_logging()

logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)
apply_security(app, settings)
app.add_middleware(RequestContextMiddleware)
app.mount("/audio", StaticFiles(directory=settings.generated_audio_dir), name="audio")

app.include_router(health.router)
app.include_router(devices.router)
app.include_router(telemetry.router)
app.include_router(voice.router)
app.include_router(audit.router)


async def _warmup_pho_whisper() -> None:
    try:
        await asyncio.to_thread(whisper_service.warmup)
        logger.info("PhoWhisper model warmup completed")
    except Exception:
        logger.exception("PhoWhisper warmup failed")


@app.on_event("startup")
async def startup() -> None:
    current_settings = get_settings()
    init_db(current_settings)
    start_telemetry_sampler()
    await asyncio.to_thread(tts_service.cleanup_old_files)
    if current_settings.pho_whisper_warmup and whisper_service.available:
        asyncio.create_task(_warmup_pho_whisper())


@app.on_event("shutdown")
async def shutdown() -> None:
    await stop_telemetry_sampler()


frontend_dist_dir = settings.frontend_dist_dir

if settings.serve_frontend and frontend_dist_dir.exists():
    assets_dir = frontend_dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def serve_index():
        return FileResponse(frontend_dist_dir / "index.html")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        requested_path = frontend_dist_dir / full_path
        if requested_path.exists() and requested_path.is_file():
            return FileResponse(requested_path)
        return FileResponse(frontend_dist_dir / "index.html")
else:

    @app.get("/")
    def root():
        return {
            "message": "Smart Home Dashboard API is running.",
            "frontend_built": False,
            "frontend_path": str(frontend_dist_dir),
        }
