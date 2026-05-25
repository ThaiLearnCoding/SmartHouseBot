def test_latest_telemetry_returns_sensor_and_device_status(client, monkeypatch):
    monkeypatch.setattr(
        "backend.app.routers.telemetry.get_latest_telemetry",
        lambda: {
            "temperature": 28.5,
            "humidity": 62.1,
            "collected_at": 1714290000000,
            "device_status": {
                "led_on": True,
                "servo_angle": 30,
                "active_devices": 2,
                "status_source": "telemetry",
            },
        },
    )

    response = client.get("/api/telemetry/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["temperature"] == 28.5
    assert body["device_status"]["active_devices"] == 2


def test_history_uses_range_query_and_returns_points(client, monkeypatch):
    captured = {}

    def fake_get_history(range_hours):
        captured["range_hours"] = range_hours
        return {
            "range_hours": range_hours,
            "sample_interval_seconds": 60,
            "points": [
                {
                    "timestamp": 1714290000000,
                    "iso_time": "2026-04-28T09:00:00+00:00",
                    "temperature": 28.5,
                    "humidity": 62.1,
                }
            ],
        }

    monkeypatch.setattr("backend.app.routers.telemetry.get_history", fake_get_history)

    response = client.get("/api/telemetry/history", params={"range_hours": 48})

    assert response.status_code == 200
    assert captured["range_hours"] == 48
    assert response.json()["points"][0]["humidity"] == 62.1


def test_history_rejects_invalid_range(client):
    response = client.get("/api/telemetry/history", params={"range_hours": 0})

    assert response.status_code == 422
