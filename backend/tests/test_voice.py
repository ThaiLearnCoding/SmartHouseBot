from io import BytesIO


def test_text_turn_returns_assistant_result(client, monkeypatch):
    monkeypatch.setattr(
        "backend.app.routers.voice.process_text_turn",
        lambda text: {
            "transcript": text,
            "intent": "set_led",
            "response_text": "The LED is now on.",
            "audio_url": "/audio/reply.wav",
        },
    )

    response = client.post("/api/voice/text-turn", json={"text": "bat den"})

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "set_led"
    assert body["audio_url"] == "/audio/reply.wav"


def test_text_turn_rate_limit_kicks_in(client, monkeypatch):
    monkeypatch.setattr(
        "backend.app.routers.voice.get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "voice_rate_limit_count": 1,
                "voice_rate_limit_window_seconds": 60,
            },
        )(),
    )
    monkeypatch.setattr(
        "backend.app.routers.voice.process_text_turn",
        lambda text: {
            "transcript": text,
            "intent": "read_sensor",
            "response_text": "Current temperature is 28 degrees Celsius and humidity is 60 percent.",
            "audio_url": None,
        },
    )

    first = client.post("/api/voice/text-turn", json={"text": "doc nhiet do"})
    second = client.post("/api/voice/text-turn", json={"text": "doc nhiet do"})

    assert first.status_code == 200
    assert second.status_code == 429


def test_audio_turn_accepts_upload_and_passes_suffix(client, monkeypatch):
    captured = {}

    def fake_audio_turn(suffix, content):
        captured["suffix"] = suffix
        captured["content"] = content
        return {
            "transcript": "turn on led",
            "intent": "set_led",
            "response_text": "The LED is now on.",
            "audio_url": "/audio/voice.wav",
        }

    monkeypatch.setattr("backend.app.routers.voice.process_audio_turn", fake_audio_turn)

    response = client.post(
        "/api/voice/audio-turn",
        files={"audio": ("voice.webm", BytesIO(b"fake-audio"), "audio/webm")},
    )

    assert response.status_code == 200
    assert captured["suffix"] == ".webm"
    assert captured["content"] == b"fake-audio"


def test_audio_turn_requires_file(client):
    response = client.post("/api/voice/audio-turn")

    assert response.status_code == 422
