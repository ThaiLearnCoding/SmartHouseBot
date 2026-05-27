from backend.app.services.coreiot_service import CoreIotService


def test_device_status_uses_coreiot_attributes():
    service = CoreIotService()

    status = service._build_device_status(
        attributes={
            "LED_02": True,
            "servoAngle": "90",
        },
    )

    assert status.led_on is True
    assert status.servo_angle == 90
    assert status.active_devices == 2
    assert status.status_source == "coreiot_attributes"


def test_device_status_falls_back_to_telemetry_keys():
    service = CoreIotService()

    status = service._build_device_status(
        raw={
            "ledState": [{"value": "false", "ts": 1714290000000}],
            "servoAngle": [{"value": "45", "ts": 1714290000000}],
        },
    )

    assert status.led_on is False
    assert status.servo_angle == 45
    assert status.active_devices == 1
    assert status.status_source == "telemetry"


def test_set_servo_converts_coreiot_timeout_to_502():
    service = CoreIotService()

    class FailingClient:
        def send_rpc(self, _method, _params):
            raise TimeoutError("timed out")

    service._get_client = lambda: FailingClient()

    try:
        service.set_servo(90)
    except Exception as exc:
        assert exc.status_code == 502
        assert "CoreIoT servo command failed" in exc.detail
    else:
        raise AssertionError("Expected CoreIoT failure to raise")


def test_history_query_divides_range_into_576_buckets():
    service = CoreIotService()
    buckets = service._history_bucket_count()

    for hours, expected_interval_ms in [
        (6, 6 * 3600 * 1000 // buckets),
        (12, 12 * 3600 * 1000 // buckets),
        (24, 24 * 3600 * 1000 // buckets),
        (48, 48 * 3600 * 1000 // buckets),
    ]:
        start = 1_000_000
        end = start + hours * 3600 * 1000
        interval_ms, bucket_count = service._history_query(start, end)
        assert bucket_count == buckets
        assert interval_ms == expected_interval_ms


def test_history_falls_back_to_latest_reading_when_range_is_empty():
    service = CoreIotService()
    recent_ts = int(__import__("time").time() * 1000) - 60_000

    class FakeClient:
        def __init__(self):
            self.calls = []

        def fetch_timeseries(self, **kwargs):
            self.calls.append(kwargs)
            if kwargs.get("limit") == 1:
                return {
                    "temperature": [{"value": "32.56", "ts": recent_ts}],
                    "humidity": [{"value": "62.51", "ts": recent_ts}],
                }
            return {}

    fake_client = FakeClient()
    service._get_client = lambda: fake_client

    history = service.get_history(24)

    assert history.sample_interval_seconds == 150
    assert len(history.points) == 576
    populated = [point for point in history.points if point.temperature is not None]
    assert len(populated) == 1
    assert populated[0].temperature == 32.56
    assert populated[0].humidity == 62.51
    assert fake_client.calls[0]["order_by"] == "ASC"
    assert fake_client.calls[0]["agg"] == "AVG"
    assert fake_client.calls[0]["interval_ms"] == 150_000
    assert fake_client.calls[0]["limit"] == 576
    assert fake_client.calls[-1]["order_by"] == "DESC"


def test_align_grid_covers_requested_window():
    service = CoreIotService()
    start = 1_000_000
    end = start + 24 * 3600 * 1000
    interval_ms, bucket_count = service._history_query(start, end)
    points = [
        service._build_history_points(
            {
                "temperature": [{"value": str(20 + index), "ts": start + index * 5000}],
                "humidity": [{"value": str(50 + index), "ts": start + index * 5000}],
            }
        )[0]
        for index in range(100)
    ]

    aligned = service._align_points_to_grid(points, start, end, interval_ms, bucket_count)

    assert len(aligned) == 576
    assert aligned[0].timestamp == start
    assert aligned[-1].timestamp <= end
