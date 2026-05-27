from typing import List, Optional

from pydantic import BaseModel

from backend.app.schemas.device import DeviceStatus


class TelemetryPoint(BaseModel):
    timestamp: int
    iso_time: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None


class TelemetryLatestResponse(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    collected_at: Optional[int] = None
    device_status: DeviceStatus


class TelemetryHistoryResponse(BaseModel):
    range_hours: int
    sample_interval_seconds: int
    points: List[TelemetryPoint]
