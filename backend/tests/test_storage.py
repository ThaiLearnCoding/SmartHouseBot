from backend.app.db.repository import storage_repository
from backend.app.schemas.device import DeviceStatus
from backend.app.schemas.telemetry import TelemetryLatestResponse, TelemetryPoint


def test_save_and_read_telemetry_snapshot():
    snapshot = TelemetryLatestResponse(
        temperature=27.5,
        humidity=50.0,
        collected_at=1710000000000,
        device_status=DeviceStatus(
            led_on=False,
            servo_angle=0,
            active_devices=0,
            status_source="coreiot_attributes",
        ),
    )

    storage_repository.save_telemetry_snapshot(snapshot)
    storage_repository.save_telemetry_snapshot(snapshot)

    points = storage_repository.get_telemetry_history(
        start_ts_ms=1709990000000,
        end_ts_ms=1710010000000,
        limit=10,
    )

    assert len(points) == 1
    assert points[0].temperature == 27.5
    assert points[0].humidity == 50.0


def test_save_periodic_snapshots_with_custom_timestamp():
    snapshot = TelemetryLatestResponse(
        temperature=27.5,
        humidity=50.0,
        collected_at=1710000000000,
        device_status=DeviceStatus(
            led_on=False,
            servo_angle=0,
            active_devices=0,
            status_source="coreiot_attributes",
        ),
    )

    storage_repository.save_telemetry_snapshot(snapshot, 1710000001000)
    storage_repository.save_telemetry_snapshot(snapshot, 1710000002000)

    points = storage_repository.get_telemetry_history(
        start_ts_ms=1710000000000,
        end_ts_ms=1710000003000,
        limit=10,
    )

    assert len(points) == 2
    assert points[0].timestamp == 1710000001000
    assert points[1].timestamp == 1710000002000


def test_log_device_command_and_voice_interaction():
    storage_repository.log_device_command("led", {"on": True}, source="web", success=True)
    storage_repository.log_device_command("servo", {"angle": 90}, source="voice", success=True)
    storage_repository.log_voice_interaction(
        "bat den",
        "set_led",
        "Den LED hien da bat.",
        success=True,
    )

    from backend.app.db.database import get_connection

    device_rows = get_connection().execute("SELECT COUNT(*) AS c FROM device_commands").fetchone()
    voice_rows = get_connection().execute("SELECT COUNT(*) AS c FROM voice_logs").fetchone()

    assert device_rows["c"] == 2
    assert voice_rows["c"] == 1
