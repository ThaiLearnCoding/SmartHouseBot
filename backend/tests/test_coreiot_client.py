import requests

from backend.app.clients.coreiot_client import CoreIotClient
from backend.app.services import coreiot_service as coreiot_service_module
from backend.app.services.coreiot_service import CoreIotService


def test_get_client_reuses_cached_instance(monkeypatch):
    class CountingClient:
        instances = 0

        def __init__(self, **_kwargs):
            CountingClient.instances += 1

    monkeypatch.setattr(coreiot_service_module, "CoreIotClient", CountingClient)

    service = CoreIotService()
    service.settings.coreiot_email = "user@example.com"
    service.settings.coreiot_password = "secret"
    service.settings.coreiot_device_id = "device-id"

    service._get_client()
    service._get_client()

    assert CountingClient.instances == 1


def test_get_client_recreates_when_credentials_change(monkeypatch):
    class CountingClient:
        instances = 0

        def __init__(self, **_kwargs):
            CountingClient.instances += 1

    monkeypatch.setattr(coreiot_service_module, "CoreIotClient", CountingClient)

    service = CoreIotService()
    service.settings.coreiot_email = "user@example.com"
    service.settings.coreiot_password = "secret"
    service.settings.coreiot_device_id = "device-id"
    service._get_client()

    service.settings.coreiot_password = "new-secret"
    service._get_client()

    assert CountingClient.instances == 2


def test_client_retries_once_after_unauthorized(monkeypatch):
    client = CoreIotClient(
        email="user@example.com",
        password="secret",
        device_id="device-id",
    )
    client.token = "expired-token"
    calls = {"login": 0, "request": 0}

    class FakeResponse:
        def __init__(self, status_code, payload=None):
            self.status_code = status_code
            self._payload = payload or {}

        def json(self):
            return self._payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(response=self)

    def fake_login():
        calls["login"] += 1
        client.token = "fresh-token"

    def fake_request(method, url, timeout=None, **kwargs):
        calls["request"] += 1
        if calls["request"] == 1:
            return FakeResponse(401)
        return FakeResponse(200, {"ok": True})

    monkeypatch.setattr(client, "login", fake_login)
    monkeypatch.setattr(client._session, "request", fake_request)

    result = client.send_rpc("setLED02", True)

    assert result == {"ok": True}
    assert calls["login"] == 1
    assert calls["request"] == 2


def test_login_only_on_first_api_call(monkeypatch):
    client = CoreIotClient(
        email="user@example.com",
        password="secret",
        device_id="device-id",
    )
    calls = {"login": 0, "request": 0}

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {}

        @staticmethod
        def raise_for_status():
            return None

    def fake_login():
        calls["login"] += 1
        client.token = "token"

    def fake_request(method, url, timeout=None, **kwargs):
        calls["request"] += 1
        return FakeResponse()

    monkeypatch.setattr(client, "login", fake_login)
    monkeypatch.setattr(client._session, "request", fake_request)

    client.fetch_timeseries(keys="temperature")
    client.fetch_attributes("ledState")

    assert calls["login"] == 1
    assert calls["request"] == 2
