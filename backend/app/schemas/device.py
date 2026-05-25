from typing import Optional

from pydantic import BaseModel, Field


class DeviceStatus(BaseModel):
    led_on: Optional[bool] = None
    servo_angle: Optional[int] = None
    active_devices: int = 0
    status_source: str = "unknown"


class LedRequest(BaseModel):
    on: bool


class ServoRequest(BaseModel):
    angle: int = Field(ge=0, le=180)


class DeviceCommandResponse(BaseModel):
    ok: bool
    message: str
    status: DeviceStatus
