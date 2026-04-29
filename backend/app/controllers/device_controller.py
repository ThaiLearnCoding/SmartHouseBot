from backend.app.schemas.device import DeviceCommandResponse
from backend.app.services.coreiot_service import coreiot_service


def get_device_status():
    return coreiot_service.get_device_status()


def set_led(on: bool) -> DeviceCommandResponse:
    status = coreiot_service.set_led(on)
    return DeviceCommandResponse(
        ok=True,
        message=f"LED turned {'on' if on else 'off'}.",
        status=status,
    )


def set_servo(angle: int) -> DeviceCommandResponse:
    status = coreiot_service.set_servo(angle)
    current_angle = status.servo_angle if status.servo_angle is not None else angle
    return DeviceCommandResponse(
        ok=True,
        message=f"Servo moved to {current_angle} degrees.",
        status=status,
    )
