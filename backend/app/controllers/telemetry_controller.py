from backend.app.services.coreiot_service import coreiot_service


def get_latest_telemetry():
    return coreiot_service.get_latest_snapshot()


def get_history(range_hours: int):
    return coreiot_service.get_history(range_hours)
