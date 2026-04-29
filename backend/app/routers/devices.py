from fastapi import APIRouter, Request

from backend.app.controllers.device_controller import get_device_status, set_led, set_servo
from backend.app.core.config import get_settings
from backend.app.core.rate_limit import build_rate_limit_key, rate_limiter
from backend.app.schemas.device import DeviceCommandResponse, DeviceStatus, LedRequest, ServoRequest


router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("/status", response_model=DeviceStatus)
def read_device_status():
    return get_device_status()


@router.post("/led", response_model=DeviceCommandResponse)
def update_led(payload: LedRequest, request: Request):
    settings = get_settings()
    rate_limiter.enforce(
        build_rate_limit_key(request, "devices-led"),
        settings.device_rate_limit_count,
        settings.device_rate_limit_window_seconds,
    )
    return set_led(payload.on)


@router.post("/servo", response_model=DeviceCommandResponse)
def update_servo(payload: ServoRequest, request: Request):
    settings = get_settings()
    rate_limiter.enforce(
        build_rate_limit_key(request, "devices-servo"),
        settings.device_rate_limit_count,
        settings.device_rate_limit_window_seconds,
    )
    return set_servo(payload.angle)
