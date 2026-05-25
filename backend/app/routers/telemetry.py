from fastapi import APIRouter, Query

from backend.app.controllers.telemetry_controller import get_history, get_latest_telemetry
from backend.app.schemas.telemetry import TelemetryHistoryResponse, TelemetryLatestResponse


router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


@router.get("/latest", response_model=TelemetryLatestResponse)
def read_latest():
    return get_latest_telemetry()


@router.get("/history", response_model=TelemetryHistoryResponse)
def read_history(range_hours: int = Query(default=24, ge=1, le=72)):
    return get_history(range_hours)
