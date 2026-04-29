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


def test_history_falls_back_to_latest_reading_when_range_is_empty():
    service = CoreIotService()

    class FakeClient:
        def __init__(self):
            self.calls = []

        def fetch_timeseries(self, **kwargs):
            self.calls.append(kwargs)
            if "start_ts" in kwargs:
                return {}
            return {
                "temperature": [{"value": "32.56", "ts": 1775057162232}],
                "humidity": [{"value": "62.51", "ts": 1775057162232}],
            }

    fake_client = FakeClient()
    service._get_client = lambda: fake_client

    history = service.get_history(24)

    assert len(history.points) == 1
    assert history.points[0].temperature == 32.56
    assert history.points[0].humidity == 62.51
    assert len(fake_client.calls) == 2
