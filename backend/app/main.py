from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.core.security import apply_security
from backend.app.middleware.request_context import RequestContextMiddleware
from backend.app.routers import devices, health, telemetry, voice


configure_logging()

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)
apply_security(app, settings)
app.add_middleware(RequestContextMiddleware)
app.mount("/audio", StaticFiles(directory=settings.generated_audio_dir), name="audio")

app.include_router(health.router)
app.include_router(devices.router)
app.include_router(telemetry.router)
app.include_router(voice.router)


frontend_dist_dir = settings.frontend_dist_dir

if frontend_dist_dir.exists():
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
