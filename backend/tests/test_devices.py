from fastapi import HTTPException


def test_get_device_status_returns_payload(client, monkeypatch):
    monkeypatch.setattr(
        "backend.app.routers.devices.get_device_status",
        lambda: {
            "led_on": True,
            "servo_angle": 45,
            "active_devices": 2,
            "status_source": "telemetry",
        },
    )

    response = client.get("/api/devices/status")

    assert response.status_code == 200
    assert response.json()["servo_angle"] == 45


def test_update_led_enforces_rate_limit(client, monkeypatch):
    monkeypatch.setattr(
        "backend.app.routers.devices.get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "device_rate_limit_count": 1,
                "device_rate_limit_window_seconds": 60,
            },
        )(),
    )
    monkeypatch.setattr(
        "backend.app.routers.devices.set_led",
        lambda on: {
            "ok": True,
            "message": f"LED turned {'on' if on else 'off'}.",
            "status": {
                "led_on": on,
                "servo_angle": None,
                "active_devices": 1 if on else 0,
                "status_source": "cache",
            },
        },
    )

    first = client.post("/api/devices/led", json={"on": True})
    second = client.post("/api/devices/led", json={"on": False})

    assert first.status_code == 200
    assert second.status_code == 429


def test_update_servo_validates_angle(client):
    response = client.post("/api/devices/servo", json={"angle": 181})

    assert response.status_code == 422


def test_update_servo_surfaces_backend_errors(client, monkeypatch):
    def fail_set_servo(_):
        raise HTTPException(status_code=502, detail="CoreIoT unavailable")

    monkeypatch.setattr("backend.app.routers.devices.set_servo", fail_set_servo)

    response = client.post("/api/devices/servo", json={"angle": 90})

    assert response.status_code == 502
    assert response.json()["detail"] == "CoreIoT unavailable"
