from types import SimpleNamespace


def test_health_reports_dependency_status(client, monkeypatch):
    monkeypatch.setattr("backend.app.routers.health.whisper_service", SimpleNamespace(available=True))
    monkeypatch.setattr("backend.app.routers.health.tts_service", SimpleNamespace(available=False))

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["whisper_available"] is True
    assert body["tts_available"] is False
    assert "ollama_model" in body
