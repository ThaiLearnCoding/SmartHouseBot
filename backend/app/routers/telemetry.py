from typing import Optional

from fastapi import APIRouter, Query

from backend.app.controllers.telemetry_controller import get_history, get_latest_telemetry
from backend.app.core.config import get_settings
from backend.app.schemas.telemetry import TelemetryHistoryResponse, TelemetryLatestResponse


router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


@router.get("/latest", response_model=TelemetryLatestResponse)
def read_latest():
    return get_latest_telemetry()


@router.get("/history", response_model=TelemetryHistoryResponse)
def read_history(
    range_hours: Optional[int] = Query(default=None, ge=1, le=72),
):
    settings = get_settings()
    hours = range_hours if range_hours is not None else settings.telemetry_default_hours
    return get_history(hours)
